from django.core.management.base import BaseCommand
from django.apps import apps

class Command(BaseCommand):
    help = 'Inspect a specific model instance and print each field type, value repr, and decoding information. Usage: manage.py inspect_instance <app_label>.<ModelName> <id> [--fix]'

    def add_arguments(self, parser):
        parser.add_argument('model', help='Model in the form app_label.ModelName')
        parser.add_argument('id', type=int, help='Primary key of the instance to inspect')
        parser.add_argument('--fix', action='store_true', help='Attempt safe fix for bytes fields (decode with replace and save)')

    def handle(self, *args, **options):
        model_label = options['model']
        pk = options['id']
        fix = options['fix']

        try:
            app_label, model_name = model_label.split('.')
        except ValueError:
            self.stderr.write('Model must be specified as app_label.ModelName')
            return

        model = apps.get_model(app_label, model_name)
        if model is None:
            self.stderr.write(f'Model {model_label} not found')
            return

        try:
            obj = model.objects.get(pk=pk)
        except model.DoesNotExist:
            self.stderr.write(f'{model_label} with id={pk} does not exist')
            return

        self.stdout.write(self.style.NOTICE(f'Inspecting {model_label} id={pk}'))
        problematic = []

        for field in model._meta.fields:
            name = field.name
            try:
                val = getattr(obj, name)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Field {name}: access error: {e}'))
                problematic.append((name, 'access-error', str(e)))
                continue

            if isinstance(val, (bytes, bytearray)):
                self.stdout.write(self.style.ERROR(f'Field {name}: bytes ({len(val)} bytes)'))
                # try decode
                try:
                    decoded = val.decode('utf-8')
                    self.stdout.write(self.style.SUCCESS(f'  decodes as UTF-8: {decoded[:200]!r}'))
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'  decode error: {e}'))
                    try:
                        decoded = val.decode('utf-8', 'replace')
                        self.stdout.write(self.style.NOTICE(f'  decode-replace preview: {decoded[:200]!r}'))
                    except Exception as e2:
                        self.stdout.write(self.style.ERROR(f'  decode-replace also failed: {e2}'))
                problematic.append((name, 'bytes', None))
            elif isinstance(val, str):
                # show if contains replacement char
                if '\ufffd' in val:
                    self.stdout.write(self.style.WARNING(f'Field {name}: str (contains replacement char) repr: {val[:200]!r}'))
                    problematic.append((name, 'replacement-char', val[:200]))
                else:
                    self.stdout.write(f'Field {name}: str repr preview: {val[:200]!r}')
            elif val is None:
                self.stdout.write(f'Field {name}: None')
            else:
                self.stdout.write(f'Field {name}: {type(val)} repr: {repr(val)[:200]}')

        self.stdout.write(self.style.NOTICE(f'Inspection complete. Problematic fields: {len(problematic)}'))

        if fix and problematic:
            self.stdout.write(self.style.NOTICE('Attempting fixes for bytes fields...'))
            changed = False
            for name, ptype, _ in problematic:
                try:
                    val = getattr(obj, name)
                except Exception:
                    continue
                if isinstance(val, (bytes, bytearray)):
                    try:
                        safe = val.decode('utf-8')
                    except Exception:
                        safe = val.decode('utf-8', 'replace')
                    setattr(obj, name, safe)
                    changed = True
                    self.stdout.write(self.style.SUCCESS(f'Field {name}: decoded and set (replace)'))
            if changed:
                obj.save()
                self.stdout.write(self.style.SUCCESS('Saved instance with fixes'))
            else:
                self.stdout.write(self.style.WARNING('No fields fixed'))
