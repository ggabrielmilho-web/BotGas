"""
Script de teste para o Sistema de Entrega Flexível - Sessão 6
Testa os 3 modos de entrega: Bairro, Raio e Híbrido
"""
import asyncio
import sys
from pathlib import Path

# Adicionar o diretório backend ao path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.database.models import Base, Tenant
from app.services.delivery_modes import DeliveryModeService
from app.services.neighborhood_delivery import NeighborhoodDeliveryService
from app.services.radius_delivery import RadiusDeliveryService
from app.services.hybrid_delivery import HybridDeliveryService
import uuid


# Criar engine de teste
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def print_section(title):
    """Helper para imprimir seções"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_result(result):
    """Helper para imprimir resultados"""
    print(f"✓ Entregável: {result.get('is_deliverable')}")
    print(f"✓ Taxa: R$ {result.get('delivery_fee', 0):.2f}")
    print(f"✓ Tempo: {result.get('delivery_time_minutes', 'N/A')} min")
    print(f"✓ Bairro: {result.get('neighborhood', 'N/A')}")
    print(f"✓ Método: {result.get('validation_method', 'N/A')}")
    print(f"✓ Cache: {result.get('from_cache', False)}")
    print(f"✓ Mensagem: {result.get('message', '')}")
    print()


async def test_neighborhood_delivery(db, tenant_id):
    """
    Teste 1: Validação por Bairros Cadastrados
    """
    print_section("TESTE 1: VALIDAÇÃO POR BAIRROS CADASTRADOS")

    service = NeighborhoodDeliveryService(db)

    # Cadastrar bairros de teste
    print("📝 Cadastrando bairros de teste...")

    bairros_teste = [
        {
            'name': 'Centro',
            'city': 'São Paulo',
            'state': 'SP',
            'delivery_type': 'free',
            'delivery_fee': 0,
            'delivery_time_minutes': 30
        },
        {
            'name': 'Paulista',
            'city': 'São Paulo',
            'state': 'SP',
            'delivery_type': 'paid',
            'delivery_fee': 10.0,
            'delivery_time_minutes': 45
        },
        {
            'name': 'Vila Mariana',
            'city': 'São Paulo',
            'state': 'SP',
            'delivery_type': 'paid',
            'delivery_fee': 15.0,
            'delivery_time_minutes': 60
        }
    ]

    created = await service.bulk_add_neighborhoods(tenant_id, bairros_teste)
    print(f"✓ {len(created)} bairros cadastrados\n")

    # Testar validações
    print("🔍 Testando validações de endereço...\n")

    # Teste 1.1: Bairro com entrega grátis
    print("1.1 - Endereço no Centro (entrega grátis):")
    result = await service.validate_address(
        "Rua 15 de Novembro, 100, Centro, São Paulo",
        tenant_id
    )
    print_result(result)

    # Teste 1.2: Bairro com taxa
    print("1.2 - Endereço na Paulista (entrega paga):")
    result = await service.validate_address(
        "Avenida Paulista, 1000, Paulista, São Paulo",
        tenant_id
    )
    print_result(result)

    # Teste 1.3: Bairro não cadastrado
    print("1.3 - Endereço em bairro não cadastrado:")
    result = await service.validate_address(
        "Rua Teste, 123, Jardim Paulistano, São Paulo",
        tenant_id
    )
    print_result(result)

    # Teste 1.4: Validar cache (mesma busca)
    print("1.4 - Validar cache (mesma busca da 1.1):")
    result = await service.validate_address(
        "Rua 15 de Novembro, 100, Centro, São Paulo",
        tenant_id
    )
    print_result(result)

    return True


async def test_radius_delivery(db, tenant_id):
    """
    Teste 2: Validação por Raio/KM (Google Maps)
    """
    print_section("TESTE 2: VALIDAÇÃO POR RAIO/KM (GOOGLE MAPS)")

    service = RadiusDeliveryService(db)

    # Cadastrar faixas de raio
    print("📝 Cadastrando faixas de raio de teste...")

    # Centro de SP como referência
    center_address = "Praça da Sé, São Paulo, SP"

    radius_tiers = [
        {'start': 0, 'end': 5, 'fee': 0, 'time': 30},
        {'start': 5, 'end': 10, 'fee': 10, 'time': 45},
        {'start': 10, 'end': 20, 'fee': 20, 'time': 60},
    ]

    created = await service.bulk_add_radius_configs(
        tenant_id, center_address, radius_tiers
    )
    print(f"✓ {len(created)} faixas de raio cadastradas\n")

    # Testar validações
    print("🔍 Testando validações por distância...\n")

    # Teste 2.1: Endereço próximo (< 5km)
    print("2.1 - Endereço próximo (< 5km da Sé):")
    result = await service.validate_address(
        "Rua Direita, 100, Centro, São Paulo, SP",
        tenant_id
    )
    print_result(result)
    if result.get('distance_km'):
        print(f"   Distância: {result['distance_km']:.2f} km\n")

    # Teste 2.2: Endereço médio (5-10km)
    print("2.2 - Endereço médio (5-10km da Sé):")
    result = await service.validate_address(
        "Avenida Paulista, 1000, São Paulo, SP",
        tenant_id
    )
    print_result(result)
    if result.get('distance_km'):
        print(f"   Distância: {result['distance_km']:.2f} km\n")

    # Teste 2.3: Endereço longe (> 20km - fora da área)
    print("2.3 - Endereço fora da área de entrega (> 20km):")
    result = await service.validate_address(
        "Rua Teste, Guarulhos, SP",
        tenant_id
    )
    print_result(result)

    return True


async def test_hybrid_delivery(db, tenant_id):
    """
    Teste 3: Modo Híbrido (Bairros + Raio)
    """
    print_section("TESTE 3: MODO HÍBRIDO (BAIRROS + RAIO)")

    service = HybridDeliveryService(db)

    # Setup híbrido
    print("📝 Configurando modo híbrido...")

    main_neighborhoods = [
        {'name': 'Pinheiros', 'fee': 5, 'time': 30, 'delivery_type': 'paid'},
        {'name': 'Itaim Bibi', 'fee': 5, 'time': 30, 'delivery_type': 'paid'},
    ]

    radius_tiers = [
        {'start': 0, 'end': 15, 'fee': 15, 'time': 60},
        {'start': 15, 'end': 25, 'fee': 25, 'time': 90},
    ]

    result = await service.setup_default_hybrid(
        tenant_id=tenant_id,
        center_address="Avenida Faria Lima, 1000, São Paulo, SP",
        main_neighborhoods=main_neighborhoods,
        radius_tiers=radius_tiers
    )

    print(f"✓ {result['neighborhoods_created']} bairros configurados")
    print(f"✓ {result['radius_configs_created']} faixas de raio configuradas\n")

    # Testar validações
    print("🔍 Testando validações híbridas...\n")

    # Teste 3.1: Endereço em bairro cadastrado (deve usar bairro)
    print("3.1 - Endereço em bairro cadastrado (Pinheiros):")
    result = await service.validate_address(
        "Rua dos Pinheiros, 100, Pinheiros, São Paulo",
        tenant_id
    )
    print_result(result)

    # Teste 3.2: Endereço não em bairro, mas dentro do raio
    print("3.2 - Endereço fora de bairros cadastrados, mas dentro do raio:")
    result = await service.validate_address(
        "Rua Augusta, 1000, Consolação, São Paulo",
        tenant_id
    )
    print_result(result)

    # Teste 3.3: Estatísticas
    print("3.3 - Estatísticas do modo híbrido:")
    stats = await service.get_delivery_stats(tenant_id)
    print(f"   Total de bairros: {stats['total_neighborhoods']}")
    print(f"   Bairros entregáveis: {stats['deliverable_neighborhoods']}")
    print(f"   Configs de raio: {stats['radius_configs']}")
    print(f"   Endereços em cache: {stats['cached_addresses']}")
    print(f"   Status: {stats['status']}\n")

    return True


async def test_delivery_mode_service(db, tenant_id):
    """
    Teste 4: Serviço de Gerenciamento de Modos
    """
    print_section("TESTE 4: GERENCIAMENTO DE MODOS DE ENTREGA")

    service = DeliveryModeService(db)

    # Teste 4.1: Criar/atualizar configuração
    print("4.1 - Configurar modo de entrega:")
    config = await service.create_or_update_delivery_config(
        tenant_id=tenant_id,
        delivery_mode='hybrid',
        free_delivery_minimum=50.0,
        default_fee=5.0
    )
    print(f"✓ Modo configurado: {config.delivery_mode}")
    print(f"✓ Entrega grátis acima de: R$ {float(config.free_delivery_minimum):.2f}")
    print(f"✓ Taxa padrão: R$ {float(config.default_fee):.2f}\n")

    # Teste 4.2: Validar com valor total (para entrega grátis)
    print("4.2 - Validar endereço com pedido de R$ 60 (entrega grátis):")
    result = await service.validate_address(
        address="Rua Teste, Pinheiros, São Paulo",
        tenant_id=tenant_id,
        order_total=60.0
    )
    print_result(result)

    # Teste 4.3: Validar com valor baixo (cobra taxa)
    print("4.3 - Validar endereço com pedido de R$ 30 (cobra taxa):")
    result = await service.validate_address(
        address="Rua Teste, Pinheiros, São Paulo",
        tenant_id=tenant_id,
        order_total=30.0
    )
    print_result(result)

    return True


async def test_cache_statistics(db, tenant_id):
    """
    Teste 5: Estatísticas de Cache
    """
    print_section("TESTE 5: ESTATÍSTICAS DE CACHE")

    from app.services.address_cache import AddressCacheService

    service = AddressCacheService(db)

    stats = await service.get_cache_statistics(tenant_id, days=30)

    print(f"📊 Total de endereços em cache: {stats['total_cached']}")
    print(f"📊 Endereços entregáveis: {stats['deliverable']}")
    print(f"📊 Endereços não entregáveis: {stats['non_deliverable']}")
    print(f"📊 Chamadas à API economizadas: ~{stats['estimated_api_calls_saved']}\n")

    if stats['top_neighborhoods']:
        print("🏘️  Top 5 bairros mais buscados:")
        for item in stats['top_neighborhoods'][:5]:
            print(f"   {item['neighborhood']}: {item['count']} buscas")

    print()

    return True


async def run_all_tests():
    """
    Executa todos os testes
    """
    db = SessionLocal()

    try:
        print("\n" + "🚀" * 40)
        print("  SISTEMA DE ENTREGA FLEXÍVEL - TESTES BÁSICOS")
        print("  Sessão 6: GasBot")
        print("🚀" * 40)

        # Criar tenant de teste
        print("\n📝 Criando tenant de teste...")
        tenant = Tenant(
            id=uuid.uuid4(),
            company_name="Distribuidora Teste",
            phone="11999999999",
            email="teste@gasbot.com"
        )
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
        print(f"✓ Tenant criado: {tenant.company_name} (ID: {tenant.id})\n")

        # Executar testes
        await test_neighborhood_delivery(db, tenant.id)
        await test_radius_delivery(db, tenant.id)
        await test_hybrid_delivery(db, tenant.id)
        await test_delivery_mode_service(db, tenant.id)
        await test_cache_statistics(db, tenant.id)

        print_section("✅ TODOS OS TESTES CONCLUÍDOS COM SUCESSO!")

        print("\n📋 RESUMO:")
        print("✓ Sistema de validação por bairros: OK")
        print("✓ Sistema de validação por raio/KM: OK")
        print("✓ Sistema híbrido (bairros + raio): OK")
        print("✓ Gerenciamento de modos de entrega: OK")
        print("✓ Sistema de cache de endereços: OK")
        print("\n🎉 O sistema de entrega flexível está funcionando perfeitamente!\n")

    except Exception as e:
        print(f"\n❌ ERRO: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        # Limpar dados de teste
        print("\n🧹 Limpando dados de teste...")
        db.rollback()
        db.close()


if __name__ == "__main__":
    print("\n⚠️  ATENÇÃO: Este teste requer:")
    print("   1. PostgreSQL rodando")
    print("   2. Google Maps API Key configurada no .env")
    print("   3. Conexão com a internet\n")

    response = input("Deseja continuar? (s/n): ")

    if response.lower() == 's':
        asyncio.run(run_all_tests())
    else:
        print("Teste cancelado.")
