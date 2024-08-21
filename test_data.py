import requests
import argparse

def validate_data(data):
    errors = 0    
    for item in data:
        # Validar campos principais
        required_fields = [
            '_id', 'contact_id', 'country', 'date_started', 'date_submitted',
            'id', 'ip_address', 'language', 'referer', 'session_id', 'status', 'survey_data', 'user_agent'
        ]
        for field in required_fields:
            if field not in item or item[field] == "":
                print(f"Erro: O campo '{field}' está faltando ou vazio.")
                errors += 1

        # Validar survey_data
        survey_data = item['survey_data']
        for question_id, question_data in survey_data.items():
            # Validar question_data
            if 'question' not in question_data or not question_data['question']:
                print(f"Erro: A pergunta com ID '{question_id}' está faltando ou vazia.")
                errors += 1
             
            # Validar answer
            answer = question_data.get('answer', None)
            if question_data.get('type') == "RANK":
                if answer is not None and isinstance(answer, list) and len(answer) != 3:
                    print(f"Erro: 'answer' é uma lista com {len(answer)} item e precisa ter 3 itens para a pergunta com ID '{question_id}' quando 'type' é 'RANK' e answer null.")
                    errors += 1
            else:
                if answer is not None and not isinstance(answer, str):
                    print(f"Erro: 'answer' deve ser uma string para a pergunta com ID '{question_id}' quando 'type' não é 'RANK'.")
                    errors += 1

            # Validar comments
            comments = question_data.get('comments', None)
            if comments is not None and not isinstance(comments, str):
                print(f"Erro: 'comments' deve ser uma string ou null para a pergunta com ID '{question_id}'.")
                errors += 1

    print("Validação concluída com sucesso." if errors == 0 else f"Total de erros encontrados: {errors}")
    return errors == 0

def fetch_data_from_api(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Levanta um erro para respostas de erro HTTP
        return response.json()  # Retorna o JSON como um dicionário
    except requests.RequestException as e:
        print(f"Erro ao fazer requisição: {e}")
        return None

def main(id_item):
    # URL da API com o ID passado como parâmetro
    api_url = f'http://localhost:5000/data/{id_item}'

    # Coletar e validar os dados
    response_data = fetch_data_from_api(api_url)
    if response_data:
        data = response_data.get('data', [])
        validate_data([data])  # Passa os dados para validação

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Valida dados de uma API com base no ID fornecido.')
    parser.add_argument('id_item', type=int, help='ID do item para buscar os dados na API')

    args = parser.parse_args()
    main(args.id_item)
