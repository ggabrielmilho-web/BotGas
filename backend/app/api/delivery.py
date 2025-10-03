"""
Delivery Configuration API Endpoints
Endpoints para gerenciar configuração de entrega (bairros, raio, híbrido)
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.base import get_db
from app.middleware.tenant import get_current_tenant
from app.database.models import Tenant
from app.services.delivery_modes import DeliveryModeService
from app.services.neighborhood_delivery import NeighborhoodDeliveryService
from app.services.radius_delivery import RadiusDeliveryService
from app.services.hybrid_delivery import HybridDeliveryService


router = APIRouter(prefix="/api/v1/delivery", tags=["delivery"])


# ============================================================================
# SCHEMAS
# ============================================================================

class DeliveryConfigBase(BaseModel):
    delivery_mode: str = Field(..., description="neighborhood, radius ou hybrid")
    free_delivery_minimum: Optional[float] = None
    default_fee: Optional[float] = None


class DeliveryConfigResponse(DeliveryConfigBase):
    id: UUID
    tenant_id: UUID

    class Config:
        from_attributes = True


class NeighborhoodCreate(BaseModel):
    neighborhood_name: str
    city: str = "São Paulo"
    state: str = "SP"
    delivery_type: str = "paid"  # free, paid, not_available
    delivery_fee: float = 0
    delivery_time_minutes: int = 60
    zip_codes: Optional[List[str]] = None
    notes: Optional[str] = None


class NeighborhoodUpdate(BaseModel):
    neighborhood_name: Optional[str] = None
    delivery_type: Optional[str] = None
    delivery_fee: Optional[float] = None
    delivery_time_minutes: Optional[int] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class NeighborhoodResponse(BaseModel):
    id: UUID
    neighborhood_name: str
    city: str
    state: str
    delivery_type: str
    delivery_fee: float
    delivery_time_minutes: int
    is_active: bool

    class Config:
        from_attributes = True


class RadiusConfigCreate(BaseModel):
    center_address: str
    radius_km_start: float
    radius_km_end: float
    delivery_fee: float
    delivery_time_minutes: int = 60


class RadiusConfigUpdate(BaseModel):
    center_address: Optional[str] = None
    radius_km_start: Optional[float] = None
    radius_km_end: Optional[float] = None
    delivery_fee: Optional[float] = None
    delivery_time_minutes: Optional[int] = None
    is_active: Optional[bool] = None


class RadiusConfigResponse(BaseModel):
    id: UUID
    center_address: str
    center_lat: Optional[float]
    center_lng: Optional[float]
    radius_km_start: float
    radius_km_end: float
    delivery_fee: float
    delivery_time_minutes: int
    is_active: bool

    class Config:
        from_attributes = True


class AddressValidationRequest(BaseModel):
    address: str
    order_total: Optional[float] = None


class AddressValidationResponse(BaseModel):
    is_deliverable: bool
    delivery_fee: Optional[float] = None
    delivery_time_minutes: Optional[int] = None
    neighborhood: Optional[str] = None
    coordinates: Optional[dict] = None
    normalized_address: Optional[str] = None
    message: str
    validation_method: Optional[str] = None


class BulkNeighborhoodCreate(BaseModel):
    neighborhoods: List[dict]


class BulkRadiusCreate(BaseModel):
    center_address: str
    radius_tiers: List[dict]


class HybridSetupRequest(BaseModel):
    center_address: str
    main_neighborhoods: List[dict]
    radius_tiers: List[dict]


# ============================================================================
# ENDPOINTS - DELIVERY CONFIG
# ============================================================================

@router.get("/config", response_model=DeliveryConfigResponse)
async def get_delivery_config(
    db: Session = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    Retorna configuração de entrega do tenant
    """
    service = DeliveryModeService(db)
    config = await service.get_delivery_config(current_tenant.id)

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuração de entrega não encontrada"
        )

    return config


@router.put("/mode")
async def update_delivery_mode(
    config_data: DeliveryConfigBase,
    db: Session = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    Atualiza modo de entrega (neighborhood, radius, hybrid)
    """
    if config_data.delivery_mode not in ['neighborhood', 'radius', 'hybrid']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Modo de entrega inválido. Use: neighborhood, radius ou hybrid"
        )

    service = DeliveryModeService(db)
    config = await service.create_or_update_delivery_config(
        tenant_id=current_tenant.id,
        delivery_mode=config_data.delivery_mode,
        free_delivery_minimum=config_data.free_delivery_minimum,
        default_fee=config_data.default_fee
    )

    return {
        "success": True,
        "message": f"Modo de entrega alterado para {config_data.delivery_mode}",
        "config": config
    }


@router.post("/validate")
async def validate_address(
    request: AddressValidationRequest,
    db: Session = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    Valida endereço de entrega de acordo com modo configurado
    """
    service = DeliveryModeService(db)
    result = await service.validate_address(
        address=request.address,
        tenant_id=current_tenant.id,
        order_total=request.order_total
    )

    return result


# ============================================================================
# ENDPOINTS - NEIGHBORHOODS (Bairros)
# ============================================================================

@router.get("/neighborhoods", response_model=List[NeighborhoodResponse])
async def list_neighborhoods(
    db: Session = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    Lista todos os bairros cadastrados
    """
    service = NeighborhoodDeliveryService(db)
    neighborhoods = await service.get_neighborhoods(current_tenant.id)

    # Converter para dict
    from app.database.models import NeighborhoodConfig

    return [
        {
            "id": n.id,
            "neighborhood_name": n.neighborhood_name,
            "city": n.city,
            "state": n.state,
            "delivery_type": n.delivery_type,
            "delivery_fee": float(n.delivery_fee),
            "delivery_time_minutes": n.delivery_time_minutes,
            "is_active": n.is_active
        }
        for n in neighborhoods
    ]


@router.post("/neighborhoods")
async def create_neighborhood(
    neighborhood: NeighborhoodCreate,
    db: Session = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    Adiciona novo bairro
    """
    service = NeighborhoodDeliveryService(db)

    try:
        config = await service.add_neighborhood(
            tenant_id=current_tenant.id,
            neighborhood_name=neighborhood.neighborhood_name,
            city=neighborhood.city,
            state=neighborhood.state,
            delivery_type=neighborhood.delivery_type,
            delivery_fee=neighborhood.delivery_fee,
            delivery_time_minutes=neighborhood.delivery_time_minutes,
            zip_codes=neighborhood.zip_codes,
            notes=neighborhood.notes
        )

        return {
            "success": True,
            "message": f"Bairro {neighborhood.neighborhood_name} cadastrado com sucesso",
            "neighborhood": config
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/neighborhoods/{neighborhood_id}")
async def update_neighborhood(
    neighborhood_id: UUID,
    neighborhood: NeighborhoodUpdate,
    db: Session = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    Atualiza configuração de bairro
    """
    service = NeighborhoodDeliveryService(db)

    try:
        config = await service.update_neighborhood(
            neighborhood_id=neighborhood_id,
            tenant_id=current_tenant.id,
            **neighborhood.model_dump(exclude_unset=True)
        )

        return {
            "success": True,
            "message": "Bairro atualizado com sucesso",
            "neighborhood": config
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/neighborhoods/{neighborhood_id}")
async def delete_neighborhood(
    neighborhood_id: UUID,
    db: Session = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    Remove bairro (soft delete)
    """
    service = NeighborhoodDeliveryService(db)
    success = await service.delete_neighborhood(neighborhood_id, current_tenant.id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bairro não encontrado"
        )

    return {
        "success": True,
        "message": "Bairro removido com sucesso"
    }


@router.post("/neighborhoods/bulk")
async def bulk_create_neighborhoods(
    request: BulkNeighborhoodCreate,
    db: Session = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    Adiciona múltiplos bairros de uma vez
    """
    service = NeighborhoodDeliveryService(db)
    created = await service.bulk_add_neighborhoods(
        tenant_id=current_tenant.id,
        neighborhoods=request.neighborhoods
    )

    return {
        "success": True,
        "message": f"{len(created)} bairros cadastrados com sucesso",
        "neighborhoods": created
    }


# ============================================================================
# ENDPOINTS - RADIUS (Raio/KM)
# ============================================================================

@router.get("/radius", response_model=List[RadiusConfigResponse])
async def list_radius_configs(
    db: Session = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    Lista todas as configurações de raio
    """
    service = RadiusDeliveryService(db)
    configs = await service.get_radius_configs(current_tenant.id)

    return [
        {
            "id": c.id,
            "center_address": c.center_address,
            "center_lat": float(c.center_lat) if c.center_lat else None,
            "center_lng": float(c.center_lng) if c.center_lng else None,
            "radius_km_start": float(c.radius_km_start),
            "radius_km_end": float(c.radius_km_end),
            "delivery_fee": float(c.delivery_fee),
            "delivery_time_minutes": c.delivery_time_minutes,
            "is_active": c.is_active
        }
        for c in configs
    ]


@router.post("/radius")
async def create_radius_config(
    radius: RadiusConfigCreate,
    db: Session = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    Adiciona configuração de raio/KM
    """
    service = RadiusDeliveryService(db)

    try:
        config = await service.add_radius_config(
            tenant_id=current_tenant.id,
            center_address=radius.center_address,
            radius_km_start=radius.radius_km_start,
            radius_km_end=radius.radius_km_end,
            delivery_fee=radius.delivery_fee,
            delivery_time_minutes=radius.delivery_time_minutes
        )

        return {
            "success": True,
            "message": "Configuração de raio cadastrada com sucesso",
            "config": config
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/radius/{config_id}")
async def update_radius_config(
    config_id: UUID,
    radius: RadiusConfigUpdate,
    db: Session = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    Atualiza configuração de raio
    """
    service = RadiusDeliveryService(db)

    try:
        config = await service.update_radius_config(
            config_id=config_id,
            tenant_id=current_tenant.id,
            **radius.model_dump(exclude_unset=True)
        )

        return {
            "success": True,
            "message": "Configuração de raio atualizada com sucesso",
            "config": config
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/radius/{config_id}")
async def delete_radius_config(
    config_id: UUID,
    db: Session = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    Remove configuração de raio (soft delete)
    """
    service = RadiusDeliveryService(db)
    success = await service.delete_radius_config(config_id, current_tenant.id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuração não encontrada"
        )

    return {
        "success": True,
        "message": "Configuração de raio removida com sucesso"
    }


@router.post("/radius/bulk")
async def bulk_create_radius_configs(
    request: BulkRadiusCreate,
    db: Session = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    Adiciona múltiplas faixas de raio de uma vez
    """
    service = RadiusDeliveryService(db)

    try:
        created = await service.bulk_add_radius_configs(
            tenant_id=current_tenant.id,
            center_address=request.center_address,
            radius_tiers=request.radius_tiers
        )

        return {
            "success": True,
            "message": f"{len(created)} configurações de raio cadastradas com sucesso",
            "configs": created
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================================
# ENDPOINTS - HYBRID (Modo Híbrido)
# ============================================================================

@router.post("/hybrid/setup")
async def setup_hybrid_delivery(
    request: HybridSetupRequest,
    db: Session = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    Setup completo de modo híbrido (bairros + raio)
    """
    service = HybridDeliveryService(db)

    try:
        result = await service.setup_default_hybrid(
            tenant_id=current_tenant.id,
            center_address=request.center_address,
            main_neighborhoods=request.main_neighborhoods,
            radius_tiers=request.radius_tiers
        )

        return {
            "success": True,
            **result
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/hybrid/stats")
async def get_hybrid_stats(
    db: Session = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    Estatísticas do modo híbrido
    """
    service = HybridDeliveryService(db)
    stats = await service.get_delivery_stats(current_tenant.id)

    return stats


# ============================================================================
# ENDPOINTS - CACHE & STATISTICS
# ============================================================================

@router.get("/cache/stats")
async def get_cache_stats(
    days: int = 30,
    db: Session = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    Estatísticas do cache de endereços
    """
    from app.services.address_cache import AddressCacheService

    service = AddressCacheService(db)
    stats = await service.get_cache_statistics(current_tenant.id, days)

    return stats


@router.post("/cache/cleanup")
async def cleanup_expired_cache(
    db: Session = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """
    Remove endereços expirados do cache
    """
    from app.services.address_cache import AddressCacheService

    service = AddressCacheService(db)
    deleted = await service.cleanup_expired_cache(current_tenant.id)

    return {
        "success": True,
        "message": f"{deleted} endereços expirados removidos do cache"
    }
