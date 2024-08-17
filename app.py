from flask import Flask, jsonify, request
from flask_pymongo import PyMongo
import os
from dotenv import load_dotenv
from bson import ObjectId
import secrets
from pymongo.errors import ServerSelectionTimeoutError

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

app = Flask(__name__)

# Configurações do Flask
app.config['SECRET_KEY'] = secrets.token_hex(16)  # Gera uma nova chave secreta a cada inicialização
app.config['MONGO_URI'] = os.getenv('MONGO_URI')

mongo = PyMongo(app)
db = mongo.db
collection = db[os.getenv('MONGO_COLLECTION')]  # Configura a coleção

def test_mongo_connection():
    uri = app.config['MONGO_URI']
    try:
        # Tenta acessar uma coleção para verificar a conexão
        mongo.db.command('ping')
        print("Conexão com o MongoDB estabelecida com sucesso!")
    except ServerSelectionTimeoutError as e:
        print(f"Erro de conexão com o MongoDB ({uri}): {e}")
        exit(1)  # Encerra o programa com código de erro

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
    return jsonify(data)

@app.route('/data', methods=['POST'])
def add_data():
    json_data = request.json
    result = collection.insert_one(json_data)
    return jsonify({"inserted_id": str(result.inserted_id)}), 201

@app.route('/data/<string:id>', methods=['GET'])
def get_single_data(id):
    try:
        data = collection.find_one({"_id": ObjectId(id)})
        return jsonify(data) if data else ("Not Found", 404)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
    app.run(debug=True)
