"""
Audio processing service using OpenAI Whisper
"""
import base64
import tempfile
import logging
from typing import Dict, Any, Optional
from pathlib import Path
import aiohttp
import asyncio

from openai import AsyncOpenAI
from pydub import AudioSegment

from app.core.config import settings

logger = logging.getLogger(__name__)


class AudioProcessor:
    """Process WhatsApp audio messages using Whisper"""

    MAX_AUDIO_DURATION_SECONDS = 60
    MAX_AUDIO_SIZE_MB = 10

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def process_whatsapp_audio(self, audio_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process audio from WhatsApp/Evolution API

        Args:
            audio_data: {
                "base64": str (optional),
                "url": str (optional),
                "mimetype": str,
                "duration": int (seconds)
            }

        Returns:
            {
                "text": str,
                "type": "audio",
                "duration": int,
                "success": bool,
                "error": str (optional)
            }
        """
        try:
            # Validate duration
            duration = audio_data.get("duration", 0)
            if duration > self.MAX_AUDIO_DURATION_SECONDS:
                return {
                    "text": f"Desculpe, áudio muito longo ({duration}s). Envie áudios de até {self.MAX_AUDIO_DURATION_SECONDS} segundos.",
                    "type": "audio",
                    "success": False,
                    "error": "duration_exceeded"
                }

            # Get audio bytes
            audio_bytes = await self._get_audio_bytes(audio_data)

            if not audio_bytes:
                return {
                    "text": "Desculpe, não consegui processar o áudio. Pode tentar novamente?",
                    "type": "audio",
                    "success": False,
                    "error": "no_audio_data"
                }

            # Check size
            size_mb = len(audio_bytes) / (1024 * 1024)
            if size_mb > self.MAX_AUDIO_SIZE_MB:
                return {
                    "text": f"Desculpe, áudio muito grande ({size_mb:.1f}MB). Tamanho máximo: {self.MAX_AUDIO_SIZE_MB}MB.",
                    "type": "audio",
                    "success": False,
                    "error": "size_exceeded"
                }

            # Prepare audio file
            audio_file_path = await self._prepare_audio_file(audio_bytes, audio_data.get("mimetype"))

            # Transcribe
            transcription = await self._transcribe(audio_file_path)

            # Cleanup
            self._cleanup_file(audio_file_path)

            return {
                "text": transcription,
                "type": "audio",
                "duration": duration,
                "success": True,
                "original_format": audio_data.get("mimetype", "unknown")
            }

        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            return {
                "text": "Desculpe, tive um problema ao ouvir o áudio. Pode escrever sua mensagem ou tentar o áudio novamente?",
                "type": "audio",
                "success": False,
                "error": str(e)
            }

    async def _get_audio_bytes(self, audio_data: Dict[str, Any]) -> Optional[bytes]:
        """Get audio bytes from base64 or URL"""

        # Try base64 first
        if audio_data.get("base64"):
            try:
                return base64.b64decode(audio_data["base64"])
            except Exception as e:
                logger.error(f"Error decoding base64 audio: {e}")

        # Try URL
        if audio_data.get("url"):
            try:
                return await self._download_audio(audio_data["url"])
            except Exception as e:
                logger.error(f"Error downloading audio: {e}")

        return None

    async def _download_audio(self, url: str) -> bytes:
        """Download audio from URL"""
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    return await response.read()
                else:
                    raise Exception(f"Failed to download audio: HTTP {response.status}")

    async def _prepare_audio_file(self, audio_bytes: bytes, mimetype: Optional[str]) -> str:
        """
        Prepare audio file for Whisper
        WhatsApp sends OGG/OPUS, may need conversion
        """
        # Create temp file
        temp_dir = Path(tempfile.gettempdir())
        temp_file = temp_dir / f"audio_{asyncio.current_task().get_name()}.ogg"

        # Write original audio
        with open(temp_file, "wb") as f:
            f.write(audio_bytes)

        # Check if conversion needed
        if mimetype and "ogg" in mimetype.lower():
            # WhatsApp OGG format - convert to MP3 for better compatibility
            try:
                output_file = temp_dir / f"audio_{asyncio.current_task().get_name()}.mp3"
                audio = AudioSegment.from_ogg(str(temp_file))
                audio.export(str(output_file), format="mp3")

                # Cleanup original
                temp_file.unlink()

                return str(output_file)
            except Exception as e:
                logger.warning(f"Audio conversion failed, using original: {e}")
                return str(temp_file)

        return str(temp_file)

    async def _transcribe(self, audio_file_path: str) -> str:
        """
        Transcribe audio using OpenAI Whisper API
        """
        try:
            with open(audio_file_path, "rb") as audio_file:
                response = await self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="pt",
                    prompt="Transcreva o pedido do cliente para distribuidora de gás e água. Contexto: atendimento comercial."
                )

            transcription = response.text.strip()

            if not transcription:
                return "[Áudio vazio ou inaudível. Pode repetir?]"

            logger.info(f"Audio transcribed successfully: {transcription[:50]}...")

            return transcription

        except Exception as e:
            logger.error(f"Whisper transcription error: {e}")
            raise Exception("Transcription failed")

    def _cleanup_file(self, file_path: str):
        """Delete temporary file"""
        try:
            Path(file_path).unlink(missing_ok=True)
        except Exception as e:
            logger.warning(f"Failed to cleanup audio file {file_path}: {e}")

    async def text_to_speech(self, text: str, voice: str = "alloy") -> bytes:
        """
        Convert text to speech (optional feature)
        Can be used to send voice responses
        """
        try:
            response = await self.client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text[:4096]  # Max length
            )

            return response.content

        except Exception as e:
            logger.error(f"TTS error: {e}")
            raise Exception("Text-to-speech failed")
