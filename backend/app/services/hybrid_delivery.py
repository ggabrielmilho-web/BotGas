"""
Hybrid Delivery Service
Validação de entrega híbrida (combina bairros cadastrados + raio/KM)
"""
from typing import Dict, Any, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.database.models import HybridRule
from app.services.neighborhood_delivery import NeighborhoodDeliveryService
from app.services.radius_delivery import RadiusDeliveryService
from app.services.address_cache import AddressCacheService


class HybridDeliveryService:
    """
    Serviço para validação híbrida de entrega

    Funcionamento:
    1. Tenta validar por bairros cadastrados primeiro (mais rápido, sem API)
    2. Se não encontrar bairro, tenta por raio/KM (usa Google Maps)
    3. Aplica regras de prioridade configuradas
    4. Economiza chamadas à API do Google Maps

    Casos de uso:
    - Tenant tem bairros principais cadastrados (mais baratos)
    - Para bairros não cadastrados, usa validação por raio
    - Flexibilidade para atender mais clientes
    """

    def __init__(self, db: Session):
        self.db = db
        self.neighborhood_service = NeighborhoodDeliveryService(db)
        self.radius_service = RadiusDeliveryService(db)
        self.cache_service = AddressCacheService(db)

    async def validate_address(
        self,
        address: str,
        tenant_id: UUID
    ) -> Dict[str, Any]:
        """
        Valida endereço usando modo híbrido

        Estratégia:
        1. Verificar cache primeiro
        2. Tentar bairros cadastrados (rápido, sem custo)
        3. Se não encontrar, tentar raio/KM (Google Maps)
        4. Aplicar regras de prioridade

        Args:
            address: Endereço completo do cliente
            tenant_id: ID do tenant

        Returns:
            {
                'is_deliverable': bool,
                'delivery_fee': float,
                'delivery_time_minutes': int,
                'validation_method': 'neighborhood' | 'radius',
                'neighborhood': str,
                'coordinates': dict,
                'normalized_address': str,
                'message': str
            }
        """
        # Verificar cache primeiro
        cached = await self.cache_service.get_cached_address(address, tenant_id)
        if cached:
            return {
                'is_deliverable': cached.is_deliverable,
                'delivery_fee': float(cached.delivery_fee or 0),
                'delivery_time_minutes': 60,
                'neighborhood': cached.neighborhood,
                'coordinates': cached.coordinates,
                'normalized_address': cached.normalized_address,
                'validation_method': 'cache',
                'message': f'Endereço validado! 🎉' if cached.is_deliverable
                          else 'Fora da área de entrega 😔',
                'from_cache': True
            }

        # Buscar regras híbridas do tenant
        rules = await self.get_hybrid_rules(tenant_id)

        # Determinar ordem de validação (padrão: bairro primeiro)
        try_neighborhood_first = True

        if rules:
            # Se tem regras, verificar prioridade
            for rule in rules:
                if rule.rule_type == 'radius_first':
                    try_neighborhood_first = False
                    break

        # Tentar validação por bairro primeiro (mais rápido e econômico)
        if try_neighborhood_first:
            neighborhood_result = await self.neighborhood_service.validate_address(
                address, tenant_id
            )

            # Se encontrou bairro e é entregável, retornar
            if neighborhood_result.get('is_deliverable'):
                neighborhood_result['validation_method'] = 'neighborhood'
                neighborhood_result['message'] = (
                    f"{neighborhood_result.get('message', '')} "
                    "(Validado por bairro cadastrado)"
                )
                return neighborhood_result

            # Se não encontrou ou não é entregável, tentar por raio
            radius_result = await self.radius_service.validate_address(
                address, tenant_id
            )

            if radius_result.get('is_deliverable'):
                radius_result['validation_method'] = 'radius'
                radius_result['message'] = (
                    f"{radius_result.get('message', '')} "
                    "(Validado por distância)"
                )
                return radius_result

            # Nenhum dos dois funcionou
            return {
                'is_deliverable': False,
                'validation_method': 'hybrid',
                'message': 'Desculpe, não conseguimos entregar nesse endereço 😔',
                'tried_methods': ['neighborhood', 'radius']
            }

        else:
            # Tentar por raio primeiro
            radius_result = await self.radius_service.validate_address(
                address, tenant_id
            )

            if radius_result.get('is_deliverable'):
                radius_result['validation_method'] = 'radius'
                return radius_result

            # Se não funcionou, tentar por bairro
            neighborhood_result = await self.neighborhood_service.validate_address(
                address, tenant_id
            )

            if neighborhood_result.get('is_deliverable'):
                neighborhood_result['validation_method'] = 'neighborhood'
                return neighborhood_result

            # Nenhum dos dois funcionou
            return {
                'is_deliverable': False,
                'validation_method': 'hybrid',
                'message': 'Desculpe, não conseguimos entregar nesse endereço 😔',
                'tried_methods': ['radius', 'neighborhood']
            }

    async def get_hybrid_rules(self, tenant_id: UUID) -> list:
        """
        Retorna regras híbridas do tenant (ordenadas por prioridade)
        """
        return self.db.query(HybridRule).filter(
            HybridRule.tenant_id == tenant_id,
            HybridRule.is_active == True
        ).order_by(HybridRule.priority).all()

    async def add_hybrid_rule(
        self,
        tenant_id: UUID,
        rule_type: str,
        config: dict,
        priority: int = 100
    ) -> HybridRule:
        """
        Adiciona regra híbrida

        Args:
            rule_type: Tipo da regra
                - 'neighborhood_first': Tenta bairro primeiro (padrão)
                - 'radius_first': Tenta raio primeiro
                - 'neighborhood_only_premium': Bairros cadastrados = taxa menor
                - 'radius_fallback': Raio só se bairro não encontrado
            config: Configuração específica da regra (JSON)
            priority: Prioridade (menor = mais alta)
        """
        from app.database.models import DeliveryArea

        # Buscar delivery_area do tenant
        delivery_area = self.db.query(DeliveryArea).filter(
            DeliveryArea.tenant_id == tenant_id
        ).first()

        if not delivery_area:
            # Criar área de entrega se não existir
            delivery_area = DeliveryArea(
                tenant_id=tenant_id,
                delivery_mode='hybrid'
            )
            self.db.add(delivery_area)
            self.db.flush()

        # Criar regra
        rule = HybridRule(
            tenant_id=tenant_id,
            delivery_area_id=delivery_area.id,
            rule_type=rule_type,
            config=config,
            priority=priority,
            is_active=True
        )

        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)

        return rule

    async def update_hybrid_rule(
        self,
        rule_id: UUID,
        tenant_id: UUID,
        **kwargs
    ) -> HybridRule:
        """
        Atualiza regra híbrida
        """
        rule = self.db.query(HybridRule).filter(
            HybridRule.id == rule_id,
            HybridRule.tenant_id == tenant_id
        ).first()

        if not rule:
            raise ValueError('Regra não encontrada')

        # Atualizar campos
        for key, value in kwargs.items():
            if hasattr(rule, key) and value is not None:
                setattr(rule, key, value)

        self.db.commit()
        self.db.refresh(rule)

        return rule

    async def delete_hybrid_rule(
        self,
        rule_id: UUID,
        tenant_id: UUID
    ) -> bool:
        """
        Desativa regra híbrida (soft delete)
        """
        rule = self.db.query(HybridRule).filter(
            HybridRule.id == rule_id,
            HybridRule.tenant_id == tenant_id
        ).first()

        if not rule:
            return False

        rule.is_active = False
        self.db.commit()

        return True

    async def setup_default_hybrid(
        self,
        tenant_id: UUID,
        center_address: str,
        main_neighborhoods: list,
        radius_tiers: list
    ) -> Dict[str, Any]:
        """
        Setup rápido de modo híbrido

        Args:
            center_address: Endereço central para cálculo de raio
            main_neighborhoods: Lista de bairros principais com taxas
                [{'name': 'Centro', 'fee': 5, 'time': 30}, ...]
            radius_tiers: Faixas de raio para outros endereços
                [{'start': 0, 'end': 10, 'fee': 10, 'time': 45}, ...]

        Returns:
            {
                'neighborhoods_created': int,
                'radius_configs_created': int,
                'hybrid_rule_created': bool
            }
        """
        # Criar bairros principais
        neighborhoods = await self.neighborhood_service.bulk_add_neighborhoods(
            tenant_id=tenant_id,
            neighborhoods=main_neighborhoods
        )

        # Criar configurações de raio
        radius_configs = await self.radius_service.bulk_add_radius_configs(
            tenant_id=tenant_id,
            center_address=center_address,
            radius_tiers=radius_tiers
        )

        # Criar regra híbrida (bairro primeiro)
        rule = await self.add_hybrid_rule(
            tenant_id=tenant_id,
            rule_type='neighborhood_first',
            config={
                'description': 'Tenta validar por bairro cadastrado primeiro, '
                               'depois por raio se não encontrar',
                'fallback_enabled': True
            },
            priority=1
        )

        return {
            'neighborhoods_created': len(neighborhoods),
            'radius_configs_created': len(radius_configs),
            'hybrid_rule_created': bool(rule),
            'message': (
                f'Setup híbrido completo! '
                f'{len(neighborhoods)} bairros e '
                f'{len(radius_configs)} faixas de raio configuradas.'
            )
        }

    async def get_delivery_stats(self, tenant_id: UUID) -> Dict[str, Any]:
        """
        Retorna estatísticas de configuração híbrida
        """
        from sqlalchemy import func

        neighborhoods = await self.neighborhood_service.get_neighborhoods(tenant_id)
        radius_configs = await self.radius_service.get_radius_configs(tenant_id)

        # Contar endereços em cache
        from app.database.models import AddressCache

        cache_count = self.db.query(func.count(AddressCache.id)).filter(
            AddressCache.tenant_id == tenant_id
        ).scalar()

        neighborhood_deliverable = len([n for n in neighborhoods if n.delivery_type != 'not_available'])

        return {
            'total_neighborhoods': len(neighborhoods),
            'deliverable_neighborhoods': neighborhood_deliverable,
            'radius_configs': len(radius_configs),
            'cached_addresses': cache_count,
            'delivery_mode': 'hybrid',
            'status': 'active' if (neighborhoods or radius_configs) else 'not_configured'
        }
