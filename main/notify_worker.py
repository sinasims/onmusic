import os, sys, traceback
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
import django
django.setup()
try:
    from main.notifications import notify_admin
    notify_admin(sys.argv[1])
except Exception:
    traceback.print_exc()
