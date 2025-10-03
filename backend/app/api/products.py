"""
Product API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database.base import get_db
from app.database.models import Product, Tenant
from app.database.schemas import ProductCreate, ProductUpdate, ProductResponse
from app.middleware.tenant import get_current_tenant


router = APIRouter(prefix="/api/v1/products", tags=["Products"])


@router.get("", response_model=List[ProductResponse])
async def list_products(
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """List all products for the current tenant"""
    products = db.query(Product).filter(Product.tenant_id == tenant.id).all()
    return products


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Create a new product"""
    product = Product(
        tenant_id=tenant.id,
        **product_data.model_dump()
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: UUID,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Get a specific product"""
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.tenant_id == tenant.id
    ).first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    return product


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: UUID,
    product_data: ProductUpdate,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Update a product"""
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.tenant_id == tenant.id
    ).first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    update_data = product_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: UUID,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Delete a product"""
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.tenant_id == tenant.id
    ).first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    db.delete(product)
    db.commit()
    return None
