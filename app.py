from flask import Flask, jsonify, request
from flask_pymongo import PyMongo
import os
from dotenv import load_dotenv
from bson import ObjectId
import secrets
from pymongo.errors import ServerSelectionTimeoutError
from data_process import fetch_data, process_and_save_data


# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Configurações do Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)  # Gera uma nova chave secreta a cada inicialização

#  URI do MongoDB
mongo_ip = os.getenv('MONGO_IP')
mongo_port = os.getenv('MONGO_PORT')
mongo_user = os.getenv('MONGO_USER')
mongo_password = os.getenv('MONGO_PASSWORD')
mongo_dbname = os.getenv('MONGO_DBNAME')
mongo_collection = os.getenv('MONGO_COLLECTION')
# Verifica se todas as variáveis de ambiente estão definidas
if not all([mongo_ip, mongo_port, mongo_user, mongo_password, mongo_dbname, mongo_collection]):
    raise ValueError("Uma ou mais variáveis de ambiente não estão definidas.")

mongo_uri = f"mongodb://{mongo_user}:{mongo_password}@{mongo_ip}:{mongo_port}/{mongo_dbname}"

app.config['MONGO_URI'] = mongo_uri

# Inicializa o PyMongo com o construtor
mongo = PyMongo(app)

# Configura a coleção
db = mongo.db
collection = db[mongo_collection]

def test_mongo_connection():
    uri = app.config['MONGO_URI']
    try:
        # Tenta acessar uma coleção para verificar a conexão
        mongo.db.command('ping')
        print("Conexão com o MongoDB estabelecida com sucesso!")
    except ServerSelectionTimeoutError as e:
        print(f"Erro de conexão com o MongoDB ({uri}): {e}")
        exit(1)  # Encerra o programa com código de erro


# Função para salvar os dados no MongoDB
def save_to_mongo(data):
    """Salva os dados no MongoDB."""
    try:
        collection.insert_many(data)
        print("Os dados combinados foram salvos no MongoDB.")
    except Exception as e:
        print(f"Erro ao salvar os dados no MongoDB: {e}")

# Verifica se a coleção existe e executa o fetch e o processamento dos dados se necessário
def fetch_and_process_data_if_collection_missing():
    """Executa o fetch e o processamento dos dados se a coleção não existir."""
    if mongo_collection not in db.list_collection_names():
        print(f"A coleção '{mongo_collection}' não existe. Executando fetch e processamento de dados.")
        dict_1, dict_2, dict_3 = fetch_data()
        if dict_1 and dict_2 and dict_3:
            # Processa os dados e obtém o cleaned_data
            cleaned_data = process_and_save_data(dict_1, dict_2, dict_3)
            # Salva os dados processados no MongoDB
            save_to_mongo(cleaned_data)
        else:
            print("Erro ao buscar os dados. O processamento não será executado.")
            exit(1)  # Encerra o programa com código de erro
    else:
        print(f"A coleção '{collection}' já existe. Fetch e processamento de dados não são necessários.")


def serialize_document(document):
    """Converte um documento MongoDB para um formato JSON serializável."""
    if document is None:
        return None
    document['_id'] = str(document['_id'])  # Converte ObjectId para string
    return document

@app.route('/')
def index():
    return (
        "API simples com FLASK e MongoDB\n"
        "Acesse /data para solicitar todos os dados do banco de dados.\n"
        "Acesse /data/<id> para solicitar um dado específico pelo ID.\n"
        "Métodos disponíveis:\n"
        "GET /data - Retorna todos os dados.\n"
        "POST /data - Adiciona um novo dado.\n"
        "GET /data/<id> - Retorna um dado específico pelo ID.\n"
        "PUT /data/<id> - Atualiza um dado específico pelo ID.\n"
        "DELETE /data/<id> - Remove um dado específico pelo ID."
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


@app.route('/data', methods=['POST'])
def add_data():
    json_data = request.json
    result = collection.insert_one(json_data)
    return jsonify({"inserted_id": str(result.inserted_id)}), 201

@app.route('/data/<string:id>', methods=['PUT'])
def update_data(id):
    try:
        json_data = request.json
        result = collection.update_one({"_id": ObjectId(id)}, {"$set": json_data})
        if result.matched_count:
            return jsonify({"status": "updated"}), 200
        else:
            return jsonify({"status": "not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/data/<string:id>', methods=['DELETE'])
def delete_data(id):
    try:
        result = collection.delete_one({"_id": ObjectId(id)})
        if result.deleted_count:
            return jsonify({"status": "deleted"}), 200
        else:
            return jsonify({"status": "not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    test_mongo_connection()  # Testa a conexão antes de iniciar o servidor
    fetch_and_process_data_if_collection_missing() # Executa o fetch e o processamento se a coleção não existir
    app.run(debug=True)
