"""
MessageExtractor - Extrai informações estruturadas usando modelo fine-tuned

Responsável por extrair:
- Produto (nome, quantidade, confidence)
- Endereço (rua, número, bairro, complemento, referência, confidence)
- Pagamento (método, troco, confidence)
- Metadados (urgência, tom do cliente)
"""
import logging
from typing import Dict, Any, Optional
from openai import AsyncOpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)


class MessageExtractor:
    """
    Extrai informações estruturadas de mensagens usando modelo fine-tuned

    Usa function calling para extrair dados de forma estruturada:
    - product: informações sobre o produto solicitado
    - address: endereço de entrega
    - payment: método de pagamento e troco
    - metadata: informações auxiliares (urgência, tom)
    """

    def __init__(self):
        """Inicializa o extractor com o modelo fine-tuned"""
        self.model = settings.FINETUNED_EXTRACTOR_MODEL
        self.client = AsyncOpenAI()
        self.function_schema = self._build_function_schema()

    def _build_function_schema(self) -> Dict[str, Any]:
        """
        Constrói o schema para function calling

        Define a estrutura esperada do JSON de resposta
        com todos os campos necessários para extrair informações
        """
        return {
            "type": "function",
            "function": {
                "name": "extract_order_info",
                "description": "Extrai informações estruturadas de mensagem de pedido de gás",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "product": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "description": "Nome do produto: Botijão P5, Botijão P8, Botijão P13, Botijão P20, Botijão P45, Galão 20L"
                                },
                                "quantity": {
                                    "type": "integer",
                                    "description": "Quantidade solicitada (1-10)"
                                },
                                "confidence": {
                                    "type": "number",
                                    "description": "Confiança da extração (0.0-1.0)"
                                }
                            },
                            "required": ["name", "quantity", "confidence"]
                        },
                        "address": {
                            "type": "object",
                            "properties": {
                                "street": {
                                    "type": "string",
                                    "description": "Nome da rua/avenida"
                                },
                                "number": {
                                    "type": "string",
                                    "description": "Número do imóvel"
                                },
                                "neighborhood": {
                                    "type": "string",
                                    "description": "Bairro"
                                },
                                "complement": {
                                    "type": "string",
                                    "description": "Complemento (apto, bloco, casa, etc)"
                                },
                                "reference": {
                                    "type": "string",
                                    "description": "Ponto de referência"
                                },
                                "confidence": {
                                    "type": "number",
                                    "description": "Confiança da extração (0.0-1.0)"
                                }
                            },
                            "required": ["confidence"]
                        },
                        "payment": {
                            "type": "object",
                            "properties": {
                                "method": {
                                    "type": "string",
                                    "enum": ["pix", "dinheiro", "cartao", "unknown"],
                                    "description": "Método de pagamento"
                                },
                                "change_for": {
                                    "type": "number",
                                    "description": "Valor para troco (se pagamento em dinheiro)"
                                },
                                "confidence": {
                                    "type": "number",
                                    "description": "Confiança da extração (0.0-1.0)"
                                }
                            },
                            "required": ["method", "confidence"]
                        },
                        "metadata": {
                            "type": "object",
                            "properties": {
                                "is_urgent": {
                                    "type": "boolean",
                                    "description": "Cliente indicou urgência"
                                },
                                "has_complement": {
                                    "type": "boolean",
                                    "description": "Endereço tem complemento"
                                },
                                "has_change_request": {
                                    "type": "boolean",
                                    "description": "Cliente pediu troco"
                                },
                                "customer_tone": {
                                    "type": "string",
                                    "enum": ["polite", "neutral", "urgent", "informal"],
                                    "description": "Tom da mensagem do cliente"
                                }
                            },
                            "required": ["is_urgent", "has_complement", "has_change_request", "customer_tone"]
                        }
                    },
                    "required": ["product", "address", "payment", "metadata"]
                }
            }
        }

    async def extract(self, message: str) -> Dict[str, Any]:
        """
        Extrai informações estruturadas da mensagem usando function calling

        Args:
            message: Mensagem do cliente

        Returns:
            Dict com estrutura:
            {
                "product": {"name": str, "quantity": int, "confidence": float},
                "address": {"street": str, "number": str, "neighborhood": str, ...},
                "payment": {"method": str, "change_for": float, "confidence": float},
                "metadata": {"is_urgent": bool, "customer_tone": str, ...}
            }

        Raises:
            Exception: Se houver erro na chamada da API
        """
        try:
            # Chamar API com function calling
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Você é um assistente especializado em extrair informações estruturadas de mensagens de pedidos de gás. Analise a mensagem e extraia todas as informações possíveis."
                    },
                    {
                        "role": "user",
                        "content": message
                    }
                ],
                tools=[self.function_schema],
                tool_choice={"type": "function", "function": {"name": "extract_order_info"}}
            )

            # Extrair function call da resposta
            tool_call = response.choices[0].message.tool_calls[0]
            import json
            extracted_data = json.loads(tool_call.function.arguments)

            # Normalizar dados (garantir campos obrigatórios)
            normalized_data = self._normalize_extracted_data(extracted_data)

            # Log para debug
            logger.info(f"MessageExtractor - Extracted from '{message[:50]}...': {normalized_data}")

            return normalized_data

        except Exception as e:
            logger.error(f"Error in MessageExtractor.extract: {e}")
            # Retornar estrutura vazia em caso de erro
            return self._get_empty_structure()

    def _normalize_extracted_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normaliza dados extraídos, garantindo todos os campos obrigatórios

        Args:
            data: Dados extraídos do function calling

        Returns:
            Dados normalizados com estrutura completa
        """
        normalized = {
            "product": {
                "name": data.get("product", {}).get("name", ""),
                "quantity": data.get("product", {}).get("quantity", 1),
                "confidence": data.get("product", {}).get("confidence", 0.0)
            },
            "address": {
                "street": data.get("address", {}).get("street"),
                "number": data.get("address", {}).get("number"),
                "neighborhood": data.get("address", {}).get("neighborhood"),
                "complement": data.get("address", {}).get("complement"),
                "reference": data.get("address", {}).get("reference"),
                "confidence": data.get("address", {}).get("confidence", 0.0)
            },
            "payment": {
                "method": data.get("payment", {}).get("method", "unknown"),
                "change_for": data.get("payment", {}).get("change_for"),
                "confidence": data.get("payment", {}).get("confidence", 0.0)
            },
            "metadata": {
                "is_urgent": data.get("metadata", {}).get("is_urgent", False),
                "has_complement": data.get("metadata", {}).get("has_complement", False),
                "has_change_request": data.get("metadata", {}).get("has_change_request", False),
                "customer_tone": data.get("metadata", {}).get("customer_tone", "neutral")
            }
        }

        return normalized

    def _get_empty_structure(self) -> Dict[str, Any]:
        """
        Retorna estrutura vazia para casos de erro

        Returns:
            Estrutura com todos os campos mas valores vazios/padrão
        """
        return {
            "product": {
                "name": "",
                "quantity": 1,
                "confidence": 0.0
            },
            "address": {
                "street": None,
                "number": None,
                "neighborhood": None,
                "complement": None,
                "reference": None,
                "confidence": 0.0
            },
            "payment": {
                "method": "unknown",
                "change_for": None,
                "confidence": 0.0
            },
            "metadata": {
                "is_urgent": False,
                "has_complement": False,
                "has_change_request": False,
                "customer_tone": "neutral"
            }
        }
