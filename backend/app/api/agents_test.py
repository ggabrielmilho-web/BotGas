"""
API endpoint for testing agents directly
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging

from app.agents.master import MasterAgent
from app.agents.base import AgentContext

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/agents", tags=["Agents Testing"])


class TestMessageRequest(BaseModel):
    message: str


class TestMessageResponse(BaseModel):
    success: bool
    response: str
    intent: str
    agent: str
    error: Optional[str] = None


@router.post("/test", response_model=TestMessageResponse)
async def test_agent(request: TestMessageRequest):
    """
    Test agent directly without WhatsApp/Evolution API

    This endpoint allows testing the agents in isolation for development purposes.
    """
    try:
        # Create mock context for testing
        context = AgentContext(
            tenant_id="test-tenant",
            customer_id="test-customer",
            session_id="test-session",
            customer_name="Test User",
            customer_phone="5534999999999",
            conversation_history=[],
            business_context={}
        )

        # Initialize master agent
        master_agent = MasterAgent()

        # Process message
        response = await master_agent.process(
            message={"type": "text", "content": request.message},
            context=context,
            db=None  # No database for testing
        )

        return TestMessageResponse(
            success=True,
            response=response.get("content", ""),
            intent=response.get("intent", "unknown"),
            agent=response.get("agent", "unknown")
        )

    except Exception as e:
        logger.error(f"Error testing agent: {str(e)}")
        return TestMessageResponse(
            success=False,
            response="",
            intent="error",
            agent="none",
            error=str(e)
        )
