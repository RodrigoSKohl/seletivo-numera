import os

# Obtém a porta da variável de ambiente, com valor padrão 8000 se não estiver definida
web_port = os.getenv('WEB_PORT', '8000')
bind = f"0.0.0.0:{web_port}"
loglevel = "info"
preload = True  # Precarrega a aplicação antes de fork

worker_class = 'gevent'
workers = 4
worker_connections = 250
max_requests = 500
timeout = 120
graceful_timeout = 30
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190