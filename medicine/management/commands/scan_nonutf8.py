from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import transaction
import sys

class Command(BaseCommand):
    help = 'Scan CharField/TextField values across all models for non-UTF8 or bytes content. Use --fix to attempt a safe replace-decoding.'

    def add_arguments(self, parser):
        parser.add_argument('--fix', action='store_true', help='Attempt to fix found fields by decoding bytes with utf-8 (replace) and saving back.')
        parser.add_argument('--limit', type=int, default=0, help='Limit the number of records to inspect per model (0 = no limit)')

    def handle(self, *args, **options):
        fix = options['fix']
        limit = options['limit']
        models = apps.get_models()
        total_found = 0
        for model in models:
            model_name = f"{model._meta.app_label}.{model._meta.object_name}"
            text_fields = [f for f in model._meta.fields if f.get_internal_type() in ('CharField', 'TextField')]
            if not text_fields:
                continue

            qs = model.objects.all()
            if limit > 0:
                qs = qs[:limit]

            for obj in qs:
                for field in text_fields:
                    name = field.name
                    try:
                        val = getattr(obj, name)
                    except Exception as e:
                        # Accessing value may raise if DB driver chokes on decoding
                        self.stdout.write(self.style.WARNING(f"{model_name} id={getattr(obj, 'id', '?')} field={name} - access error: {e}"))
                        total_found += 1
                        continue

                    if isinstance(val, (bytes, bytearray)):
                        self.stdout.write(self.style.ERROR(f"{model_name} id={getattr(obj,'id', '?')} field={name} - bytes value"))
                        total_found += 1
                        if fix:
                            try:
                                safe = val.decode('utf-8')
                            except Exception:
                                safe = val.decode('utf-8', 'replace')
                            setattr(obj, name, safe)
                            try:
                                with transaction.atomic():
                                    obj.save()
                                self.stdout.write(self.style.SUCCESS(f"Fixed {model_name} id={getattr(obj,'id','?')} field={name} (bytes->utf8-replace)"))
                            except Exception as e:
                                self.stdout.write(self.style.ERROR(f"Failed to save {model_name} id={getattr(obj,'id','?')} : {e}"))

                    elif isinstance(val, str):
                        # Detect presence of replacement char � as a heuristic for prior repairs
                        if '\ufffd' in val:
                            self.stdout.write(self.style.WARNING(f"{model_name} id={getattr(obj,'id','?')} field={name} - contains replacement characters"))
                            total_found += 1

                    elif val is not None:
                        # non-str non-bytes unusual values
                        self.stdout.write(self.style.WARNING(f"{model_name} id={getattr(obj,'id','?')} field={name} - unexpected type {type(val)}"))
                        total_found += 1

        self.stdout.write(self.style.NOTICE(f"Scan complete. Issues found: {total_found}"))
        if total_found == 0:
            return
        if not fix:
            self.stdout.write("Run with --fix to attempt automatic safe fixes (decoding with replacement).")
