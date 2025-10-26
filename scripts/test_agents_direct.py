"""
Script de Teste Direto dos Agentes

Testa os agentes fazendo requisições HTTP diretas ao backend.
NÃO usa Evolution API, NÃO envia para WhatsApp.
Apenas testa os agentes isoladamente.

Uso:
    python scripts/test_agents_direct.py
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
BACKEND_URL = "http://localhost:8000"

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


def test_agent_endpoint(message: str) -> dict:
    """
    Testa endpoint direto do agente (se existir)

    Args:
        message: Mensagem de teste

    Returns:
        dict com response e status
    """
    # Vamos tentar criar um endpoint de teste no backend
    url = f"{BACKEND_URL}/api/v1/agents/test"

    payload = {
        "message": message
    }

    try:
        response = requests.post(url, json=payload, timeout=30)

        if response.status_code == 200:
            return {
                "success": True,
                "response": response.json().get("response", ""),
                "intent": response.json().get("intent", "unknown"),
                "agent": response.json().get("agent", "unknown")
            }
        else:
            return {
                "success": False,
                "error": f"Status {response.status_code}",
                "detail": response.text[:200]
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def run_tests():
    """Executa todos os testes"""

    print("\n" + "="*70)
    print("  🧪 TESTE DIRETO DOS AGENTES - BotGas".center(70))
    print("="*70 + "\n")

    print(f"🔗 Backend: {BACKEND_URL}")
    print(f"📋 Total de testes: {sum(len(tests) for tests in TESTS.values())}")
    print(f"⚠️  Testando agentes SEM WhatsApp/Evolution\n")

    # Verifica se backend está online
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend está online\n")
        else:
            print("⚠️  Backend respondeu mas com status diferente\n")
    except:
        print("❌ Backend não está respondendo!")
        print("   Certifique-se que o Docker está rodando: docker-compose ps\n")
        return

    results = []
    test_number = 0
    total_tests = sum(len(tests) for tests in TESTS.values())

    for category, messages in TESTS.items():
        print("\n" + "="*70)
        print(f"  📁 {category}".center(70))
        print("="*70 + "\n")

        for message in messages:
            test_number += 1

            print(f"[Teste {test_number}/{total_tests}]")
            print(f"💬 Testando: \"{message}\"")

            # Testa o agente
            result = test_agent_endpoint(message)

            if result.get("success"):
                response_text = result.get("response", "")
                intent = result.get("intent", "unknown")
                agent = result.get("agent", "unknown")

                print(f"✅ Agente: {agent}")
                print(f"🎯 Intent: {intent}")
                print(f"🤖 Resposta: {response_text[:150]}...")

                results.append({
                    "category": category,
                    "message": message,
                    "success": True,
                    "agent": agent,
                    "intent": intent,
                    "response": response_text,
                    "timestamp": datetime.now().isoformat()
                })
            else:
                error = result.get("error", "Erro desconhecido")
                print(f"❌ Erro: {error}")

                results.append({
                    "category": category,
                    "message": message,
                    "success": False,
                    "error": error,
                    "timestamp": datetime.now().isoformat()
                })

            print()

    # Resumo
    print("="*70)
    print("  📊 RESUMO DOS TESTES".center(70))
    print("="*70 + "\n")

    successful = sum(1 for r in results if r.get('success'))
    failed = sum(1 for r in results if not r.get('success'))

    print(f"✅ Testes bem-sucedidos: {successful}/{len(results)}")
    print(f"❌ Testes com falha: {failed}/{len(results)}\n")

    if successful > 0:
        # Agrupa por agente
        agents_used = {}
        for r in results:
            if r.get('success'):
                agent = r.get('agent', 'unknown')
                agents_used[agent] = agents_used.get(agent, 0) + 1

        print("📊 Uso dos Agentes:")
        for agent, count in sorted(agents_used.items()):
            print(f"   {agent}: {count} mensagens")
        print()

    # Salva relatório
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"scripts/direct_test_{timestamp}.json"

    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": timestamp,
            "backend_url": BACKEND_URL,
            "total_tests": len(results),
            "successful": successful,
            "failed": failed,
            "results": results
        }, f, indent=2, ensure_ascii=False)

    print(f"💾 Relatório salvo em: {report_file}\n")
    print("="*70 + "\n")


if __name__ == "__main__":
    try:
        run_tests()
    except KeyboardInterrupt:
        print("\n\n⚠️  Teste interrompido pelo usuário.\n")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {str(e)}\n")
