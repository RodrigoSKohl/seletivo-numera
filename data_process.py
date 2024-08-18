import requests
import xmltodict
import json
from bson import ObjectId


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

# Função para buscar os dados dos três modelos
def fetch_data():
    try:
        # Carregar os dados dos três modelos
        response_1 = requests.get('https://numera-case.web.app/v1/survey/1/answers')
        response_1.raise_for_status()  # Verifica se a requisição foi bem-sucedida
        dict_1 = response_1.json()

        response_2 = requests.get('https://numera-case.web.app/v1/survey/2/answers')
        response_2.raise_for_status()
        dict_2 = response_2.json()

        response_3 = requests.get('https://numera-case.web.app/v1/survey/3/answers')
        response_3.raise_for_status()
        dict_3 = xmltodict.parse(response_3.text)

        # Retornar os dados apenas se todas as requisições forem bem-sucedidas
        return dict_1, dict_2, dict_3

    except requests.exceptions.RequestException as e:
        print(f"Erro na requisição: {e}")
        return None, None, None
    except ValueError as e:
        print(f"Erro ao processar os dados: {e}")
        return None, None, None

# Função para padronizar e salvar os dados
def process_and_save_data(dict_1, dict_2, dict_3):

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
                "comments": question_data.get("comments", None) if question_data.get("comments", "") != "" else None
            }
            
            # Ajusta o formato da resposta para o padrão desejado
            if isinstance(survey_data_entry["answer"], list):
                formatted_answer = []
                for item in survey_data_entry["answer"]:
                    if isinstance(item, dict):
                        formatted_answer.append({
                            "id": item.get("id", ""),
                            "option": item.get("option", ""),
                            "rank": item.get("rank", "")
                        })
                    else:
                        formatted_answer.append({
                            "id": "",
                            "option": item,
                            "rank": ""
                        })
                survey_data_entry["answer"] = formatted_answer
            
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

        # Tratamento dos dados para inserir no MongoDB
        cleaned_data = []
        for k, v in combined_data.items():
            try:
                # Tenta converter o valor de k para ObjectId
                object_id = ObjectId(k)
            except Exception:
                # Se a conversão falhar, gere um novo ObjectId
                object_id = ObjectId()
            
            # Cria um novo documento com _id como ObjectId e mantém o campo 'id'
            document = {
                "_id": object_id,  # Converte o valor de k para ObjectId
                "id": k,  # Mantém o campo 'id' original
                **{key: value for key, value in v.items()}  # Mantém os outros campos
            }
            cleaned_data.append(document)
    
    return cleaned_data
