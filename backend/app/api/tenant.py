"""
Tenant management API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from uuid import UUID

from app.database.base import get_db
from app.database.models import Tenant
from app.middleware.tenant import get_current_tenant, get_current_user
from app.services.tenant import TenantService


router = APIRouter(prefix="/api/v1/tenant", tags=["Tenant"])


# Pydantic Schemas
class TenantResponse(BaseModel):
    """Tenant response schema"""
    id: str
    company_name: str
    cnpj: Optional[str]
    phone: str
    email: str
    address: Optional[Dict[str, Any]]
    whatsapp_connected: bool
    whatsapp_instance_id: Optional[str]
    subscription_status: str
    trial_ends_at: Optional[str]
    payment_methods: List[str]
    pix_enabled: bool
    pix_key: Optional[str]
    pix_name: Optional[str]
    payment_instructions: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


class TenantUpdateRequest(BaseModel):
    """Tenant update request schema"""
    company_name: Optional[str] = Field(None, min_length=3, max_length=255)
    phone: Optional[str] = Field(None, pattern=r"^\+?[1-9]\d{10,14}$")
    email: Optional[str] = None
    address: Optional[Dict[str, Any]] = None
    payment_methods: Optional[List[str]] = None
    pix_enabled: Optional[bool] = None
    pix_key: Optional[str] = None
    pix_name: Optional[str] = None
    payment_instructions: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class TenantStatsResponse(BaseModel):
    """Tenant statistics response"""
    tenant_id: str
    company_name: str
    subscription_status: str
    is_trial: bool
    trial_days_left: Optional[int]
    whatsapp_connected: bool
    total_orders: int
    total_customers: int
    total_products: int


@router.get("", response_model=TenantResponse)
async def get_tenant(
    tenant: Tenant = Depends(get_current_tenant)
):
    """
    Get current tenant information

    Returns tenant profile for authenticated user.
    """
    return TenantResponse(
        id=str(tenant.id),
        company_name=tenant.company_name,
        cnpj=tenant.cnpj,
        phone=tenant.phone,
        email=tenant.email,
        address=tenant.address,
        whatsapp_connected=tenant.whatsapp_connected,
        whatsapp_instance_id=tenant.whatsapp_instance_id,
        subscription_status=tenant.subscription_status,
        trial_ends_at=tenant.trial_ends_at.isoformat() if tenant.trial_ends_at else None,
        payment_methods=tenant.payment_methods or ["Dinheiro"],
        pix_enabled=tenant.pix_enabled,
        pix_key=tenant.pix_key,
        pix_name=tenant.pix_name,
        payment_instructions=tenant.payment_instructions,
        created_at=tenant.created_at.isoformat()
    )


@router.put("", response_model=TenantResponse)
async def update_tenant(
    data: TenantUpdateRequest,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Update tenant information

    Updates tenant profile with provided fields.
    """
    # Convert data to dict, excluding None values
    update_data = data.model_dump(exclude_unset=True)

    # Update tenant
    updated_tenant = TenantService.update_tenant(
        db=db,
        tenant_id=tenant.id,
        **update_data
    )

    return TenantResponse(
        id=str(updated_tenant.id),
        company_name=updated_tenant.company_name,
        cnpj=updated_tenant.cnpj,
        phone=updated_tenant.phone,
        email=updated_tenant.email,
        address=updated_tenant.address,
        whatsapp_connected=updated_tenant.whatsapp_connected,
        whatsapp_instance_id=updated_tenant.whatsapp_instance_id,
        subscription_status=updated_tenant.subscription_status,
        trial_ends_at=updated_tenant.trial_ends_at.isoformat() if updated_tenant.trial_ends_at else None,
        payment_methods=updated_tenant.payment_methods or ["Dinheiro"],
        pix_enabled=updated_tenant.pix_enabled,
        pix_key=updated_tenant.pix_key,
        pix_name=updated_tenant.pix_name,
        payment_instructions=updated_tenant.payment_instructions,
        created_at=updated_tenant.created_at.isoformat()
    )


@router.get("/stats", response_model=TenantStatsResponse)
async def get_tenant_stats(
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Get tenant statistics

    Returns comprehensive stats about orders, customers, products, etc.
    """
    stats = TenantService.get_tenant_stats(db, tenant.id)
    return stats


@router.post("/setup")
async def complete_setup(
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Mark tenant setup as complete

    Called after onboarding flow is finished.
    """
    settings = tenant.settings or {}
    settings["setup_completed"] = True

    TenantService.update_tenant(
        db=db,
        tenant_id=tenant.id,
        settings=settings
    )

    return {"message": "Setup completed successfully"}
