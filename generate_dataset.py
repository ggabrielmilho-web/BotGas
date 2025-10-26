# Script para gerar dataset de fine-tuning do GasBot
import json
import random

def create_tool_def():
    """Retorna a definição das tools"""
    return [{'type': 'function', 'function': {'name': 'extract_order_info', 'description': 'Extrai informações estruturadas de uma mensagem de pedido de gás', 'parameters': {'type': 'object', 'properties': {'product': {'type': 'object', 'properties': {'name': {'type': 'string'}, 'quantity': {'type': 'integer'}, 'confidence': {'type': 'number'}}}, 'address': {'type': 'object', 'properties': {'street': {'type': 'string'}, 'number': {'type': 'string'}, 'neighborhood': {'type': 'string'}, 'complement': {'type': 'string'}, 'reference': {'type': 'string'}, 'confidence': {'type': 'number'}}}, 'payment': {'type': 'object', 'properties': {'method': {'type': 'string', 'enum': ['pix', 'dinheiro', 'cartao', 'unknown']}, 'change_for': {'type': 'number'}, 'confidence': {'type': 'number'}}}, 'metadata': {'type': 'object', 'properties': {'is_urgent': {'type': 'boolean'}, 'has_complement': {'type': 'boolean'}, 'has_change_request': {'type': 'boolean'}, 'customer_tone': {'type': 'string', 'enum': ['polite', 'neutral', 'urgent', 'informal']}}}}, 'required': ['product', 'address', 'payment', 'metadata']}}}]

def create_example(call_id, user_message, product_name, quantity, product_conf,
                   street, number, neighborhood, complement, reference, address_conf,
                   payment_method, change_for, payment_conf,
                   is_urgent, has_complement, has_change_request, customer_tone):
    """Cria um exemplo de treinamento"""

    arguments = {
        "product": {
            "name": product_name,
            "quantity": quantity,
            "confidence": product_conf
        },
        "address": {
            "street": street,
            "number": number,
            "neighborhood": neighborhood,
            "complement": complement,
            "reference": reference,
            "confidence": address_conf
        },
        "payment": {
            "method": payment_method,
            "change_for": change_for,
            "confidence": payment_conf
        },
        "metadata": {
            "is_urgent": is_urgent,
            "has_complement": has_complement,
            "has_change_request": has_change_request,
            "customer_tone": customer_tone
        }
    }

    return {
        'messages': [
            {'role': 'system', 'content': 'Você é um extrator de informações para pedidos de gás via WhatsApp. Analise a mensagem do cliente e extraia: produto/quantidade, endereço completo, forma de pagamento, e metadados adicionais.'},
            {'role': 'user', 'content': user_message},
            {'role': 'assistant', 'tool_calls': [{'id': f'call_{call_id:03d}', 'type': 'function', 'function': {'name': 'extract_order_info', 'arguments': json.dumps(arguments, ensure_ascii=False)}}]}
        ],
        'tools': create_tool_def()
    }

# Listas de variações para gerar exemplos diversos
ruas = ["Silva", "Joao Batista", "Pedro Alvares", "Maria da Gloria", "Santos Dumont", "Tiradentes",
        "XV de Novembro", "Sete de Setembro", "Amazonas", "Paraná", "São Paulo", "Rio Branco",
        "Barão do Rio Branco", "Marechal Deodoro", "Getulio Vargas", "Presidente Vargas",
        "Dom Pedro II", "Voluntários da Pátria", "Flores", "das Palmeiras", "do Comercio",
        "Industrial", "Central", "Principal", "Bela Vista", "Boa Esperança", "Nova Era"]

avenidas = ["Paulista", "Ipiranga", "Brasil", "Atlantica", "Copacabana", "Beira Mar",
            "Castelo Branco", "Afonso Pena", "Assis Brasil", "Protasio Alves", "JK",
            "Tiradentes", "Independência", "Liberdade", "Republica", "Sete de Setembro"]

bairros = ["Centro", "Jardim", "Vila Nova", "São José", "Santa Maria", "Boa Vista",
           "Cidade Nova", "Industrial", "Comercial", "Bela Vista", "Alto da Colina",
           "Esperanca", "Progresso", "Santa Rita", "São Pedro", "Parque das Flores"]

# Gerando exemplos
examples = []
call_id = 1

print("Gerando exemplos Tipo A (Mensagens Simples)...")
# TIPO A: Mensagens Simples - 105 exemplos
tipo_a_messages = [
    # P13 (maioria)
    "quero um gas", "preciso de gas", "manda um gas", "1 gas", "um botijao",
    "quero botijao", "preciso 1 gas", "queria gas", "bom dia quero gas",
    "oi preciso de um gas", "quero 1 p13", "me manda gas", "to sem gas",
    "2 gas", "2 botijao", "3 gas", "quero 2 botijao", "preciso de 2 gas",
    "manda 2 butijao", "queria 3 botijao de gas", "4 gas por favor",
    "bujao", "botija", "um butijão", "preciso butijão", "QUERO GAS",
    "GAS", "gas pfv", "1 botijao obrigado", "quero gas de cozinha",
    # Galões
    "1 galao", "quero galao", "galao de agua", "agua", "2 galao", "3 galao",
    "quero agua", "preciso de agua", "galao agua mineral", "4 galoes",
    "queria 2 galao", "manda agua", "5 galao de agua", "agua mineral",
    # P45
    "quero p45", "preciso de p45", "1 p45", "2 botijao de 45kg",
    "um botijao industrial", "botijao grande", "p45 pfv", "3 p45",
    "quero industrial", "botijao 45kg",
    # P5
    "quero p5", "tem botijao pequeno", "mini botijao", "p5 por favor",
    "botijao pequeno", "1 p5", "botija pequena",
    # P8
    "quero p8", "preciso p8", "botijao de 8kg", "1 p8", "p8 pfv",
    # P20
    "quero p20", "botijao de 20kg", "p20 pfv",
    # Mais P13
    "opa quero gas", "fala, queria um gas", "to precisando de gas",
    "acabou o gas aqui", "quero gas urgente", "precisa gas",
    "um gas por gentileza", "gas delivery", "entrega de gas",
    "quero comprar gas", "vende gas", "tem gas", "gas disponivel"
]

# Adicionando exemplos Tipo A
for msg in tipo_a_messages[:105]:
    # Determinar produto baseado na mensagem
    if "galao" in msg.lower() or "agua" in msg.lower() or "água" in msg.lower():
        product = "Galão 20L"
        conf = round(random.uniform(0.92, 0.98), 2)
    elif "p45" in msg.lower() or "45kg" in msg.lower() or "industrial" in msg.lower() or "grande" in msg.lower():
        product = "Botijão P45"
        conf = round(random.uniform(0.88, 0.98), 2)
    elif "p5" in msg.lower() or "5kg" in msg.lower() or "pequeno" in msg.lower() or "mini" in msg.lower() or "pequena" in msg.lower():
        product = "Botijão P5"
        conf = round(random.uniform(0.85, 0.98), 2)
    elif "p8" in msg.lower() or "8kg" in msg.lower():
        product = "Botijão P8"
        conf = round(random.uniform(0.90, 0.98), 2)
    elif "p20" in msg.lower() or "20kg" in msg.lower():
        product = "Botijão P20"
        conf = round(random.uniform(0.88, 0.97), 2)
    elif "p13" in msg.lower() or "13kg" in msg.lower():
        product = "Botijão P13"
        conf = round(random.uniform(0.93, 0.98), 2)
    else:
        # Assume P13 como padrão
        product = "Botijão P13"
        conf = round(random.uniform(0.90, 0.96), 2)

    # Extrair quantidade
    qty = 1
    for num in ["2", "3", "4", "5", "dois", "tres", "quatro", "cinco"]:
        if num in msg.lower():
            qty = {"2": 2, "dois": 2, "3": 3, "tres": 3, "4": 4, "quatro": 4, "5": 5, "cinco": 5}.get(num, 1)
            conf += 0.01  # Aumenta confiança se quantidade explícita
            break

    # Determinar tom
    if any(x in msg.lower() for x in ["por favor", "pfv", "obrigado", "bom dia", "boa tarde", "gentileza"]):
        tone = "polite"
    elif any(x in msg.lower() for x in ["opa", "fala", "ae", "manda"]):
        tone = "informal"
    elif "URGENTE" in msg or msg.isupper():
        tone = "urgent"
    else:
        tone = "neutral"

    ex = create_example(
        call_id, msg, product, qty, min(conf, 0.99),
        None, None, None, None, None, 0.0,
        "unknown", None, 0.0,
        "urgente" in msg.lower(), False, False, tone
    )
    examples.append(ex)
    call_id += 1

print(f"Gerados {len(examples)} exemplos Tipo A")

# Salvando os exemplos já existentes (20) + novos
print(f"\nTotal de exemplos gerados: {len(examples)}")
print(f"Ainda faltam {300 - 21 - len(examples)} exemplos para completar os 300")

print("\nAgora vou gerar os Tipos B, C, D e E...")
