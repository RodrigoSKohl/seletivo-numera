from flask import Flask, jsonify
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import secrets
from data_process import fetch_data, process_and_save_data
import sys
import fcntl


load_dotenv()

def create_app():
    # Configurações do Flask
    app = Flask(__name__)
    app.config['SECRET_KEY'] = secrets.token_hex(16)  # Gera uma nova chave secreta a cada inicialização

    def get_mongo_client():
        """Cria e retorna uma instância do MongoClient."""
        mongo_ip = os.getenv('MONGO_IP')
        mongo_port = os.getenv('MONGO_PORT')
        mongo_dbname = os.getenv('MONGO_DBNAME')
        mongo_root_user = os.getenv('MONGO_ROOT_USER')
        mongo_root_password = os.getenv('MONGO_ROOT_PASSWORD')
        mongo_uri = f"mongodb://{mongo_root_user}:{mongo_root_password}@{mongo_ip}:{mongo_port}/{mongo_dbname}?authSource=admin"
        
        # Configura o pool de conexões
        client = MongoClient(mongo_uri, maxPoolSize=50)
        return client

    # Inicializa o MongoDB
    mongo_client = get_mongo_client()
    db = mongo_client.get_database()
    collection = db[os.getenv('MONGO_COLLECTION')]

    def save_to_mongo(data):
        """Salva os dados no MongoDB."""
        try:
            collection.insert_many(data)
            print("Os dados combinados foram salvos no MongoDB.")
        except Exception as e:
            print(f"Erro ao salvar os dados no MongoDB: {e}")

    def fetch_and_process_data_if_collection_missing():
        """Executa o fetch e o processamento dos dados se a coleção não existir."""
        lock_file = '/tmp/mongo_data_lock'
        with open(lock_file, 'w') as f:
            try:
                # Adquire o lock no arquivo
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                if os.getenv('MONGO_COLLECTION') not in db.list_collection_names():
                    print(f"A coleção '{os.getenv('MONGO_COLLECTION')}' não existe. Executando fetch e processamento de dados.")
                    dict_1, dict_2, dict_3 = fetch_data()
                    if dict_1 and dict_2 and dict_3:
                        try:
                            # Processa os dados e obtém o cleaned_data
                            cleaned_data = process_and_save_data(dict_1, dict_2, dict_3)
                            # Salva os dados processados no MongoDB
                            save_to_mongo(cleaned_data)
                        except Exception:
                            print("Erro ao processar e salvar os dados.")
                            sys.exit(1)
                    else:
                        print("Erro ao buscar os dados. O processamento não será executado.")
                        sys.exit(1)
                else:
                    print(f"A coleção '{os.getenv('MONGO_COLLECTION')}' já existe. Fetch e processamento de dados não são necessários.")
            except BlockingIOError:
                print("Outro processo já está executando a função de inicialização.")
                

    def serialize_document(document):
        """Converte um documento MongoDB para um formato JSON serializável."""
        if document is None:
            return None
        document['_id'] = str(document['_id'])  # Converte ObjectId para string
        return document

    @app.route('/')
    def index():
        return (
            "<h1>API simples com FLASK e MongoDB</h1><br>"
            "Acesse <strong><a href='/data'>/data</a></strong> para solicitar todos os dados do banco de dados.<br>"
            "Acesse <strong><a href='/data/#id'>/data/id</a></strong>> para solicitar um dado específico pelo ID."
        )

    @app.route('/data', methods=['GET'])
    def get_data():
        data = list(collection.find({}))
        # Aplica a função de serialização a cada documento
        serialized_data = [serialize_document(doc) for doc in data]
        # Envolve os dados em um objeto com a chave 'data'
        return jsonify({"data": serialized_data})

    @app.route('/data/<string:id>', methods=['GET'])
    def get_single_data(id):
        try:
            # Busque pelo campo 'id' em vez de '_id' do MongoDB
            data = collection.find_one({"id": id})
            serialized_data = serialize_document(data)
            return jsonify({"data": serialized_data}) if serialized_data else ("Not Found", 404)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # Inicialização
    fetch_and_process_data_if_collection_missing()

    return app

# Cria a aplicação
app = create_app()

if __name__ == '__main__':
    app.run(log_level='info')
