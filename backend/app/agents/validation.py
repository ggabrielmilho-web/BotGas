"""
Validation Agent - Validates delivery addresses using 3 modes
"""
from typing import Dict, Any, Optional, Tuple
from uuid import UUID
from datetime import datetime, timedelta
import logging
import re

from app.agents.base import BaseAgent, AgentContext, AgentResponse
from app.database.models import (
    DeliveryArea, NeighborhoodConfig, RadiusConfig,
    HybridRule, AddressCache, Tenant
)
from sqlalchemy.orm import Session
import googlemaps

from app.core.config import settings

logger = logging.getLogger(__name__)


class ValidationAgent(BaseAgent):
    """
    Validates delivery addresses

    Supports 3 delivery modes:
    1. Neighborhood - Manual cadastro de bairros
    2. Radius - Validação por distância (KM)
    3. Hybrid - Combina ambos (prioriza bairros, fallback para raio)
    """

    def __init__(self):
        super().__init__(model_name="gpt-4-turbo-preview", temperature=0.3)
        self.gmaps = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)
        self.cache_duration_days = 30

    async def ask_for_address(self, context: AgentContext) -> AgentResponse:
        """
        Pede endereço de entrega ao cliente

        Usado quando cliente finaliza pedido e não forneceu endereço ainda.

        Args:
            context: Contexto da conversa

        Returns:
            AgentResponse pedindo endereço
        """

        # Verificar se já tem endereço no contexto
        if context.session_data.get("delivery_address"):
            # Já tem endereço, pedir confirmação
            address_info = context.session_data["delivery_address"]
            return AgentResponse(
                text=f"""Endereço confirmado anteriormente:
{address_info.get('normalized_address', 'Endereço registrado')}

Deseja usar este endereço?""",
                intent="confirm_address",
                next_agent="validation",
                context_updates={"stage": "confirming_address"},
                should_end=False
            )

        # Não tem endereço, solicitar
        return AgentResponse(
            text="""Para finalizar o pedido, preciso do seu endereço de entrega.

Por favor, me envie:
📍 Rua, número, bairro e cidade

Exemplo: Rua das Flores, 123, Centro, São Paulo""",
            intent="address_needed",
            next_agent="validation",
            context_updates={"stage": "awaiting_address"},
            should_end=False
        )

    async def process(self, message: str, context: AgentContext) -> AgentResponse:
        """Process address validation"""

        from app.database.base import get_db

        db = next(get_db())

        try:
            # Extract address from message
            address = await self._extract_address(message, context)

            if not address:
                return AgentResponse(
                    text="""Não consegui identificar o endereço.

Por favor, me envie seu endereço completo:
Rua, número, bairro e cidade

Exemplo: Rua das Flores, 123, Centro, São Paulo""",
                    intent="address_needed",
                    should_end=False
                )

            # Validate delivery
            validation_result = await self.validate_delivery(address, context.tenant_id, db)

            if validation_result["is_deliverable"]:
                # Success - address is in delivery area
                fee = validation_result.get("delivery_fee", 0)
                fee_str = f"R$ {fee:.2f}".replace(".", ",")

                response_text = f"""✅ Ótimo! Entregamos no seu endereço!

📍 *Endereço confirmado:*
{validation_result['normalized_address']}

🚚 *Taxa de entrega:* {fee_str if fee > 0 else 'GRÁTIS'}
⏱️ *Tempo estimado:* {validation_result.get('delivery_time', 60)} minutos

Está correto? Podemos continuar com o pedido?"""

                return AgentResponse(
                    text=response_text,
                    intent="address_validated",
                    next_agent="order",
                    context_updates={
                        "stage": "confirming_order",
                        "delivery_address": validation_result,
                        "delivery_fee": fee
                    },
                    should_end=False
                )

            else:
                # Not deliverable
                reason = validation_result.get("reason", "endereço fora da área de entrega")

                response_text = f"""😔 Infelizmente não entregamos neste endereço.

Motivo: {reason}

Gostaria de:
• Tentar outro endereço
• Falar com um atendente"""

                return AgentResponse(
                    text=response_text,
                    intent="address_rejected",
                    requires_human=True,
                    should_end=False
                )

        except Exception as e:
            logger.error(f"Error in validation agent: {e}")
            return AgentResponse(
                text="Desculpe, tive um problema ao validar o endereço. Pode tentar novamente?",
                intent="error",
                should_end=False
            )

        finally:
            db.close()

    async def process_with_extracted_data(
        self,
        extracted_info: dict,
        context: AgentContext,
        db: Session
    ) -> AgentResponse:
        """
        Validate address with pre-extracted data from MessageExtractor

        Args:
            extracted_info: Information extracted by fine-tuned model
            context: AgentContext
            db: Database session

        Returns:
            AgentResponse
        """
        try:
            # Get address information from extracted_info
            address_info = extracted_info.get("address", {})
            confidence = address_info.get("confidence", 0.0)

            # If confidence is low, ask for address again
            if confidence < 0.7:
                return AgentResponse(
                    text="""Não consegui identificar o endereço completo.

Por favor, me envie:
Rua, número, bairro

Exemplo: Rua das Flores, 123, Centro""",
                    intent="address_needed",
                    should_end=False
                )

            # Build complete address string
            street = address_info.get("street", "")
            number = address_info.get("number", "")
            neighborhood = address_info.get("neighborhood", "")
            complement = address_info.get("complement")
            reference = address_info.get("reference")

            # Construct address string
            address_parts = []
            if street:
                address_parts.append(street)
            if number:
                address_parts.append(number)
            if neighborhood:
                address_parts.append(neighborhood)

            if not address_parts:
                return AgentResponse(
                    text="Não consegui identificar o endereço. Por favor, envie rua, número e bairro.",
                    intent="address_needed",
                    should_end=False
                )

            address = ", ".join(address_parts)

            if complement:
                address += f", {complement}"

            # Validate delivery
            validation_result = await self.validate_delivery(address, context.tenant_id, db)

            if validation_result["is_deliverable"]:
                # Success - address is in delivery area
                fee = validation_result.get("delivery_fee", 0)
                fee_str = f"R$ {fee:.2f}".replace(".", ",")

                response_text = f"""✅ Ótimo! Entregamos no seu endereço!

📍 *Endereço confirmado:*
{validation_result['normalized_address']}"""

                if reference:
                    response_text += f"\n🏠 *Referência:* {reference}"

                response_text += f"""

🚚 *Taxa de entrega:* {fee_str if fee > 0 else 'GRÁTIS'}
⏱️ *Tempo estimado:* {validation_result.get('delivery_time', 60)} minutos

Está correto? Podemos continuar com o pedido?"""

                return AgentResponse(
                    text=response_text,
                    intent="address_validated",
                    next_agent="order",
                    context_updates={
                        "stage": "confirming_order",
                        "delivery_address": validation_result,
                        "delivery_fee": fee
                    },
                    should_end=False
                )

            else:
                # Not deliverable
                reason = validation_result.get("reason", "endereço fora da área de entrega")

                response_text = f"""😔 Infelizmente não entregamos neste endereço.

Motivo: {reason}

Gostaria de:
• Tentar outro endereço
• Falar com um atendente"""

                return AgentResponse(
                    text=response_text,
                    intent="address_rejected",
                    requires_human=True,
                    should_end=False
                )

        except Exception as e:
            logger.error(f"Error in process_with_extracted_data: {e}")
            return AgentResponse(
                text="Desculpe, tive um problema ao validar o endereço. Pode tentar novamente?",
                intent="error",
                should_end=False
            )

    async def validate_delivery(
        self,
        address: str,
        tenant_id: UUID,
        db: Session
    ) -> Dict[str, Any]:
        """
        Main validation method - routes to appropriate mode
        """

        # Check cache first
        cached = await self._check_address_cache(address, tenant_id, db)
        if cached:
            logger.info(f"Address loaded from cache: {address[:50]}")
            return cached

        # Get delivery configuration
        delivery_config = db.query(DeliveryArea).filter(
            DeliveryArea.tenant_id == tenant_id
        ).first()

        if not delivery_config:
            return {
                "is_deliverable": False,
                "reason": "Configuração de entrega não encontrada"
            }

        mode = delivery_config.delivery_mode

        # Route to appropriate validation method
        if mode == "neighborhood":
            result = await self._validate_by_neighborhood(address, tenant_id, db)
        elif mode == "radius":
            result = await self._validate_by_radius(address, tenant_id, db, delivery_config)
        elif mode == "hybrid":
            result = await self._validate_hybrid(address, tenant_id, db, delivery_config)
        else:
            result = {
                "is_deliverable": False,
                "reason": f"Modo de entrega inválido: {mode}"
            }

        # Save to cache if successful
        if result.get("is_deliverable"):
            await self._save_to_cache(address, tenant_id, result, db)

        return result

    async def _validate_by_neighborhood(
        self,
        address: str,
        tenant_id: UUID,
        db: Session
    ) -> Dict[str, Any]:
        """Validate by neighborhood (manual cadastro)"""

        # Strategy 1: Try to extract neighborhood from message text directly
        # This is faster and works even without Google Maps
        address_lower = address.lower()

        # Get all neighborhood configs for this tenant
        all_neighborhoods = db.query(NeighborhoodConfig).filter(
            NeighborhoodConfig.tenant_id == tenant_id,
            NeighborhoodConfig.is_active == True
        ).all()

        # Try to find neighborhood name in the address text
        for neighborhood_config in all_neighborhoods:
            neighborhood_name_lower = neighborhood_config.neighborhood_name.lower()
            if neighborhood_name_lower in address_lower:
                # Found neighborhood in address text!
                logger.info(f"Neighborhood found in text: {neighborhood_config.neighborhood_name}")

                # Complete address with city and state from neighborhood config
                normalized_address = f"{address}, {neighborhood_config.city}, {neighborhood_config.state}"

                return {
                    "is_deliverable": True,
                    "normalized_address": normalized_address,
                    "coordinates": {"lat": 0, "lng": 0},  # No coordinates in this mode
                    "neighborhood": neighborhood_config.neighborhood_name,
                    "city": neighborhood_config.city,
                    "state": neighborhood_config.state,
                    "delivery_fee": float(neighborhood_config.delivery_fee),
                    "delivery_time": neighborhood_config.delivery_time_minutes,
                    "validation_mode": "neighborhood_text"
                }

        # Strategy 2: Fallback to Google Maps if neighborhood not found in text
        geocode_result = await self._geocode_address(address)

        if geocode_result:
            neighborhood = geocode_result.get("neighborhood", "").lower()
            city = geocode_result.get("city", "").lower()

            # Find matching neighborhood config
            neighborhood_config = db.query(NeighborhoodConfig).filter(
                NeighborhoodConfig.tenant_id == tenant_id,
                NeighborhoodConfig.is_active == True,
                NeighborhoodConfig.neighborhood_name.ilike(f"%{neighborhood}%")
            ).first()

            if neighborhood_config:
                return {
                    "is_deliverable": True,
                    "normalized_address": geocode_result["formatted_address"],
                    "coordinates": geocode_result["coordinates"],
                    "neighborhood": neighborhood_config.neighborhood_name,
                    "delivery_fee": float(neighborhood_config.delivery_fee),
                    "delivery_time": neighborhood_config.delivery_time_minutes,
                    "validation_mode": "neighborhood_geocoded"
                }

        # Neither strategy worked
        return {
            "is_deliverable": False,
            "reason": "Não consegui identificar o bairro. Por favor, informe o bairro claramente (ex: Centro, Jardins, Vila Mariana)"
        }

    async def _validate_by_radius(
        self,
        address: str,
        tenant_id: UUID,
        db: Session,
        delivery_config: DeliveryArea
    ) -> Dict[str, Any]:
        """Validate by radius/distance (Google Maps)"""

        # Geocode address
        geocode_result = await self._geocode_address(address)

        if not geocode_result:
            return {
                "is_deliverable": False,
                "reason": "Endereço não encontrado"
            }

        dest_coords = geocode_result["coordinates"]

        # Get all radius configs
        radius_configs = db.query(RadiusConfig).filter(
            RadiusConfig.tenant_id == tenant_id,
            RadiusConfig.is_active == True
        ).order_by(RadiusConfig.radius_km_start).all()

        if not radius_configs:
            return {
                "is_deliverable": False,
                "reason": "Configuração de raio não encontrada"
            }

        # Calculate distance from center
        for config in radius_configs:
            origin = (config.center_lat, config.center_lng)
            destination = (dest_coords["lat"], dest_coords["lng"])

            distance = self._calculate_distance(origin, destination)

            # Check if within this radius range
            if config.radius_km_start <= distance <= config.radius_km_end:
                return {
                    "is_deliverable": True,
                    "normalized_address": geocode_result["formatted_address"],
                    "coordinates": dest_coords,
                    "distance_km": round(distance, 2),
                    "delivery_fee": float(config.delivery_fee),
                    "delivery_time": config.delivery_time_minutes,
                    "validation_mode": "radius"
                }

        return {
            "is_deliverable": False,
            "reason": f"Endereço fora da área de entrega (distância: {distance:.1f}km)"
        }

    async def _validate_hybrid(
        self,
        address: str,
        tenant_id: UUID,
        db: Session,
        delivery_config: DeliveryArea
    ) -> Dict[str, Any]:
        """Hybrid mode - Try neighborhood first, fallback to radius"""

        # Try neighborhood first
        neighborhood_result = await self._validate_by_neighborhood(address, tenant_id, db)

        if neighborhood_result.get("is_deliverable"):
            neighborhood_result["validation_mode"] = "hybrid_neighborhood"
            return neighborhood_result

        # Fallback to radius
        radius_result = await self._validate_by_radius(address, tenant_id, db, delivery_config)

        if radius_result.get("is_deliverable"):
            radius_result["validation_mode"] = "hybrid_radius"
            return radius_result

        return {
            "is_deliverable": False,
            "reason": "Endereço não está em nossa área de entrega"
        }

    async def _geocode_address(self, address: str) -> Optional[Dict[str, Any]]:
        """Geocode address using Google Maps API"""

        try:
            geocode_result = self.gmaps.geocode(address, language="pt-BR")

            if not geocode_result:
                return None

            result = geocode_result[0]
            components = result["address_components"]

            # Extract components
            neighborhood = ""
            city = ""
            state = ""
            zip_code = ""

            for component in components:
                types = component["types"]

                if "sublocality" in types or "neighborhood" in types:
                    neighborhood = component["long_name"]
                elif "locality" in types or "administrative_area_level_2" in types:
                    city = component["long_name"]
                elif "administrative_area_level_1" in types:
                    state = component["short_name"]
                elif "postal_code" in types:
                    zip_code = component["long_name"]

            location = result["geometry"]["location"]

            return {
                "formatted_address": result["formatted_address"],
                "coordinates": {
                    "lat": location["lat"],
                    "lng": location["lng"]
                },
                "neighborhood": neighborhood,
                "city": city,
                "state": state,
                "zip_code": zip_code,
                "place_id": result["place_id"]
            }

        except Exception as e:
            logger.error(f"Geocoding error: {e}")
            return None

    def _calculate_distance(self, origin: Tuple[float, float], destination: Tuple[float, float]) -> float:
        """Calculate distance in KM using Haversine formula"""

        from math import radians, cos, sin, asin, sqrt

        lat1, lon1 = origin
        lat2, lon2 = destination

        # Convert to radians
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

        # Haversine formula
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * asin(sqrt(a))
        km = 6371 * c  # Earth radius in km

        return km

    async def _check_address_cache(
        self,
        address: str,
        tenant_id: UUID,
        db: Session
    ) -> Optional[Dict[str, Any]]:
        """Check if address is in cache"""

        cached = db.query(AddressCache).filter(
            AddressCache.tenant_id == tenant_id,
            AddressCache.address_text == address.lower()
        ).first()

        if not cached:
            return None

        # Check if cache is still valid
        age = datetime.utcnow() - cached.validated_at
        if age > timedelta(days=self.cache_duration_days):
            return None

        if not cached.is_deliverable:
            return {
                "is_deliverable": False,
                "reason": "Endereço fora da área de entrega (cache)"
            }

        return {
            "is_deliverable": True,
            "normalized_address": cached.normalized_address,
            "coordinates": cached.coordinates,
            "neighborhood": cached.neighborhood,
            "delivery_fee": float(cached.delivery_fee or 0),
            "validation_mode": "cache"
        }

    async def _save_to_cache(
        self,
        address: str,
        tenant_id: UUID,
        result: Dict[str, Any],
        db: Session
    ):
        """Save validated address to cache"""

        try:
            cache_entry = AddressCache(
                tenant_id=tenant_id,
                address_text=address.lower(),
                normalized_address=result.get("normalized_address"),
                coordinates=result.get("coordinates"),
                neighborhood=result.get("neighborhood"),
                delivery_fee=result.get("delivery_fee", 0),
                is_deliverable=result.get("is_deliverable", False),
                validated_at=datetime.utcnow()
            )

            db.add(cache_entry)
            db.commit()

            logger.info(f"Address saved to cache: {address[:50]}")

        except Exception as e:
            logger.error(f"Error saving to cache: {e}")
            db.rollback()

    async def _extract_address(self, message: str, context: AgentContext) -> Optional[str]:
        """Extract address from message"""

        # Check if address is already in context
        if context.session_data.get("pending_address"):
            return message.strip()

        # Try to detect address pattern
        # Brazilian address usually has: street, number, neighborhood
        address_pattern = r"(rua|avenida|av|alameda|travessa|praça)\s+.*?\d+"

        if re.search(address_pattern, message.lower()):
            return message.strip()

        # If message is long enough and contains location indicators
        location_words = ["rua", "avenida", "bairro", "número", "nº", "n°"]
        if len(message) > 15 and any(word in message.lower() for word in location_words):
            return message.strip()

        return None
