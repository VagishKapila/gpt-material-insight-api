after we updted 

[2025-10-26 21:08:30 +0000] [1] [ERROR] Worker (pid:2) exited with code 3
[2025-10-26 21:08:30 +0000] [1] [ERROR] Shutting down: Master
[2025-10-26 21:08:30 +0000] [1] [ERROR] Reason: Worker failed to boot.
[2025-10-26 21:08:33 +0000] [1] [INFO] Starting gunicorn 21.2.0
[2025-10-26 21:08:33 +0000] [1] [INFO] Listening at: http://0.0.0.0:8080 (1)
[2025-10-26 21:08:33 +0000] [1] [INFO] Using worker: sync
[2025-10-26 21:08:33 +0000] [2] [INFO] Booting worker with pid: 2
  File "/app/.venv/lib/python3.10/site-packages/gunicorn/app/wsgiapp.py", line 48, in load_wsgiapp
    return util.import_app(self.app_uri)
  File "/app/.venv/lib/python3.10/site-packages/gunicorn/util.py", line 371, in import_app
    mod = importlib.import_module(module)
/app/.venv/lib/python3.10/site-packages/fuzzywuzzy/fuzz.py:11: UserWarning: Using slow pure-python SequenceMatcher. Install python-Levenshtein to remove this warning
  warnings.warn('Using slow pure-python SequenceMatcher. Install python-Levenshtein to remove this warning')
[2025-10-26 21:08:34 +0000] [2] [ERROR] Exception in worker process
Traceback (most recent call last):
    worker.init_process()
  File "/app/.venv/lib/python3.10/site-packages/gunicorn/arbiter.py", line 609, in spawn_worker
  File "/app/.venv/lib/python3.10/site-packages/gunicorn/workers/base.py", line 134, in init_process
    self.load_wsgi()
  File "/app/.venv/lib/python3.10/site-packages/gunicorn/app/base.py", line 67, in wsgi
  File "/app/.venv/lib/python3.10/site-packages/gunicorn/workers/base.py", line 146, in load_wsgi
    self.wsgi = self.app.wsgi()
    self.callable = self.load()
  File "/app/.venv/lib/python3.10/site-packages/gunicorn/app/wsgiapp.py", line 58, in load
    return self.load_wsgiapp()
  File "/mise/installs/python/3.10.12/lib/python3.10/importlib/__init__.py", line 126, in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
  File "<frozen importlib._bootstrap>", line 1050, in _gcd_import
  File "<frozen importlib._bootstrap>", line 1027, in _find_and_load
  File "<frozen importlib._bootstrap>", line 1006, in _find_and_load_unlocked
  File "<frozen importlib._bootstrap>", line 688, in _load_unlocked
  File "<frozen importlib._bootstrap_external>", line 883, in exec_module
  File "<frozen importlib._bootstrap>", line 241, in _call_with_frames_removed
  File "/app/app.py", line 10, in <module>
    from utils.compare_scope_vs_log import (
ImportError: cannot import name 'load_scope_for_project' from 'utils.compare_scope_vs_log' (/app/utils/compare_scope_vs_log.py)
[2025-10-26 21:08:34 +0000] [2] [INFO] Worker exiting (pid: 2)
[2025-10-26 21:08:34 +0000] [1] [ERROR] Worker (pid:2) exited with code 3
[2025-10-26 21:08:34 +0000] [1] [ERROR] Shutting down: Master
[2025-10-26 21:08:34 +0000] [1] [ERROR] Reason: Worker failed to boot.
[2025-10-26 21:08:36 +0000] [1] [INFO] Starting gunicorn 21.2.0
[2025-10-26 21:08:36 +0000] [1] [INFO] Listening at: http://0.0.0.0:8080 (1)
[2025-10-26 21:08:36 +0000] [1] [INFO] Using worker: sync
[2025-10-26 21:08:36 +0000] [2] [INFO] Booting worker with pid: 2
/app/.venv/lib/python3.10/site-packages/fuzzywuzzy/fuzz.py:11: UserWarning: Using slow pure-python SequenceMatcher. Install python-Levenshtein to remove this warning
  warnings.warn('Using slow pure-python SequenceMatcher. Install python-Levenshtein to remove this warning')
[2025-10-26 21:08:37 +0000] [2] [ERROR] Exception in worker process
Traceback (most recent call last):
  File "/app/.venv/lib/python3.10/site-packages/gunicorn/arbiter.py", line 609, in spawn_worker
    worker.init_process()
  File "/app/.venv/lib/python3.10/site-packages/gunicorn/workers/base.py", line 134, in init_process
    self.load_wsgi()
  File "/app/.venv/lib/python3.10/site-packages/gunicorn/workers/base.py", line 146, in load_wsgi
    self.wsgi = self.app.wsgi()
  File "/app/.venv/lib/python3.10/site-packages/gunicorn/app/base.py", line 67, in wsgi
    self.callable = self.load()
  File "/app/.venv/lib/python3.10/site-packages/gunicorn/app/wsgiapp.py", line 58, in load
    return self.load_wsgiapp()
  File "/app/.venv/lib/python3.10/site-packages/gunicorn/app/wsgiapp.py", line 48, in load_wsgiapp
    return util.import_app(self.app_uri)
  File "/app/.venv/lib/python3.10/site-packages/gunicorn/util.py", line 371, in import_app
    mod = importlib.import_module(module)
  File "/mise/installs/python/3.10.12/lib/python3.10/importlib/__init__.py", line 126, in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
  File "<frozen importlib._bootstrap>", line 1050, in _gcd_import
  File "<frozen importlib._bootstrap>", line 1027, in _find_and_load
  File "<frozen importlib._bootstrap>", line 1006, in _find_and_load_unlocked
  File "<frozen importlib._bootstrap>", line 688, in _load_unlocked
  File "<frozen importlib._bootstrap_external>", line 883, in exec_module
  File "<frozen importlib._bootstrap>", line 241, in _call_with_frames_removed
  File "/app/app.py", line 10, in <module>
    from utils.compare_scope_vs_log import (
ImportError: cannot import name 'load_scope_for_project' from 'utils.compare_scope_vs_log' (/app/utils/compare_scope_vs_log.py)
[2025-10-26 21:08:37 +0000] [2] [INFO] Worker exiting (pid: 2)
[2025-10-26 21:08:37 +0000] [1] [ERROR] Worker (pid:2) exited with code 3
[2025-10-26 21:08:37 +0000] [1] [ERROR] Shutting down: Master
[2025-10-26 21:08:37 +0000] [1] [ERROR] Reason: Worker failed to boot.
[2025-10-26 21:08:39 +0000] [1] [INFO] Starting gunicorn 21.2.0
[2025-10-26 21:08:39 +0000] [1] [INFO] Listening at: http://0.0.0.0:8080 (1)
[2025-10-26 21:08:39 +0000] [2] [INFO] Booting worker with pid: 2
[2025-10-26 21:08:39 +0000] [1] [INFO] Using worker: sync
  File "/app/.venv/lib/python3.10/site-packages/gunicorn/app/wsgiapp.py", line 48, in load_wsgiapp
    return util.import_app(self.app_uri)
/app/.venv/lib/python3.10/site-packages/fuzzywuzzy/fuzz.py:11: UserWarning: Using slow pure-python SequenceMatcher. Install python-Levenshtein to remove this warning
  File "/app/.venv/lib/python3.10/site-packages/gunicorn/util.py", line 371, in import_app
    mod = importlib.import_module(module)
  warnings.warn('Using slow pure-python SequenceMatcher. Install python-Levenshtein to remove this warning')
[2025-10-26 21:08:40 +0000] [2] [ERROR] Exception in worker process
Traceback (most recent call last):
  File "/app/.venv/lib/python3.10/site-packages/gunicorn/arbiter.py", line 609, in spawn_worker
    worker.init_process()
  File "/app/.venv/lib/python3.10/site-packages/gunicorn/workers/base.py", line 134, in init_process
    self.load_wsgi()
  File "/app/.venv/lib/python3.10/site-packages/gunicorn/workers/base.py", line 146, in load_wsgi
    self.wsgi = self.app.wsgi()
  File "/app/.venv/lib/python3.10/site-packages/gunicorn/app/base.py", line 67, in wsgi
    self.callable = self.load()
  File "/app/.venv/lib/python3.10/site-packages/gunicorn/app/wsgiapp.py", line 58, in load
    return self.load_wsgiapp()
  File "<frozen importlib._bootstrap>", line 241, in _call_with_frames_removed
  File "/app/app.py", line 10, in <module>
  File "/mise/installs/python/3.10.12/lib/python3.10/importlib/__init__.py", line 126, in import_module
    from utils.compare_scope_vs_log import (
    return _bootstrap._gcd_import(name[level:], package, level)
ImportError: cannot import name 'load_scope_for_project' from 'utils.compare_scope_vs_log' (/app/utils/compare_scope_vs_log.py)
[2025-10-26 21:08:40 +0000] [2] [INFO] Worker exiting (pid: 2)
  File "<frozen importlib._bootstrap>", line 1050, in _gcd_import
  File "<frozen importlib._bootstrap>", line 1027, in _find_and_load
  File "<frozen importlib._bootstrap>", line 1006, in _find_and_load_unlocked
  File "<frozen importlib._bootstrap>", line 688, in _load_unlocked
  File "<frozen importlib._bootstrap_external>", line 883, in exec_module
[2025-10-26 21:08:40 +0000] [1] [ERROR] Worker (pid:2) exited with code 3
[2025-10-26 21:08:40 +0000] [1] [ERROR] Shutting down: Master
