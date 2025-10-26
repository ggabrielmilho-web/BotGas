"""
Script Simplificado de Teste de Agentes

Testa os agentes fazendo requisicoes HTTP diretas ao backend que ja esta rodando no Docker.
Nao precisa de dependencias Python locais!

Uso:
    python scripts/test_agent_simple.py
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

# Configurações
BACKEND_URL = "http://localhost:8000"
EVOLUTION_API_URL = "https://api.carvalhoia.com"
EVOLUTION_API_KEY = "03fd4f2fc18afc835d3e83d343eae714"

# Tenant e customer de teste
# Nao precisa de login - apenas envia mensagens via webhook
EMAIL = "contratocarvalhoia@gmail.com"
PASSWORD = ""  # Nao usado

# Testes por categoria
TESTS = {
    "Saudações e Atendimento": [
        "Olá",
        "Boa tarde",
        "Quanto custa a botija de gás?",
        "Quais produtos vocês tem?",
    ],
    "Pedidos": [
        "Quero comprar uma botija",
        "Preciso de um P13",
    ],
    "Endereço": [
        "Rua das Flores, 123, Centro, Uberlândia",
    ],
    "Pagamento": [
        "Aceita PIX?",
        "Posso pagar no cartão?",
    ]
}


def login():
    """Faz login e retorna o token"""
    print("🔐 Fazendo login...")
    response = requests.post(
        f"{BACKEND_URL}/api/v1/auth/login",
        json={"email": EMAIL, "password": PASSWORD}
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Login bem-sucedido! Usuário: {data['user']['email']}")
        return data['access_token'], data['user']['tenant_id']
    else:
        print(f"❌ Erro no login: {response.status_code}")
        print(response.text)
        return None, None


def send_test_message_via_webhook(message: str, phone: str = "5534996554613"):
    """
    Simula envio de mensagem via Evolution API webhook
    """
    # Constrói payload similar ao Evolution API
    payload = {
        "instance": "carvalhoia",
        "data": {
            "key": {
                "remoteJid": f"{phone}@s.whatsapp.net",
                "fromMe": False,
                "id": f"TEST_{int(time.time() * 1000)}"
            },
            "message": {
                "conversation": message,
                "pushName": "Teste"
            },
            "messageTimestamp": int(time.time())
        },
        "destination": phone,
        "date_time": datetime.now().isoformat(),
        "sender": phone,
        "server_url": BACKEND_URL,
        "apikey": EVOLUTION_API_KEY
    }

    # Envia para o webhook
    response = requests.post(
        f"{BACKEND_URL}/api/v1/webhook/evolution",
        json=payload,
        headers={"Content-Type": "application/json"}
    )

    return response.status_code == 200


def get_last_conversation_messages(token: str):
    """Busca últimas mensagens da conversa"""
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(
        f"{BACKEND_URL}/api/v1/dashboard/conversations",
        headers=headers
    )

    if response.status_code == 200:
        conversations = response.json()
        if conversations:
            # Pega a conversa mais recente
            latest = conversations[0]
            messages = latest.get('messages', [])
            return messages
    return []


def run_tests():
    """Executa todos os testes"""

    print("\n" + "="*70)
    print("  🧪 TESTE SIMPLIFICADO DE AGENTES - BotGas".center(70))
    print("="*70 + "\n")

    print(f"\n📋 Executando {sum(len(tests) for tests in TESTS.values())} testes...")
    print(f"⏱️ Aguarde alguns segundos entre cada teste para o bot processar...")
    print(f"⚠️  MODO SIMPLIFICADO: Apenas envia mensagens via webhook\n")

    results = []

    for category, messages in TESTS.items():
        print(f"\n{'='*70}")
        print(f"  📁 {category}".center(70))
        print(f"{'='*70}\n")

        for i, message in enumerate(messages, 1):
            print(f"[Teste {i}/{len(messages)}]")
            print(f"💬 Enviando: \"{message}\"")

            # Envia mensagem via webhook
            success = send_test_message_via_webhook(message)

            if success:
                print(f"✅ Mensagem enviada para o webhook")

                # Aguarda processamento
                print(f"⏳ Aguardando processamento (5s)...")
                time.sleep(5)

                results.append({
                    "category": category,
                    "message": message,
                    "response": "Webhook processado",
                    "intent": "webhook_sent",
                    "success": True
                })

            else:
                print(f"❌ Erro ao enviar mensagem para webhook")
                results.append({
                    "category": category,
                    "message": message,
                    "response": "Erro no envio",
                    "intent": "error",
                    "success": False
                })

            print()

    # Resumo
    print(f"\n{'='*70}")
    print("  📊 RESUMO DOS TESTES".center(70))
    print(f"{'='*70}\n")

    total_tests = len(results)
    successful_tests = sum(1 for r in results if r["success"])

    print(f"✅ Testes bem-sucedidos: {successful_tests}/{total_tests}")
    print(f"❌ Testes com falha: {total_tests - successful_tests}/{total_tests}\n")

    # Salva relatório
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"scripts/simple_test_{timestamp}.json"

    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": timestamp,
            "results": results
        }, f, indent=2, ensure_ascii=False)

    print(f"💾 Relatório salvo em: {report_file}\n")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    try:
        run_tests()
    except KeyboardInterrupt:
        print("\n\n⚠️ Teste interrompido pelo usuário.\n")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {str(e)}\n")
        import traceback
        traceback.print_exc()
