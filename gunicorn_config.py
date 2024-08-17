# gunicorn_config.py

# Número de trabalhadores
workers = 4

# Tipo de worker
worker_class = 'gunicorn.workers.ggevent'

# Endereço de escuta
bind = '0.0.0.0:8000'

# Timeout
timeout = 120

# Registra logs
accesslog = 'access.log'
errorlog = 'error.log'

# Nível de log
loglevel = 'info'