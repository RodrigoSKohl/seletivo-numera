#!/bin/sh
# entrypoint.sh

# Adiciona logs para verificar a execução
echo "Executando init_db.py..."

# Executa o script Python e redireciona logs para um arquivo
python /app/init_db.py >> /app/init_db.log 2>&1
if [ $? -eq 0 ]; then
    echo "Script init_db.py executado com sucesso. Iniciando Gunicorn."
else
    echo "Erro ao executar init_db.py. Verifique /app/init_db.log para detalhes."
    exit 1
fi

# Inicia o Gunicorn
exec gunicorn -c gunicorn_config.py app:app
