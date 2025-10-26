"""
Teste isolado do MessageExtractor
Importa apenas o necessário sem carregar todo o sistema
"""
import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

# Set environment variables
os.environ.setdefault("DATABASE_URL", "postgresql://dummy")
os.environ.setdefault("REDIS_URL", "redis://dummy")
os.environ.setdefault("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", ""))
os.environ.setdefault("EVOLUTION_API_URL", "http://dummy")
os.environ.setdefault("EVOLUTION_API_KEY", "dummy")
os.environ.setdefault("JWT_SECRET_KEY", "dummy")
os.environ.setdefault("WEBHOOK_URL", "http://dummy")
os.environ.setdefault("FINETUNED_EXTRACTOR_MODEL", "ft:gpt-4o-mini-2024-07-18:carvalho-ia:botgas:CTt20bmy")

# Import direto do arquivo, sem passar pelo __init__.py
import importlib.util
spec = importlib.util.spec_from_file_location(
    "message_extractor",
    backend_path / "app" / "agents" / "message_extractor.py"
)
message_extractor_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(message_extractor_module)

MessageExtractor = message_extractor_module.MessageExtractor


async def test_simple_message():
    """Teste 1: mensagem simples"""
    print("\n" + "="*60)
    print("TESTE 1: Mensagem simples")
    print("="*60)

    extractor = MessageExtractor()
    result = await extractor.extract("quero um gas")

    print(f"\n📥 Input: 'quero um gas'")
    print(f"\n📤 Output:")
    print(f"  Product: {result['product']['name']} x{result['product']['quantity']} (conf: {result['product']['confidence']:.2f})")
    print(f"  Address: {result['address']['street'] or 'N/A'} (conf: {result['address']['confidence']:.2f})")
    print(f"  Payment: {result['payment']['method']} (conf: {result['payment']['confidence']:.2f})")
    print(f"  Urgent: {result['metadata']['is_urgent']}")
    print(f"  Tone: {result['metadata']['customer_tone']}")

    # Validações
    product_name_lower = result['product']['name'].lower()
    assert "p13" in product_name_lower or "13" in product_name_lower, \
        f"❌ Esperado P13, recebido: {result['product']['name']}"
    assert result['product']['quantity'] == 1, \
        f"❌ Esperado quantidade 1, recebido: {result['product']['quantity']}"
    assert result['product']['confidence'] > 0.6, \
        f"❌ Esperado confiança > 0.6, recebido: {result['product']['confidence']}"

    print("\n✅ TESTE 1 PASSOU!")
    return True


async def test_complete_message():
    """Teste 2: mensagem completa"""
    print("\n" + "="*60)
    print("🧪 TESTE 2: Mensagem completa")
    print("="*60)

    extractor = MessageExtractor()
    result = await extractor.extract("manda 1 gas na rua joao batista 45 centro pix")

    print(f"\n📥 Input: 'manda 1 gas na rua joao batista 45 centro pix'")
    print(f"\n📤 Output:")
    print(f"  Product: {result['product']['name']} x{result['product']['quantity']} (conf: {result['product']['confidence']:.2f})")
    print(f"  Address:")
    print(f"    - Street: {result['address']['street']}")
    print(f"    - Number: {result['address']['number']}")
    print(f"    - Neighborhood: {result['address']['neighborhood']}")
    print(f"    - Confidence: {result['address']['confidence']:.2f}")
    print(f"  Payment: {result['payment']['method']} (conf: {result['payment']['confidence']:.2f})")

    # Validações
    assert result['address']['street'] is not None, "❌ Rua não foi extraída"
    assert result['address']['number'] == "45", \
        f"❌ Esperado número 45, recebido: {result['address']['number']}"
    assert result['payment']['method'] == "pix", \
        f"❌ Esperado pagamento pix, recebido: {result['payment']['method']}"

    print("\n✅ TESTE 2 PASSOU!")
    return True


async def test_with_change():
    """Teste 3: com troco"""
    print("\n" + "="*60)
    print("🧪 TESTE 3: Com troco")
    print("="*60)

    extractor = MessageExtractor()
    result = await extractor.extract("2 p45 rua y 78 dinheiro troco pra 100")

    print(f"\n📥 Input: '2 p45 rua y 78 dinheiro troco pra 100'")
    print(f"\n📤 Output:")
    print(f"  Product: {result['product']['name']} x{result['product']['quantity']}")
    print(f"  Payment: {result['payment']['method']}")
    print(f"  Change for: R$ {result['payment']['change_for']}")
    print(f"  Has change request: {result['metadata']['has_change_request']}")

    # Validações
    product_name_lower = result['product']['name'].lower()
    assert "p45" in product_name_lower or "45" in product_name_lower, \
        f"❌ Esperado P45, recebido: {result['product']['name']}"
    assert result['product']['quantity'] == 2, \
        f"❌ Esperado quantidade 2, recebido: {result['product']['quantity']}"
    assert result['payment']['method'] == "dinheiro", \
        f"❌ Esperado pagamento dinheiro, recebido: {result['payment']['method']}"
    assert result['payment']['change_for'] == 100.0, \
        f"❌ Esperado troco 100.0, recebido: {result['payment']['change_for']}"

    print("\n✅ TESTE 3 PASSOU!")
    return True


async def test_urgent_message():
    """Teste 4: mensagem urgente"""
    print("\n" + "="*60)
    print("🧪 TESTE 4: Mensagem urgente")
    print("="*60)

    extractor = MessageExtractor()
    result = await extractor.extract("URGENTE preciso de gas rua x 12 centro pix")

    print(f"\n📥 Input: 'URGENTE preciso de gas rua x 12 centro pix'")
    print(f"\n📤 Output:")
    print(f"  Is urgent: {result['metadata']['is_urgent']}")
    print(f"  Customer tone: {result['metadata']['customer_tone']}")

    # Validações
    assert result['metadata']['is_urgent'] == True, \
        f"❌ Esperado urgente=True, recebido: {result['metadata']['is_urgent']}"
    assert result['metadata']['customer_tone'] == "urgent", \
        f"❌ Esperado tom urgent, recebido: {result['metadata']['customer_tone']}"

    print("\n✅ TESTE 4 PASSOU!")
    return True


async def test_polite_message():
    """Teste 5: mensagem educada"""
    print("\n" + "="*60)
    print("🧪 TESTE 5: Mensagem educada")
    print("="*60)

    extractor = MessageExtractor()
    result = await extractor.extract("quero gas rua z 56 pix por favor")

    print(f"\n📥 Input: 'quero gas rua z 56 pix por favor'")
    print(f"\n📤 Output:")
    print(f"  Customer tone: {result['metadata']['customer_tone']}")

    # Validação
    assert result['metadata']['customer_tone'] == "polite", \
        f"❌ Esperado tom polite, recebido: {result['metadata']['customer_tone']}"

    print("\n✅ TESTE 5 PASSOU!")
    return True


async def run_all_tests():
    """Executa todos os testes"""
    print("\n" + "="*60)
    print("🚀 INICIANDO TESTES DO MESSAGE EXTRACTOR")
    print("="*60)
    print(f"\n🔧 Modelo: {os.getenv('FINETUNED_EXTRACTOR_MODEL', 'NOT SET')}")

    tests = [
        ("Mensagem simples", test_simple_message),
        ("Mensagem completa", test_complete_message),
        ("Com troco", test_with_change),
        ("Mensagem urgente", test_urgent_message),
        ("Mensagem educada", test_polite_message),
    ]

    passed = 0
    failed = 0
    errors = []

    for test_name, test_func in tests:
        try:
            await test_func()
            passed += 1
        except AssertionError as e:
            print(f"\n❌ TESTE '{test_name}' FALHOU: {e}")
            failed += 1
            errors.append((test_name, str(e)))
        except Exception as e:
            print(f"\n❌ ERRO NO TESTE '{test_name}': {e}")
            failed += 1
            errors.append((test_name, f"Exception: {e}"))

    print("\n" + "="*60)
    print(f"📊 RESUMO DOS TESTES")
    print("="*60)
    print(f"✅ Passou: {passed}/{len(tests)}")
    print(f"❌ Falhou: {failed}/{len(tests)}")

    if failed > 0:
        print("\n📋 Erros encontrados:")
        for test_name, error in errors:
            print(f"  - {test_name}: {error}")

    if failed == 0:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("\n✅ MessageExtractor está funcionando corretamente!")
        print("✅ FASE 1 VALIDADA COM SUCESSO!")
    else:
        print(f"\n⚠️  {failed} teste(s) falharam")
        print("\nℹ️  Alguns testes podem falhar se o modelo fine-tuned")
        print("   ainda estiver em treinamento ou se a API key não estiver configurada.")

    print("="*60)

    return failed == 0


if __name__ == "__main__":
    # Verificar se OPENAI_API_KEY está configurada
    if not os.getenv("OPENAI_API_KEY"):
        print("\n" + "="*60)
        print("❌ ERRO: OPENAI_API_KEY não está configurada!")
        print("="*60)
        print("\n💡 Para rodar os testes, configure a variável de ambiente:")
        print("   export OPENAI_API_KEY='sua-chave-aqui'  # Linux/Mac")
        print("   set OPENAI_API_KEY=sua-chave-aqui       # Windows CMD")
        print("   $env:OPENAI_API_KEY='sua-chave-aqui'    # Windows PowerShell")
        print("\nOu adicione no arquivo .env")
        print("="*60)
        sys.exit(1)

    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Testes interrompidos pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Erro fatal ao executar testes: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
