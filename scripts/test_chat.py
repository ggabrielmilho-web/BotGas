"""
Script de Teste Interativo - BotGas Agents

Permite conversar com o MasterAgent via terminal, simulando uma conversa real
com o WhatsApp, mas sem precisar de WhatsApp/Evolution API.

Uso:
    cd C:\Phyton-Projetos\BotGas
    python scripts/test_chat.py

Digite suas mensagens e receba respostas do GPT-4 em tempo real.
Digite 'sair' ou Ctrl+C para encerrar.
"""

import sys
import os
from uuid import uuid4, UUID
from datetime import datetime
from typing import Dict, Any

# Adiciona o diretório raiz ao path para importar os módulos do backend
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
    """Mock de um Tenant para testes"""
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


class ProductMock:
    """Mock de produto para testes"""
    def __init__(self, name: str, price: float, available: bool = True):
        self.id = uuid4()
        self.name = name
        self.description = f"Botija de gás {name}"
        self.price = price
        self.is_available = available


def print_header():
    """Imprime o cabeçalho do chat"""
    print("\n" + "="*70)
    print("  🤖 BOTGAS - TESTE INTERATIVO DE AGENTES".center(70))
    print("="*70)
    print("\n📋 INSTRUÇÕES:")
    print("  • Digite suas mensagens e pressione Enter")
    print("  • O bot responderá simulando uma conversa real")
    print("  • Digite 'sair' ou pressione Ctrl+C para encerrar")
    print("  • Digite 'limpar' para resetar a conversa")
    print("\n" + "-"*70 + "\n")


def print_message(role: str, content: str, agent_name: str = None):
    """Formata e imprime uma mensagem"""
    timestamp = datetime.now().strftime("%H:%M:%S")

    if role == "user":
        print(f"\n[{timestamp}] 👤 Você:")
        print(f"  {content}")
    else:
        agent_info = f" ({agent_name})" if agent_name else ""
        print(f"\n[{timestamp}] 🤖 Bot{agent_info}:")
        print(f"  {content}")
    print()


async def main():
    """Função principal do chat interativo"""

    # Inicializa o agente mestre
    master_agent = MasterAgent()

    # Mock de tenant e produtos
    tenant = TenantMock()
    products = [
        ProductMock("P13 (13kg)", 95.00),
        ProductMock("P20 (20kg)", 120.00),
        ProductMock("P45 (45kg)", 230.00),
    ]

    # Contexto da conversa
    conversation_id = uuid4()
    customer_phone = "5534996554613"  # Telefone de teste

    # Histórico de mensagens
    message_history = []

    # Session data (contexto compartilhado entre agentes)
    session_data: Dict[str, Any] = {
        "stage": "greeting"
    }

    # Imprime cabeçalho
    print_header()

    print("💬 Iniciando conversa simulada...")
    print(f"📍 Tenant: {tenant.company_name}")
    print(f"📱 Telefone: {customer_phone}")
    print(f"🆔 Conversa ID: {conversation_id}")
    print(f"\n{'='*70}\n")

    # Loop principal do chat
    try:
        while True:
            # Lê input do usuário
            user_input = input("Você: ").strip()

            # Comandos especiais
            if user_input.lower() in ['sair', 'exit', 'quit']:
                print("\n👋 Encerrando chat. Até logo!\n")
                break

            if user_input.lower() in ['limpar', 'clear', 'reset']:
                message_history = []
                session_data = {"stage": "greeting"}
                print("\n🔄 Conversa resetada!\n")
                continue

            if not user_input:
                continue

            # Adiciona mensagem do usuário ao histórico
            user_message = {
                "role": "user",
                "content": user_input,
                "timestamp": datetime.utcnow().isoformat(),
                "type": "text"
            }
            message_history.append(user_message)

            # Cria contexto do agente
            agent_context = AgentContext(
                tenant_id=UUID(str(tenant.id)),
                customer_phone=customer_phone,
                conversation_id=UUID(str(conversation_id)),
                session_data=session_data,
                message_history=message_history
            )

            # Processa mensagem com o MasterAgent
            # Nota: Em produção, isso seria feito dentro do webhook
            # Aqui estamos simulando sem banco de dados
            print("\n⏳ Processando...")

            try:
                # Chama o agente (sem passar db, pois não temos)
                response = await master_agent.process(
                    message={"type": "text", "content": user_input},
                    context=agent_context,
                    db=None  # Mock - não usa banco de dados
                )

                if response:
                    # Imprime resposta do bot
                    print_message(
                        "assistant",
                        response.text,
                        agent_name=response.intent or "MasterAgent"
                    )

                    # Adiciona resposta ao histórico
                    assistant_message = {
                        "role": "assistant",
                        "content": response.text,
                        "timestamp": datetime.utcnow().isoformat(),
                        "type": "text",
                        "intent": response.intent
                    }
                    message_history.append(assistant_message)

                    # Atualiza session_data com updates do agente
                    if response.context_updates:
                        session_data.update(response.context_updates)

                        # Debug: mostra contexto atualizado
                        if os.getenv("DEBUG") == "true":
                            print(f"\n[DEBUG] Contexto atualizado: {session_data}\n")

                else:
                    print("\n⚠️ Nenhuma resposta recebida do agente.\n")

            except Exception as e:
                print(f"\n❌ Erro ao processar mensagem: {str(e)}\n")
                if os.getenv("DEBUG") == "true":
                    import traceback
                    traceback.print_exc()

    except KeyboardInterrupt:
        print("\n\n👋 Chat interrompido. Até logo!\n")

    except Exception as e:
        print(f"\n❌ Erro inesperado: {str(e)}\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import asyncio

    # Verifica se OpenAI API key está configurada
    if not os.getenv("OPENAI_API_KEY"):
        print("\n❌ ERRO: OPENAI_API_KEY não encontrada!")
        print("Configure no arquivo .env na raiz do projeto.\n")
        sys.exit(1)

    # Executa o chat
    asyncio.run(main())
