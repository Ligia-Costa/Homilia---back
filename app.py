# Imports necessários
from flask import Flask, jsonify, request # Flask, jsonify para formatar resposta, request para acessar dados da requisição
from flask_cors import CORS # Para lidar com Cross-Origin Resource Sharing
from google import genai # Biblioteca para interagir com o modelo Gemini
import os # Módulo para interagir com o sistema operacional (usaremos para variáveis de ambiente)
from dotenv import load_dotenv # Importa a função para carregar .env (se python-dotenv foi instalado)
import json
from datetime import datetime

# Carrega variáveis de ambiente do arquivo .env (se existir)
load_dotenv()

# Cria uma instância da aplicação Flask
app = Flask(__name__)

API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=API_KEY)

# Habilita o CORS para a aplicação inteira... Isso permitirá que qualquer origem (qualquer domínio/porta) faça requisições ao seu back-end.
CORS(app)

def criar_homilia(data):

# Cria o prompt para a API Gemini, instruindo-a a gerar a homília com base na data fornecida e a formatar a resposta como JSON.
    prompt = f"""
    Gere uma homilia católica para a missa do dia {data}, com base no Catecismo, na Bíblia, no Magistério da Igreja, e nas leituras litúrgicas do dia segundo o calendário da Igreja Católica (visto que estamos no ano C). Seja assertivo com as leituras e evite erros.

    Faça a geração da homilia com base na liturgia diária oferecida pelo site da CNBB (no seguinte site: https://www.cnbb.org.br/liturgia-diaria/) ou outro site confiável.

    A homilia deve ser escrita com linguagem acessível, acolhedora e pastoral, podendo conter citação de santos, do Catecismo da Igreja Católica ou do Papa, quando apropriado. Evite erros e não utilize linguagem teológica complexa. Bem como traga realmente a homília do dia solicitado (inclusive se for dia de santos). 
    
    A homilia é um discurso religioso proferido durante a missa, com o objetivo de explicar e aplicar as leituras bíblicas do dia, além de oferecer uma reflexão sobre a vida cristã. 

    A homilia deve refletir os ensinamentos de Jesus Cristo e a doutrina da Igreja Católica. Ela deve conter:
    - Uma explicação clara e fiel das leituras do dia;
    - Uma mensagem prática de fé, caridade e esperança;
    - Aplicações concretas para a vida dos fiéis.

    Se o conteúdo solicitado for ofensivo à fé católica, herético, impróprio ou desrespeitoso, **não gere a homilia** e retorne um alerta ao usuário, mantendo a estrutura abaixo.

    Atenção: Retorne APENAS o objeto JSON, sem nenhum texto adicional antes ou depois.
    Estrutura de resposta no formato JSON:
    homilia = {{
        "titulo": "Título da homilia",
        "referencia_biblica": "Ex: Mt 5,1-12",
        "tema_central": "Frase com o tema principal",
        "pontos_da_reflexao": [
            "Ponto 1",
            "Ponto 2",
            "Ponto 3"
        ],
        "aplicacao_pratica": [
            "Aplicação 1",
            "Aplicação 2",
            "Aplicação 3"
        ]
    }}
    """
		# Envia a requisição para a API Gemini para gerar o conteúdo da homilia.
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-lite",
            contents=prompt, 
            config={"response_mime_type": "application/json"}
        )

        texto = response.text.strip()

        # Garante que é um JSON válido
        resultado = json.loads(texto)

        return resultado

    except json.JSONDecodeError as js:
        print(f"❌ Erro ao decodificar JSON: {js}")
        print(f"Resposta da API Gemini: {response.text}")
        return {
            "titulo": "Erro ao interpretar a homilia",
            "referencia_biblica": "",
            "tema_central": "",
            "pontos_da_reflexao": [],
            "aplicacao_pratica": [],
            "erro": "A resposta da IA veio em formato inválido. Tente novamente."
        }

    except Exception as e:
        print(f"❌ Erro na chamada da Gemini: {e}")
        return {
            "titulo": "Erro ao gerar a homilia",
            "referencia_biblica": "",
            "tema_central": "",
            "pontos_da_reflexao": [],
            "aplicacao_pratica": [],
            "erro": "Ocorreu um erro inesperado. Tente novamente em instantes."
        }

@app.route('/homilia', methods=['POST'])
def make_homilia():
    try:
        data = request.get_json()
        if not data or not isinstance(data, dict):
            return jsonify({'error': 'Requisição JSON inválida. Esperava um objeto JSON.'}), 400

        data_str = data.get('data')
        if not data_str:
            return jsonify({'error': 'O campo "data" é obrigatório.'}), 400

        try:
            data_formatada = datetime.strptime(data_str, '%d/%m/%Y').date()
        except ValueError:
            return jsonify({'error': 'O campo "data" deve estar no formato DD/MM/YYYY.'}), 400

        # Gera a homilia com base na data
        resultado = criar_homilia(data_formatada.strftime('%d/%m/%Y'))
        return jsonify(resultado), 200

    except Exception as e:
        print(f"Erro interno: {e}")
        return jsonify({'error': 'Erro interno ao gerar a homilia.'}), 500
    
# Rota para o chat
@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        pergunta = data.get("pergunta")

        if not pergunta:
            return jsonify({"erro": "Pergunta não fornecida."}), 400

        prompt = f"""
        Você é um assistente católico que responde com base no Catecismo, na Bíblia e no Magistério da Igreja. Responda com acolhimento, clareza e fidelidade à doutrina, seja sucinto. Pergunta: "{pergunta}"
        """

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )

        texto = response.text.strip()
        return jsonify({"resposta": texto}), 200

    except Exception as e:
        print("Erro no chat:", e)
        return jsonify({"erro": "Erro ao gerar resposta."}), 500

    
if __name__ == '__main__':
    app.run(debug=True, threaded=True)
