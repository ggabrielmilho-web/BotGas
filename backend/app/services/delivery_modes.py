"""
Base Service for Delivery Mode Management
Gerencia os 3 modos de entrega: Bairro, Raio e Híbrido
"""
from typing import Dict, Any, Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.database.models import (
    DeliveryArea, NeighborhoodConfig, RadiusConfig, HybridRule
)


class DeliveryModeService:
    """
    Serviço base para gerenciar modos de entrega
    """

    def __init__(self, db: Session):
        self.db = db

    async def get_delivery_config(self, tenant_id: UUID) -> Optional[DeliveryArea]:
        """
        Retorna configuração de entrega do tenant
        """
        config = self.db.query(DeliveryArea).filter(
            DeliveryArea.tenant_id == tenant_id
        ).first()

        return config

    async def create_or_update_delivery_config(
        self,
        tenant_id: UUID,
        delivery_mode: str,
        free_delivery_minimum: Optional[float] = None,
        default_fee: Optional[float] = None
    ) -> DeliveryArea:
        """
        Cria ou atualiza configuração de entrega

        Args:
            tenant_id: ID do tenant
            delivery_mode: 'neighborhood', 'radius' ou 'hybrid'
            free_delivery_minimum: Valor mínimo para entrega grátis
            default_fee: Taxa padrão de entrega
        """
        config = await self.get_delivery_config(tenant_id)

        if config:
            # Atualizar existente
            config.delivery_mode = delivery_mode
            if free_delivery_minimum is not None:
                config.free_delivery_minimum = free_delivery_minimum
            if default_fee is not None:
                config.default_fee = default_fee
        else:
            # Criar novo
            config = DeliveryArea(
                tenant_id=tenant_id,
                delivery_mode=delivery_mode,
                free_delivery_minimum=free_delivery_minimum,
                default_fee=default_fee or 0
            )
            self.db.add(config)

        self.db.commit()
        self.db.refresh(config)

        return config

    async def get_delivery_mode(self, tenant_id: UUID) -> str:
        """
        Retorna o modo de entrega ativo do tenant
        """
        config = await self.get_delivery_config(tenant_id)
        return config.delivery_mode if config else 'neighborhood'

    async def validate_address(
        self,
        address: str,
        tenant_id: UUID,
        order_total: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Valida endereço de acordo com o modo de entrega configurado

        Returns:
            {
                'is_deliverable': bool,
                'delivery_fee': float,
                'delivery_time_minutes': int,
                'neighborhood': str,
                'coordinates': dict,
                'normalized_address': str,
                'message': str
            }
        """
        config = await self.get_delivery_config(tenant_id)

        if not config:
            return {
                'is_deliverable': False,
                'message': 'Configuração de entrega não encontrada'
            }

        # Importar serviços específicos
        from app.services.neighborhood_delivery import NeighborhoodDeliveryService
        from app.services.radius_delivery import RadiusDeliveryService
        from app.services.hybrid_delivery import HybridDeliveryService

        # Selecionar serviço de acordo com o modo
        if config.delivery_mode == 'neighborhood':
            service = NeighborhoodDeliveryService(self.db)
        elif config.delivery_mode == 'radius':
            service = RadiusDeliveryService(self.db)
        elif config.delivery_mode == 'hybrid':
            service = HybridDeliveryService(self.db)
        else:
            return {
                'is_deliverable': False,
                'message': f'Modo de entrega inválido: {config.delivery_mode}'
            }

        # Validar endereço
        result = await service.validate_address(address, tenant_id)

        # Aplicar regra de entrega grátis se configurado
        if (config.free_delivery_minimum and
            order_total and
            order_total >= float(config.free_delivery_minimum) and
            result.get('is_deliverable')):
            result['delivery_fee'] = 0
            result['message'] = f"{result.get('message', '')} 🎉 Entrega grátis!"

        return result

    async def get_neighborhoods(self, tenant_id: UUID) -> List[NeighborhoodConfig]:
        """
        Lista todos os bairros cadastrados
        """
        return self.db.query(NeighborhoodConfig).filter(
            and_(
                NeighborhoodConfig.tenant_id == tenant_id,
                NeighborhoodConfig.is_active == True
            )
        ).all()

    async def get_radius_configs(self, tenant_id: UUID) -> List[RadiusConfig]:
        """
        Lista todas as configurações de raio
        """
        return self.db.query(RadiusConfig).filter(
            and_(
                RadiusConfig.tenant_id == tenant_id,
                RadiusConfig.is_active == True
            )
        ).order_by(RadiusConfig.radius_km_start).all()

    async def get_hybrid_rules(self, tenant_id: UUID) -> List[HybridRule]:
        """
        Lista todas as regras híbridas
        """
        return self.db.query(HybridRule).filter(
            and_(
                HybridRule.tenant_id == tenant_id,
                HybridRule.is_active == True
            )
        ).order_by(HybridRule.priority).all()

    async def calculate_delivery_fee(
        self,
        address_result: Dict[str, Any],
        order_total: float,
        tenant_id: UUID
    ) -> float:
        """
        Calcula taxa de entrega considerando promoções e mínimos
        """
        if not address_result.get('is_deliverable'):
            return 0

        config = await self.get_delivery_config(tenant_id)
        base_fee = address_result.get('delivery_fee', 0)

        # Aplicar entrega grátis se atingir mínimo
        if config and config.free_delivery_minimum:
            if order_total >= float(config.free_delivery_minimum):
                return 0

        return base_fee
