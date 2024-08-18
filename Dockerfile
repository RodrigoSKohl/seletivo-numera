# Use uma imagem base do Python
FROM python:3.11

# Define o diretório de trabalho
WORKDIR /app

# Copia o arquivo de requirements e instala as dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código da aplicação
COPY . .

# Define o comando para iniciar o Gunicorn
CMD ["gunicorn", "-c", "gunicorn_config.py", "app:app"]
