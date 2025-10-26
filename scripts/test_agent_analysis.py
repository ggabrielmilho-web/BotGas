"""
Script de Análise de Desempenho dos Agentes - BotGas

Testa cada agente individualmente e gera relatório de performance
mostrando quais estão funcionando bem e quais precisam de ajustes.

Uso:
    cd C:\Phyton-Projetos\BotGas
    python scripts/test_agent_analysis.py

Gera:
- Relatório de cada agente (AttendanceAgent, ValidationAgent, OrderAgent, PaymentAgent)
- Score de qualidade das respostas
- Identificação de problemas
- Recomendações de melhorias
"""

import sys
import os
from uuid import uuid4, UUID
from datetime import datetime
from typing import List, Dict, Any
import json

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


# Testes por agente
AGENT_TESTS = {
    "AttendanceAgent": {
        "description": "Agente de Atendimento - Saudações e Informações Gerais",
        "tests": [
            {
                "message": "Olá",
                "expected_keywords": ["olá", "bem-vindo", "ajudar"],
                "weight": 10
            },
            {
                "message": "Boa tarde",
                "expected_keywords": ["boa", "tarde", "ajudar"],
                "weight": 10
            },
            {
                "message": "Quanto custa a botija de gás?",
                "expected_keywords": ["preço", "r$", "valor", "custa"],
                "weight": 20
            },
            {
                "message": "Quais produtos vocês tem?",
                "expected_keywords": ["produto", "p13", "p20", "botija"],
                "weight": 20
            },
            {
                "message": "Qual o horário de funcionamento?",
                "expected_keywords": ["horário", "aberto", "funciona", "atende"],
                "weight": 15
            },
            {
                "message": "Qual o telefone?",
                "expected_keywords": ["telefone", "contato", "5534", "whatsapp"],
                "weight": 10
            },
            {
                "message": "Onde vocês ficam?",
                "expected_keywords": ["endereço", "rua", "fica", "local"],
                "weight": 15
            }
        ]
    },
    "OrderAgent": {
        "description": "Agente de Pedidos - Montagem de Pedidos",
        "tests": [
            {
                "message": "Quero comprar uma botija",
                "expected_keywords": ["pedido", "endereço", "entregar", "onde"],
                "weight": 30
            },
            {
                "message": "Preciso de um P13",
                "expected_keywords": ["p13", "endereço", "entrega", "onde"],
                "weight": 30
            },
            {
                "message": "Quero fazer um pedido",
                "expected_keywords": ["produto", "qual", "endereço", "escolha"],
                "weight": 20
            },
            {
                "message": "Pode entregar 2 botijas?",
                "expected_keywords": ["endereço", "onde", "entrega", "local"],
                "weight": 20
            }
        ]
    },
    "ValidationAgent": {
        "description": "Agente de Validação - Verificação de Endereços",
        "tests": [
            {
                "message": "Rua das Flores, 123, Centro, Uberlândia",
                "expected_keywords": ["endereço", "entregamos", "confirma", "correto"],
                "weight": 40
            },
            {
                "message": "Meu endereço é Av Paulista, 100",
                "expected_keywords": ["validando", "endereço", "entrega", "área"],
                "weight": 30
            },
            {
                "message": "Bairro Centro",
                "expected_keywords": ["endereço", "completo", "rua", "número"],
                "weight": 30
            }
        ]
    },
    "PaymentAgent": {
        "description": "Agente de Pagamento - Formas de Pagamento",
        "tests": [
            {
                "message": "Aceita PIX?",
                "expected_keywords": ["pix", "aceita", "sim", "chave"],
                "weight": 30
            },
            {
                "message": "Posso pagar no cartão?",
                "expected_keywords": ["cartão", "aceita", "sim", "débito", "crédito"],
                "weight": 25
            },
            {
                "message": "Qual a forma de pagamento?",
                "expected_keywords": ["pix", "dinheiro", "cartão", "pagamento"],
                "weight": 25
            },
            {
                "message": "Vou pagar no dinheiro",
                "expected_keywords": ["dinheiro", "troco", "precisar"],
                "weight": 20
            }
        ]
    }
}


def calculate_score(response: str, expected_keywords: List[str]) -> float:
    """Calcula score baseado nas keywords presentes na resposta"""
    response_lower = response.lower()
    found_keywords = sum(1 for keyword in expected_keywords if keyword.lower() in response_lower)
    return (found_keywords / len(expected_keywords)) * 100 if expected_keywords else 0


def analyze_response_quality(response: str) -> Dict[str, Any]:
    """Analisa qualidade da resposta"""
    issues = []

    # Verifica se a resposta é muito curta
    if len(response) < 20:
        issues.append("Resposta muito curta")

    # Verifica se a resposta é muito longa
    if len(response) > 500:
        issues.append("Resposta muito longa")

    # Verifica se tem emojis (bom para engajamento)
    has_emojis = any(char in response for char in "😊✅🎯📍💬🤖❤️👍")

    # Verifica se tem formatação
    has_formatting = any(char in response for char in "*_`")

    return {
        "length": len(response),
        "has_emojis": has_emojis,
        "has_formatting": has_formatting,
        "issues": issues
    }


async def test_agent(agent_name: str, tests: List[Dict[str, Any]], master_agent: MasterAgent, tenant: TenantMock) -> Dict[str, Any]:
    """Testa um agente específico"""

    results = []
    total_score = 0
    total_weight = 0

    for test in tests:
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
            response = await master_agent.process(
                message={"type": "text", "content": test["message"]},
                context=agent_context,
                db=None
            )

            if response:
                # Calcula score
                score = calculate_score(response.text, test["expected_keywords"])
                quality = analyze_response_quality(response.text)

                weighted_score = score * (test["weight"] / 100)
                total_score += weighted_score
                total_weight += test["weight"]

                results.append({
                    "message": test["message"],
                    "response": response.text,
                    "agent_detected": response.intent or "unknown",
                    "score": round(score, 1),
                    "weighted_score": round(weighted_score, 1),
                    "weight": test["weight"],
                    "quality": quality,
                    "success": True
                })
            else:
                results.append({
                    "message": test["message"],
                    "response": "Sem resposta",
                    "agent_detected": "none",
                    "score": 0,
                    "weighted_score": 0,
                    "weight": test["weight"],
                    "quality": {"issues": ["Sem resposta"]},
                    "success": False
                })

        except Exception as e:
            results.append({
                "message": test["message"],
                "response": f"Erro: {str(e)}",
                "agent_detected": "error",
                "score": 0,
                "weighted_score": 0,
                "weight": test["weight"],
                "quality": {"issues": [str(e)]},
                "success": False
            })

    # Calcula score final
    final_score = (total_score / total_weight * 100) if total_weight > 0 else 0

    # Classifica performance
    if final_score >= 80:
        performance = "EXCELENTE ✅"
    elif final_score >= 60:
        performance = "BOM 👍"
    elif final_score >= 40:
        performance = "REGULAR ⚠️"
    else:
        performance = "PRECISA MELHORAR ❌"

    return {
        "agent_name": agent_name,
        "final_score": round(final_score, 1),
        "performance": performance,
        "total_tests": len(tests),
        "successful_tests": sum(1 for r in results if r["success"]),
        "results": results
    }


def print_agent_report(report: Dict[str, Any]):
    """Imprime relatório de um agente"""

    print(f"\n{'='*80}")
    print(f"  {report['agent_name']}".center(80))
    print(f"{'='*80}\n")

    print(f"📊 PERFORMANCE GERAL: {report['performance']}")
    print(f"🎯 Score Final: {report['final_score']}%")
    print(f"✅ Testes Bem-sucedidos: {report['successful_tests']}/{report['total_tests']}")
    print(f"\n{'-'*80}\n")

    for i, result in enumerate(report['results'], 1):
        print(f"[Teste {i}/{len(report['results'])}] Peso: {result['weight']}%")
        print(f"💬 Mensagem: \"{result['message']}\"")
        print(f"🤖 Agente Detectado: {result['agent_detected']}")
        print(f"📈 Score: {result['score']}% (Ponderado: {result['weighted_score']})")

        if result['success']:
            print(f"💡 Resposta: {result['response'][:150]}...")

            # Qualidade
            quality = result['quality']
            print(f"   📏 Tamanho: {quality['length']} caracteres")
            if quality.get('has_emojis'):
                print(f"   😊 Contém emojis: Sim")
            if quality.get('has_formatting'):
                print(f"   📝 Contém formatação: Sim")
            if quality.get('issues'):
                print(f"   ⚠️ Problemas: {', '.join(quality['issues'])}")
        else:
            print(f"❌ {result['response']}")

        print()


def generate_summary(all_reports: List[Dict[str, Any]]):
    """Gera resumo geral de todos os agentes"""

    print(f"\n{'='*80}")
    print("  📊 RESUMO GERAL - ANÁLISE DE TODOS OS AGENTES".center(80))
    print(f"{'='*80}\n")

    # Ranking
    sorted_reports = sorted(all_reports, key=lambda x: x['final_score'], reverse=True)

    print("🏆 RANKING DE PERFORMANCE:\n")
    for i, report in enumerate(sorted_reports, 1):
        print(f"   {i}. {report['agent_name']}: {report['final_score']}% - {report['performance']}")

    print(f"\n{'-'*80}\n")

    # Estatísticas gerais
    total_tests = sum(r['total_tests'] for r in all_reports)
    total_success = sum(r['successful_tests'] for r in all_reports)
    avg_score = sum(r['final_score'] for r in all_reports) / len(all_reports)

    print("📈 ESTATÍSTICAS GERAIS:\n")
    print(f"   • Total de testes executados: {total_tests}")
    print(f"   • Testes bem-sucedidos: {total_success}/{total_tests} ({total_success/total_tests*100:.1f}%)")
    print(f"   • Score médio geral: {avg_score:.1f}%")

    print(f"\n{'-'*80}\n")

    # Recomendações
    print("💡 RECOMENDAÇÕES:\n")

    for report in all_reports:
        if report['final_score'] < 60:
            print(f"   ⚠️ {report['agent_name']} precisa de melhorias:")
            print(f"      - Revisar prompts do agente")
            print(f"      - Adicionar mais contexto nas respostas")
            print(f"      - Melhorar detecção de intenções")
            print()

    excellent_agents = [r for r in all_reports if r['final_score'] >= 80]
    if excellent_agents:
        print(f"   ✅ Agentes com excelente performance:")
        for report in excellent_agents:
            print(f"      - {report['agent_name']} ({report['final_score']}%)")
        print()

    print(f"{'='*80}\n")


async def main():
    """Função principal"""

    print("\n" + "="*80)
    print("  🔍 ANÁLISE DE DESEMPENHO DOS AGENTES - BotGas".center(80))
    print("="*80)
    print()

    # Verifica OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("\n❌ ERRO: OPENAI_API_KEY não encontrada!")
        print("Configure no arquivo .env na raiz do projeto.\n")
        sys.exit(1)

    print("🚀 Iniciando análise completa dos agentes...")
    print(f"📊 Agentes a serem testados: {len(AGENT_TESTS)}")
    print(f"⏱️ Isso pode levar alguns minutos...\n")

    # Inicializa
    master_agent = MasterAgent()
    tenant = TenantMock()
    all_reports = []

    # Testa cada agente
    for agent_name, agent_data in AGENT_TESTS.items():
        print(f"🔄 Testando {agent_name}... ({len(agent_data['tests'])} testes)")

        report = await test_agent(
            agent_name,
            agent_data['tests'],
            master_agent,
            tenant
        )

        all_reports.append(report)

    print("\n✅ Análise completa!\n")

    # Imprime relatórios individuais
    for report in all_reports:
        print_agent_report(report)

    # Imprime resumo geral
    generate_summary(all_reports)

    # Salva relatório em JSON
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = os.path.join(root_dir, 'scripts', f'agent_analysis_{timestamp}.json')

    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": timestamp,
            "reports": all_reports
        }, f, indent=2, ensure_ascii=False)

    print(f"💾 Relatório salvo em: {report_file}")
    print()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
