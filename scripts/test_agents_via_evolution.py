"""
Script de Teste de Agentes via Evolution API Real

Envia mensagens reais via Evolution API para testar os agentes.
As mensagens vao para o WhatsApp e os agentes processam normalmente.

Uso:
    python scripts/test_agents_via_evolution.py
"""

import sys
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import requests
import json
from datetime import datetime
import time

# Configuração
EVOLUTION_API_URL = "https://api.carvalhoia.com"
EVOLUTION_API_KEY = "03fd4f2fc18afc835d3e83d343eae714"
INSTANCE_NAME = "carvalhoia"
TEST_PHONE = "5534996554613"  # Seu número de teste

# Testes organizados por categoria
TESTS = {
    "Saudações e Atendimento": [
        "Olá",
        "Boa tarde",
        "Quanto custa a botija de gás?",
        "Quais produtos vocês tem?"
    ],
    "Pedidos": [
        "Quero comprar uma botija",
        "Preciso de um P13"
    ],
    "Endereço": [
        "Rua das Flores, 123, Centro, Uberlândia"
    ],
    "Pagamento": [
        "Aceita PIX?",
        "Posso pagar no cartão?"
    ]
}


def send_message_via_evolution(message: str, phone: str) -> bool:
    """
    Envia mensagem real via Evolution API

    Args:
        message: Texto da mensagem
        phone: Número do destinatário (formato: 5534996554613)

    Returns:
        bool: True se enviou com sucesso
    """
    url = f"{EVOLUTION_API_URL}/message/sendText/{INSTANCE_NAME}"

    headers = {
        "Content-Type": "application/json",
        "apikey": EVOLUTION_API_KEY
    }

    payload = {
        "number": phone,
        "text": message
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)

        if response.status_code == 201 or response.status_code == 200:
            return True
        else:
            print(f"   ⚠️  Status: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"   ❌ Erro: {str(e)}")
        return False


def run_tests():
    """Executa todos os testes"""

    print("\n" + "="*70)
    print("  🧪 TESTE DE AGENTES VIA EVOLUTION API - BotGas".center(70))
    print("="*70 + "\n")

    print(f"📱 Número de teste: {TEST_PHONE}")
    print(f"🔗 Evolution API: {EVOLUTION_API_URL}")
    print(f"📦 Instância: {INSTANCE_NAME}\n")

    print(f"📋 Executando {sum(len(tests) for tests in TESTS.values())} testes...")
    print(f"⏱️  Aguarde 8 segundos entre cada mensagem...")
    print(f"⚠️  As mensagens serão enviadas para o WhatsApp real!\n")

    # Confirmação
    print("⚠️  ATENÇÃO: Este script vai enviar mensagens REAIS via WhatsApp!")
    confirm = input("Digite 'SIM' para continuar: ")

    if confirm.upper() != "SIM":
        print("\n❌ Teste cancelado pelo usuário.\n")
        return

    results = []
    test_number = 0

    for category, messages in TESTS.items():
        print("\n" + "="*70)
        print(f"  📁 {category}".center(70))
        print("="*70 + "\n")

        for message in messages:
            test_number += 1
            total_tests = sum(len(tests) for tests in TESTS.values())

            print(f"[Teste {test_number}/{total_tests}]")
            print(f"💬 Enviando: \"{message}\"")

            # Envia via Evolution API
            success = send_message_via_evolution(message, TEST_PHONE)

            if success:
                print(f"✅ Mensagem enviada via Evolution API")

                results.append({
                    "category": category,
                    "message": message,
                    "sent": True,
                    "timestamp": datetime.now().isoformat()
                })

                # Aguarda antes da próxima mensagem
                if test_number < total_tests:
                    print(f"⏳ Aguardando 8 segundos...\n")
                    time.sleep(8)
            else:
                print(f"❌ Erro ao enviar mensagem\n")
                results.append({
                    "category": category,
                    "message": message,
                    "sent": False,
                    "timestamp": datetime.now().isoformat()
                })

    # Resumo
    print("\n" + "="*70)
    print("  📊 RESUMO DOS TESTES".center(70))
    print("="*70 + "\n")

    sent = sum(1 for r in results if r['sent'])
    failed = sum(1 for r in results if not r['sent'])

    print(f"✅ Mensagens enviadas: {sent}/{len(results)}")
    print(f"❌ Mensagens com falha: {failed}/{len(results)}\n")

    # Salva relatório
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"scripts/evolution_test_{timestamp}.json"

    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": timestamp,
            "phone": TEST_PHONE,
            "instance": INSTANCE_NAME,
            "total_tests": len(results),
            "sent": sent,
            "failed": failed,
            "results": results
        }, f, indent=2, ensure_ascii=False)

    print(f"💾 Relatório salvo em: {report_file}\n")

    print("📱 Agora verifique as respostas no WhatsApp do número de teste!")
    print("📊 Você também pode ver as conversas no Dashboard: http://localhost:3000/dashboard\n")

    print("="*70 + "\n")


if __name__ == "__main__":
    try:
        run_tests()
    except KeyboardInterrupt:
        print("\n\n⚠️  Teste interrompido pelo usuário.\n")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {str(e)}\n")
