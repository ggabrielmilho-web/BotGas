"""
Neighborhood-based Delivery Service
Validação de entrega baseada em bairros cadastrados manualmente
"""
from typing import Dict, Any, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.database.models import NeighborhoodConfig, DeliveryArea, AddressCache
from app.services.address_cache import AddressCacheService
import re


class NeighborhoodDeliveryService:
    """
    Serviço para validação de entrega por bairros cadastrados

    Funcionamento:
    1. Cliente informa endereço
    2. Sistema extrai o bairro do texto
    3. Verifica se bairro está cadastrado
    4. Retorna taxa e tempo de entrega configurados
    """

    def __init__(self, db: Session):
        self.db = db
        self.cache_service = AddressCacheService(db)

    async def validate_address(
        self,
        address: str,
        tenant_id: UUID
    ) -> Dict[str, Any]:
        """
        Valida se o endereço está em um bairro atendido

        Args:
            address: Endereço completo do cliente
            tenant_id: ID do tenant

        Returns:
            {
                'is_deliverable': bool,
                'delivery_fee': float,
                'delivery_time_minutes': int,
                'neighborhood': str,
                'neighborhood_config': NeighborhoodConfig,
                'normalized_address': str,
                'message': str
            }
        """
        # Verificar cache primeiro
        cached = await self.cache_service.get_cached_address(address, tenant_id)
        if cached:
            config = self.db.query(NeighborhoodConfig).filter(
                NeighborhoodConfig.id == cached.delivery_area_id
            ).first()

            return {
                'is_deliverable': cached.is_deliverable,
                'delivery_fee': float(cached.delivery_fee or 0),
                'delivery_time_minutes': config.delivery_time_minutes if config else 60,
                'neighborhood': cached.neighborhood,
                'normalized_address': cached.normalized_address,
                'coordinates': cached.coordinates,
                'message': f'Entregamos no bairro {cached.neighborhood}! 🎉' if cached.is_deliverable
                          else f'Não entregamos no bairro {cached.neighborhood} ainda 😔',
                'from_cache': True
            }

        # Extrair bairro do endereço
        neighborhood_name = self._extract_neighborhood(address)

        if not neighborhood_name:
            return {
                'is_deliverable': False,
                'message': 'Não consegui identificar o bairro. Por favor, informe o nome do bairro.',
                'requires_clarification': True
            }

        # Buscar configuração do bairro
        config = await self.find_neighborhood_config(neighborhood_name, tenant_id)

        if not config:
            # Salvar no cache como não entregável
            await self.cache_service.cache_address(
                address=address,
                tenant_id=tenant_id,
                normalized_address=address,
                neighborhood=neighborhood_name,
                is_deliverable=False,
                delivery_fee=0
            )

            return {
                'is_deliverable': False,
                'neighborhood': neighborhood_name,
                'message': f'Desculpe, ainda não entregamos no bairro {neighborhood_name} 😔',
                'suggestion': 'Verifique os bairros atendidos ou contate o suporte.'
            }

        # Verificar se está ativo e tipo de entrega
        if config.delivery_type == 'not_available':
            return {
                'is_deliverable': False,
                'neighborhood': config.neighborhood_name,
                'message': f'No momento não estamos entregando no bairro {config.neighborhood_name}'
            }

        # Calcular taxa
        delivery_fee = float(config.delivery_fee) if config.delivery_type == 'paid' else 0

        # Salvar no cache
        await self.cache_service.cache_address(
            address=address,
            tenant_id=tenant_id,
            normalized_address=address,
            neighborhood=config.neighborhood_name,
            city=config.city,
            state=config.state,
            is_deliverable=True,
            delivery_fee=delivery_fee,
            delivery_area_id=config.id
        )

        message = f'Entregamos no {config.neighborhood_name}! 🎉'
        if config.delivery_type == 'free':
            message += ' Entrega GRÁTIS! 🎁'
        elif delivery_fee > 0:
            message += f' Taxa de entrega: R$ {delivery_fee:.2f}'

        return {
            'is_deliverable': True,
            'delivery_fee': delivery_fee,
            'delivery_time_minutes': config.delivery_time_minutes,
            'neighborhood': config.neighborhood_name,
            'city': config.city,
            'state': config.state,
            'neighborhood_config': config,
            'normalized_address': address,
            'message': message,
            'from_cache': False
        }

    async def find_neighborhood_config(
        self,
        neighborhood_name: str,
        tenant_id: UUID
    ) -> Optional[NeighborhoodConfig]:
        """
        Busca configuração de bairro (case-insensitive)
        """
        return self.db.query(NeighborhoodConfig).filter(
            and_(
                NeighborhoodConfig.tenant_id == tenant_id,
                func.lower(NeighborhoodConfig.neighborhood_name) == neighborhood_name.lower(),
                NeighborhoodConfig.is_active == True
            )
        ).first()

    def _extract_neighborhood(self, address: str) -> Optional[str]:
        """
        Extrai nome do bairro do endereço

        Procura por padrões comuns:
        - "Bairro X"
        - "no bairro X"
        - "em X"
        - Bairros conhecidos no final do endereço
        """
        address_lower = address.lower().strip()

        # Padrões comuns
        patterns = [
            r'(?:bairro|no bairro|bairro:)\s+([a-záàâãéèêíïóôõöúçñ\s]+?)(?:,|\.|$|\s+\d)',
            r'(?:em|no)\s+([a-záàâãéèêíïóôõöúçñ\s]+?)(?:,|\.|$|\s+\d)',
            r',\s*([a-záàâãéèêíïóôõöúçñ\s]+?)(?:,|\.|$)',
        ]

        for pattern in patterns:
            match = re.search(pattern, address_lower, re.IGNORECASE)
            if match:
                neighborhood = match.group(1).strip()
                # Limpar palavras comuns que não são bairros
                if neighborhood and len(neighborhood) > 2:
                    # Remover números e caracteres especiais
                    neighborhood = re.sub(r'\d+', '', neighborhood).strip()
                    return neighborhood.title()

        # Se não encontrou padrão, tentar pegar última parte antes de CEP/número
        parts = re.split(r'[,\-]', address_lower)
        if len(parts) >= 2:
            potential_neighborhood = parts[-2].strip()
            # Verificar se não é número ou CEP
            if potential_neighborhood and not re.match(r'^\d', potential_neighborhood):
                potential_neighborhood = re.sub(r'\d+', '', potential_neighborhood).strip()
                if len(potential_neighborhood) > 2:
                    return potential_neighborhood.title()

        return None

    async def add_neighborhood(
        self,
        tenant_id: UUID,
        neighborhood_name: str,
        city: str = 'São Paulo',
        state: str = 'SP',
        delivery_type: str = 'paid',
        delivery_fee: float = 0,
        delivery_time_minutes: int = 60,
        zip_codes: Optional[list] = None,
        notes: Optional[str] = None
    ) -> NeighborhoodConfig:
        """
        Adiciona novo bairro ao sistema
        """
        # Verificar se já existe
        existing = await self.find_neighborhood_config(neighborhood_name, tenant_id)
        if existing:
            raise ValueError(f'Bairro {neighborhood_name} já cadastrado')

        # Buscar delivery_area do tenant
        delivery_area = self.db.query(DeliveryArea).filter(
            DeliveryArea.tenant_id == tenant_id
        ).first()

        if not delivery_area:
            # Criar área de entrega se não existir
            delivery_area = DeliveryArea(
                tenant_id=tenant_id,
                delivery_mode='neighborhood'
            )
            self.db.add(delivery_area)
            self.db.flush()

        # Criar configuração
        config = NeighborhoodConfig(
            tenant_id=tenant_id,
            delivery_area_id=delivery_area.id,
            neighborhood_name=neighborhood_name,
            city=city,
            state=state,
            delivery_type=delivery_type,
            delivery_fee=delivery_fee,
            delivery_time_minutes=delivery_time_minutes,
            zip_codes=zip_codes or [],
            notes=notes,
            is_active=True
        )

        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)

        return config

    async def update_neighborhood(
        self,
        neighborhood_id: UUID,
        tenant_id: UUID,
        **kwargs
    ) -> NeighborhoodConfig:
        """
        Atualiza configuração de bairro
        """
        config = self.db.query(NeighborhoodConfig).filter(
            and_(
                NeighborhoodConfig.id == neighborhood_id,
                NeighborhoodConfig.tenant_id == tenant_id
            )
        ).first()

        if not config:
            raise ValueError('Bairro não encontrado')

        # Atualizar campos
        for key, value in kwargs.items():
            if hasattr(config, key) and value is not None:
                setattr(config, key, value)

        self.db.commit()
        self.db.refresh(config)

        return config

    async def delete_neighborhood(
        self,
        neighborhood_id: UUID,
        tenant_id: UUID
    ) -> bool:
        """
        Desativa bairro (soft delete)
        """
        config = self.db.query(NeighborhoodConfig).filter(
            and_(
                NeighborhoodConfig.id == neighborhood_id,
                NeighborhoodConfig.tenant_id == tenant_id
            )
        ).first()

        if not config:
            return False

        config.is_active = False
        self.db.commit()

        return True

    async def bulk_add_neighborhoods(
        self,
        tenant_id: UUID,
        neighborhoods: list
    ) -> list:
        """
        Adiciona múltiplos bairros de uma vez

        neighborhoods: [
            {
                'name': 'Centro',
                'delivery_fee': 10.0,
                'delivery_time_minutes': 30
            },
            ...
        ]
        """
        created = []

        for neighborhood_data in neighborhoods:
            try:
                config = await self.add_neighborhood(
                    tenant_id=tenant_id,
                    neighborhood_name=neighborhood_data.get('name'),
                    city=neighborhood_data.get('city', 'São Paulo'),
                    state=neighborhood_data.get('state', 'SP'),
                    delivery_type=neighborhood_data.get('delivery_type', 'paid'),
                    delivery_fee=neighborhood_data.get('delivery_fee', 0),
                    delivery_time_minutes=neighborhood_data.get('delivery_time_minutes', 60),
                    zip_codes=neighborhood_data.get('zip_codes'),
                    notes=neighborhood_data.get('notes')
                )
                created.append(config)
            except ValueError:
                # Bairro já existe, pular
                continue

        return created
