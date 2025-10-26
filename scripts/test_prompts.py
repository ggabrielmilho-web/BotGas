"""
Script de Testes Automatizados - BotGas Agents

Executa cenários pré-definidos para testar todos os agentes do sistema.
Útil para validar prompts e respostas após mudanças nos agentes.

Uso:
    cd C:\Phyton-Projetos\BotGas
    python scripts/test_prompts.py

Testa:
- AttendanceAgent (saudações, produtos, informações)
- ValidationAgent (validação de endereços)
- OrderAgent (criação de pedidos)
- PaymentAgent (formas de pagamento)
"""

import sys
import os
from uuid import uuid4, UUID
from datetime import datetime
from typing import List, Dict, Any

# Adiciona o diretório raiz ao path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
backend_dir = os.path.join(root_dir, 'backend')
sys.path.insert(0, root_dir)
sys.path.insert(0, backend_dir)

# Carrega variáveis de ambiente
from dotenv import load_dotenv
load_dotenv(os.path.join(root_dir, '.env'))

# Importa os agentes
from app.agents.master import MasterAgent
from app.agents.base import AgentContext


class TenantMock:
    """Mock de Tenant"""
    def __init__(self):
        self.id = uuid4()
        self.company_name = "Distribuidora Teste"
        self.phone = "5534999999999"
        self.address = {
            "street": "Rua Teste, 123",
            "neighborhood": "Centro",
            "city": "Uberlândia",
            "state": "MG"
        }
        self.pix_enabled = True
        self.pix_key = "34999999999"
        self.pix_name = "Distribuidora Teste LTDA"
        self.payment_methods = ["pix", "dinheiro", "cartao"]


# Cenários de teste
TEST_SCENARIOS = [
    {
        "name": "Saudação Inicial",
        "messages": [
            "Olá",
            "Boa tarde"
        ],
        "expected_agent": "attendance",
        "description": "Testa se o bot responde adequadamente a saudações"
    },
    {
        "name": "Consulta de Produtos",
        "messages": [
            "Quanto custa a botija de gás?",
            "Quais produtos vocês tem?",
            "Preço do P13?"
        ],
        "expected_agent": "attendance",
        "description": "Testa se o bot fornece informações de produtos"
    },
    {
        "name": "Pedido de Produto",
        "messages": [
            "Quero comprar uma botija",
            "Preciso de um P13"
        ],
        "expected_agent": "order",
        "description": "Testa início do fluxo de pedido"
    },
    {
        "name": "Informação de Endereço",
        "messages": [
            "Meu endereço é Rua A, 100, Centro, Uberlândia",
        ],
        "expected_agent": "validation",
        "description": "Testa validação de endereço"
    },
    {
        "name": "Horário de Funcionamento",
        "messages": [
            "Qual o horário de funcionamento?",
            "Vocês abrem que horas?"
        ],
        "expected_agent": "attendance",
        "description": "Testa se o bot fornece informações gerais"
    },
    {
        "name": "Forma de Pagamento",
        "messages": [
            "Aceita PIX?",
            "Posso pagar no cartão?"
        ],
        "expected_agent": "payment",
        "description": "Testa informações sobre pagamento"
    }
]


def print_header():
    """Imprime cabeçalho"""
    print("\n" + "="*70)
    print("  🧪 BOTGAS - TESTES AUTOMATIZADOS DE AGENTES".center(70))
    print("="*70)
    print()


def print_scenario_header(scenario: Dict[str, Any], index: int, total: int):
    """Imprime cabeçalho de cenário"""
    print(f"\n{'-'*70}")
    print(f"📋 Cenário {index}/{total}: {scenario['name']}")
    print(f"📝 Descrição: {scenario['description']}")
    print(f"🎯 Agente esperado: {scenario['expected_agent']}")
    print(f"{'-'*70}\n")


def print_test_result(message: str, response: str, agent: str):
    """Imprime resultado de um teste"""
    print(f"💬 Mensagem: \"{message}\"")
    print(f"🤖 Resposta ({agent}):")
    print(f"   {response[:200]}..." if len(response) > 200 else f"   {response}")
    print()


async def run_scenario(scenario: Dict[str, Any], master_agent: MasterAgent, tenant: TenantMock):
    """Executa um cenário de teste"""

    results = []

    for message_text in scenario["messages"]:
        # Cria contexto limpo para cada mensagem
        conversation_id = uuid4()
        customer_phone = "5534996554613"

        agent_context = AgentContext(
            tenant_id=UUID(str(tenant.id)),
            customer_phone=customer_phone,
            conversation_id=UUID(str(conversation_id)),
            session_data={"stage": "greeting"},
            message_history=[]
        )

        try:
            # Processa mensagem
            response = await master_agent.process(
                message={"type": "text", "content": message_text},
                context=agent_context,
                db=None
            )

            if response:
                results.append({
                    "message": message_text,
                    "response": response.text,
                    "agent": response.intent or "unknown",
                    "success": True
                })

                print_test_result(message_text, response.text, response.intent or "unknown")

            else:
                results.append({
                    "message": message_text,
                    "response": "⚠️ Sem resposta",
                    "agent": "none",
                    "success": False
                })

                print(f"💬 Mensagem: \"{message_text}\"")
                print(f"❌ Erro: Nenhuma resposta recebida\n")

        except Exception as e:
            results.append({
                "message": message_text,
                "response": f"Erro: {str(e)}",
                "agent": "error",
                "success": False
            })

            print(f"💬 Mensagem: \"{message_text}\"")
            print(f"❌ Erro: {str(e)}\n")

    return results


async def main():
    """Função principal"""

    print_header()

    # Verifica OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("\n❌ ERRO: OPENAI_API_KEY não encontrada!")
        print("Configure no arquivo .env na raiz do projeto.\n")
        sys.exit(1)

    print("🚀 Inicializando testes...")
    print(f"📊 Total de cenários: {len(TEST_SCENARIOS)}")
    print()

    # Inicializa agente e tenant
    master_agent = MasterAgent()
    tenant = TenantMock()

    # Resultados gerais
    all_results = []

    # Executa cada cenário
    for index, scenario in enumerate(TEST_SCENARIOS, 1):
        print_scenario_header(scenario, index, len(TEST_SCENARIOS))

        results = await run_scenario(scenario, master_agent, tenant)
        all_results.extend(results)

    # Resumo final
    print(f"\n{'='*70}")
    print("  📊 RESUMO DOS TESTES".center(70))
    print(f"{'='*70}\n")

    total_tests = len(all_results)
    successful_tests = sum(1 for r in all_results if r["success"])
    failed_tests = total_tests - successful_tests

    print(f"✅ Testes bem-sucedidos: {successful_tests}/{total_tests}")
    print(f"❌ Testes com falha: {failed_tests}/{total_tests}")

    if failed_tests > 0:
        print(f"\n⚠️ Testes que falharam:")
        for result in all_results:
            if not result["success"]:
                print(f"   • \"{result['message']}\" → {result['response']}")

    print(f"\n{'='*70}\n")

    # Retorna código de saída
    sys.exit(0 if failed_tests == 0 else 1)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
