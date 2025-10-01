"""
Human intervention service - manages bot pausing for human operators
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import UUID
import logging

from sqlalchemy.orm import Session
from sqlalchemy import and_

logger = logging.getLogger(__name__)


class InterventionService:
    """Manages human intervention in conversations"""

    INTERVENTION_DURATION_MINUTES = 5

    def __init__(self, db: Session):
        self.db = db

    async def check_intervention_status(
        self,
        tenant_id: UUID,
        customer_phone: str,
        conversation_id: UUID
    ) -> Dict[str, Any]:
        """
        Check if conversation is under human intervention

        Returns:
            {
                "is_active": bool,
                "started_at": datetime,
                "expires_at": datetime,
                "minutes_remaining": int
            }
        """
        from app.database.models import Conversation

        conversation = self.db.query(Conversation).filter(
            and_(
                Conversation.id == conversation_id,
                Conversation.tenant_id == tenant_id
            )
        ).first()

        if not conversation or not conversation.human_intervention:
            return {"is_active": False}

        started_at = conversation.intervention_started_at
        if not started_at:
            return {"is_active": False}

        now = datetime.utcnow()
        time_passed = now - started_at
        duration = timedelta(minutes=self.INTERVENTION_DURATION_MINUTES)

        # Check if intervention has expired
        if time_passed >= duration:
            await self.end_intervention(conversation_id, auto_ended=True)
            return {"is_active": False}

        # Still active
        expires_at = started_at + duration
        minutes_remaining = int((duration - time_passed).total_seconds() / 60)

        return {
            "is_active": True,
            "started_at": started_at,
            "expires_at": expires_at,
            "minutes_remaining": minutes_remaining
        }

    async def start_intervention(
        self,
        conversation_id: UUID,
        tenant_id: UUID,
        reason: Optional[str] = None,
        operator_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Start human intervention - pauses bot for 5 minutes
        """
        from app.database.models import Conversation, HumanIntervention

        conversation = self.db.query(Conversation).filter(
            and_(
                Conversation.id == conversation_id,
                Conversation.tenant_id == tenant_id
            )
        ).first()

        if not conversation:
            raise ValueError("Conversation not found")

        now = datetime.utcnow()

        # Update conversation
        conversation.human_intervention = True
        conversation.intervention_started_at = now

        # Create intervention log
        intervention = HumanIntervention(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            started_at=now,
            reason=reason or "Manual intervention",
            messages_during_intervention=[]
        )

        self.db.add(intervention)
        self.db.commit()

        logger.info(f"Human intervention started for conversation {conversation_id}")

        return {
            "intervention_id": intervention.id,
            "started_at": now,
            "expires_at": now + timedelta(minutes=self.INTERVENTION_DURATION_MINUTES),
            "duration_minutes": self.INTERVENTION_DURATION_MINUTES
        }

    async def end_intervention(
        self,
        conversation_id: UUID,
        auto_ended: bool = False,
        operator_notes: Optional[str] = None
    ) -> bool:
        """
        End human intervention - resumes bot
        """
        from app.database.models import Conversation, HumanIntervention

        conversation = self.db.query(Conversation).first()

        if not conversation:
            return False

        now = datetime.utcnow()

        # Update conversation
        conversation.human_intervention = False
        conversation.intervention_ended_at = now

        # Update intervention log
        intervention = self.db.query(HumanIntervention).filter(
            and_(
                HumanIntervention.conversation_id == conversation_id,
                HumanIntervention.ended_at.is_(None)
            )
        ).first()

        if intervention:
            intervention.ended_at = now
            if operator_notes:
                intervention.operator_notes = operator_notes

        self.db.commit()

        reason = "Auto-expired" if auto_ended else "Manual"
        logger.info(f"Human intervention ended for conversation {conversation_id} - {reason}")

        return True

    async def log_message_during_intervention(
        self,
        conversation_id: UUID,
        message: Dict[str, Any]
    ) -> bool:
        """
        Log messages received during intervention (not processed by bot)
        """
        from app.database.models import HumanIntervention
        from sqlalchemy.dialects.postgresql import array

        intervention = self.db.query(HumanIntervention).filter(
            and_(
                HumanIntervention.conversation_id == conversation_id,
                HumanIntervention.ended_at.is_(None)
            )
        ).first()

        if not intervention:
            return False

        # Add message to log
        if intervention.messages_during_intervention is None:
            intervention.messages_during_intervention = []

        intervention.messages_during_intervention.append({
            "timestamp": datetime.utcnow().isoformat(),
            "content": message.get("content", ""),
            "type": message.get("type", "text")
        })

        self.db.commit()

        return True

    async def should_auto_intervene(
        self,
        message: str,
        context: Dict[str, Any]
    ) -> bool:
        """
        Detect if message requires automatic human intervention

        Triggers:
        - Customer explicitly asks for human
        - Complex complaints
        - Payment issues
        """
        message_lower = message.lower()

        # Explicit human request
        human_keywords = [
            "falar com atendente",
            "quero falar com alguém",
            "atendente humano",
            "falar com pessoa",
            "não estou entendendo"
        ]

        if any(keyword in message_lower for keyword in human_keywords):
            return True

        # Complaint indicators
        complaint_keywords = [
            "reclamação",
            "problema",
            "insatisfeito",
            "cancelar",
            "péssimo"
        ]

        if any(keyword in message_lower for keyword in complaint_keywords):
            return True

        return False

    async def get_active_interventions(
        self,
        tenant_id: UUID
    ) -> list:
        """
        Get all active interventions for tenant
        """
        from app.database.models import HumanIntervention, Conversation

        interventions = self.db.query(HumanIntervention).join(
            Conversation
        ).filter(
            and_(
                HumanIntervention.tenant_id == tenant_id,
                HumanIntervention.ended_at.is_(None),
                Conversation.human_intervention == True
            )
        ).all()

        result = []
        for intervention in interventions:
            status = await self.check_intervention_status(
                tenant_id,
                intervention.conversation.customer.whatsapp_number,
                intervention.conversation_id
            )

            result.append({
                "intervention_id": intervention.id,
                "conversation_id": intervention.conversation_id,
                "customer_phone": intervention.conversation.customer.whatsapp_number,
                "customer_name": intervention.conversation.customer.name,
                "started_at": intervention.started_at,
                "status": status,
                "reason": intervention.reason,
                "messages_count": len(intervention.messages_during_intervention or [])
            })

        return result
