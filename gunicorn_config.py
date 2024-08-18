import os

# Obtém a porta da variável de ambiente, com valor padrão 8000 se não estiver definida
web_port = os.getenv('WEB_PORT', '8000')

bind = f"0.0.0.0:{web_port}"
workers = 4
timeout = 120
loglevel = "info"
preload = True  # Precarrega a aplicação antes de fork