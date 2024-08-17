import requests
import xmltodict
import json
import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()


# Função para extrair campos comuns de uma entrada
def extract_common_fields(entry):
    return {
        "id": entry.get("id"),
        "contact_id": entry.get("contact_id"),
        "status": entry.get("status"),
        "date_submitted": entry.get("date_submitted"),
        "session_id": entry.get("session_id"),
        "language": entry.get("language"),
        "date_started": entry.get("date_started"),
        "ip_address": entry.get("ip_address"),
        "referer": entry.get("referer"),
        "user_agent": entry.get("user_agent"),
        "country": entry.get("country"),
    }


# Carregar os dados dos três modelos
response_1 = requests.get('https://numera-case.web.app/v1/survey/1/answers')
dict_1 = response_1.json()

response_2 = requests.get('https://numera-case.web.app/v1/survey/2/answers')
dict_2 = response_2.json()

response_3 = requests.get('https://numera-case.web.app/v1/survey/3/answers')
dict_3 = xmltodict.parse(response_3.text)

# Mapeia perguntas para IDs para usar na estrutura 2
question_id_map = {}

# Processando a primeira estrutura e criando o mapeamento
for entry in dict_1["data"]:
    for question_id, question_data in entry["survey_data"].items():
        question_text = question_data.get("question", "")
        question_id_map[question_text] = question_id

# Processando a terceira estrutura e adicionando ao mapeamento
for entry in dict_3["survey_answer"]["data"]["item"]:
    for survey_item in entry["survey_data"]["item"]:
        question_text = survey_item.get("question", "")
        question_id = survey_item["id"]
        if question_text not in question_id_map:
            question_id_map[question_text] = question_id

# Estrutura Final
combined_data = {}

# Processando a primeira estrutura e ajustando o formato
for entry in dict_1["data"]:
    combined_data[entry["id"]] = {
        **extract_common_fields(entry), 
        "survey_data": {}
    }
    
    for question_id, question_data in entry["survey_data"].items():
        survey_data_entry = {
            "question": question_data.get("question", None),
            "answer": question_data.get("answer", None),
            "comments": question_data.get("comments", None)
        }
        
        combined_data[entry["id"]]["survey_data"][question_id] = survey_data_entry

# Processando a segunda estrutura e adicionando IDs
for entry in dict_2["data"]:
    survey_id = entry["id"]
    
    # Inicializa a entrada no dicionário combinado, caso não exista
    if survey_id not in combined_data:
        combined_data[survey_id] = {
            **extract_common_fields(entry), 
            "survey_data": {}
        }
    
    # Itera sobre as perguntas e respostas
    for question, answer in entry.items():
        if question not in ["id", "contact_id", "status", "date_submitted", "session_id", "language", "date_started", "ip_address", "referer", "user_agent", "country"]:
            question_id = question_id_map.get(question, question)
            try:
                # Tenta carregar a resposta como JSON, se possível
                answer_data = json.loads(answer)
                if isinstance(answer_data, list):
                    # Ajusta o formato da resposta para o padrão desejado
                    formatted_answer = [{"id": item["id"], "option": item["option"], "rank": item["rank"]} for item in answer_data]
                    combined_data[survey_id]["survey_data"][question_id] = {
                        "answer": formatted_answer,
                        "comments": entry.get(f"{question}_comments", None)  # Garante que comments seja criado  se não existir
                    }
                else:
                    combined_data[survey_id]["survey_data"][question_id] = {
                        "question": question,
                        "answer": answer_data,
                        "comments": entry.get(f"{question}_comments", None)  # Garante que comments seja criado  se não existir
                    }
            except json.JSONDecodeError:
                # Se a resposta não for JSON, usa como está
                combined_data[survey_id]["survey_data"][question_id] = {
                    "question": question,
                    "answer": answer,
                    "comments": entry.get(f"{question}_comments", None)  # Garante que comments seja criado  se não existir
                }

# Processando a terceira estrutura e adicionando ao dicionário combinado
for entry in dict_3["survey_answer"]["data"]["item"]:
    survey_id = entry["id"]
    if survey_id not in combined_data:
        combined_data[survey_id] = {
            **extract_common_fields(entry), 
            "survey_data": {}
        }
    
    for survey_item in entry["survey_data"]["item"]:
        answer = survey_item.get("answer", None)
        if isinstance(answer, dict):
            answer = answer.get("item", answer)
        
        # Cria o dicionário para a entrada de dados
        survey_data_entry = {
            "question": survey_item["question"],
            "answer": answer,
            "comments": survey_item.get("comments", None)  # Garante que comments seja criado  se não existir
        }
        
        combined_data[survey_id]["survey_data"][survey_item["id"]] = survey_data_entry

mongo_uri = os.getenv('MONGO_URI')
mongo_dbname = os.getenv('MONGO_DBNAME')
mongo_collection = os.getenv('MONGO_COLLECTION')

if not mongo_uri or not mongo_dbname or not mongo_collection:
    raise ValueError("Uma ou mais variáveis de ambiente não estão definidas.")

# Conectar ao MongoDB
client = MongoClient(mongo_uri)
db = client[mongo_dbname]  # Certifique-se de que mongo_dbname é uma string
collection = db[mongo_collection]  # Certifique-se de que mongo_collection é uma string

# Inserir os dados combinados na coleção, removendo o campo "id" do início de cada entrada
cleaned_data = []
for k, v in combined_data.items():
    # Cria um novo documento com _id como chave principal e remove 'id' do documento
    document = {
        "_id": k,  # Utiliza 'k' como valor do campo '_id'
        **{key: value for key, value in v.items() if key != 'id'}  # Remove o campo 'id'
    }
    cleaned_data.append(document)

collection.insert_many(cleaned_data)

print("Os dados combinados foram salvos no MongoDB.")
