#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para gerar 300 exemplos de fine-tuning para o GasBot
Distribu

ição:
- 105 Tipo A (mensagem simples)
- 90 Tipo B (mensagem completa)
- 60 Tipo C (endereço parcial)
- 30 Tipo D (extras - urgência, troco)
- 15 Tipo E (pedidos múltiplos)
"""

import json
import random

def create_tool_def():
    return [{'type': 'function', 'function': {'name': 'extract_order_info', 'description': 'Extrai informações estruturadas de uma mensagem de pedido de gás', 'parameters': {'type': 'object', 'properties': {'product': {'type': 'object', 'properties': {'name': {'type': 'string'}, 'quantity': {'type': 'integer'}, 'confidence': {'type': 'number'}}}, 'address': {'type': 'object', 'properties': {'street': {'type': 'string'}, 'number': {'type': 'string'}, 'neighborhood': {'type': 'string'}, 'complement': {'type': 'string'}, 'reference': {'type': 'string'}, 'confidence': {'type': 'number'}}}, 'payment': {'type': 'object', 'properties': {'method': {'type': 'string', 'enum': ['pix', 'dinheiro', 'cartao', 'unknown']}, 'change_for': {'type': 'number'}, 'confidence': {'type': 'number'}}}, 'metadata': {'type': 'object', 'properties': {'is_urgent': {'type': 'boolean'}, 'has_complement': {'type': 'boolean'}, 'has_change_request': {'type': 'boolean'}, 'customer_tone': {'type': 'string', 'enum': ['polite', 'neutral', 'urgent', 'informal']}}}}, 'required': ['product', 'address', 'payment', 'metadata']}}}]

def create_example(call_id, user_message, product_name, quantity, product_conf,
                   street, number, neighborhood, complement, reference, address_conf,
                   payment_method, change_for, payment_conf,
                   is_urgent, has_complement, has_change_request, customer_tone):
    arguments = {
        "product": {"name": product_name, "quantity": quantity, "confidence": product_conf},
        "address": {"street": street, "number": number, "neighborhood": neighborhood, "complement": complement, "reference": reference, "confidence": address_conf},
        "payment": {"method": payment_method, "change_for": change_for, "confidence": payment_conf},
        "metadata": {"is_urgent": is_urgent, "has_complement": has_complement, "has_change_request": has_change_request, "customer_tone": customer_tone}
    }

    return {
        'messages': [
            {'role': 'system', 'content': 'Você é um extrator de informações para pedidos de gás via WhatsApp. Analise a mensagem do cliente e extraia: produto/quantidade, endereço completo, forma de pagamento, e metadados adicionais.'},
            {'role': 'user', 'content': user_message},
            {'role': 'assistant', 'tool_calls': [{'id': f'call_{call_id:03d}', 'type': 'function', 'function': {'name': 'extract_order_info', 'arguments': json.dumps(arguments, ensure_ascii=False)}}]}
        ],
        'tools': create_tool_def()
    }

# Dados para variação
ruas = ["Silva", "João Batista", "Pedro Álvares", "Maria da Glória", "Santos Dumont", "Tiradentes",
        "XV de Novembro", "Sete de Setembro", "Amazonas", "Paraná", "São Paulo", "Rio Branco",
        "Barão do Rio Branco", "Marechal Deodoro", "Getúlio Vargas", "Presidente Vargas",
        "Dom Pedro II", "Voluntários da Pátria", "das Flores", "das Palmeiras", "do Comércio",
        "Industrial", "Central", "Principal", "Bela Vista", "Boa Esperança", "Nova Era",
        "Andrade Neves", "Bento Gonçalves", "Carlos Gomes", "Coronel Genuíno"]

avenidas = ["Paulista", "Ipiranga", "Brasil", "Atlântica", "Copacabana", "Beira Mar",
            "Castelo Branco", "Afonso Pena", "Assis Brasil", "Protásio Alves", "JK",
            "Tiradentes", "Independência", "Liberdade", "República", "Sete de Setembro"]

bairros = ["Centro", "Jardim", "Vila Nova", "São José", "Santa Maria", "Boa Vista",
           "Cidade Nova", "Industrial", "Comercial", "Bela Vista", "Alto da Colina",
           "Esperança", "Progresso", "Santa Rita", "São Pedro", "Parque das Flores"]

examples = []
call_id = 1

print("="*60)
print("GERANDO 300 EXEMPLOS DE FINE-TUNING PARA GASBOT")
print("="*60)

# ===== TIPO A: Mensagens Simples (105 exemplos) =====
print("\n[1/5] Gerando Tipo A - Mensagens Simples (105 exemplos)...")

tipo_a_data = [
    # P13 - 63 exemplos (60% de 105)
    ("quero um gas", "Botijão P13", 1), ("preciso de gas", "Botijão P13", 1),
    ("manda um gas", "Botijão P13", 1), ("1 gas", "Botijão P13", 1),
    ("um botijao", "Botijão P13", 1), ("quero botijao", "Botijão P13", 1),
    ("preciso 1 gas", "Botijão P13", 1), ("queria gas", "Botijão P13", 1),
    ("bom dia quero gas", "Botijão P13", 1), ("oi preciso de um gas", "Botijão P13", 1),
    ("quero 1 p13", "Botijão P13", 1), ("me manda gas", "Botijão P13", 1),
    ("to sem gas", "Botijão P13", 1), ("2 gas", "Botijão P13", 2),
    ("2 botijao", "Botijão P13", 2), ("3 gas", "Botijão P13", 3),
    ("quero 2 botijao", "Botijão P13", 2), ("preciso de 2 gas", "Botijão P13", 2),
    ("manda 2 butijao", "Botijão P13", 2), ("queria 3 botijao de gas", "Botijão P13", 3),
    ("bujao", "Botijão P13", 1), ("botija", "Botijão P13", 1),
    ("um butijão", "Botijão P13", 1), ("preciso butijão", "Botijão P13", 1),
    ("QUERO GAS", "Botijão P13", 1), ("GAS", "Botijão P13", 1),
    ("gas pfv", "Botijão P13", 1), ("1 botijao obrigado", "Botijão P13", 1),
    ("quero gas de cozinha", "Botijão P13", 1), ("opa quero gas", "Botijão P13", 1),
    ("fala, queria um gas", "Botijão P13", 1), ("to precisando de gas", "Botijão P13", 1),
    ("acabou o gas aqui", "Botijão P13", 1), ("precisa gas", "Botijão P13", 1),
    ("um gas por gentileza", "Botijão P13", 1), ("gas delivery", "Botijão P13", 1),
    ("entrega de gas", "Botijão P13", 1), ("quero comprar gas", "Botijão P13", 1),
    ("vende gas?", "Botijão P13", 1), ("tem gas?", "Botijão P13", 1),
    ("gas disponivel", "Botijão P13", 1), ("boa tarde quero gas", "Botijão P13", 1),
    ("preciso comprar gas", "Botijão P13", 1), ("queria 1 gas", "Botijão P13", 1),
    ("oi bom dia gas", "Botijão P13", 1), ("me vende um gas", "Botijão P13", 1),
    ("1 p13 pfv", "Botijão P13", 1), ("quero o botijao", "Botijão P13", 1),
    ("um botijao de 13", "Botijão P13", 1), ("gas 13kg", "Botijão P13", 1),
    ("4 gas", "Botijão P13", 4), ("5 botijao", "Botijão P13", 5),
    ("preciso de 3 gas", "Botijão P13", 3), ("queria 4 botijao", "Botijão P13", 4),
    ("2 p13", "Botijão P13", 2), ("3 p13", "Botijão P13", 3),
    ("bom dia preciso gas", "Botijão P13", 1), ("oi quero 1 gas", "Botijão P13", 1),
    ("oii tem gas", "Botijão P13", 1), ("gas por favor", "Botijão P13", 1),
    ("preciso urgente de gas", "Botijão P13", 1),

    # Galão 20L - 21 exemplos (20% de 105)
    ("1 galao", "Galão 20L", 1), ("quero galao", "Galão 20L", 1),
    ("galao de agua", "Galão 20L", 1), ("agua", "Galão 20L", 1),
    ("2 galao", "Galão 20L", 2), ("3 galao", "Galão 20L", 3),
    ("quero agua", "Galão 20L", 1), ("preciso de agua", "Galão 20L", 1),
    ("galao agua mineral", "Galão 20L", 1), ("4 galoes", "Galão 20L", 4),
    ("queria 2 galao", "Galão 20L", 2), ("manda agua", "Galão 20L", 1),
    ("5 galao de agua", "Galão 20L", 5), ("agua mineral", "Galão 20L", 1),
    ("galao 20L", "Galão 20L", 1), ("quero galao agua", "Galão 20L", 1),
    ("1 garrafao", "Galão 20L", 1), ("agua 20 litros", "Galão 20L", 1),
    ("2 galao agua mineral", "Galão 20L", 2), ("galao retornavel", "Galão 20L", 1),
    ("3 galoes de agua", "Galão 20L", 3),

    # P45 - 11 exemplos (10% de 105)
    ("quero p45", "Botijão P45", 1), ("preciso de p45", "Botijão P45", 1),
    ("1 p45", "Botijão P45", 1), ("2 botijao de 45kg", "Botijão P45", 2),
    ("um botijao industrial", "Botijão P45", 1), ("botijao grande", "Botijão P45", 1),
    ("p45 pfv", "Botijão P45", 1), ("3 p45", "Botijão P45", 3),
    ("quero industrial", "Botijão P45", 1), ("botijao 45kg", "Botijão P45", 1),
    ("4 p45", "Botijão P45", 4),

    # P5 - 5 exemplos (5% de 105)
    ("quero p5", "Botijão P5", 1), ("tem botijao pequeno?", "Botijão P5", 1),
    ("mini botijao", "Botijão P5", 1), ("p5 por favor", "Botijão P5", 1),
    ("botija pequena", "Botijão P5", 1),

    # P8 - 3 exemplos (3% de 105)
    ("quero p8", "Botijão P8", 1), ("botijao de 8kg", "Botijão P8", 1),
    ("1 p8 pfv", "Botijão P8", 1),

    # P20 - 2 exemplos (2% de 105)
    ("quero p20", "Botijão P20", 1), ("botijao de 20kg", "Botijão P20", 1),
]

for msg, product, qty in tipo_a_data:
    conf = round(random.uniform(0.90, 0.98), 2)
    if "?" in msg:
        conf -= 0.05

    tone = "polite" if any(x in msg.lower() for x in ["por favor", "pfv", "obrigado", "bom dia", "boa tarde"]) else \
           "informal" if any(x in msg.lower() for x in ["opa", "fala", "ae", "oii", "manda"]) else \
           "urgent" if "urgente" in msg.lower() or msg.isupper() else "neutral"

    ex = create_example(call_id, msg, product, qty, min(conf, 0.99),
                        None, None, None, None, None, 0.0,
                        "unknown", None, 0.0,
                        "urgente" in msg.lower(), False, False, tone)
    examples.append(ex)
    call_id += 1

print(f"   OK {len(examples)} exemplos Tipo A gerados")

# ===== TIPO B: Mensagem Completa (90 exemplos) =====
print("\n[2/5] Gerando Tipo B - Mensagens Completas (90 exemplos)...")

# Gerando 90 mensagens completas com variação
for i in range(90):
    # Escolher produto (60% P13, 20% Galão, 10% P45, 5% P5, 3% P8, 2% P20)
    rand = random.random()
    if rand < 0.60:
        product, qty = "Botijão P13", random.choice([1, 1, 1, 2, 2, 3])
        prod_words = random.choice(["gas", "botijao", "p13", "botija", "butijao"])
    elif rand < 0.80:
        product, qty = "Galão 20L", random.choice([1, 1, 2, 2, 3])
        prod_words = random.choice(["galao", "agua", "galao agua", "galão"])
    elif rand < 0.90:
        product, qty = "Botijão P45", random.choice([1, 1, 2, 3])
        prod_words = random.choice(["p45", "botijao de 45kg", "industrial"])
    elif rand < 0.95:
        product, qty = "Botijão P5", 1
        prod_words = random.choice(["p5", "botijao pequeno", "mini botijao"])
    elif rand < 0.98:
        product, qty = "Botijão P8", 1
        prod_words = random.choice(["p8", "botijao de 8kg"])
    else:
        product, qty = "Botijão P20", 1
        prod_words = random.choice(["p20", "botijao de 20kg"])

    # Escolher rua/avenida
    if random.random() < 0.5:
        street_name = random.choice(ruas)
        street_type = "Rua"
    else:
        street_name = random.choice(avenidas)
        street_type = "Avenida"

    street_full = f"{street_type} {street_name}"
    number = str(random.randint(10, 2000))
    neighborhood = random.choice(bairros)

    # Escolher pagamento
    payment = random.choice(["pix", "pix", "pix", "dinheiro", "dinheiro", "cartao"])

    # Gerar mensagem
    templates = [
        f"quero {qty} {prod_words} na {street_type.lower()} {street_name.lower()} {number} {neighborhood.lower()} {payment}",
        f"manda {qty} {prod_words} {street_type.lower()} {street_name.lower()} numero {number} {neighborhood.lower()} {payment}",
        f"preciso de {qty} {prod_words} r {street_name.lower()} n {number} {neighborhood.lower()} pagamento {payment}",
        f"{qty} {prod_words} rua {street_name.lower()} {number} bairro {neighborhood.lower()} {payment}",
        f"queria {qty} {prod_words} av {street_name.lower()} {number} {neighborhood.lower()} pago no {payment}",
    ]

    msg = random.choice(templates)

    tone = random.choice(["neutral", "neutral", "neutral", "polite", "informal"])

    ex = create_example(call_id, msg, product, qty, round(random.uniform(0.93, 0.98), 2),
                        street_full, number, neighborhood, None, None, round(random.uniform(0.88, 0.94), 2),
                        payment, None, round(random.uniform(0.92, 0.97), 2),
                        False, False, False, tone)
    examples.append(ex)
    call_id += 1

print(f"   OK {len(examples) - 105} exemplos Tipo B gerados")

# ===== TIPO C: Endereço Parcial (60 exemplos) =====
print("\n[3/5] Gerando Tipo C - Endereço Parcial (60 exemplos)...")

for i in range(60):
    rand = random.random()
    if rand < 0.60:
        product, qty = "Botijão P13", random.choice([1, 1, 2])
        prod_words = random.choice(["gas", "botijao", "p13"])
    elif rand < 0.80:
        product, qty = "Galão 20L", random.choice([1, 2])
        prod_words = random.choice(["galao", "agua"])
    else:
        product, qty = "Botijão P45", 1
        prod_words = "p45"

    street_name = random.choice(ruas + avenidas)
    number = str(random.randint(10, 1500))

    # Metade tem bairro, metade não
    if random.random() < 0.5:
        neighborhood = random.choice(bairros)
        msg = f"{qty} {prod_words} rua {street_name.lower()} {number} {neighborhood.lower()}"
        addr_conf = round(random.uniform(0.85, 0.92), 2)
    else:
        neighborhood = None
        msg = f"quero {qty} {prod_words} av {street_name.lower()} numero {number}"
        addr_conf = round(random.uniform(0.75, 0.88), 2)

    street_full = f"Rua {street_name}" if "av" not in msg else f"Avenida {street_name}"

    ex = create_example(call_id, msg, product, qty, round(random.uniform(0.92, 0.97), 2),
                        street_full, number, neighborhood, None, None, addr_conf,
                        "unknown", None, 0.0,
                        False, False, False, "neutral")
    examples.append(ex)
    call_id += 1

print(f"   OK {len(examples) - 195} exemplos Tipo C gerados")

# ===== TIPO D: Mensagens com Extras (30 exemplos) =====
print("\n[4/5] Gerando Tipo D - Mensagens com Extras (30 exemplos)...")

for i in range(30):
    rand = random.random()
    if rand < 0.60:
        product, qty = "Botijão P13", random.choice([1, 2])
        prod_words = random.choice(["gas", "botijao"])
    elif rand < 0.80:
        product, qty = "Galão 20L", random.choice([1, 2])
        prod_words = "galao"
    else:
        product, qty = "Botijão P45", 1
        prod_words = "p45"

    street_name = random.choice(ruas)
    number = str(random.randint(10, 1000))
    neighborhood = random.choice(bairros)

    # Tipo de extra
    extra_type = random.choice(["urgente", "troco", "complemento", "referencia"])

    if extra_type == "urgente":
        msg = f"URGENTE preciso de {qty} {prod_words} rua {street_name.lower()} {number} {neighborhood.lower()} pix"
        is_urgent, has_comp, has_change = True, False, False
        complement, reference = None, None
        payment, change_for = "pix", None
        tone = "urgent"
    elif extra_type == "troco":
        troco_val = random.choice([50, 100, 200])
        msg = f"{qty} {prod_words} rua {street_name.lower()} {number} {neighborhood.lower()} dinheiro troco pra {troco_val}"
        is_urgent, has_comp, has_change = False, False, True
        complement, reference = None, None
        payment, change_for = "dinheiro", float(troco_val)
        tone = "neutral"
    elif extra_type == "complemento":
        apt = random.randint(101, 505)
        msg = f"quero {qty} {prod_words} rua {street_name.lower()} {number} apto {apt} {neighborhood.lower()} cartao"
        is_urgent, has_comp, has_change = False, True, False
        complement, reference = f"Apto {apt}", None
        payment, change_for = "cartao", None
        tone = "neutral"
    else:  # referencia
        refs = ["em frente a padaria", "do lado do mercado", "perto da escola", "prox ao posto"]
        ref_text = random.choice(refs)
        msg = f"{qty} {prod_words} rua {street_name.lower()} {number} {ref_text} {neighborhood.lower()} pix"
        is_urgent, has_comp, has_change = False, False, False
        complement = None
        reference = ref_text.capitalize()
        payment, change_for = "pix", None
        tone = "neutral"

    addr_conf = round(random.uniform(0.86, 0.93), 2)
    if has_comp or reference:
        addr_conf -= 0.03

    ex = create_example(call_id, msg, product, qty, round(random.uniform(0.92, 0.97), 2),
                        f"Rua {street_name}", number, neighborhood, complement, reference, addr_conf,
                        payment, change_for, round(random.uniform(0.90, 0.97), 2),
                        is_urgent, has_comp, has_change, tone)
    examples.append(ex)
    call_id += 1

print(f"   OK {len(examples) - 255} exemplos Tipo D gerados")

# ===== TIPO E: Pedidos Múltiplos (15 exemplos) =====
print("\n[5/5] Gerando Tipo E - Pedidos Múltiplos (15 exemplos)...")

for i in range(15):
    # Sempre extrai APENAS o primeiro produto
    first_product = random.choice(["Botijão P13", "Galão 20L"])
    first_qty = random.choice([1, 2])

    if first_product == "Botijão P13":
        first_words = random.choice(["gas", "botijao", "p13"])
        second_words = random.choice(["galao", "agua"])
    else:
        first_words = random.choice(["galao", "agua"])
        second_words = random.choice(["gas", "botijao"])

    second_qty = random.choice([1, 2, 3])

    # Metade com endereço, metade sem
    if random.random() < 0.5:
        street_name = random.choice(ruas)
        number = str(random.randint(10, 800))
        neighborhood = random.choice(bairros)
        payment = random.choice(["pix", "dinheiro", "cartao"])

        msg = f"quero {first_qty} {first_words} e {second_qty} {second_words} rua {street_name.lower()} {number} {neighborhood.lower()} {payment}"

        ex = create_example(call_id, msg, first_product, first_qty, round(random.uniform(0.92, 0.96), 2),
                            f"Rua {street_name}", number, neighborhood, None, None, round(random.uniform(0.87, 0.92), 2),
                            payment, None, round(random.uniform(0.91, 0.96), 2),
                            False, False, False, "neutral")
    else:
        msg = f"{first_qty} {first_words} e {second_qty} {second_words}"

        ex = create_example(call_id, msg, first_product, first_qty, round(random.uniform(0.90, 0.95), 2),
                            None, None, None, None, None, 0.0,
                            "unknown", None, 0.0,
                            False, False, False, "neutral")

    examples.append(ex)
    call_id += 1

print(f"   OK {len(examples) - 285} exemplos Tipo E gerados")

# ===== SALVAR ARQUIVO =====
print(f"\n{'='*60}")
print(f"TOTAL DE EXEMPLOS GERADOS: {len(examples)}")
print(f"{'='*60}")

output_file = r"c:\Phyton-Projetos\BotGas\gasbot-finetuning-dataset.jsonl"
with open(output_file, 'w', encoding='utf-8') as f:
    for ex in examples:
        f.write(json.dumps(ex, ensure_ascii=False) + '\n')

print(f"\n[OK] Arquivo salvo em: {output_file}")
print(f"[OK] Total de linhas: {len(examples)}")
print("\nDistribuição:")
print(f"  - Tipo A (Simples): 105")
print(f"  - Tipo B (Completa): 90")
print(f"  - Tipo C (Parcial): 60")
print(f"  - Tipo D (Extras): 30")
print(f"  - Tipo E (Múltiplos): 15")
print(f"  TOTAL: {105+90+60+30+15} exemplos")
