import multiprocessing
import os

# Bind to 0.0.0.0:8000 by default
bind = os.environ.get('GUNICORN_BIND', '0.0.0.0:8000')

# Number of worker processes
# A good rule of thumb is 2-4 x number of CPU cores
workers = int(os.environ.get('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))

# Worker class - use gevent for better concurrency
worker_class = os.environ.get('GUNICORN_WORKER_CLASS', 'gevent')

# Maximum number of simultaneous clients
worker_connections = int(os.environ.get('GUNICORN_WORKER_CONNECTIONS', 1000))

# Maximum number of requests a worker will process before restarting
max_requests = int(os.environ.get('GUNICORN_MAX_REQUESTS', 1000))
max_requests_jitter = int(os.environ.get('GUNICORN_MAX_REQUESTS_JITTER', 50))

# Process name
proc_name = 'remotehive'

# Timeout for worker processes (seconds)
timeout = int(os.environ.get('GUNICORN_TIMEOUT', 30))

# Restart workers that have been silent for this many seconds
graceful_timeout = int(os.environ.get('GUNICORN_GRACEFUL_TIMEOUT', 30))

# The maximum number of pending connections
backlog = int(os.environ.get('GUNICORN_BACKLOG', 2048))

# Log level
loglevel = os.environ.get('GUNICORN_LOG_LEVEL', 'info')

# Access log format
accesslog = os.environ.get('GUNICORN_ACCESS_LOG', '-')
access_log_format = os.environ.get(
    'GUNICORN_ACCESS_LOG_FORMAT',
    '%({X-Forwarded-For}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(L)s'
)

# Error log
errorlog = os.environ.get('GUNICORN_ERROR_LOG', '-')

# Preload application code before worker processes are forked
preload_app = os.environ.get('GUNICORN_PRELOAD_APP', 'true').lower() in ['true', '1', 't']

# Daemon mode
daemon = False

# SSL configuration (if needed)
# keyfile = '/path/to/key.pem'
# certfile = '/path/to/cert.pem'

# Hook functions
def on_starting(server):
    """
    Called just before the master process is initialized.
    """
    pass

def on_reload(server):
    """
    Called before a worker is reloaded.
    """
    pass

def post_fork(server, worker):
    """
    Called just after a worker has been forked.
    """
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def pre_fork(server, worker):
    """
    Called just prior to forking a worker.
    """
    pass

def when_ready(server):
    """
    Called when the server is ready to receive requests.
    """
    server.log.info("Server is ready. Spawning workers...")

def worker_int(worker):
    """
    Called when a worker receives SIGINT or SIGQUIT.
    """
    worker.log.info("Worker received interrupt signal")

def worker_abort(worker):
    """
    Called when a worker receives SIGABRT.
    """
    worker.log.info("Worker received abort signal")

def worker_exit(server, worker):
    """
    Called when a worker exits.
    """
    server.log.info("Worker exited (pid: %s)", worker.pid)
