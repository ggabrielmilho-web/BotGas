"""
Delivery Drivers API - Gestão de Motoboys
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from pydantic import BaseModel, Field

from app.database.base import get_db
from app.database.models import DeliveryDriver, Tenant
from app.middleware.tenant import get_current_tenant

router = APIRouter(prefix="/api/v1/delivery-drivers", tags=["Delivery Drivers"])


# Schemas
class DeliveryDriverCreate(BaseModel):
    name: str = Field(..., min_length=3)
    phone: str = Field(..., min_length=10)
    is_active: bool = True

class DeliveryDriverUpdate(BaseModel):
    name: str = None
    phone: str = None
    is_active: bool = None

class DeliveryDriverResponse(BaseModel):
    id: UUID
    name: str
    phone: str
    is_active: bool
    total_deliveries: int

    class Config:
        from_attributes = True


@router.post("", response_model=DeliveryDriverResponse, status_code=status.HTTP_201_CREATED)
async def create_driver(
    data: DeliveryDriverCreate,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant)
):
    """Criar novo motoboy"""
    import re

    # Normalizar telefone: remover caracteres especiais e adicionar +55 se necessário
    phone = re.sub(r'[^0-9]', '', data.phone)
    if not phone.startswith('55'):
        phone = '55' + phone

    driver = DeliveryDriver(
        tenant_id=tenant.id,
        name=data.name,
        phone=phone,
        is_active=data.is_active
    )
    db.add(driver)
    db.commit()
    db.refresh(driver)
    return driver


@router.get("", response_model=List[DeliveryDriverResponse])
async def list_drivers(
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant)
):
    """Listar todos os motoboys"""
    drivers = db.query(DeliveryDriver).filter(
        DeliveryDriver.tenant_id == tenant.id
    ).order_by(DeliveryDriver.created_at.desc()).all()
    return drivers


@router.get("/active", response_model=List[DeliveryDriverResponse])
async def list_active_drivers(
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant)
):
    """Listar apenas motoboys ativos"""
    drivers = db.query(DeliveryDriver).filter(
        DeliveryDriver.tenant_id == tenant.id,
        DeliveryDriver.is_active == True
    ).order_by(DeliveryDriver.name).all()
    return drivers


@router.put("/{driver_id}", response_model=DeliveryDriverResponse)
async def update_driver(
    driver_id: UUID,
    data: DeliveryDriverUpdate,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant)
):
    """Atualizar motoboy"""
    driver = db.query(DeliveryDriver).filter(
        DeliveryDriver.id == driver_id,
        DeliveryDriver.tenant_id == tenant.id
    ).first()

    if not driver:
        raise HTTPException(404, "Motoboy não encontrado")

    if data.name:
        driver.name = data.name
    if data.phone:
        import re
        # Normalizar telefone
        phone = re.sub(r'[^0-9]', '', data.phone)
        if not phone.startswith('55'):
            phone = '55' + phone
        driver.phone = phone
    if data.is_active is not None:
        driver.is_active = data.is_active

    db.commit()
    db.refresh(driver)
    return driver


@router.patch("/{driver_id}/toggle")
async def toggle_driver(
    driver_id: UUID,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant)
):
    """Ativar/Desativar motoboy"""
    driver = db.query(DeliveryDriver).filter(
        DeliveryDriver.id == driver_id,
        DeliveryDriver.tenant_id == tenant.id
    ).first()

    if not driver:
        raise HTTPException(404, "Motoboy não encontrado")

    driver.is_active = not driver.is_active
    db.commit()

    return {"success": True, "is_active": driver.is_active}


@router.delete("/{driver_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_driver(
    driver_id: UUID,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant)
):
    """Excluir motoboy"""
    driver = db.query(DeliveryDriver).filter(
        DeliveryDriver.id == driver_id,
        DeliveryDriver.tenant_id == tenant.id
    ).first()

    if not driver:
        raise HTTPException(404, "Motoboy não encontrado")

    db.delete(driver)
    db.commit()
    return None
