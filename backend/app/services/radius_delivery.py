"""
Radius-based Delivery Service
Validação de entrega baseada em distância (raio/KM) usando Google Maps
"""
from typing import Dict, Any, Optional, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_
import googlemaps
from datetime import datetime
import math

from app.database.models import RadiusConfig, DeliveryArea
from app.services.address_cache import AddressCacheService
from app.core.config import settings


class RadiusDeliveryService:
    """
    Serviço para validação de entrega por raio/distância

    Funcionamento:
    1. Cliente informa endereço
    2. Sistema geocodifica endereço (Google Maps)
    3. Calcula distância até ponto central
    4. Verifica em qual faixa de raio se encaixa
    5. Retorna taxa e tempo de acordo com configuração
    """

    def __init__(self, db: Session):
        self.db = db
        self.cache_service = AddressCacheService(db)
        self.gmaps = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)

    async def validate_address(
        self,
        address: str,
        tenant_id: UUID
    ) -> Dict[str, Any]:
        """
        Valida endereço por distância

        Args:
            address: Endereço completo do cliente
            tenant_id: ID do tenant

        Returns:
            {
                'is_deliverable': bool,
                'delivery_fee': float,
                'delivery_time_minutes': int,
                'distance_km': float,
                'coordinates': dict,
                'neighborhood': str,
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
                'delivery_time_minutes': 60,  # Default se não tiver config
                'coordinates': cached.coordinates,
                'neighborhood': cached.neighborhood,
                'normalized_address': cached.normalized_address,
                'message': f'Endereço validado! 🎉' if cached.is_deliverable
                          else 'Fora da área de entrega 😔',
                'from_cache': True
            }

        # Geocodificar endereço
        geocode_result = await self._geocode_address(address)

        if not geocode_result.get('success'):
            return {
                'is_deliverable': False,
                'message': geocode_result.get('error', 'Não consegui localizar o endereço'),
                'requires_clarification': True
            }

        coordinates = geocode_result['coordinates']
        normalized_address = geocode_result['formatted_address']
        neighborhood = geocode_result.get('neighborhood', '')

        # Buscar configurações de raio do tenant
        configs = await self.get_radius_configs(tenant_id)

        if not configs:
            return {
                'is_deliverable': False,
                'message': 'Configuração de entrega por raio não encontrada',
                'normalized_address': normalized_address,
                'coordinates': coordinates
            }

        # Calcular distância para cada configuração
        best_match = None
        min_distance = float('inf')

        for config in configs:
            if not config.center_lat or not config.center_lng:
                continue

            distance_km = self._calculate_distance(
                lat1=float(config.center_lat),
                lng1=float(config.center_lng),
                lat2=coordinates['lat'],
                lng2=coordinates['lng']
            )

            # Verificar se está dentro do raio
            if (float(config.radius_km_start) <= distance_km <= float(config.radius_km_end)):
                if distance_km < min_distance:
                    min_distance = distance_km
                    best_match = (config, distance_km)

        if not best_match:
            # Fora da área de entrega
            await self.cache_service.cache_address(
                address=address,
                tenant_id=tenant_id,
                normalized_address=normalized_address,
                coordinates=coordinates,
                neighborhood=neighborhood,
                is_deliverable=False,
                delivery_fee=0
            )

            return {
                'is_deliverable': False,
                'normalized_address': normalized_address,
                'coordinates': coordinates,
                'neighborhood': neighborhood,
                'message': 'Desculpe, esse endereço está fora da nossa área de entrega 😔'
            }

        # Encontrou configuração válida
        config, distance_km = best_match
        delivery_fee = float(config.delivery_fee)

        # Salvar no cache
        await self.cache_service.cache_address(
            address=address,
            tenant_id=tenant_id,
            normalized_address=normalized_address,
            coordinates=coordinates,
            neighborhood=neighborhood,
            is_deliverable=True,
            delivery_fee=delivery_fee,
            delivery_area_id=config.id
        )

        message = f'Entregamos no seu endereço! 🎉 Distância: {distance_km:.1f}km'
        if delivery_fee > 0:
            message += f' - Taxa: R$ {delivery_fee:.2f}'
        else:
            message += ' - Entrega GRÁTIS! 🎁'

        return {
            'is_deliverable': True,
            'delivery_fee': delivery_fee,
            'delivery_time_minutes': config.delivery_time_minutes,
            'distance_km': distance_km,
            'coordinates': coordinates,
            'neighborhood': neighborhood,
            'normalized_address': normalized_address,
            'radius_config': config,
            'message': message,
            'from_cache': False
        }

    async def _geocode_address(self, address: str) -> Dict[str, Any]:
        """
        Geocodifica endereço usando Google Maps API

        Returns:
            {
                'success': bool,
                'coordinates': {'lat': float, 'lng': float},
                'formatted_address': str,
                'neighborhood': str,
                'city': str,
                'state': str,
                'error': str (se success=False)
            }
        """
        try:
            result = self.gmaps.geocode(address, region='br')

            if not result:
                return {
                    'success': False,
                    'error': 'Endereço não encontrado. Verifique se está correto.'
                }

            location = result[0]['geometry']['location']
            address_components = result[0]['address_components']

            # Extrair componentes
            neighborhood = ''
            city = ''
            state = ''

            for component in address_components:
                types = component['types']
                if 'sublocality' in types or 'neighborhood' in types:
                    neighborhood = component['long_name']
                elif 'administrative_area_level_2' in types:
                    city = component['long_name']
                elif 'administrative_area_level_1' in types:
                    state = component['short_name']

            return {
                'success': True,
                'coordinates': {
                    'lat': location['lat'],
                    'lng': location['lng']
                },
                'formatted_address': result[0]['formatted_address'],
                'neighborhood': neighborhood,
                'city': city,
                'state': state,
                'place_id': result[0].get('place_id')
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Erro ao validar endereço: {str(e)}'
            }

    def _calculate_distance(
        self,
        lat1: float,
        lng1: float,
        lat2: float,
        lng2: float
    ) -> float:
        """
        Calcula distância entre dois pontos usando fórmula de Haversine

        Returns:
            Distância em quilômetros
        """
        # Raio da Terra em km
        R = 6371.0

        # Converter para radianos
        lat1_rad = math.radians(lat1)
        lng1_rad = math.radians(lng1)
        lat2_rad = math.radians(lat2)
        lng2_rad = math.radians(lng2)

        # Diferenças
        dlat = lat2_rad - lat1_rad
        dlng = lng2_rad - lng1_rad

        # Fórmula de Haversine
        a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        distance = R * c
        return distance

    async def get_radius_configs(self, tenant_id: UUID) -> list:
        """
        Retorna configurações de raio do tenant (ordenadas por raio inicial)
        """
        return self.db.query(RadiusConfig).filter(
            and_(
                RadiusConfig.tenant_id == tenant_id,
                RadiusConfig.is_active == True
            )
        ).order_by(RadiusConfig.radius_km_start).all()

    async def add_radius_config(
        self,
        tenant_id: UUID,
        center_address: str,
        radius_km_start: float,
        radius_km_end: float,
        delivery_fee: float,
        delivery_time_minutes: int = 60
    ) -> RadiusConfig:
        """
        Adiciona nova configuração de raio

        Args:
            center_address: Endereço central (ex: endereço da loja)
            radius_km_start: Raio inicial em KM
            radius_km_end: Raio final em KM
            delivery_fee: Taxa de entrega
            delivery_time_minutes: Tempo estimado de entrega
        """
        # Geocodificar endereço central
        geocode_result = await self._geocode_address(center_address)

        if not geocode_result.get('success'):
            raise ValueError(f"Não foi possível geocodificar o endereço: {center_address}")

        coordinates = geocode_result['coordinates']

        # Buscar delivery_area do tenant
        delivery_area = self.db.query(DeliveryArea).filter(
            DeliveryArea.tenant_id == tenant_id
        ).first()

        if not delivery_area:
            # Criar área de entrega se não existir
            delivery_area = DeliveryArea(
                tenant_id=tenant_id,
                delivery_mode='radius'
            )
            self.db.add(delivery_area)
            self.db.flush()

        # Criar configuração
        config = RadiusConfig(
            tenant_id=tenant_id,
            delivery_area_id=delivery_area.id,
            center_address=center_address,
            center_lat=coordinates['lat'],
            center_lng=coordinates['lng'],
            radius_km_start=radius_km_start,
            radius_km_end=radius_km_end,
            delivery_fee=delivery_fee,
            delivery_time_minutes=delivery_time_minutes,
            is_active=True
        )

        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)

        return config

    async def update_radius_config(
        self,
        config_id: UUID,
        tenant_id: UUID,
        **kwargs
    ) -> RadiusConfig:
        """
        Atualiza configuração de raio
        """
        config = self.db.query(RadiusConfig).filter(
            and_(
                RadiusConfig.id == config_id,
                RadiusConfig.tenant_id == tenant_id
            )
        ).first()

        if not config:
            raise ValueError('Configuração não encontrada')

        # Se mudou o endereço central, regecodificar
        if 'center_address' in kwargs and kwargs['center_address'] != config.center_address:
            geocode_result = await self._geocode_address(kwargs['center_address'])
            if geocode_result.get('success'):
                config.center_address = kwargs['center_address']
                config.center_lat = geocode_result['coordinates']['lat']
                config.center_lng = geocode_result['coordinates']['lng']
                kwargs.pop('center_address')

        # Atualizar outros campos
        for key, value in kwargs.items():
            if hasattr(config, key) and value is not None:
                setattr(config, key, value)

        self.db.commit()
        self.db.refresh(config)

        return config

    async def delete_radius_config(
        self,
        config_id: UUID,
        tenant_id: UUID
    ) -> bool:
        """
        Desativa configuração de raio (soft delete)
        """
        config = self.db.query(RadiusConfig).filter(
            and_(
                RadiusConfig.id == config_id,
                RadiusConfig.tenant_id == tenant_id
            )
        ).first()

        if not config:
            return False

        config.is_active = False
        self.db.commit()

        return True

    async def bulk_add_radius_configs(
        self,
        tenant_id: UUID,
        center_address: str,
        radius_tiers: list
    ) -> list:
        """
        Adiciona múltiplas faixas de raio de uma vez

        radius_tiers: [
            {'start': 0, 'end': 5, 'fee': 0, 'time': 30},
            {'start': 5, 'end': 10, 'fee': 10, 'time': 45},
            {'start': 10, 'end': 15, 'fee': 20, 'time': 60},
        ]
        """
        created = []

        for tier in radius_tiers:
            config = await self.add_radius_config(
                tenant_id=tenant_id,
                center_address=center_address,
                radius_km_start=tier['start'],
                radius_km_end=tier['end'],
                delivery_fee=tier['fee'],
                delivery_time_minutes=tier.get('time', 60)
            )
            created.append(config)

        return created
