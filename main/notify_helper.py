import subprocess, sys, os

_NOTIFY_SCRIPT = os.path.join(os.path.dirname(__file__), 'notify_worker.py')


def notify_in_background(message):
    subprocess.Popen(
        [sys.executable, _NOTIFY_SCRIPT, message],
        close_fds=True,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0,
    )
