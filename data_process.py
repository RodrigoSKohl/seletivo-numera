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

    # Mapeia perguntas para IDs e tipos para usar na estrutura 2
    question_map = {}

    # Processando a primeira estrutura e criando o mapeamento
    for entry in dict_1["data"]:
        for question_id, question_data in entry["survey_data"].items():
            question_text = question_data.get("question", "")
            question_map[question_text] = {
                "id": question_id,
                "type": question_data.get("type", None)
            }

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
                "type": question_data.get("type", None),
            }

            # Adiciona comments se não for uma string vazia ou null
            comments = question_data.get("comments", "")
            if comments not in ("", None):
                survey_data_entry["comments"] = comments

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

    # Processando a segunda estrutura e adicionando IDs e tipos
    for entry in dict_2["data"]:
        survey_id = entry["id"]

        if survey_id not in combined_data:
            combined_data[survey_id] = {
                **extract_common_fields(entry),
                "survey_data": {}
            }

        for question, answer in entry.items():
            if question not in ["id", "contact_id", "status", "date_submitted", "session_id", "language", "date_started", "ip_address", "referer", "user_agent", "country"]:
                question_id = question_map.get(question, {}).get("id", question)
                question_type = question_map.get(question, {}).get("type", None)
                question_text = question_map.get(question, {}).get("question", question)
                
                try:
                    answer_data = json.loads(answer)
                    if isinstance(answer_data, list):
                        formatted_answer = [{"id": item["id"], "option": item["option"], "rank": item["rank"]} for item in answer_data]
                        combined_data[survey_id]["survey_data"][question_id] = {
                            "answer": formatted_answer,
                            "question": question_text,
                            "type": question_type
                        }
                    else:
                        combined_data[survey_id]["survey_data"][question_id] = {
                            "answer": answer_data,
                            "question": question_text,
                            "type": question_type
                        }
                except json.JSONDecodeError:
                    combined_data[survey_id]["survey_data"][question_id] = {
                        "answer": None if answer == "" else answer,
                        "question": question_text,
                        "type": question_type
                    }
                
                # Adiciona comments se não for uma string vazia ou null
                comments = entry.get(f"{question}_comments", "")
                if comments not in ("", None):
                    combined_data[survey_id]["survey_data"][question_id]["comments"] = comments


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

            survey_data_entry = {
                "question": survey_item["question"],
                "answer": answer,
                "type": question_map.get(survey_item["question"], {}).get("type", None)
            }

            # Adiciona comments se não for uma string vazia ou null
            comments = survey_item.get("comments", "")
            if comments not in ("", None):
                survey_data_entry["comments"] = comments

            combined_data[survey_id]["survey_data"][survey_item["id"]] = survey_data_entry

        # Tratamento dos dados para inserir no MongoDB
        cleaned_data = []
        for k, v in combined_data.items():
            try:
                object_id = ObjectId(k)
            except Exception:
                object_id = ObjectId()

            document = {
                "_id": object_id,
                "id": k,
                **{key: value for key, value in v.items()}
            }
            cleaned_data.append(document)

    return cleaned_data