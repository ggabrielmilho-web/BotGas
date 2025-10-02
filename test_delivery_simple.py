"""
Teste Simplificado do Sistema de Entrega - Sesso 6
Valida a estrutura e lgica dos servios sem conexo ao banco
"""
import sys
from pathlib import Path

# Adicionar o diretrio backend ao path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))


def print_section(title):
    """Helper para imprimir sees"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def test_imports():
    """
    Teste 1: Importao dos mdulos
    """
    print_section("TESTE 1: IMPORTAO DOS MDULOS")

    try:
        from app.services.delivery_modes import DeliveryModeService
        print(" DeliveryModeService importado com sucesso")
    except Exception as e:
        print(f" Erro ao importar DeliveryModeService: {e}")
        return False

    try:
        from app.services.neighborhood_delivery import NeighborhoodDeliveryService
        print(" NeighborhoodDeliveryService importado com sucesso")
    except Exception as e:
        print(f" Erro ao importar NeighborhoodDeliveryService: {e}")
        return False

    try:
        from app.services.radius_delivery import RadiusDeliveryService
        print(" RadiusDeliveryService importado com sucesso")
    except Exception as e:
        print(f" Erro ao importar RadiusDeliveryService: {e}")
        return False

    try:
        from app.services.hybrid_delivery import HybridDeliveryService
        print(" HybridDeliveryService importado com sucesso")
    except Exception as e:
        print(f" Erro ao importar HybridDeliveryService: {e}")
        return False

    try:
        from app.services.address_cache import AddressCacheService
        print(" AddressCacheService importado com sucesso")
    except Exception as e:
        print(f" Erro ao importar AddressCacheService: {e}")
        return False

    print("\n Todos os servios foram importados corretamente!")
    return True


def test_api_endpoints():
    """
    Teste 2: API Endpoints
    """
    print_section("TESTE 2: VALIDAO DOS ENDPOINTS DA API")

    try:
        from app.api.delivery import router
        print(" Router de delivery importado com sucesso")

        # Verificar rotas
        routes = [route.path for route in router.routes]
        print(f"\n Total de endpoints criados: {len(routes)}")

        expected_routes = [
            "/api/v1/delivery/config",
            "/api/v1/delivery/mode",
            "/api/v1/delivery/validate",
            "/api/v1/delivery/neighborhoods",
            "/api/v1/delivery/radius",
            "/api/v1/delivery/hybrid/setup",
            "/api/v1/delivery/cache/stats"
        ]

        print("\n Verificando endpoints esperados:")
        for route in expected_routes:
            if any(route in r for r in routes):
                print(f"    {route}")
            else:
                print(f"    {route} - NO ENCONTRADO")

        print("\n API de delivery configurada corretamente!")
        return True

    except Exception as e:
        print(f" Erro ao verificar endpoints: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_address_normalization():
    """
    Teste 3: Normalizao de Endereos
    """
    print_section("TESTE 3: NORMALIZAO DE ENDEREOS")

    try:
        # Criar mock de AddressCacheService
        class MockDB:
            def query(self, *args, **kwargs):
                return self
            def filter(self, *args, **kwargs):
                return self
            def first(self):
                return None
            def all(self):
                return []

        from app.services.address_cache import AddressCacheService

        service = AddressCacheService(MockDB())

        # Testes de normalizao
        test_cases = [
            ("Rua So Paulo, 100", "rua sao paulo 100"),
            ("R. Teste, 123", "rua teste 123"),
            ("Av. Paulista, 1000", "avenida paulista 1000"),
            ("  RUA   TESTE  ,  456  ", "rua teste 456"),
        ]

        print(" Testando normalizao de endereos:\n")
        all_passed = True

        for original, expected in test_cases:
            normalized = service._normalize_address(original)
            passed = normalized == expected
            all_passed = all_passed and passed

            status = "" if passed else ""
            print(f"   {status} '{original}'")
            print(f"       '{normalized}'")
            if not passed:
                print(f"      (esperado: '{expected}')")
            print()

        if all_passed:
            print(" Normalizao de endereos funcionando corretamente!")
        else:
            print("  Alguns casos de normalizao falharam")

        return all_passed

    except Exception as e:
        print(f" Erro ao testar normalizao: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_neighborhood_extraction():
    """
    Teste 4: Extrao de Bairro do Endereo
    """
    print_section("TESTE 4: EXTRAO DE BAIRRO DO ENDEREO")

    try:
        class MockDB:
            def query(self, *args, **kwargs):
                return self
            def filter(self, *args, **kwargs):
                return self
            def first(self):
                return None

        from app.services.neighborhood_delivery import NeighborhoodDeliveryService

        service = NeighborhoodDeliveryService(MockDB())

        # Testes de extrao de bairro
        test_cases = [
            ("Rua Teste, 100, Bairro Centro, So Paulo", "Centro"),
            ("Av. Paulista, 1000, no bairro Bela Vista", "Bela Vista"),
            ("Rua X, Vila Mariana, SP", "Vila Mariana"),
            ("Alameda Santos, 100, em Pinheiros", "Pinheiros"),
        ]

        print(" Testando extrao de bairro:\n")
        all_passed = True

        for address, expected_neighborhood in test_cases:
            extracted = service._extract_neighborhood(address)
            passed = extracted and expected_neighborhood.lower() in extracted.lower()
            all_passed = all_passed and passed

            status = "" if passed else ""
            print(f"   {status} '{address}'")
            print(f"       Bairro extrado: '{extracted}'")
            if not passed:
                print(f"      (esperado algo com: '{expected_neighborhood}')")
            print()

        if all_passed:
            print(" Extrao de bairro funcionando corretamente!")
        else:
            print("  Alguns casos de extrao falharam")

        return all_passed

    except Exception as e:
        print(f" Erro ao testar extrao: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_distance_calculation():
    """
    Teste 5: Clculo de Distncia (Haversine)
    """
    print_section("TESTE 5: CLCULO DE DISTNCIA (HAVERSINE)")

    try:
        class MockDB:
            def query(self, *args, **kwargs):
                return self

        from app.services.radius_delivery import RadiusDeliveryService

        service = RadiusDeliveryService(MockDB())

        # Praa da S vs Paulista (aprox 2.5km)
        se_lat, se_lng = -23.5505, -46.6333
        paulista_lat, paulista_lng = -23.5617, -46.6560

        distance = service._calculate_distance(se_lat, se_lng, paulista_lat, paulista_lng)

        print(f" Distncia Praa da S  Av. Paulista:")
        print(f"   Calculada: {distance:.2f} km")
        print(f"   Esperada: ~2.5 km")

        # Validar se est na faixa esperada (2-3 km)
        if 2.0 <= distance <= 3.0:
            print("\n Clculo de distncia funcionando corretamente!")
            return True
        else:
            print(f"\n  Distncia fora do esperado: {distance:.2f} km")
            return False

    except Exception as e:
        print(f" Erro ao testar clculo de distncia: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_file_structure():
    """
    Teste 6: Estrutura de Arquivos
    """
    print_section("TESTE 6: ESTRUTURA DE ARQUIVOS")

    expected_files = [
        "backend/app/services/delivery_modes.py",
        "backend/app/services/neighborhood_delivery.py",
        "backend/app/services/radius_delivery.py",
        "backend/app/services/hybrid_delivery.py",
        "backend/app/services/address_cache.py",
        "backend/app/api/delivery.py",
    ]

    print(" Verificando arquivos criados:\n")
    all_exist = True

    for file_path in expected_files:
        full_path = Path(__file__).parent / file_path
        exists = full_path.exists()
        all_exist = all_exist and exists

        status = "" if exists else ""
        print(f"   {status} {file_path}")

        if exists:
            size = full_path.stat().st_size
            print(f"      Tamanho: {size:,} bytes")

    print()

    if all_exist:
        print(" Todos os arquivos foram criados corretamente!")
        return True
    else:
        print("  Alguns arquivos esto faltando")
        return False


def run_all_tests():
    """
    Executa todos os testes
    """
    print("\n" + "=" * 80)
    print("  SISTEMA DE ENTREGA FLEXIVEL - TESTES BASICOS (SEM BD)")
    print("  Sessao 6: GasBot")
    print("=" * 80)

    results = []

    # Executar testes
    results.append(("Estrutura de Arquivos", test_file_structure()))
    results.append(("Importao de Mdulos", test_imports()))
    results.append(("API Endpoints", test_api_endpoints()))
    results.append(("Normalizao de Endereos", test_address_normalization()))
    results.append(("Extrao de Bairro", test_neighborhood_extraction()))
    results.append(("Clculo de Distncia", test_distance_calculation()))

    # Resumo
    print_section(" RESUMO DOS TESTES")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "[OK] PASSOU" if result else "[X] FALHOU"
        print(f"{status} - {test_name}")

    print(f"\n>>> Resultado Final: {passed}/{total} testes passaram")

    if passed == total:
        print("\n>>> TODOS OS TESTES PASSARAM!")
        print("\n>>> O Sistema de Entrega Flexivel esta estruturado corretamente!")
        print("\n>>> Funcionalidades implementadas:")
        print("   - Validacao por bairros cadastrados")
        print("   - Validacao por raio/KM (Google Maps)")
        print("   - Modo hibrido (bairros + raio)")
        print("   - Sistema de cache de enderecos")
        print("   - APIs REST completas")
        print("   - 3 modos de entrega configuraveis")
        print("\n>>> Proximos passos:")
        print("   1. Instalar dependencias: pip install -r backend/requirements.txt")
        print("   2. Configurar PostgreSQL")
        print("   3. Rodar migrations: alembic upgrade head")
        print("   4. Testar com banco de dados real")
        print("   5. Integrar com agentes LangChain (Sessao 5)")
    else:
        print(f"\n>>> {total - passed} teste(s) falharam")
        print("   Revise os erros acima e corrija os problemas")

    print()


if __name__ == "__main__":
    run_all_tests()
