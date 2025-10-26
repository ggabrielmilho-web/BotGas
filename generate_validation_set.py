#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para gerar 60 exemplos NOVOS para validação do GasBot
Distribuição: 21 Tipo A, 18 Tipo B, 12 Tipo C, 6 Tipo D, 3 Tipo E
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
            {'role': 'assistant', 'tool_calls': [{'id': f'call_val_{call_id:03d}', 'type': 'function', 'function': {'name': 'extract_order_info', 'arguments': json.dumps(arguments, ensure_ascii=False)}}]}
        ],
        'tools': create_tool_def()
    }

# Dados diferentes para validação
ruas_val = ["Marechal Floriano", "Visconde de Mauá", "Duque de Caxias", "General Osório",
            "Cel. Flores", "Andradas", "Felipe Camarão", "José Bonifácio", "Castro Alves",
            "Rui Barbosa", "Quintino Bocaiuva", "Benjamin Constant", "Farroupilha"]

avenidas_val = ["Borges de Medeiros", "João Pessoa", "Senador Salgado Filho", "Praia de Belas",
                "Loureiro da Silva", "Farrapos", "Cristóvão Colombo", "Assis Brasil"]

bairros_val = ["Menino Deus", "Floresta", "Azenha", "Santana", "Navegantes", "Petrópolis",
               "Moinhos de Vento", "Rio Branco", "Humaitá", "Cristal", "Teresópolis"]

examples = []
call_id = 1

print("="*60)
print("GERANDO 60 EXEMPLOS PARA VALIDACAO")
print("="*60)

# TIPO A: 21 exemplos
print("\n[1/5] Tipo A - Mensagens Simples (21 exemplos)...")

tipo_a_msgs = [
    # P13
    ("oi quero 1 botijao pfv", "Botijão P13", 1),
    ("preciso comprar gas", "Botijão P13", 1),
    ("tem gas disponivel", "Botijão P13", 1),
    ("to precisando de 1 gas", "Botijão P13", 1),
    ("queria comprar botijao", "Botijão P13", 1),
    ("boa noite preciso gas", "Botijão P13", 1),
    ("e ai tem gas ai", "Botijão P13", 1),
    ("vcs tem botijao", "Botijão P13", 1),
    ("quero um botijao de gas", "Botijão P13", 1),
    ("2 botijao por favor", "Botijão P13", 2),
    ("preciso 3 gas urgente", "Botijão P13", 3),
    # Galão
    ("quero comprar agua", "Galão 20L", 1),
    ("tem galao de agua", "Galão 20L", 1),
    ("preciso 2 galao", "Galão 20L", 2),
    ("queria agua mineral", "Galão 20L", 1),
    ("4 galao pfv", "Galão 20L", 4),
    # P45
    ("preciso p45", "Botijão P45", 1),
    ("tem botijao industrial", "Botijão P45", 1),
    ("2 p45 pfv", "Botijão P45", 2),
    # P5
    ("quero botijao de 5kg", "Botijão P5", 1),
    # P8
    ("tem p8", "Botijão P8", 1),
]

for msg, product, qty in tipo_a_msgs:
    conf = round(random.uniform(0.91, 0.97), 2)
    tone = "polite" if "pfv" in msg or "por favor" in msg or "boa noite" in msg else \
           "informal" if "e ai" in msg or "vcs" in msg else \
           "urgent" if "urgente" in msg else "neutral"

    ex = create_example(call_id, msg, product, qty, conf,
                        None, None, None, None, None, 0.0,
                        "unknown", None, 0.0,
                        "urgente" in msg.lower(), False, False, tone)
    examples.append(ex)
    call_id += 1

print(f"   OK {len(examples)} exemplos Tipo A")

# TIPO B: 18 exemplos
print("\n[2/5] Tipo B - Mensagens Completas (18 exemplos)...")

tipo_b_templates = [
    ("1 gas rua {rua} {num} {bairro} pix", "Botijão P13", 1, "pix"),
    ("quero 2 botijao av {av} numero {num} {bairro} cartao", "Botijão P13", 2, "cartao"),
    ("manda 1 galao rua {rua} {num} {bairro} dinheiro", "Galão 20L", 1, "dinheiro"),
    ("preciso gas na rua {rua} n {num} {bairro} pagamento pix", "Botijão P13", 1, "pix"),
    ("1 p45 av {av} {num} {bairro} pix", "Botijão P45", 1, "pix"),
    ("2 agua av {av} {num} {bairro} cartao", "Galão 20L", 2, "cartao"),
    ("queria 1 botijao r {rua} {num} {bairro} pix pfv", "Botijão P13", 1, "pix"),
    ("3 galao rua {rua} {num} {bairro} dinheiro", "Galão 20L", 3, "dinheiro"),
    ("1 gas r {rua} numero {num} {bairro} pix", "Botijão P13", 1, "pix"),
    ("quero p13 rua {rua} {num} {bairro} cartao", "Botijão P13", 1, "cartao"),
    ("2 p45 avenida {av} {num} {bairro} pix", "Botijão P45", 2, "pix"),
    ("1 agua mineral rua {rua} {num} {bairro} dinheiro", "Galão 20L", 1, "dinheiro"),
    ("quero gas av {av} {num} {bairro} pix obrigado", "Botijão P13", 1, "pix"),
    ("2 botijao r {rua} n {num} {bairro} pix", "Botijão P13", 2, "pix"),
    ("1 galao agua av {av} {num} {bairro} cartao", "Galão 20L", 1, "cartao"),
    ("preciso 1 p45 rua {rua} {num} {bairro} pix", "Botijão P45", 1, "pix"),
    ("3 gas rua {rua} {num} {bairro} dinheiro", "Botijão P13", 3, "dinheiro"),
    ("1 p8 av {av} {num} {bairro} pix", "Botijão P8", 1, "pix"),
]

for template, product, qty, payment in tipo_b_templates:
    rua = random.choice(ruas_val)
    av = random.choice(avenidas_val)
    num = str(random.randint(50, 1800))
    bairro = random.choice(bairros_val)

    msg = template.format(rua=rua.lower(), av=av.lower(), num=num, bairro=bairro.lower())

    # Determinar tipo de rua
    if ' av ' in msg or 'avenida' in msg:
        street_full = f"Avenida {av}"
    else:
        street_full = f"Rua {rua}"

    tone = "polite" if "pfv" in msg or "obrigado" in msg else "neutral"

    ex = create_example(call_id, msg, product, qty, round(random.uniform(0.94, 0.98), 2),
                        street_full, num, bairro, None, None, round(random.uniform(0.89, 0.93), 2),
                        payment, None, round(random.uniform(0.93, 0.97), 2),
                        False, False, False, tone)
    examples.append(ex)
    call_id += 1

print(f"   OK {len(examples) - 21} exemplos Tipo B")

# TIPO C: 12 exemplos
print("\n[3/5] Tipo C - Endereco Parcial (12 exemplos)...")

tipo_c_templates = [
    ("1 gas rua {rua} {num}", "Botijão P13", 1, None),
    ("quero botijao av {av} numero {num}", "Botijão P13", 1, None),
    ("2 galao rua {rua} {num} {bairro}", "Galão 20L", 2, "bairro"),
    ("preciso gas r {rua} n {num}", "Botijão P13", 1, None),
    ("1 p45 avenida {av} {num}", "Botijão P45", 1, None),
    ("queria agua rua {rua} {num} {bairro}", "Galão 20L", 1, "bairro"),
    ("2 gas av {av} {num}", "Botijão P13", 2, None),
    ("1 botijao r {rua} numero {num} {bairro}", "Botijão P13", 1, "bairro"),
    ("3 galao rua {rua} {num}", "Galão 20L", 3, None),
    ("quero p13 av {av} {num} {bairro}", "Botijão P13", 1, "bairro"),
    ("1 p45 rua {rua} {num}", "Botijão P45", 1, None),
    ("2 agua av {av} numero {num}", "Galão 20L", 2, None),
]

for template, product, qty, has_bairro in tipo_c_templates:
    rua = random.choice(ruas_val)
    av = random.choice(avenidas_val)
    num = str(random.randint(30, 1200))
    bairro = random.choice(bairros_val) if has_bairro else None

    msg = template.format(rua=rua.lower(), av=av.lower(), num=num, bairro=bairro.lower() if bairro else "")

    if ' av ' in msg or 'avenida' in msg:
        street_full = f"Avenida {av}"
    else:
        street_full = f"Rua {rua}"

    addr_conf = round(random.uniform(0.86, 0.91), 2) if bairro else round(random.uniform(0.78, 0.85), 2)

    ex = create_example(call_id, msg, product, qty, round(random.uniform(0.93, 0.97), 2),
                        street_full, num, bairro, None, None, addr_conf,
                        "unknown", None, 0.0,
                        False, False, False, "neutral")
    examples.append(ex)
    call_id += 1

print(f"   OK {len(examples) - 39} exemplos Tipo C")

# TIPO D: 6 exemplos
print("\n[4/5] Tipo D - Com Extras (6 exemplos)...")

tipo_d_data = [
    ("URGENTE gas rua {rua} {num} {bairro} pix", "Botijão P13", 1, "pix", None, "urgente"),
    ("1 botijao rua {rua} {num} {bairro} dinheiro troco pra 100", "Botijão P13", 1, "dinheiro", 100, "troco"),
    ("quero gas av {av} {num} apt 205 {bairro} cartao", "Botijão P13", 1, "cartao", None, "apto"),
    ("2 galao rua {rua} {num} perto da igreja {bairro} pix", "Galão 20L", 2, "pix", None, "ref"),
    ("1 p45 rua {rua} {num} bloco b {bairro} dinheiro", "Botijão P45", 1, "dinheiro", None, "bloco"),
    ("gas urgente av {av} {num} {bairro} pix rapido", "Botijão P13", 1, "pix", None, "urgente2"),
]

for template, product, qty, payment, troco, tipo_extra in tipo_d_data:
    rua = random.choice(ruas_val)
    av = random.choice(avenidas_val)
    num = str(random.randint(40, 900))
    bairro = random.choice(bairros_val)

    msg = template.format(rua=rua.lower(), av=av.lower(), num=num, bairro=bairro.lower())

    if ' av ' in msg or 'avenida' in msg:
        street_full = f"Avenida {av}"
    else:
        street_full = f"Rua {rua}"

    # Determinar extras
    is_urgent = tipo_extra in ["urgente", "urgente2"]
    has_comp = tipo_extra in ["apto", "bloco"]
    has_change = tipo_extra == "troco"
    has_ref = tipo_extra == "ref"

    complement = "Apt 205" if tipo_extra == "apto" else "Bloco B" if tipo_extra == "bloco" else None
    reference = "Perto da igreja" if has_ref else None

    tone = "urgent" if is_urgent else "neutral"

    ex = create_example(call_id, msg, product, qty, round(random.uniform(0.92, 0.96), 2),
                        street_full, num, bairro, complement, reference, round(random.uniform(0.87, 0.92), 2),
                        payment, float(troco) if troco else None, round(random.uniform(0.91, 0.96), 2),
                        is_urgent, has_comp, has_change, tone)
    examples.append(ex)
    call_id += 1

print(f"   OK {len(examples) - 51} exemplos Tipo D")

# TIPO E: 3 exemplos
print("\n[5/5] Tipo E - Pedidos Multiplos (3 exemplos)...")

tipo_e_data = [
    ("quero 1 gas e 2 galao", "Botijão P13", 1, None, None, None),
    ("1 p13 e 1 agua rua {rua} {num} {bairro} pix", "Botijão P13", 1, "{rua}", "{num}", "{bairro}"),
    ("2 botijao e 3 galao agua av {av} {num} {bairro} cartao", "Botijão P13", 2, "{av}", "{num}", "{bairro}"),
]

for msg_template, product, qty, rua_t, num_t, bairro_t in tipo_e_data:
    if rua_t:
        rua = random.choice(ruas_val)
        av = random.choice(avenidas_val)
        num = str(random.randint(60, 800))
        bairro = random.choice(bairros_val)
        msg = msg_template.format(rua=rua.lower(), av=av.lower(), num=num, bairro=bairro.lower())

        if ' av ' in msg:
            street_full = f"Avenida {av}"
        else:
            street_full = f"Rua {rua}"

        payment = "pix" if "pix" in msg else "cartao"

        ex = create_example(call_id, msg, product, qty, round(random.uniform(0.91, 0.95), 2),
                            street_full, num, bairro, None, None, round(random.uniform(0.88, 0.92), 2),
                            payment, None, round(random.uniform(0.92, 0.96), 2),
                            False, False, False, "neutral")
    else:
        msg = msg_template
        ex = create_example(call_id, msg, product, qty, round(random.uniform(0.92, 0.96), 2),
                            None, None, None, None, None, 0.0,
                            "unknown", None, 0.0,
                            False, False, False, "neutral")

    examples.append(ex)
    call_id += 1

print(f"   OK {len(examples) - 57} exemplos Tipo E")

# Salvar arquivo
print(f"\n{'='*60}")
print(f"TOTAL: {len(examples)} exemplos")
print(f"{'='*60}")

output_file = r"c:\Phyton-Projetos\BotGas\gasbot-validation.jsonl"
with open(output_file, 'w', encoding='utf-8') as f:
    for ex in examples:
        f.write(json.dumps(ex, ensure_ascii=False) + '\n')

print(f"\n[OK] Arquivo salvo: {output_file}")
print(f"[OK] Total de linhas: {len(examples)}")
print("\nDistribuicao:")
print("  - Tipo A (Simples): 21")
print("  - Tipo B (Completa): 18")
print("  - Tipo C (Parcial): 12")
print("  - Tipo D (Extras): 6")
print("  - Tipo E (Multiplos): 3")
print("  TOTAL: 60 exemplos")
