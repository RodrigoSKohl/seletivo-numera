import os
import sys
import pymongo
from dotenv import load_dotenv
from data_process import fetch_data, process_and_save_data

# Carregar variáveis de ambiente
load_dotenv()

# Armazenar variáveis de ambiente em variáveis locais
MONGO_IP = os.getenv('MONGO_IP')
MONGO_PORT = os.getenv('MONGODB_PORT_NUMBER')
MONGO_DBNAME = os.getenv('MONGO_DBNAME')
MONGO_ROOT_USER = os.getenv('MONGO_INITDB_ROOT_USERNAME')
MONGO_ROOT_PASSWORD = os.getenv('MONGO_INITDB_ROOT_PASSWORD')
MONGO_USER = os.getenv('MONGO_USER')
MONGO_PASSWORD = os.getenv('MONGO_PASSWORD')
MONGO_COLLECTION = os.getenv('MONGO_COLLECTION')

def get_mongo_client():
    """Cria e retorna uma instância do MongoClient com a URI montada dinamicamente."""
    mongo_uri = f"mongodb://{MONGO_ROOT_USER}:{MONGO_ROOT_PASSWORD}@{MONGO_IP}:{MONGO_PORT}/{MONGO_DBNAME}?authsource=admin"
    
    # Configura o pool de conexões
    client = pymongo.MongoClient(mongo_uri, maxPoolSize=50)
    return client

def save_to_mongo(collection, data):
    """Salva os dados no MongoDB."""
    try:
        collection.insert_many(data)
        print("Os dados combinados foram salvos no MongoDB.")
    except Exception as e:
        print(f"Erro ao salvar os dados no MongoDB: {e}")

def create_mongo_user(client):
    db = client[MONGO_DBNAME]  # Use o banco de dados correto
    try:
        db.command("createUser", MONGO_USER, pwd=MONGO_PASSWORD,
                   roles=[{"role": "readWrite", "db": MONGO_DBNAME}])
        print(f"Usuário '{MONGO_USER}' criado com sucesso.")
    except pymongo.errors.OperationFailure as e:
        print(f"Erro ao criar usuário: {e}")
        sys.exit(1)

def fetch_and_process_data_if_collection_missing(db):
    """Executa o fetch e o processamento dos dados se a coleção não existir."""
    collection = db[MONGO_COLLECTION]

    if MONGO_COLLECTION not in db.list_collection_names():
        print(f"A coleção '{MONGO_COLLECTION}' não existe. Executando fetch e processamento de dados.")
        dict_1, dict_2, dict_3 = fetch_data()
        if dict_1 and dict_2 and dict_3:
            try:
                cleaned_data = process_and_save_data(dict_1, dict_2, dict_3)
                save_to_mongo(collection, cleaned_data)
            except Exception as e:
                print(f"Erro ao processar e salvar os dados: {e}")
                sys.exit(1)
        else:
            print("Erro ao buscar os dados. O processamento não será executado.")
            sys.exit(1)
    else:
        print(f"A coleção '{MONGO_COLLECTION}' já existe. Fetch e processamento de dados não são necessários.")

if __name__ == "__main__":
    # Cria o cliente MongoDB usando a URI montada
    client = get_mongo_client()
    db = client[MONGO_DBNAME]

    # Cria o usuário MongoDB
    create_mongo_user(client)

    # Executa a função de fetch e processamento de dados
    fetch_and_process_data_if_collection_missing(db)
