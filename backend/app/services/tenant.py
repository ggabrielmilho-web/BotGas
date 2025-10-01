"""
Tenant service for multi-tenant operations
"""
from typing import Optional
from datetime import datetime, timedelta
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from app.database.models import Tenant, User
from app.core.security import get_password_hash


class TenantService:
    """Service for tenant management"""

    @staticmethod
    def get_tenant_by_id(db: Session, tenant_id: UUID) -> Optional[Tenant]:
        """Get tenant by ID"""
        return db.query(Tenant).filter(Tenant.id == tenant_id).first()

    @staticmethod
    def get_tenant_by_cnpj(db: Session, cnpj: str) -> Optional[Tenant]:
        """Get tenant by CNPJ"""
        return db.query(Tenant).filter(Tenant.cnpj == cnpj).first()

    @staticmethod
    def get_tenant_by_phone(db: Session, phone: str) -> Optional[Tenant]:
        """Get tenant by phone"""
        return db.query(Tenant).filter(Tenant.phone == phone).first()

    @staticmethod
    def create_tenant(
        db: Session,
        company_name: str,
        email: str,
        password: str,
        phone: str,
        cnpj: Optional[str] = None,
        trial_days: int = 7
    ) -> Tenant:
        """
        Create new tenant with trial period and admin user

        Args:
            db: Database session
            company_name: Company name
            email: Admin user email
            password: Admin user password
            phone: Company phone
            cnpj: Optional CNPJ
            trial_days: Trial period in days (default 7)

        Returns:
            Created tenant

        Raises:
            HTTPException: If CNPJ or email already exists
        """
        # Check if CNPJ already exists
        if cnpj:
            existing_tenant = TenantService.get_tenant_by_cnpj(db, cnpj)
            if existing_tenant:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="CNPJ already registered"
                )

        # Check if email already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        try:
            # Create tenant
            trial_ends_at = datetime.utcnow() + timedelta(days=trial_days)
            tenant = Tenant(
                company_name=company_name,
                cnpj=cnpj,
                phone=phone,
                email=email,
                trial_ends_at=trial_ends_at,
                subscription_status="trial",
                payment_methods=["Dinheiro"],
                pix_enabled=False
            )
            db.add(tenant)
            db.flush()  # Get tenant.id

            # Create admin user
            admin_user = User(
                tenant_id=tenant.id,
                email=email,
                password_hash=get_password_hash(password),
                full_name=company_name,
                role="admin",
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            db.refresh(tenant)

            return tenant

        except IntegrityError as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error creating tenant"
            ) from e

    @staticmethod
    def update_tenant(
        db: Session,
        tenant_id: UUID,
        **kwargs
    ) -> Tenant:
        """
        Update tenant information

        Args:
            db: Database session
            tenant_id: Tenant UUID
            **kwargs: Fields to update

        Returns:
            Updated tenant
        """
        tenant = TenantService.get_tenant_by_id(db, tenant_id)
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )

        # Update allowed fields
        allowed_fields = [
            'company_name', 'phone', 'email', 'address',
            'payment_methods', 'pix_enabled', 'pix_key',
            'pix_name', 'payment_instructions', 'settings'
        ]

        for field, value in kwargs.items():
            if field in allowed_fields and value is not None:
                setattr(tenant, field, value)

        tenant.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(tenant)
        return tenant

    @staticmethod
    def is_trial_active(tenant: Tenant) -> bool:
        """
        Check if tenant trial is still active

        Args:
            tenant: Tenant object

        Returns:
            True if trial is active, False otherwise
        """
        if tenant.subscription_status != "trial":
            return False

        if tenant.trial_ends_at and tenant.trial_ends_at > datetime.utcnow():
            return True

        return False

    @staticmethod
    def is_subscription_active(tenant: Tenant) -> bool:
        """
        Check if tenant has active subscription (trial or paid)

        Args:
            tenant: Tenant object

        Returns:
            True if subscription is active
        """
        if tenant.subscription_status == "trial":
            return TenantService.is_trial_active(tenant)

        return tenant.subscription_status == "active"

    @staticmethod
    def update_whatsapp_connection(
        db: Session,
        tenant_id: UUID,
        instance_id: str,
        connected: bool
    ) -> Tenant:
        """
        Update WhatsApp connection status

        Args:
            db: Database session
            tenant_id: Tenant UUID
            instance_id: WhatsApp instance ID
            connected: Connection status

        Returns:
            Updated tenant
        """
        tenant = TenantService.get_tenant_by_id(db, tenant_id)
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )

        tenant.whatsapp_instance_id = instance_id
        tenant.whatsapp_connected = connected
        tenant.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(tenant)
        return tenant

    @staticmethod
    def get_tenant_stats(db: Session, tenant_id: UUID) -> dict:
        """
        Get tenant statistics

        Args:
            db: Database session
            tenant_id: Tenant UUID

        Returns:
            Dictionary with tenant stats
        """
        from app.database.models import Order, Customer, Product

        tenant = TenantService.get_tenant_by_id(db, tenant_id)
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )

        # Count orders
        total_orders = db.query(Order).filter(Order.tenant_id == tenant_id).count()

        # Count customers
        total_customers = db.query(Customer).filter(Customer.tenant_id == tenant_id).count()

        # Count products
        total_products = db.query(Product).filter(
            Product.tenant_id == tenant_id,
            Product.is_available == True
        ).count()

        # Trial info
        is_trial = tenant.subscription_status == "trial"
        trial_days_left = None
        if is_trial and tenant.trial_ends_at:
            delta = tenant.trial_ends_at - datetime.utcnow()
            trial_days_left = max(0, delta.days)

        return {
            "tenant_id": str(tenant_id),
            "company_name": tenant.company_name,
            "subscription_status": tenant.subscription_status,
            "is_trial": is_trial,
            "trial_days_left": trial_days_left,
            "whatsapp_connected": tenant.whatsapp_connected,
            "total_orders": total_orders,
            "total_customers": total_customers,
            "total_products": total_products
        }
