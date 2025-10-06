#!/usr/bin/env python3
"""
Script de testes automatizados para o sistema de agentes BotGas
Envia mensagens via Evolution API e verifica respostas no banco de dados
"""
import asyncio
import httpx
import psycopg2
import json
import time
from datetime import datetime
from typing import Dict, List, Optional

# Configurações
EVOLUTION_API_URL = "https://api.carvalhoia.com"
EVOLUTION_API_KEY = "03fd4f2fc18afc835d3e83d343eae714"
INSTANCE_NAME = "tenant_6bf18c92-943e-43e9-a407-39a98e026165"
TEST_PHONE = "5511999999999"  # Número de teste - ALTERE PARA SEU NÚMERO

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "gasbot",
    "user": "gasbot",
    "password": "password"
}

# Categorias de teste
TEST_CASES = {
    "1. Saudação": [
        {"message": "Oi", "expected_intent": "greeting", "expected_keywords": ["menu", "ajudar", "produtos"]},
        {"message": "Olá", "expected_intent": "greeting", "expected_keywords": ["menu", "ajudar"]},
        {"message": "Bom dia", "expected_intent": "greeting", "expected_keywords": ["ajudar", "produtos"]},
    ],

    "2. Consulta de Produtos": [
        {"message": "Quais produtos?", "expected_intent": "product_inquiry", "expected_keywords": ["botijão", "p13", "preço", "r$"]},
        {"message": "Preços", "expected_intent": "product_inquiry", "expected_keywords": ["r$", "botijão"]},
        {"message": "Quanto custa?", "expected_intent": "product_inquiry", "expected_keywords": ["r$"]},
    ],

    "3. Início de Pedido": [
        {"message": "Quero fazer um pedido", "expected_intent": "make_order", "expected_keywords": ["produto", "botijão", "endereço"]},
        {"message": "Quero 1 botijão", "expected_intent": "make_order", "expected_keywords": ["endereço", "confirma"]},
        {"message": "Uma botija por favor", "expected_intent": "make_order", "expected_keywords": ["endereço"]},
    ],

    "4. Fornecimento de Endereço": [
        {"message": "Rua das Flores, 123", "expected_intent": "provide_address", "expected_keywords": ["confirma", "endereço", "bairro"]},
        {"message": "Av. Principal, 500 - Centro", "expected_intent": "provide_address", "expected_keywords": ["confirma"]},
    ],

    "5. Perguntas Gerais": [
        {"message": "Qual seu horário?", "expected_intent": "general", "expected_keywords": ["horário", "funciona"]},
        {"message": "Fazem entrega?", "expected_intent": "general", "expected_keywords": ["entrega", "sim"]},
    ],

    "6. Solicitação de Atendente": [
        {"message": "Quero falar com atendente", "expected_intent": "human_requested", "expected_keywords": ["atendente", "momento", "chamar"]},
        {"message": "Falar com uma pessoa", "expected_intent": "human_requested", "expected_keywords": ["atendente"]},
    ],
}


class BotTester:
    def __init__(self):
        self.headers = {
            "apikey": EVOLUTION_API_KEY,
            "Content-Type": "application/json"
        }
        self.results = []
        self.conversation_id = None

    def get_db_connection(self):
        """Conecta ao PostgreSQL"""
        return psycopg2.connect(**DB_CONFIG)

    def get_last_bot_response(self, phone: str) -> Optional[Dict]:
        """Busca última resposta do bot no banco de dados"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            query = """
                SELECT c.id, c.messages, c.context
                FROM conversations c
                JOIN customers cu ON c.customer_id = cu.id
                WHERE cu.whatsapp_number = %s
                ORDER BY c.started_at DESC
                LIMIT 1
            """

            cursor.execute(query, (phone,))
            result = cursor.fetchone()

            if result:
                conv_id, messages_json, context_json = result
                self.conversation_id = conv_id

                messages = json.loads(messages_json) if messages_json else []

                # Pega última mensagem do bot
                for msg in reversed(messages):
                    if msg.get('role') == 'assistant':
                        return msg

            cursor.close()
            conn.close()
            return None

        except Exception as e:
            print(f"   ⚠️  Erro ao buscar resposta no banco: {e}")
            return None

    async def send_message(self, message: str) -> bool:
        """Envia mensagem via Evolution API"""
        url = f"{EVOLUTION_API_URL}/message/sendText/{INSTANCE_NAME}"

        data = {
            "number": TEST_PHONE,
            "text": message
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=self.headers, json=data)

                if response.status_code == 200:
                    return True
                else:
                    print(f"   ❌ Erro ao enviar: {response.status_code} - {response.text}")
                    return False

        except Exception as e:
            print(f"   ❌ Exceção ao enviar: {e}")
            return False

    def check_response(self, response: Dict, expected_intent: str, expected_keywords: List[str]) -> Dict:
        """Verifica se resposta está correta"""
        result = {
            "intent_match": False,
            "keywords_found": [],
            "has_response": False
        }

        if not response:
            return result

        result["has_response"] = True

        # Verifica intent
        actual_intent = response.get('intent', '')
        if actual_intent == expected_intent:
            result["intent_match"] = True

        # Verifica keywords no conteúdo
        content = response.get('content', '').lower()
        for keyword in expected_keywords:
            if keyword.lower() in content:
                result["keywords_found"].append(keyword)

        return result

    async def run_test_case(self, category: str, test: Dict, test_num: int, total: int):
        """Executa um caso de teste"""
        message = test["message"]
        expected_intent = test["expected_intent"]
        expected_keywords = test["expected_keywords"]

        print(f"\n[{test_num}/{total}] Testando: '{message}'")

        # 1. Envia mensagem
        print("   📤 Enviando mensagem...")
        sent = await self.send_message(message)

        if not sent:
            self.results.append({
                "category": category,
                "message": message,
                "status": "❌ FALHA",
                "error": "Não conseguiu enviar mensagem"
            })
            return

        # 2. Aguarda processamento (bot precisa tempo para processar)
        print("   ⏳ Aguardando resposta do bot (5s)...")
        await asyncio.sleep(5)

        # 3. Busca resposta no banco
        print("   🔍 Buscando resposta no banco...")
        response = self.get_last_bot_response(TEST_PHONE)

        # 4. Verifica resposta
        check = self.check_response(response, expected_intent, expected_keywords)

        if not check["has_response"]:
            print("   ❌ Bot não respondeu!")
            self.results.append({
                "category": category,
                "message": message,
                "status": "❌ SEM RESPOSTA",
                "error": "Bot não gerou resposta"
            })
            return

        # 5. Avalia resultado
        intent_ok = "✅" if check["intent_match"] else "❌"
        keywords_ok = len(check["keywords_found"])
        keywords_total = len(expected_keywords)

        print(f"   {intent_ok} Intent: esperado='{expected_intent}', recebido='{response.get('intent')}'")
        print(f"   📝 Keywords: {keywords_ok}/{keywords_total} encontradas: {check['keywords_found']}")
        print(f"   💬 Resposta: {response.get('content', '')[:100]}...")

        # Status geral
        if check["intent_match"] and keywords_ok >= (keywords_total * 0.5):  # 50% das keywords
            status = "✅ PASSOU"
        elif check["has_response"]:
            status = "⚠️  PARCIAL"
        else:
            status = "❌ FALHOU"

        self.results.append({
            "category": category,
            "message": message,
            "status": status,
            "intent_expected": expected_intent,
            "intent_actual": response.get('intent'),
            "keywords_found": f"{keywords_ok}/{keywords_total}",
            "response": response.get('content', '')[:100]
        })

    async def run_all_tests(self):
        """Executa todos os testes"""
        print("=" * 80)
        print("🧪 INICIANDO TESTES AUTOMATIZADOS DOS AGENTES")
        print("=" * 80)
        print(f"\n📱 Número de teste: {TEST_PHONE}")
        print(f"🤖 Instância: {INSTANCE_NAME}")
        print(f"⏰ Início: {datetime.now().strftime('%H:%M:%S')}\n")

        # Conta total de testes
        total_tests = sum(len(tests) for tests in TEST_CASES.values())
        current_test = 0

        # Executa cada categoria
        for category, tests in TEST_CASES.items():
            print("\n" + "=" * 80)
            print(f"📂 {category}")
            print("=" * 80)

            for test in tests:
                current_test += 1
                await self.run_test_case(category, test, current_test, total_tests)

                # Pequena pausa entre testes
                await asyncio.sleep(2)

        # Exibe resultados finais
        self.print_summary()

    def print_summary(self):
        """Exibe resumo dos resultados"""
        print("\n\n" + "=" * 80)
        print("📊 RESUMO DOS TESTES")
        print("=" * 80)

        passed = sum(1 for r in self.results if "✅" in r["status"])
        partial = sum(1 for r in self.results if "⚠️" in r["status"])
        failed = sum(1 for r in self.results if "❌" in r["status"])
        total = len(self.results)

        print(f"\n✅ Passou: {passed}/{total}")
        print(f"⚠️  Parcial: {partial}/{total}")
        print(f"❌ Falhou: {failed}/{total}")

        success_rate = (passed / total * 100) if total > 0 else 0
        print(f"\n📈 Taxa de sucesso: {success_rate:.1f}%")

        # Detalhes por categoria
        print("\n" + "-" * 80)
        print("DETALHES POR CATEGORIA")
        print("-" * 80)

        current_category = None
        for result in self.results:
            if result["category"] != current_category:
                current_category = result["category"]
                print(f"\n{current_category}")

            print(f"  {result['status']} | {result['message']}")
            if "intent_actual" in result:
                print(f"     Intent: {result['intent_actual']} | Keywords: {result['keywords_found']}")

        # Salva em arquivo
        self.save_results()

        print("\n" + "=" * 80)
        print(f"⏰ Fim: {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 80)

    def save_results(self):
        """Salva resultados em arquivo JSON"""
        filename = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "phone": TEST_PHONE,
                "instance": INSTANCE_NAME,
                "conversation_id": str(self.conversation_id) if self.conversation_id else None,
                "results": self.results
            }, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Resultados salvos em: {filename}")


async def main():
    """Função principal"""
    print("\n⚠️  ATENÇÃO:")
    print(f"   - Certifique-se de que o número {TEST_PHONE} está correto!")
    print(f"   - Este script enviará mensagens reais via WhatsApp")
    print(f"   - O bot responderá a cada mensagem")
    print(f"   - Total de ~{sum(len(tests) for tests in TEST_CASES.values())} mensagens serão enviadas\n")

    response = input("Deseja continuar? (s/n): ")

    if response.lower() != 's':
        print("Testes cancelados.")
        return

    tester = BotTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Testes interrompidos pelo usuário")
    except Exception as e:
        print(f"\n\n❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()
