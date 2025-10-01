"""
Evolution API v2 Integration Service
Documentação: https://doc.evolution-api.com/v2/
"""
import httpx
import logging
from typing import Optional, Dict, Any, List
from uuid import UUID
from fastapi import HTTPException, status

from app.core.config import settings

logger = logging.getLogger(__name__)


class EvolutionAPIService:
    """Service for Evolution API v2.3.1 integration"""

    def __init__(self):
        self.base_url = settings.EVOLUTION_API_URL.rstrip('/')
        self.api_key = settings.EVOLUTION_API_KEY
        self.headers = {
            "apikey": self.api_key,
            "Content-Type": "application/json"
        }

    async def _request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Evolution API

        Args:
            method: HTTP method (GET, POST, DELETE, etc)
            endpoint: API endpoint
            json_data: JSON payload
            params: Query parameters

        Returns:
            Response data

        Raises:
            HTTPException: If request fails
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    json=json_data,
                    params=params
                )

                if response.status_code >= 400:
                    logger.error(f"Evolution API error: {response.status_code} - {response.text}")
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail=f"Evolution API error: {response.text}"
                    )

                return response.json()

        except httpx.RequestError as e:
            logger.error(f"Evolution API request failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Evolution API unavailable: {str(e)}"
            )

    async def create_instance(
        self,
        instance_name: str,
        webhook_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create new WhatsApp instance

        Args:
            instance_name: Unique instance name (use tenant_id)
            webhook_url: URL to receive webhooks

        Returns:
            Instance data with QR code
        """
        webhook = webhook_url or settings.WEBHOOK_URL

        data = {
            "instanceName": instance_name,
            "integration": "WHATSAPP-BAILEYS",  # Obrigatório para Evolution API
            "token": self.api_key,
            "qrcode": True,
            "webhook": webhook,
            "webhookByEvents": True,
            "webhookEvents": [
                "QRCODE_UPDATED",
                "CONNECTION_UPDATE",
                "MESSAGES_UPSERT",
                "MESSAGES_UPDATE",
                "SEND_MESSAGE"
            ]
        }

        result = await self._request("POST", "/instance/create", json_data=data)
        logger.info(f"Instance created: {instance_name}")
        return result

    async def get_instance_status(self, instance_name: str) -> Dict[str, Any]:
        """
        Get instance connection status

        Args:
            instance_name: Instance name

        Returns:
            Status data with connection state
        """
        result = await self._request("GET", f"/instance/connectionState/{instance_name}")
        return result

    async def get_qr_code(self, instance_name: str) -> Dict[str, Any]:
        """
        Get QR code for instance connection

        Args:
            instance_name: Instance name

        Returns:
            QR code data (base64 image)
        """
        result = await self._request("GET", f"/instance/connect/{instance_name}")
        return result

    async def logout_instance(self, instance_name: str) -> Dict[str, Any]:
        """
        Logout from WhatsApp instance

        Args:
            instance_name: Instance name

        Returns:
            Logout confirmation
        """
        result = await self._request("DELETE", f"/instance/logout/{instance_name}")
        logger.info(f"Instance logged out: {instance_name}")
        return result

    async def delete_instance(self, instance_name: str) -> Dict[str, Any]:
        """
        Delete WhatsApp instance completely

        Args:
            instance_name: Instance name

        Returns:
            Delete confirmation
        """
        result = await self._request("DELETE", f"/instance/delete/{instance_name}")
        logger.info(f"Instance deleted: {instance_name}")
        return result

    async def send_text_message(
        self,
        instance_name: str,
        number: str,
        message: str
    ) -> Dict[str, Any]:
        """
        Send text message via WhatsApp

        Args:
            instance_name: Instance name
            number: Phone number with country code (e.g., 5511999999999)
            message: Text message

        Returns:
            Message send confirmation
        """
        data = {
            "number": number,
            "text": message
        }

        result = await self._request(
            "POST",
            f"/message/sendText/{instance_name}",
            json_data=data
        )
        logger.info(f"Text message sent to {number}")
        return result

    async def send_audio_message(
        self,
        instance_name: str,
        number: str,
        audio_url: str
    ) -> Dict[str, Any]:
        """
        Send audio message via WhatsApp

        Args:
            instance_name: Instance name
            number: Phone number with country code
            audio_url: URL of audio file

        Returns:
            Message send confirmation
        """
        data = {
            "number": number,
            "audioMessage": {
                "audio": audio_url
            }
        }

        result = await self._request(
            "POST",
            f"/message/sendWhatsAppAudio/{instance_name}",
            json_data=data
        )
        logger.info(f"Audio message sent to {number}")
        return result

    async def send_media_message(
        self,
        instance_name: str,
        number: str,
        media_url: str,
        caption: Optional[str] = None,
        media_type: str = "image"
    ) -> Dict[str, Any]:
        """
        Send media message (image, video, document)

        Args:
            instance_name: Instance name
            number: Phone number
            media_url: URL of media file
            caption: Optional caption
            media_type: Type of media (image, video, document)

        Returns:
            Message send confirmation
        """
        data = {
            "number": number,
            "mediaMessage": {
                "mediatype": media_type,
                "media": media_url
            }
        }

        if caption:
            data["mediaMessage"]["caption"] = caption

        result = await self._request(
            "POST",
            f"/message/sendMedia/{instance_name}",
            json_data=data
        )
        logger.info(f"Media message sent to {number}")
        return result

    async def download_media(
        self,
        instance_name: str,
        message_id: str
    ) -> bytes:
        """
        Download media from message

        Args:
            instance_name: Instance name
            message_id: WhatsApp message ID

        Returns:
            Media file bytes
        """
        url = f"{self.base_url}/message/download/{instance_name}/{message_id}"

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(url, headers=self.headers)

            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Failed to download media"
                )

            return response.content

    async def set_presence(
        self,
        instance_name: str,
        number: str,
        presence: str = "available"
    ) -> Dict[str, Any]:
        """
        Set presence (online, typing, recording)

        Args:
            instance_name: Instance name
            number: Phone number
            presence: Presence type (available, unavailable, composing, recording)

        Returns:
            Presence confirmation
        """
        data = {
            "number": number,
            "presence": presence
        }

        result = await self._request(
            "POST",
            f"/chat/presence/{instance_name}",
            json_data=data
        )
        return result

    async def mark_message_read(
        self,
        instance_name: str,
        message_key: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Mark message as read

        Args:
            instance_name: Instance name
            message_key: Message key object

        Returns:
            Read confirmation
        """
        data = {
            "readMessages": [message_key]
        }

        result = await self._request(
            "POST",
            f"/chat/markMessageRead/{instance_name}",
            json_data=data
        )
        return result

    async def get_profile_picture(
        self,
        instance_name: str,
        number: str
    ) -> Dict[str, Any]:
        """
        Get profile picture URL

        Args:
            instance_name: Instance name
            number: Phone number

        Returns:
            Profile picture URL
        """
        result = await self._request(
            "GET",
            f"/chat/fetchProfilePictureUrl/{instance_name}",
            params={"number": number}
        )
        return result


# Singleton instance
evolution_service = EvolutionAPIService()
