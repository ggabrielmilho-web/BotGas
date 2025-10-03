"""
WhatsApp API endpoints for Evolution integration
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional

from app.database.base import get_db
from app.database.models import Tenant
from app.middleware.tenant import get_current_tenant
from app.services.evolution import evolution_service
from app.services.tenant import TenantService


router = APIRouter(prefix="/api/v1/whatsapp", tags=["WhatsApp"])


# Pydantic Schemas
class QRCodeResponse(BaseModel):
    """QR Code response schema"""
    qr_code: str
    instance_name: str
    status: str


class ConnectionStatusResponse(BaseModel):
    """Connection status response"""
    connected: bool
    instance_name: str
    state: str
    phone_number: Optional[str] = None


class SendMessageRequest(BaseModel):
    """Send message request schema"""
    phone_number: str = Field(..., description="Phone with country code (e.g., 5511999999999)")
    message: str = Field(..., min_length=1)


class SendMessageResponse(BaseModel):
    """Send message response"""
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None


@router.get("/qr", response_model=QRCodeResponse)
async def get_qr_code(
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Get QR Code to connect WhatsApp

    Returns QR code for the user to scan with WhatsApp.
    If instance doesn't exist, creates a new one.
    """
    instance_name = f"tenant_{tenant.id}"

    try:
        # Check if instance exists
        try:
            status_data = await evolution_service.get_instance_status(instance_name)

            # If already connected, return status
            if status_data.get("instance", {}).get("state") == "open":
                return QRCodeResponse(
                    qr_code="",
                    instance_name=instance_name,
                    status="already_connected"
                )

        except:
            # Instance doesn't exist, create it
            await evolution_service.create_instance(instance_name)

            # Wait a bit for Evolution to generate QR code
            import asyncio
            await asyncio.sleep(2)

        # Get QR code
        qr_data = await evolution_service.get_qr_code(instance_name)

        qr_code = qr_data.get("base64", "")

        if not qr_code:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate QR code"
            )

        return QRCodeResponse(
            qr_code=qr_code,
            instance_name=instance_name,
            status="waiting_scan"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting QR code: {str(e)}"
        )


@router.get("/status", response_model=ConnectionStatusResponse)
async def get_connection_status(
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Get WhatsApp connection status

    Returns current connection state and phone number if connected.
    """
    instance_name = f"tenant_{tenant.id}"

    try:
        status_data = await evolution_service.get_instance_status(instance_name)

        instance_info = status_data.get("instance", {})
        state = instance_info.get("state", "close")
        phone_number = instance_info.get("owner", "")

        connected = state == "open"

        # Update tenant status in database
        if connected != tenant.whatsapp_connected:
            TenantService.update_whatsapp_connection(
                db=db,
                tenant_id=tenant.id,
                instance_id=instance_name,
                connected=connected
            )

        return ConnectionStatusResponse(
            connected=connected,
            instance_name=instance_name,
            state=state,
            phone_number=phone_number if connected else None
        )

    except Exception as e:
        # Instance not found or error
        return ConnectionStatusResponse(
            connected=False,
            instance_name=instance_name,
            state="not_found"
        )


@router.post("/send", response_model=SendMessageResponse)
async def send_message(
    data: SendMessageRequest,
    tenant: Tenant = Depends(get_current_tenant)
):
    """
    Send WhatsApp message

    Sends a text message to the specified phone number.
    """
    instance_name = f"tenant_{tenant.id}"

    # Check if WhatsApp is connected
    if not tenant.whatsapp_connected:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="WhatsApp not connected. Please scan QR code first."
        )

    try:
        result = await evolution_service.send_text_message(
            instance_name=instance_name,
            number=data.phone_number,
            message=data.message
        )

        message_id = result.get("key", {}).get("id")

        return SendMessageResponse(
            success=True,
            message_id=message_id
        )

    except Exception as e:
        return SendMessageResponse(
            success=False,
            error=str(e)
        )


@router.post("/disconnect")
async def disconnect_whatsapp(
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Disconnect WhatsApp

    Logs out from WhatsApp and clears the session.
    """
    instance_name = f"tenant_{tenant.id}"

    try:
        await evolution_service.logout_instance(instance_name)

        # Update tenant status
        TenantService.update_whatsapp_connection(
            db=db,
            tenant_id=tenant.id,
            instance_id=None,
            connected=False
        )

        return {"message": "WhatsApp disconnected successfully"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error disconnecting WhatsApp: {str(e)}"
        )


@router.delete("/instance")
async def delete_instance(
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """
    Delete WhatsApp instance completely

    Removes the instance and all associated data.
    Use with caution - this cannot be undone.
    """
    instance_name = f"tenant_{tenant.id}"

    try:
        await evolution_service.delete_instance(instance_name)

        # Update tenant status
        TenantService.update_whatsapp_connection(
            db=db,
            tenant_id=tenant.id,
            instance_id=None,
            connected=False
        )

        return {"message": "Instance deleted successfully"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting instance: {str(e)}"
        )
