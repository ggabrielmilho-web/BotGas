"""
Audio processing service using OpenAI Whisper
"""
import logging
import tempfile
import base64
from typing import Dict, Any, Optional
from pathlib import Path
import httpx
from openai import AsyncOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)


class AudioProcessor:
    """Process audio messages using OpenAI Whisper"""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.max_audio_size = 25 * 1024 * 1024  # 25MB (Whisper limit)

    async def download_audio(self, audio_url: str) -> bytes:
        """
        Download audio from URL

        Args:
            audio_url: URL of audio file

        Returns:
            Audio file bytes

        Raises:
            Exception: If download fails
        """
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(audio_url)
                response.raise_for_status()

                audio_data = response.content

                if len(audio_data) > self.max_audio_size:
                    raise ValueError(f"Audio file too large: {len(audio_data)} bytes")

                return audio_data

        except Exception as e:
            logger.error(f"Failed to download audio: {str(e)}")
            raise

    async def transcribe_audio(
        self,
        audio_data: bytes,
        language: str = "pt",
        prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transcribe audio using Whisper API

        Args:
            audio_data: Audio file bytes
            language: Language code (default: pt for Portuguese)
            prompt: Optional prompt to guide transcription

        Returns:
            Transcription result with text and metadata
        """
        try:
            # Create temporary file for audio
            with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as temp_audio:
                temp_audio.write(audio_data)
                temp_audio_path = temp_audio.name

            # Default prompt for gas/water delivery context
            default_prompt = (
                "Transcreva o pedido do cliente. "
                "Contexto: distribuidora de gás e água. "
                "Pode incluir: quantidade de botijões, endereço, forma de pagamento."
            )

            transcription_prompt = prompt or default_prompt

            # Transcribe with Whisper
            with open(temp_audio_path, "rb") as audio_file:
                transcription = await self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=language,
                    prompt=transcription_prompt,
                    response_format="verbose_json"
                )

            # Clean up temp file
            Path(temp_audio_path).unlink(missing_ok=True)

            result = {
                "text": transcription.text,
                "language": transcription.language,
                "duration": transcription.duration,
                "success": True
            }

            logger.info(f"Audio transcribed successfully: {len(transcription.text)} chars")
            return result

        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            return {
                "text": "[Áudio não compreendido. Por favor, repita ou envie mensagem de texto]",
                "error": str(e),
                "success": False
            }

    async def process_whatsapp_audio(
        self,
        audio_url: str,
        language: str = "pt"
    ) -> Dict[str, Any]:
        """
        Complete pipeline: download + transcribe WhatsApp audio

        Args:
            audio_url: URL of WhatsApp audio
            language: Language code

        Returns:
            Transcription result
        """
        try:
            # Download audio
            audio_data = await self.download_audio(audio_url)

            # Transcribe
            result = await self.transcribe_audio(audio_data, language)

            return result

        except Exception as e:
            logger.error(f"Failed to process WhatsApp audio: {str(e)}")
            return {
                "text": "[Erro ao processar áudio. Tente novamente ou envie texto]",
                "error": str(e),
                "success": False
            }

    async def process_base64_audio(
        self,
        base64_audio: str,
        language: str = "pt"
    ) -> Dict[str, Any]:
        """
        Process base64 encoded audio

        Args:
            base64_audio: Base64 encoded audio data
            language: Language code

        Returns:
            Transcription result
        """
        try:
            # Decode base64
            audio_data = base64.b64decode(base64_audio)

            # Transcribe
            result = await self.transcribe_audio(audio_data, language)

            return result

        except Exception as e:
            logger.error(f"Failed to process base64 audio: {str(e)}")
            return {
                "text": "[Erro ao processar áudio. Tente novamente ou envie texto]",
                "error": str(e),
                "success": False
            }


# Singleton instance
audio_processor = AudioProcessor()
