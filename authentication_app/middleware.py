from django.core.cache import cache
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
import time


class RefreshRateLimitMiddleware(MiddlewareMixin):
    """Rate limit POST requests.

    By default this middleware applies to all POST requests. You can configure
    it with Django settings:

    REFRESH_RATE_LIMIT = {
        'LIMIT': 5,
        'WINDOW_SECONDS': 60,
        # if TARGET_PATHS is None or empty, middleware applies to all POSTs
        'TARGET_PATHS': None,  # list of path suffixes or exact paths
        'EXCLUDE_PATHS': None, # list of path suffixes to exclude
        'CACHE_KEY_PREFIX': 'rl:'
    }

    Uses Django cache. For production use a shared cache (Redis/Memcached).
    """

    def __init__(self, get_response=None):
        super().__init__(get_response)
        cfg = getattr(settings, 'REFRESH_RATE_LIMIT', {}) or {}
        self.limit = int(cfg.get('LIMIT', 5))
        self.window_seconds = int(cfg.get('WINDOW_SECONDS', 60))
        self.target_paths = cfg.get('TARGET_PATHS')
        self.exclude_paths = cfg.get('EXCLUDE_PATHS')
        self.cache_key_prefix = cfg.get('CACHE_KEY_PREFIX', 'rl:')

    def _get_client_ip(self, request):
        # Respect X-Forwarded-For when behind a proxy if present
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        if xff:
            # first in list is original client
            return xff.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')

    def process_request(self, request):
        # Only rate limit POST requests
        try:
            path = request.path
        except Exception:
            path = ''

        if request.method != 'POST':
            return None

        # Exclusion rules
        if self.exclude_paths:
            for ex in self.exclude_paths:
                if path.endswith(ex) or path == ex:
                    return None

        # Inclusion rules (if provided) else include all POSTs
        if self.target_paths:
            matched = False
            for tp in self.target_paths:
                if path.endswith(tp) or path == tp:
                    matched = True
                    break
            if not matched:
                return None

        ip = self._get_client_ip(request) or 'anonymous'
        cache_key = f"{self.cache_key_prefix}{ip}"
        data = cache.get(cache_key)

        now = int(time.time())
        if not data:
            # data = (count, window_start)
            cache.set(cache_key, (1, now), timeout=self.window_seconds)
            return None

        count, window_start = data

        if now - window_start < self.window_seconds:
            if count >= self.limit:
                # Too many requests
                return JsonResponse({'detail': 'Request was throttled. Expected available in %d seconds.' % (self.window_seconds - (now - window_start))}, status=429)
            else:
                cache.set(cache_key, (count + 1, window_start), timeout=self.window_seconds - (now - window_start))
                return None
        else:
            # window expired — reset
            cache.set(cache_key, (1, now), timeout=self.window_seconds)
            return None
