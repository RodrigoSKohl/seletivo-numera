from flask import Flask, jsonify
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import secrets
import logging

load_dotenv()

def create_app():
    # Configurações do Flask
    app = Flask(__name__)
    app.config['SECRET_KEY'] = secrets.token_hex(16)  # Gera uma nova chave secreta a cada inicialização

    def get_mongo_client():
        """Cria e retorna uma instância do MongoClient."""
        mongo_ip = os.getenv('MONGO_IP')
        mongo_port = os.getenv('MONGODB_PORT_NUMBER')
        mongo_dbname = os.getenv('MONGO_DBNAME')
        mongo_user = os.getenv('MONGO_USER')
        mongo_password = os.getenv('MONGO_PASSWORD')
        mongo_uri = f"mongodb://{mongo_user}:{mongo_password}@{mongo_ip}:{mongo_port}/{mongo_dbname}"
        
        # Configura o pool de conexões
        client = MongoClient(mongo_uri, maxPoolSize=50)
        return client

    # Inicializa o MongoDB
    mongo_client = get_mongo_client()
    db = mongo_client.get_database()
    collection = db[os.getenv('MONGO_COLLECTION')]
                
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

    return app

# Cria a aplicação
app = create_app()

if __name__ == '__main__':
    # Configura o nível de log
    logging.basicConfig(level=logging.INFO)
    
    # Inicia a aplicação
    app.run()
