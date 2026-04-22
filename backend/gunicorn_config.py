"""
Configuración de Gunicorn para producción
"""

import multiprocessing
import os

# Número de workers (recomendado: 2-4 x número de CPUs)
workers = int(os.getenv("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))

# Clase de worker (Uvicorn para FastAPI async)
worker_class = "uvicorn.workers.UvicornWorker"

# Bind address
bind = os.getenv("GUNICORN_BIND", "0.0.0.0:8000")

# Timeout
timeout = int(os.getenv("GUNICORN_TIMEOUT", 120))

# Logging
accesslog = os.getenv("GUNICORN_ACCESS_LOG", "-")  # stdout
errorlog = os.getenv("GUNICORN_ERROR_LOG", "-")  # stderr
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")

# Preload app (mejora performance pero aumenta uso de memoria)
preload_app = True

# Max requests (previene memory leaks)
max_requests = int(os.getenv("GUNICORN_MAX_REQUESTS", 1000))
max_requests_jitter = int(os.getenv("GUNICORN_MAX_REQUESTS_JITTER", 50))

# Graceful timeout
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", 30))

# Keepalive
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", 5))
