#!/bin/sh
# entrypoint.sh

# Adiciona logs para verificar a execução
echo "Verificando se o script init_db.py deve ser executado..."

if [ ! -f /app/init_db_done ]; then
    echo "Executando init_db.py..."
    python /app/init_db.py >> /app/init_db.log 2>&1
    if [ $? -eq 0 ]; then
        echo "Script init_db.py executado com sucesso."
        touch /app/init_db_done
    else
        echo "Erro ao executar init_db.py. Verifique /app/init_db.log para detalhes."
        exit 1
    fi
else
    echo "init_db.py já foi executado. Iniciando Gunicorn."
fi

# Inicia o Gunicorn
exec gunicorn -c gunicorn_config.py app:app