from django.test import TestCase, Client, override_settings


class RefreshRateLimitMiddlewareTests(TestCase):
	def setUp(self):
		self.client = Client()

	@override_settings(DEBUG=True)
	def test_refresh_rate_limit_blocks_after_limit(self):
		url = '/api/token/refresh/'

		# Send 5 POST requests - should not be throttled by middleware
		responses = [self.client.post(url, data={'refresh': 'dummy'}) for _ in range(5)]
		for resp in responses:
			# Middleware should not block the first 5; views may return 400 due to invalid body,
			# but should not be 429. So assert status_code != 429.
			self.assertNotEqual(resp.status_code, 429, f"Unexpected 429 on initial requests: got {resp.status_code}")

		# 6th request should be throttled and return 429
		resp6 = self.client.post(url, data={'refresh': 'dummy'})
		self.assertEqual(resp6.status_code, 429)
		self.assertIn('Request was throttled', resp6.json().get('detail', ''))
