# Use uma imagem base do Python
FROM python:3.11

# Define o diretório de trabalho
WORKDIR /app

# Copia o arquivo de requirements e instala as dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código da aplicação
COPY . .

# Copia o script de inicialização
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Define o script de inicialização como ponto de entrada
ENTRYPOINT ["/app/entrypoint.sh"]

