"""
Middleware for tenant isolation and authentication
"""
from typing import Optional
from uuid import UUID
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.security import decode_token, verify_token_type
from app.database.base import get_db
from app.database.models import User, Tenant
from app.services.tenant import TenantService


security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get current authenticated user from JWT token

    Args:
        credentials: Bearer token from request
        db: Database session

    Returns:
        Current user object

    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials
    payload = decode_token(token)
    verify_token_type(payload, "access")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    return user


async def get_current_tenant(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Tenant:
    """
    Dependency to get current tenant from authenticated user
    Também verifica status do trial

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        Current tenant object

    Raises:
        HTTPException: If tenant not found
    """
    tenant = TenantService.get_tenant_by_id(db, current_user.tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    return tenant


async def verify_trial_status(
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
) -> Tenant:
    """
    Dependency to verify tenant has active trial or subscription
    Bloqueia acesso se trial expirado

    Args:
        tenant: Current tenant
        db: Database session

    Returns:
        Tenant object if access is allowed

    Raises:
        HTTPException: If trial expired and no active subscription
    """
    from app.services.trial import TrialService
    from datetime import datetime

    # Se já tem assinatura ativa, liberar acesso
    if tenant.subscription_status == 'active':
        return tenant

    # Se está em trial, verificar se expirou
    if tenant.subscription_status == 'trial':
        if tenant.trial_ends_at and datetime.now() > tenant.trial_ends_at:
            # Trial expirado
            tenant.subscription_status = 'expired'
            db.commit()

            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Trial expirado. Por favor, assine um plano para continuar."
            )

    # Se status é 'expired', bloquear
    if tenant.subscription_status == 'expired':
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Acesso bloqueado. Por favor, assine um plano."
        )

    return tenant


async def verify_subscription(
    tenant: Tenant = Depends(get_current_tenant)
) -> Tenant:
    """
    Dependency to verify tenant has active subscription

    Args:
        tenant: Current tenant

    Returns:
        Tenant object if subscription is active

    Raises:
        HTTPException: If subscription is expired
    """
    if not TenantService.is_subscription_active(tenant):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Subscription expired. Please renew your subscription."
        )

    return tenant


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
    tenant: Tenant = Depends(verify_subscription)
) -> User:
    """
    Combined dependency: get current user with active subscription

    Args:
        current_user: Current authenticated user
        tenant: Current tenant (with subscription verification)

    Returns:
        Current user object
    """
    return current_user


class TenantMiddleware:
    """
    Middleware to add tenant context to all requests
    Ensures multi-tenant data isolation
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Extract tenant_id from token if present
        request = Request(scope, receive)
        tenant_id = None

        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                payload = decode_token(token)
                tenant_id = payload.get("tenant_id")
            except:
                pass  # Invalid token, will be handled by route dependencies

        # Add tenant_id to request state
        scope["state"] = {"tenant_id": tenant_id}

        await self.app(scope, receive, send)


def get_tenant_id_from_request(request: Request) -> Optional[UUID]:
    """
    Extract tenant_id from request state

    Args:
        request: FastAPI request object

    Returns:
        Tenant UUID if available, None otherwise
    """
    tenant_id = getattr(request.state, "tenant_id", None)
    if tenant_id:
        return UUID(tenant_id)
    return None


def ensure_tenant_isolation(
    tenant_id: UUID,
    resource_tenant_id: UUID
) -> None:
    """
    Ensure a resource belongs to the current tenant

    Args:
        tenant_id: Current user's tenant ID
        resource_tenant_id: Resource's tenant ID

    Raises:
        HTTPException: If tenant IDs don't match
    """
    if tenant_id != resource_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to resource from different tenant"
        )
