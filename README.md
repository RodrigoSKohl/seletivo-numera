[![Docker Image CI](https://github.com/RodrigoSKohl/seletivo_numera/actions/workflows/docker-image.yml/badge.svg)](https://github.com/RodrigoSKohl/seletivo_numera/actions/workflows/docker-image.yml)
# Processo seletivo Numera
## Desafio
#### Seu papel é desenvolver uma solução simples e eficaz para armazenar e disponibilizar os dados das pesquisas de forma centralizada, com a capacidade de acesso através de uma API em Python simples. 
 - Você deve consumir uma API disponibilizada para realizar a extração dos dados referente a várias pesquisas realizadas pela empresa.
- Para simular a variedade de serviços de formulários online utilizados pela empresa, cada endpoint possui um formato diferente dos dados,  Devendo assim padronizar as informações da melhor forma possível.

### Requisitos:
1. Armazenamento Centralizado: Criar um sistema que extraia, apenas 1 vez, as respostas das pesquisas e armazene de forma organizada em um banco de dados
de sua preferência.
2. API em Python: Desenvolver uma API em Python extremamente simples que permita o acesso aos dados armazenados.
3. Simplicidade e Eficiência: Priorizar uma solução simples, clara e organizada.

### Entregáveis Esperados:
1. Código-fonte da solução desenvolvida em um repositório git de sua preferência de forma pública.
2. Instruções para implantação e configuração da solução em um ambiente de produção.


# SOLUÇÃO
### Armazenamento Centralizado
Para o armazenamento centralizado eu escolhi o banco de dados não relacional **MongoDB**, pela estrutura dinamica dos dados baseada e BSON, modelo de dados orientado a documentos que simplificam consultas em APIs. Ao realizar os req do desafio e manipular os dados, adicionei um _id de objeto baseado no id original, porém no controller da API executei um método de busca pela entrada do id, visto que um ObjectID não é um método de busca conveniente para esse desafio. Por padrão ele usa UTF-8 como charset.
### API em Python
Para a [API](app.py) em Python utilizei **Flask** com **Gunicorn** para o ambiente de produção. A escolha foi pela simplicidade, não optei por outros mais robustos como FasAPI e Django pela simplicidade do projeto.

Não optei por usar algum **ODM**, pois para o projeto o plugin do Flask para Mongo já supriu as necessidades.

### Simplicidade e eficácia
Criei um [script](data_process.py) a parte para coleta de dados, tentei simplificar ao máximo a modelagem dos dados para seguir em um padrão limpo, porém sem deixar de remover informações que possam ser importantes. As verificações se a collection se encontram no banco não necessitando executar o mesmo script, foram centralizada no arquivo de execução da [API](app.py)

Para a coleta de dados usei a biblioteca nativa do Python, json e para o xml a xmltodict. Nos requests para consumir a API da empresa usei a biblioteca request. O arquivo de processamento se baseia em duas funções que eu importo no arquivo de API. 

A primeira funão `fetch_data`  realiza o request dos 3 links passados no desafio e adiciona eles nas variáveis como dicionários, no request dos dados no formato xml, utilizo a função `xmltodict.parse` específica para retornar os dados em formato texto.

A segunda função `process_and_save_data`, padroniza os dados para este formato que decidi escolher(existe uma função adicional onde adicioneis todas entradas que pretendo manter):

```JSON
{
  "data": [
    {
      "_id": "",
      "contact_id": "",
      "country": "",
      "date_started": "",
      "date_submitted": "",
      "id": "",
      "ip_address": "",
      "language": "",
      "referer": "",
      "session_id": "",
      "status": "",
      "survey_data": {
        "": {
          "answer": [
            {
              "id": ,
              "option": "",
              "rank": ""
            }
          ],
          "comments": "",
          "question": ""
        }
      },
      "user_agent": ""
    }
  ]
}

```

Esse seria o resultado final dos dados retornados pela API, como estou a utilizar Mongo, criei uma função adicional onde eu gero um ObjectID baseado no **id** original e adiciono ele como **_id**. Outro detalhe que o mongo por padrão faz o sort dos dados em ordem alfabetica, não tendo nenhum problema, sendo somente visualmente diferente.
Não utilizei bibliotecas para modelar os dados como Pandas ou Marshmalow, porém para grandes quantidades de dados faria-se necessário, como por exemplo usar a abordagem de dataframes do Pandas ou então até de outras bibliotecas para evitar malloc como Dask. Acabei optando por simples estruturas de controle de fluxo e condições, os conhecidos for, if e lambda para criar funções simples. Usando essa abordagem, para chegar no resultado final acima, dentre as estruturas, a do request2 acabou sendo a mais dificil, visto que as questions não possuiam ID, então precisei a partir dos outros dois request mapear os IDs para adicionar no processamento do request2. Outro detalhe do request2 que quando as questões eram de rank, elas não retornavam um objeto aninhado e sim uma lista [], sendo necessário um tratamento maior, porém também facilitou que a própria biblioteca do Python ja trata muitas situações, como os caracteres de escape. Para padronizar foi adicionada a entrada comments em todas as answer, mesmo grande maioria não possuindo, isso facilitar a conversão dos dados por exemplo para serem usados em algum formato tabular como csv. No XML foi fácil, pois so mantive a mesma estrutura padronizada, removendo qualquer aninhamento maior. Nas questions de rank como padrão eu fiz o append só dos campos importantes, outros campos como type,shown seriam irrelevantes nesse contexto. No meu ponto de vista, iterar sobre os dados é um maneira interessante de manipular eles, porém para grandes quantidades de dados, realizar isso seria talvez inviável, ou teria que se tomar outros rumos nesse mesmo contexto para executar uma manipulação de bigdata.


### Código-fonte da solução desenvolvida em um repositório git de sua preferência de forma pública.
Disponibilizado aqui, no Github.

### Instruções para implantação e configuração da solução em um ambiente de produção.
Para ambiente de produção, escolhi o Gunicorn, por ser fácil de configurar, porem como ele trabalha com multithreads, necessitei criar uma logica pra captura dos dados da API para salvar em uma collection no Mongo, visto que a idéia na inicialização é somente fazer o request caso a collection não exista no banco de dados ainda.
Foi realizada a orquestração da aplicação e banco no Docker.

## Implementação

Seguem as instruções para implantação da aplicação em produção:

#### Requisitos necessários:

- [Docker-composer](https://docs.docker.com/compose/install/)

- [Git](https://git-scm.com/downloads)
#### Implementação
1. Realizar clone da repo com o comando:

   - `git clone https://github.com/RodrigoSKohl/seletivo_numera.git `

1. Renomear [.env.example](.env.example) para **.env**

1. Executar os comandos do docker

   - `docker-composer build`

   - `docker-composer up -d`

1. A API pode ser acessada em [localhost:8000](http://localhost:8000/)
