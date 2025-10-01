"""
WhatsApp webhook handler for Evolution API events
"""
from fastapi import APIRouter, Request, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import logging
from datetime import datetime

from app.database.session import get_db
from app.database.models import Tenant, Customer, Conversation, WebhookLog
from app.services.audio_processor import audio_processor
from app.services.evolution import evolution_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/webhook", tags=["Webhooks"])


async def get_tenant_from_instance(instance_name: str, db: Session) -> Optional[Tenant]:
    """
    Get tenant from instance name

    Args:
        instance_name: Instance name (format: tenant_{uuid})
        db: Database session

    Returns:
        Tenant object or None
    """
    if not instance_name.startswith("tenant_"):
        return None

    tenant_id = instance_name.replace("tenant_", "")

    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    return tenant


async def get_or_create_customer(
    db: Session,
    tenant_id: str,
    phone_number: str,
    name: Optional[str] = None
) -> Customer:
    """
    Get existing customer or create new one

    Args:
        db: Database session
        tenant_id: Tenant UUID
        phone_number: Customer WhatsApp number
        name: Optional customer name

    Returns:
        Customer object
    """
    customer = db.query(Customer).filter(
        Customer.tenant_id == tenant_id,
        Customer.whatsapp_number == phone_number
    ).first()

    if not customer:
        customer = Customer(
            tenant_id=tenant_id,
            whatsapp_number=phone_number,
            name=name or phone_number
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)

    return customer


async def get_or_create_conversation(
    db: Session,
    tenant_id: str,
    customer_id: str,
    session_id: str
) -> Conversation:
    """
    Get active conversation or create new one

    Args:
        db: Database session
        tenant_id: Tenant UUID
        customer_id: Customer UUID
        session_id: Session identifier (phone number)

    Returns:
        Conversation object
    """
    # Get active conversation
    conversation = db.query(Conversation).filter(
        Conversation.tenant_id == tenant_id,
        Conversation.customer_id == customer_id,
        Conversation.status == "active"
    ).first()

    if not conversation:
        conversation = Conversation(
            tenant_id=tenant_id,
            customer_id=customer_id,
            session_id=session_id,
            status="active",
            messages=[],
            context={}
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    return conversation


async def process_text_message(
    tenant: Tenant,
    customer: Customer,
    conversation: Conversation,
    message_text: str,
    db: Session
) -> None:
    """
    Process incoming text message

    Args:
        tenant: Tenant object
        customer: Customer object
        conversation: Conversation object
        message_text: Message text
        db: Database session
    """
    # Add message to conversation
    messages = conversation.messages or []
    messages.append({
        "role": "user",
        "content": message_text,
        "timestamp": datetime.utcnow().isoformat(),
        "type": "text"
    })
    conversation.messages = messages
    conversation.total_messages = len(messages)

    db.commit()

    # TODO: Process with AI agents (Session 5)
    logger.info(f"Text message received from {customer.whatsapp_number}: {message_text[:50]}")


async def process_audio_message(
    tenant: Tenant,
    customer: Customer,
    conversation: Conversation,
    audio_url: str,
    db: Session
) -> None:
    """
    Process incoming audio message

    Args:
        tenant: Tenant object
        customer: Customer object
        conversation: Conversation object
        audio_url: URL of audio file
        db: Database session
    """
    # Transcribe audio
    transcription_result = await audio_processor.process_whatsapp_audio(audio_url)

    transcribed_text = transcription_result.get("text", "")
    success = transcription_result.get("success", False)

    # Add message to conversation
    messages = conversation.messages or []
    messages.append({
        "role": "user",
        "content": transcribed_text,
        "timestamp": datetime.utcnow().isoformat(),
        "type": "audio",
        "audio_url": audio_url,
        "transcription_success": success,
        "duration": transcription_result.get("duration")
    })
    conversation.messages = messages
    conversation.total_messages = len(messages)

    db.commit()

    # TODO: Process with AI agents (Session 5)
    logger.info(f"Audio transcribed from {customer.whatsapp_number}: {transcribed_text[:50]}")


@router.post("/evolution")
async def evolution_webhook(request: Request):
    """
    Receive webhooks from Evolution API

    Handles all Evolution API events:
    - MESSAGES_UPSERT: New messages (text, audio, media)
    - QRCODE_UPDATED: QR code changes
    - CONNECTION_UPDATE: Connection status changes
    - etc.
    """
    try:
        payload = await request.json()

        # Log webhook
        db = next(get_db())
        webhook_log = WebhookLog(
            event_type=payload.get("event"),
            payload=payload,
            processed=False
        )
        db.add(webhook_log)
        db.commit()

        # Extract event type
        event = payload.get("event")

        logger.info(f"Webhook received: {event}")

        # Handle different event types
        if event == "messages.upsert":
            await handle_message_upsert(payload, db)
            webhook_log.processed = True

        elif event == "connection.update":
            await handle_connection_update(payload, db)
            webhook_log.processed = True

        elif event == "qrcode.updated":
            logger.info("QR code updated")
            webhook_log.processed = True

        else:
            logger.info(f"Unhandled event: {event}")

        db.commit()
        return {"status": "ok"}

    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return {"status": "error", "message": str(e)}


async def handle_message_upsert(payload: Dict[str, Any], db: Session):
    """
    Handle incoming message event

    Args:
        payload: Webhook payload
        db: Database session
    """
    try:
        data = payload.get("data", {})
        instance = payload.get("instance")

        # Get tenant from instance
        tenant = await get_tenant_from_instance(instance, db)
        if not tenant:
            logger.warning(f"Tenant not found for instance: {instance}")
            return

        # Extract message info
        message = data.get("message", {})
        key = data.get("key", {})

        # Ignore messages from bot (sent by us)
        if key.get("fromMe"):
            return

        # Get sender info
        remote_jid = key.get("remoteJid", "")
        phone_number = remote_jid.replace("@s.whatsapp.net", "")

        push_name = message.get("pushName", phone_number)

        # Get or create customer
        customer = await get_or_create_customer(
            db=db,
            tenant_id=str(tenant.id),
            phone_number=phone_number,
            name=push_name
        )

        # Get or create conversation
        conversation = await get_or_create_conversation(
            db=db,
            tenant_id=str(tenant.id),
            customer_id=str(customer.id),
            session_id=phone_number
        )

        # Check if human intervention is active
        if conversation.human_intervention:
            # TODO: Handle human intervention (just log for now)
            logger.info(f"Human intervention active for {phone_number}")
            await process_text_message(
                tenant, customer, conversation,
                "[Durante intervenção humana]",
                db
            )
            return

        # Process message based on type
        message_type = message.get("messageType")

        if message_type == "conversation" or message_type == "extendedTextMessage":
            # Text message
            text = message.get("conversation") or message.get("extendedTextMessage", {}).get("text", "")
            await process_text_message(tenant, customer, conversation, text, db)

        elif message_type == "audioMessage":
            # Audio message
            audio_msg = message.get("audioMessage", {})
            audio_url = audio_msg.get("url")

            if audio_url:
                await process_audio_message(tenant, customer, conversation, audio_url, db)
            else:
                logger.warning("Audio message without URL")

        elif message_type in ["imageMessage", "videoMessage", "documentMessage"]:
            # Media message (future implementation)
            logger.info(f"Media message received: {message_type}")
            await process_text_message(
                tenant, customer, conversation,
                "[Mensagem de mídia recebida - processamento futuro]",
                db
            )

        else:
            logger.warning(f"Unknown message type: {message_type}")

    except Exception as e:
        logger.error(f"Error handling message: {str(e)}")


async def handle_connection_update(payload: Dict[str, Any], db: Session):
    """
    Handle connection status update

    Args:
        payload: Webhook payload
        db: Database session
    """
    try:
        instance = payload.get("instance")
        data = payload.get("data", {})

        state = data.get("state")

        logger.info(f"Connection update for {instance}: {state}")

        # Get tenant
        tenant = await get_tenant_from_instance(instance, db)
        if not tenant:
            return

        # Update tenant connection status
        connected = state == "open"

        if tenant.whatsapp_connected != connected:
            tenant.whatsapp_connected = connected
            db.commit()
            logger.info(f"Tenant {tenant.id} WhatsApp status updated: {connected}")

    except Exception as e:
        logger.error(f"Error handling connection update: {str(e)}")
