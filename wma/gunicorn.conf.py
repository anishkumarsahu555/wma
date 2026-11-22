"""Conservative process limits for a shared VPS; CLI worker/timeout flags still win."""
import os


def nonnegative(name, default):
    value = int(os.environ.get(name, default))
    if value < 0:
        raise ValueError(f'{name} must not be negative')
    return value


# Keep sync workers for compatibility with existing views and background threads.
workers = 1
worker_class = 'sync'
worker_tmp_dir = '/dev/shm' if os.path.isdir('/dev/shm') else None
max_requests = nonnegative('WEB_MAX_REQUESTS', 2000)
max_requests_jitter = nonnegative('WEB_MAX_REQUESTS_JITTER', 200)
graceful_timeout = 30
errorlog = '-'
