"""Keep the retired transaction entry point fail-closed."""
import sys

print('Legacy transaction CLI retired. Use python -m line_backup_batch.daily --help.',
      file=sys.stderr)
raise SystemExit(64)
