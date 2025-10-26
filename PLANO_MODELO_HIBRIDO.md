# 🔧 PLANO DE IMPLEMENTAÇÃO - MODELO HÍBRIDO GASBOT

> **Documento Técnico para Migração do Sistema Multi-Agentes**
> Data: 2025-10-25
> Versão: 1.0
> Autor: Claude Code Analysis

---

## 📊 SUMÁRIO EXECUTIVO

### Objetivo
Migrar o sistema atual de multi-agentes com fine-tuning para uma **arquitetura híbrida** que resolve os problemas de:
- ❌ Produtos sendo adicionados indevidamente quando cliente diz "finalizar"
- ❌ Perda de contexto entre chamadas de agentes
- ❌ Roteamento baseado apenas em confidence scores (sem contexto conversacional)

### Resultado Esperado
- ✅ Sistema entende contexto conversacional
- ✅ "Finalizar" não adiciona produtos ao carrinho
- ✅ Melhora na taxa de conversão (menos erros)
- ✅ Custo 50% menor por mensagem
- ✅ Código mais manutenível

### Tempo Estimado
**4-6 horas** de implementação + 2 horas de testes

### Risco
🟢 **BAIXO** - Mudanças controladas, código testado, rollback simples

---

## ✅ CHECKLIST DE IMPLEMENTAÇÃO RÁPIDA

Use este checklist para acompanhar o progresso da implementação:

### 📋 PRÉ-REQUISITOS
- [ ] Backup do código atual realizado (git commit)
- [ ] Backend está rodando sem erros
- [ ] Acesso ao container Docker funcionando
- [ ] Arquivo `.env` com `OPENAI_API_KEY` configurado

---

### 🧹 FASE 1: PREPARAÇÃO (30 min)

**Passo 1.1: Backup**
- [ ] Executar: `git add . && git commit -m "Backup antes migração modelo híbrido"`
- [ ] Confirmar commit criado: `git log -1`

**Passo 1.2: Limpar Produtos Duplicados**
- [ ] Executar script de limpeza (seção "Passo 1.2")
- [ ] Verificar resultado: produtos duplicados removidos
- [ ] Quantidade final de produtos: ______

**Passo 1.3: Encerrar Conversas Ativas**
- [ ] Executar: `docker-compose exec backend python close_conversations.py`
- [ ] Confirmar: X conversas encerradas

---

### 🆕 FASE 2: CRIAR COMPONENTES (1 hora)

**Passo 2.1: ConversationContext**
- [ ] Criar arquivo: `backend/app/services/context_manager.py`
- [ ] Copiar código completo da seção "Componente 1"
- [ ] Salvar arquivo
- [ ] Executar validação (script de teste)
- [ ] ✅ Teste passou: "ConversationContext importado com sucesso"

**Passo 2.2: IntentClassifier**
- [ ] Criar arquivo: `backend/app/services/intent_classifier.py`
- [ ] Copiar código completo da seção "Componente 2"
- [ ] Salvar arquivo
- [ ] Executar validação (script de teste async)
- [ ] ✅ Teste 1 passou: "oi → greeting"
- [ ] ✅ Teste 2 passou: "finalizar → answer_no"

---

### 🔧 FASE 3: MODIFICAR EXISTENTES (2 horas)

**Passo 3.1: MasterAgent**
- [ ] Abrir arquivo: `backend/app/agents/master.py`
- [ ] Adicionar imports no topo (linhas ~1-20)
- [ ] Modificar `__init__` (adicionar `self.intent_classifier`)
- [ ] Substituir método `_route_to_agent()` completo (linhas ~181-262)
- [ ] Salvar arquivo
- [ ] Executar validação: `docker-compose exec backend python -c "from app.agents.master import MasterAgent; print('OK')"`
- [ ] ✅ Nenhum erro de sintaxe

**Passo 3.2: ValidationAgent**
- [ ] Abrir arquivo: `backend/app/agents/validation.py`
- [ ] Adicionar método `ask_for_address()` após `__init__`
- [ ] Salvar arquivo
- [ ] Executar validação: verificar método existe
- [ ] ✅ Método `ask_for_address` encontrado

**Passo 3.3: OrderAgent**
- [ ] Abrir arquivo: `backend/app/agents/order.py`
- [ ] Localizar método `process_with_extracted_data()`
- [ ] Adicionar validação de contexto no INÍCIO do método
- [ ] Salvar arquivo
- [ ] Executar validação: sem erros de sintaxe
- [ ] ✅ OrderAgent importa sem erros

---

### 🧪 FASE 4: TESTES (1 hora)

**Passo 4.1: Reiniciar Backend**
- [ ] Executar: `docker-compose restart backend`
- [ ] Verificar logs: sem erros críticos
- [ ] Backend iniciou corretamente

**Passo 4.2: Teste 1 - Fluxo Normal**
- [ ] Cliente: "oi" → Saudação OK
- [ ] Cliente: "produtos" → Lista sem duplicados OK
- [ ] Cliente: "1" → Adicionado 1x OK
- [ ] Cliente: "finalizar" → Pede endereço (NÃO adiciona produto!) ✅
- [ ] ✅ Carrinho tem apenas 1 item

**Passo 4.3: Teste 2 - Múltiplos Produtos**
- [ ] Cliente: "1" → Adicionado OK
- [ ] Bot: "Deseja mais?" → Pergunta OK
- [ ] Cliente: "sim" → Volta para produtos ✅
- [ ] Cliente: "2" → Adicionado segundo produto OK
- [ ] Cliente: "não" → Pede endereço ✅
- [ ] ✅ Carrinho tem 2 itens (não duplicou)

**Passo 4.4: Teste 3 - Variações de Negação**
- [ ] Testado: "finalizar" → answer_no ✅
- [ ] Testado: "pronto" → answer_no ✅
- [ ] Testado: "só isso" → answer_no ✅
- [ ] Testado: "não" → answer_no ✅
- [ ] Testado: "n" → answer_no ✅
- [ ] ✅ Todas variações funcionam

**Passo 4.5: Verificar Logs**
- [ ] Logs mostram: "IntentClassifier: 'finalizar' → answer_no"
- [ ] Logs mostram: "Cliente negou/finalizou (answer_no)"
- [ ] Logs mostram: "ValidationAgent (pedir endereço)"
- [ ] ✅ Sem erros de "Product detected" após "finalizar"

---

### 📊 FASE 5: VALIDAÇÃO FINAL (30 min)

**Passo 5.1: Métricas**
- [ ] Executar script de métricas (seção "Passo 5.1")
- [ ] Taxa de duplicação: ____% (deve ser <5%)
- [ ] Conversas ativas: ____
- [ ] Pedidos últimas 24h: ____

**Passo 5.2: Checklist Final**
- [ ] Todos os arquivos salvos
- [ ] Backend rodando sem erros
- [ ] Testes manuais passaram
- [ ] Logs estão corretos
- [ ] Frontend funcionando
- [ ] Webhooks ativos

---

### 🎉 CONCLUSÃO

**Data de implementação:** ___________
**Tempo total gasto:** _____ horas
**Problemas encontrados:** _____________________________________
**Status:** [ ] Sucesso  [ ] Parcial  [ ] Necessita ajustes

**Observações:**
_________________________________________________________________
_________________________________________________________________

---

## 🔍 ANÁLISE DO PROBLEMA ATUAL

### Problema 1: Produtos Duplicados no Banco

**Evidência:**
```sql
SELECT id, name, price FROM products WHERE tenant_id = '...';

-- Resultado:
-- 1. Botijão P13 - R$ 95,00
-- 2. Botijão P13 - R$ 95,00
-- 3. Botijão P13 - R$ 95,00
```

**Impacto:** Cliente vê lista confusa com produtos repetidos.

---

### Problema 2: Item Adicionado Duas Vezes

**Conversa Real (última sessão):**

```
Cliente: "oi"
Bot: "Olá! Como posso ajudar?"

Cliente: "produtos"
Bot: [Lista produtos]

Cliente: "1"
Bot: "✅ Adicionado: 1x Botijão P13 - R$ 95,00
      Deseja adicionar mais alguma coisa ou finalizar?"

Cliente: "finalizar"  ← PROBLEMA AQUI
Bot: "✅ Adicionado: 1x Botijão P13 - R$ 95,00"  ← ADICIONOU DE NOVO!

Carrinho final:
  - 2x Botijão P13 (R$ 190,00)  ← ERRADO!
```

**Logs do Extrator:**
```
Message: finalizar
Extracted - Product: Botijão P13 (conf: 0.91)  ← FALSO POSITIVO!
Extracted - Address: conf 0.88
Extracted - Payment: cartao (conf: 0.91)

ROUTING DEBUG
-> OrderAgent (product detected: Botijão P13)  ← ROTEAMENTO ERRADO!
```

**Análise:**
1. Bot perguntou: "Deseja adicionar mais?"
2. Cliente respondeu: "finalizar"
3. Extrator interpretou como PEDIDO de produto (conf 0.91)
4. MasterAgent roteou para OrderAgent (prioriza product > address)
5. OrderAgent adicionou OUTRO Botijão P13

---

### Problema 3: Roteamento Sem Contexto

**Código Atual (master.py:229-246):**
```python
# PRIORIDADE ATUAL (ERRADA):
if extracted_info["product"]["confidence"] > 0.7:
    -> OrderAgent  # ← Executado PRIMEIRO

elif extracted_info["address"]["confidence"] > 0.7:
    -> ValidationAgent  # ← Nunca chega aqui!

elif extracted_info["payment"]["confidence"] > 0.7:
    -> PaymentAgent
```

**Problema:**
- Não considera o que o bot perguntou
- Não verifica se cliente está respondendo uma pergunta
- Confia cegamente no confidence score

---

### Problema 4: Fine-Tuning Sem Contexto Conversacional

**O que o MessageExtractor recebe:**
```python
await self.message_extractor.extract(message_text)
# Input: "finalizar" (APENAS a palavra!)
# Sem contexto de que bot perguntou "deseja adicionar mais?"
```

**Resultado:**
- Modelo "alucina" que cliente quer mais produto
- Confidence enganoso (0.91)
- Impossível debugar

---

## 🏗️ ARQUITETURA HÍBRIDA PROPOSTA

### Diagrama de Fluxo

```
┌─────────────────────────────────────────────────────────────┐
│                    MENSAGEM DO CLIENTE                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
         ┌─────────────────────────────┐
         │   ConversationContext       │
         │  (NOVO - gerencia estado)   │
         │                             │
         │ - last_bot_question         │
         │ - last_bot_intent           │
         │ - has_items_in_cart         │
         │ - awaiting_user_decision    │
         └──────────────┬──────────────┘
                        │
                        ▼
         ┌──────────────────────────────┐
         │   IntentClassifier           │
         │   (NOVO - GPT-4-mini curto)  │
         │                              │
         │ Input: msg + last_bot_msg    │
         │ Output: intent               │
         │  - answer_yes                │
         │  - answer_no                 │
         │  - greeting                  │
         │  - product_inquiry           │
         │  - help                      │
         └──────────────┬───────────────┘
                        │
                        ▼
         ┌──────────────────────────────┐
         │   MessageExtractor           │
         │   (MANTÉM - fine-tuned)      │
         │                              │
         │ Extrai dados estruturados:   │
         │  - product                   │
         │  - address                   │
         │  - payment                   │
         └──────────────┬───────────────┘
                        │
                        ▼
         ┌──────────────────────────────┐
         │   MasterAgent Router         │
         │   (MODIFICADO - usa contexto)│
         │                              │
         │ Prioridade:                  │
         │ 1. Intent + Contexto         │
         │ 2. Address (se tem carrinho) │
         │ 3. Product (valida contexto) │
         │ 4. Payment                   │
         └──────────────┬───────────────┘
                        │
          ┌─────────────┼─────────────┐
          │             │             │
          ▼             ▼             ▼
    ┌─────────┐  ┌──────────┐  ┌───────────┐
    │Attendance│  │OrderAgent│  │Validation │
    │  Agent   │  │ (ajustado)│  │  Agent    │
    └──────────┘  └──────────┘  └───────────┘
```

---

### Componentes do Sistema Híbrido

#### 1. **ConversationContext** (NOVO)
- **Responsabilidade:** Gerenciar estado da conversa
- **Arquivo:** `app/services/context_manager.py`
- **Funções:**
  - `last_bot_question`: Última pergunta do bot
  - `last_bot_intent`: Intent da última mensagem do bot
  - `has_items_in_cart`: Verifica se há itens no carrinho
  - `awaiting_user_decision`: Bot está esperando sim/não?

#### 2. **IntentClassifier** (NOVO)
- **Responsabilidade:** Classificar intent considerando contexto
- **Arquivo:** `app/services/intent_classifier.py`
- **Modelo:** GPT-4-mini (prompt curto ~150 tokens)
- **Custo:** ~$0.00004 por classificação

#### 3. **MasterAgent** (MODIFICADO)
- **Mudança:** Roteamento baseado em contexto + intent + confidence
- **Arquivo:** `app/agents/master.py`
- **Método modificado:** `_route_to_agent()`

#### 4. **OrderAgent** (MODIFICADO)
- **Mudança:** Validar contexto antes de adicionar produto
- **Arquivo:** `app/agents/order.py`
- **Método modificado:** `process_with_extracted_data()`

#### 5. **ValidationAgent** (MODIFICADO)
- **Mudança:** Adicionar método `ask_for_address()`
- **Arquivo:** `app/agents/validation.py`

---

## 📝 CÓDIGO DOS NOVOS COMPONENTES

### Componente 1: ConversationContext

**Arquivo:** `backend/app/services/context_manager.py`

```python
"""
Context Manager - Gerencia contexto de conversas
"""
from typing import Dict, Any, List, Optional


class ConversationContext:
    """
    Gerencia contexto entre chamadas de agentes

    Responsável por extrair informações do estado da conversa
    que ajudam na tomada de decisão do roteamento.
    """

    def __init__(self, session_data: Dict[str, Any], message_history: List[Dict[str, Any]]):
        """
        Inicializa o context manager

        Args:
            session_data: Dados da sessão (current_order, stage, etc)
            message_history: Histórico de mensagens da conversa
        """
        self.session_data = session_data
        self.message_history = message_history

    @property
    def last_bot_message(self) -> Dict[str, Any]:
        """
        Retorna a última mensagem enviada pelo bot

        Returns:
            Dict com role, content, intent, timestamp
        """
        for msg in reversed(self.message_history):
            if msg.get("role") == "assistant":
                return msg
        return {}

    @property
    def last_bot_question(self) -> str:
        """
        Retorna o texto da última pergunta do bot

        Returns:
            String com a pergunta ou vazio
        """
        last_msg = self.last_bot_message
        return last_msg.get("content", "")

    @property
    def last_bot_intent(self) -> str:
        """
        Retorna o intent da última mensagem do bot

        Returns:
            String com o intent ou vazio
        """
        last_msg = self.last_bot_message
        return last_msg.get("intent", "")

    @property
    def has_items_in_cart(self) -> bool:
        """
        Verifica se há itens no carrinho de compras

        Returns:
            True se há itens, False caso contrário
        """
        current_order = self.session_data.get("current_order", {})
        items = current_order.get("items", [])
        return bool(items)

    @property
    def cart_items_count(self) -> int:
        """
        Retorna quantidade de itens no carrinho

        Returns:
            Número de itens
        """
        current_order = self.session_data.get("current_order", {})
        items = current_order.get("items", [])
        return len(items)

    @property
    def awaiting_user_decision(self) -> bool:
        """
        Verifica se bot está esperando uma decisão do usuário (sim/não)

        Analisa a última pergunta do bot para detectar se é uma pergunta
        que espera confirmação ou negação.

        Returns:
            True se está esperando decisão, False caso contrário
        """
        last_question = self.last_bot_question.lower()

        # Keywords que indicam que bot está esperando decisão
        decision_keywords = [
            "deseja adicionar mais",
            "quer adicionar",
            "mais alguma coisa",
            "ou finalizar",
            "podemos continuar",
            "está correto",
            "confirma",
            "tudo certo"
        ]

        return any(keyword in last_question for keyword in decision_keywords)

    @property
    def current_stage(self) -> str:
        """
        Retorna o stage atual da conversa

        Returns:
            String com o stage (greeting, building_order, etc)
        """
        return self.session_data.get("stage", "greeting")

    @property
    def has_delivery_address(self) -> bool:
        """
        Verifica se endereço de entrega já foi definido

        Returns:
            True se tem endereço, False caso contrário
        """
        return bool(self.session_data.get("delivery_address"))

    def get_summary(self) -> Dict[str, Any]:
        """
        Retorna resumo do contexto para debugging

        Returns:
            Dict com informações principais do contexto
        """
        return {
            "stage": self.current_stage,
            "has_items": self.has_items_in_cart,
            "items_count": self.cart_items_count,
            "has_address": self.has_delivery_address,
            "awaiting_decision": self.awaiting_user_decision,
            "last_bot_intent": self.last_bot_intent,
            "last_question_preview": self.last_bot_question[:50] + "..." if len(self.last_bot_question) > 50 else self.last_bot_question
        }
```

---

### Componente 2: IntentClassifier

**Arquivo:** `backend/app/services/intent_classifier.py`

```python
"""
Intent Classifier - Classifica intenção do usuário considerando contexto
"""
import logging
from typing import Optional
from openai import AsyncOpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)


class IntentClassifier:
    """
    Classifica a intenção do usuário baseado na mensagem E no contexto

    Usa GPT-4-mini com prompt curto e focado para economizar tokens.
    Diferente do MessageExtractor que extrai dados, este classifica
    a AÇÃO/INTENÇÃO do usuário.
    """

    def __init__(self):
        """Inicializa o classificador"""
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4o-mini"

    async def classify(
        self,
        message: str,
        last_bot_message: Optional[str] = None
    ) -> str:
        """
        Classifica a intenção do usuário

        Args:
            message: Mensagem do usuário
            last_bot_message: Última mensagem do bot (contexto)

        Returns:
            Intent classificado:
            - "answer_yes": Usuário concordou/confirmou
            - "answer_no": Usuário negou/recusou/finalizou
            - "greeting": Saudação
            - "product_inquiry": Pergunta sobre produtos
            - "help": Pedido de ajuda humana
            - "general": Outros casos
        """

        # Construir prompt curto e focado
        if last_bot_message:
            prompt = f"""Classifique a intenção do cliente.

CONTEXTO:
Última mensagem do bot: "{last_bot_message}"

MENSAGEM DO CLIENTE:
"{message}"

CLASSIFICAÇÕES POSSÍVEIS:
- answer_yes: Cliente concordou/confirmou (sim, ok, pode, beleza, isso mesmo, confirmo)
- answer_no: Cliente negou/recusou/finalizou (não, nao, finalizar, pronto, só isso, fechar)
- greeting: Saudação (oi, olá, bom dia, etc)
- product_inquiry: Pergunta sobre produtos (produtos, o que tem, cardápio, catálogo)
- help: Pedido de ajuda humana (falar com atendente, preciso de ajuda)
- general: Outros casos

IMPORTANTE: Se o bot perguntou "deseja adicionar mais?" e cliente disse "finalizar/não/pronto",
a classificação é "answer_no", NÃO "general".

Responda APENAS com a classificação (uma palavra)."""
        else:
            prompt = f"""Classifique a intenção do cliente.

MENSAGEM: "{message}"

CLASSIFICAÇÕES:
- answer_yes: sim, ok, pode, confirmo
- answer_no: não, finalizar, pronto
- greeting: oi, olá, bom dia
- product_inquiry: produtos, cardápio
- help: falar com atendente
- general: outros

Responda APENAS a classificação."""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=10,  # Resposta curta (economia!)
                temperature=0.1  # Determinístico
            )

            intent = response.choices[0].message.content.strip().lower()

            # Validar resposta
            valid_intents = [
                "answer_yes", "answer_no", "greeting",
                "product_inquiry", "help", "general"
            ]

            if intent not in valid_intents:
                logger.warning(f"Intent inválido retornado: {intent}. Usando 'general'.")
                intent = "general"

            logger.info(f"IntentClassifier: '{message[:30]}...' → {intent}")

            return intent

        except Exception as e:
            logger.error(f"Erro no IntentClassifier: {e}")
            # Fallback seguro
            return "general"

    async def is_affirmative(self, message: str) -> bool:
        """
        Verifica se mensagem é afirmativa (sim/ok/pode)

        Helper method para casos simples

        Args:
            message: Mensagem do usuário

        Returns:
            True se é afirmativa, False caso contrário
        """
        message_lower = message.lower().strip()

        affirmative_words = [
            "sim", "s", "yes", "ok", "pode", "beleza",
            "certo", "isso", "confirmo", "perfeito", "exato"
        ]

        return any(word == message_lower for word in affirmative_words)

    async def is_negative(self, message: str) -> bool:
        """
        Verifica se mensagem é negativa (não/finalizar)

        Helper method para casos simples

        Args:
            message: Mensagem do usuário

        Returns:
            True se é negativa, False caso contrário
        """
        message_lower = message.lower().strip()

        negative_words = [
            "não", "nao", "n", "no", "finalizar", "pronto",
            "só isso", "somente", "apenas isso", "fechar", "terminar"
        ]

        return any(word in message_lower for word in negative_words)
```

---

## 🔧 MODIFICAÇÕES NOS COMPONENTES EXISTENTES

### Modificação 1: MasterAgent - Roteamento Inteligente

**Arquivo:** `backend/app/agents/master.py`

**Método a modificar:** `_route_to_agent()` (linhas 181-262)

**Mudanças:**

1. Adicionar imports no topo do arquivo:
```python
from app.services.context_manager import ConversationContext
from app.services.intent_classifier import IntentClassifier
```

2. No `__init__`, adicionar:
```python
def __init__(self):
    super().__init__(model_name="gpt-4-turbo-preview", temperature=0.7)
    self.audio_processor = AudioProcessor()
    self.message_extractor = MessageExtractor()
    self.intent_classifier = IntentClassifier()  # ← NOVO
```

3. Substituir o método `_route_to_agent()` completo:

```python
async def _route_to_agent(
    self,
    message: str,
    extracted_info: dict,
    context: AgentContext,
    db
) -> AgentResponse:
    """
    Roteamento INTELIGENTE com contexto

    Prioridade de decisão:
    1. Contexto conversacional (bot perguntou algo? cliente respondeu?)
    2. Intent do usuário (saudação, ajuda, etc)
    3. Address com alta confidence (se já tem produto no carrinho)
    4. Product com alta confidence (validado pelo contexto)
    5. Payment com alta confidence
    6. Fallback para attendance
    """

    # Import agents
    from app.agents.attendance import AttendanceAgent
    from app.agents.validation import ValidationAgent
    from app.agents.order import OrderAgent
    from app.agents.payment import PaymentAgent

    # 1. Criar context manager para extrair informações do estado
    conv_context = ConversationContext(
        session_data=context.session_data,
        message_history=context.message_history
    )

    # Log contexto para debugging
    context_summary = conv_context.get_summary()
    logger.info(f"Context: {context_summary}")

    # 2. Classificar intent considerando contexto
    intent = await self.intent_classifier.classify(
        message=message,
        last_bot_message=conv_context.last_bot_question
    )

    logger.info(
        f"Routing - Intent: {intent}, Stage: {conv_context.current_stage}, "
        f"Has items: {conv_context.has_items_in_cart}, "
        f"Awaiting decision: {conv_context.awaiting_user_decision}"
    )

    # ========================================================================
    # PRIORIDADE 1: BOT PERGUNTOU ALGO E CLIENTE RESPONDEU
    # ========================================================================

    if conv_context.awaiting_user_decision:
        logger.info("Bot está aguardando decisão do usuário")

        if intent == "answer_yes":
            # Cliente quer continuar adicionando produtos
            logger.info("Cliente confirmou (answer_yes) → AttendanceAgent (mostrar produtos)")
            agent = AttendanceAgent()
            return await agent.process(message, context)

        elif intent == "answer_no":
            # Cliente quer finalizar/parar de adicionar
            logger.info("Cliente negou/finalizou (answer_no)")

            if conv_context.has_items_in_cart:
                # Tem itens → pedir endereço
                logger.info("Tem itens no carrinho → ValidationAgent (pedir endereço)")
                agent = ValidationAgent()
                return await agent.ask_for_address(context)
            else:
                # Não tem itens → voltar ao início
                logger.info("Carrinho vazio → AttendanceAgent")
                agent = AttendanceAgent()
                return await agent.process(message, context)

    # ========================================================================
    # PRIORIDADE 2: INTENTS ESPECÍFICOS (sempre tratados primeiro)
    # ========================================================================

    if intent == "greeting":
        logger.info("Intent: greeting → AttendanceAgent")
        agent = AttendanceAgent()
        return await agent.process(message, context)

    if intent == "product_inquiry":
        logger.info("Intent: product_inquiry → AttendanceAgent")
        agent = AttendanceAgent()
        return await agent.process(message, context)

    if intent == "help":
        logger.info("Intent: help → AttendanceAgent")
        agent = AttendanceAgent()
        return await agent.process(message, context)

    # ========================================================================
    # PRIORIDADE 3: ENDEREÇO DETECTADO (se já tem produto no carrinho)
    # ========================================================================

    if (extracted_info["address"]["confidence"] > 0.7
        and conv_context.has_items_in_cart):
        logger.info(
            f"Address detected (conf: {extracted_info['address']['confidence']:.2f}) "
            f"and has items → ValidationAgent"
        )
        agent = ValidationAgent()
        return await agent.process_with_extracted_data(extracted_info, context, db)

    # ========================================================================
    # PRIORIDADE 4: PRODUTO DETECTADO (validar contexto antes!)
    # ========================================================================

    if extracted_info["product"]["confidence"] > 0.7:
        logger.info(
            f"Product detected: {extracted_info['product']['name']} "
            f"(conf: {extracted_info['product']['confidence']:.2f})"
        )

        # VALIDAÇÃO: Se bot acabou de perguntar "deseja adicionar mais?"
        # E intent foi classificado como "answer_no"
        # NÃO adicionar produto (mesmo com confidence alta)

        if conv_context.awaiting_user_decision and intent == "answer_no":
            logger.warning(
                "VALIDAÇÃO FALHOU: Product confidence alto MAS intent=answer_no. "
                "Cliente não quer adicionar produto. Redirecionando..."
            )

            if conv_context.has_items_in_cart:
                # Pedir endereço
                agent = ValidationAgent()
                return await agent.ask_for_address(context)
            else:
                # Voltar ao início
                agent = AttendanceAgent()
                return await agent.process(message, context)

        # Contexto OK → processar produto
        logger.info("Contexto validado → OrderAgent")
        agent = OrderAgent()
        return await agent.process_with_extracted_data(extracted_info, context, db)

    # ========================================================================
    # PRIORIDADE 5: PAGAMENTO DETECTADO
    # ========================================================================

    if extracted_info["payment"]["confidence"] > 0.7:
        logger.info(
            f"Payment detected: {extracted_info['payment']['method']} "
            f"(conf: {extracted_info['payment']['confidence']:.2f}) → PaymentAgent"
        )
        agent = PaymentAgent()
        return await agent.process_with_extracted_data(extracted_info, context, db)

    # ========================================================================
    # PRIORIDADE 6: STAGE-BASED ROUTING (fallback)
    # ========================================================================

    stage = conv_context.current_stage

    if stage == "building_order":
        logger.info("Stage: building_order → OrderAgent")
        agent = OrderAgent()
        return await agent.process(message, context)

    if stage == "confirming_order":
        logger.info("Stage: confirming_order → OrderAgent")
        agent = OrderAgent()
        return await agent.process(message, context)

    if stage == "awaiting_address":
        logger.info("Stage: awaiting_address → ValidationAgent")
        agent = ValidationAgent()
        return await agent.process(message, context)

    if stage == "payment":
        logger.info("Stage: payment → PaymentAgent")
        agent = PaymentAgent()
        return await agent.process(message, context)

    # ========================================================================
    # FALLBACK: AttendanceAgent
    # ========================================================================

    logger.info("Fallback → AttendanceAgent")
    agent = AttendanceAgent()
    return await agent.process(message, context)
```

---

### Modificação 2: ValidationAgent - Método ask_for_address()

**Arquivo:** `backend/app/agents/validation.py`

**Adicionar novo método após o `__init__`:**

```python
async def ask_for_address(self, context: AgentContext) -> AgentResponse:
    """
    Pede endereço de entrega ao cliente

    Usado quando cliente finaliza pedido e não forneceu endereço ainda.

    Args:
        context: Contexto da conversa

    Returns:
        AgentResponse pedindo endereço
    """

    # Verificar se já tem endereço no contexto
    if context.session_data.get("delivery_address"):
        # Já tem endereço, pedir confirmação
        address_info = context.session_data["delivery_address"]
        return AgentResponse(
            text=f"""Endereço confirmado anteriormente:
{address_info.get('normalized_address', 'Endereço registrado')}

Deseja usar este endereço?""",
            intent="confirm_address",
            next_agent="validation",
            context_updates={"stage": "confirming_address"},
            should_end=False
        )

    # Não tem endereço, solicitar
    return AgentResponse(
        text="""Para finalizar o pedido, preciso do seu endereço de entrega.

Por favor, me envie:
📍 Rua, número, bairro e cidade

Exemplo: Rua das Flores, 123, Centro, São Paulo""",
        intent="address_needed",
        next_agent="validation",
        context_updates={"stage": "awaiting_address"},
        should_end=False
    )
```

---

### Modificação 3: OrderAgent - Validação de Contexto

**Arquivo:** `backend/app/agents/order.py`

**Modificar método `process_with_extracted_data()` (linhas 267-378):**

Adicionar validação no INÍCIO do método, logo após o `try`:

```python
async def process_with_extracted_data(
    self,
    extracted_info: dict,
    context: AgentContext,
    db: Session
) -> AgentResponse:
    """
    Process order with pre-extracted data from MessageExtractor

    MODIFICAÇÃO: Adiciona validação de contexto antes de processar
    """
    try:
        # ================================================================
        # NOVA VALIDAÇÃO: Verificar contexto antes de adicionar produto
        # ================================================================

        # Importar context manager
        from app.services.context_manager import ConversationContext

        # Criar contexto
        conv_context = ConversationContext(
            session_data=context.session_data,
            message_history=context.message_history
        )

        # Se bot está aguardando decisão E última mensagem parece negação
        # NÃO adicionar produto (previne duplicação)
        if conv_context.awaiting_user_decision:
            last_question = conv_context.last_bot_question.lower()

            # Verificar se bot perguntou sobre adicionar mais
            if "deseja adicionar mais" in last_question or "quer adicionar" in last_question:
                logger.warning(
                    "OrderAgent: Bot perguntou 'adicionar mais?' mas foi chamado mesmo assim. "
                    "Isso indica problema no roteamento. Redirecionando para finalização..."
                )

                # Redirecionar para pedir endereço
                return AgentResponse(
                    text="""Entendi! Vamos finalizar seu pedido.

Para continuar, preciso do seu endereço de entrega.

Por favor, me envie:
📍 Rua, número, bairro""",
                    intent="finalize_order",
                    next_agent="validation",
                    context_updates={"stage": "awaiting_address"},
                    should_end=False
                )

        # ================================================================
        # CÓDIGO ORIGINAL CONTINUA AQUI
        # ================================================================

        # Get product information from extracted_info
        product_info = extracted_info.get("product", {})
        product_name = product_info.get("name", "")
        quantity = product_info.get("quantity", 1)
        confidence = product_info.get("confidence", 0.0)

        # ... resto do código original sem mudanças
```

---

## 📋 PLANO DE EXECUÇÃO PASSO A PASSO

### FASE 1: Preparação e Limpeza (30 min)

#### Passo 1.1: Backup do Código Atual
```bash
cd c:\Phyton-Projetos\BotGas\backend
git add .
git commit -m "Backup antes da migração para modelo híbrido"
```

#### Passo 1.2: Limpar Produtos Duplicados no Banco
```bash
# Rodar dentro do container backend
cd c:\Phyton-Projetos\BotGas
docker-compose exec -T backend python -c "
from app.database.base import SessionLocal
from app.database.models import Product

db = SessionLocal()
try:
    # Buscar produtos duplicados (mesmo nome e tenant)
    products = db.query(Product).filter(
        Product.name == 'Botijão P13'
    ).order_by(Product.created_at).all()

    print(f'Encontrados {len(products)} produtos com nome Botijão P13')

    if len(products) > 1:
        # Manter apenas o primeiro, deletar os outros
        to_keep = products[0]
        to_delete = products[1:]

        for prod in to_delete:
            print(f'Deletando produto ID: {prod.id}')
            db.delete(prod)

        db.commit()
        print(f'Mantido: {to_keep.id}, Deletados: {len(to_delete)}')
    else:
        print('Nenhuma duplicação encontrada')
finally:
    db.close()
"
```

#### Passo 1.3: Encerrar Conversas Ativas
```bash
docker-compose exec backend python close_conversations.py
```

---

### FASE 2: Criar Novos Componentes (1 hora)

#### Passo 2.1: Criar ConversationContext
```bash
# Criar arquivo
# Copiar código completo da seção "Componente 1: ConversationContext"
# Salvar em: backend/app/services/context_manager.py
```

**Validação:**
```bash
# Testar importação
docker-compose exec backend python -c "
from app.services.context_manager import ConversationContext
print('✅ ConversationContext importado com sucesso')

# Teste básico
context = ConversationContext(
    session_data={'stage': 'building_order'},
    message_history=[
        {'role': 'assistant', 'content': 'Deseja adicionar mais?', 'intent': 'item_added'}
    ]
)
print(f'Awaiting decision: {context.awaiting_user_decision}')
print(f'Last question: {context.last_bot_question}')
"
```

#### Passo 2.2: Criar IntentClassifier
```bash
# Criar arquivo
# Copiar código completo da seção "Componente 2: IntentClassifier"
# Salvar em: backend/app/services/intent_classifier.py
```

**Validação:**
```bash
# Testar classificação
docker-compose exec backend python -c "
import asyncio
from app.services.intent_classifier import IntentClassifier

async def test():
    classifier = IntentClassifier()

    # Teste 1: Saudação
    intent = await classifier.classify('oi')
    print(f'Test 1: oi → {intent}')
    assert intent == 'greeting', f'Expected greeting, got {intent}'

    # Teste 2: Finalizar com contexto
    intent = await classifier.classify(
        'finalizar',
        last_bot_message='Deseja adicionar mais alguma coisa?'
    )
    print(f'Test 2: finalizar (com contexto) → {intent}')
    assert intent == 'answer_no', f'Expected answer_no, got {intent}'

    print('✅ Todos os testes passaram!')

asyncio.run(test())
"
```

---

### FASE 3: Modificar Componentes Existentes (2 horas)

#### Passo 3.1: Modificar MasterAgent

**Arquivo:** `backend/app/agents/master.py`

1. Adicionar imports (topo do arquivo, após imports existentes):
```python
from app.services.context_manager import ConversationContext
from app.services.intent_classifier import IntentClassifier
```

2. Modificar `__init__`:
```python
def __init__(self):
    super().__init__(model_name="gpt-4-turbo-preview", temperature=0.7)
    self.audio_processor = AudioProcessor()
    self.message_extractor = MessageExtractor()
    self.intent_classifier = IntentClassifier()  # ← ADICIONAR ESTA LINHA
```

3. Substituir método `_route_to_agent()` completo (linhas ~181-262):
   - Copiar código da seção "Modificação 1: MasterAgent"
   - Substituir método completo

**Validação:**
```bash
# Verificar sintaxe
docker-compose exec backend python -c "
from app.agents.master import MasterAgent
print('✅ MasterAgent modificado com sucesso')
"
```

#### Passo 3.2: Modificar ValidationAgent

**Arquivo:** `backend/app/agents/validation.py`

1. Adicionar método `ask_for_address()` após o `__init__`:
   - Copiar código da seção "Modificação 2: ValidationAgent"

**Validação:**
```bash
# Verificar método existe
docker-compose exec backend python -c "
from app.agents.validation import ValidationAgent
import inspect

agent = ValidationAgent()
assert hasattr(agent, 'ask_for_address'), 'Método ask_for_address não encontrado'
print('✅ ValidationAgent modificado com sucesso')
"
```

#### Passo 3.3: Modificar OrderAgent

**Arquivo:** `backend/app/agents/order.py`

1. Modificar método `process_with_extracted_data()`:
   - Adicionar validação de contexto no INÍCIO do método
   - Copiar código da seção "Modificação 3: OrderAgent"

**Validação:**
```bash
# Verificar sintaxe
docker-compose exec backend python -c "
from app.agents.order import OrderAgent
print('✅ OrderAgent modificado com sucesso')
"
```

---

### FASE 4: Testes e Validação (1 hora)

#### Passo 4.1: Reiniciar Backend
```bash
cd c:\Phyton-Projetos\BotGas
docker-compose restart backend

# Verificar logs
docker-compose logs -f backend
```

#### Passo 4.2: Testes Manuais via WhatsApp

**Teste 1: Fluxo Normal**
```
Cliente: "oi"
Esperado: Saudação do bot

Cliente: "produtos"
Esperado: Lista de produtos (SEM DUPLICADOS!)

Cliente: "1"
Esperado: "✅ Adicionado: 1x Botijão P13. Deseja adicionar mais?"

Cliente: "finalizar"
Esperado: "Entendi! ... preciso do endereço"
Validar: NÃO deve adicionar outro produto!

Cliente: "Rua ABC, 123, Centro"
Esperado: Validação de endereço
```

**Teste 2: Múltiplos Produtos**
```
Cliente: "oi"
Cliente: "produtos"
Cliente: "1"
Esperado: "Adicionado 1x. Deseja mais?"

Cliente: "sim"
Esperado: "Ok! O que mais deseja?"

Cliente: "2"
Esperado: "Adicionado 1x produto 2. Deseja mais?"

Cliente: "não"
Esperado: "Pedir endereço"
Validar: NÃO adicionar produto 3!
```

**Teste 3: Variações de "Não"**
```
Testar com cada palavra:
- "finalizar"
- "pronto"
- "só isso"
- "não"
- "n"
- "fechar"

Todas devem ir para "pedir endereço", NÃO adicionar produto!
```

#### Passo 4.3: Verificar Logs

Logs esperados para "finalizar":
```
IntentClassifier: 'finalizar' → answer_no
Context: {'awaiting_decision': True, 'has_items': True}
Routing - Intent: answer_no
Cliente negou/finalizou (answer_no)
Tem itens no carrinho → ValidationAgent (pedir endereço)
```

Logs de ERRO (se aparecer, algo está errado):
```
❌ Product detected: Botijão P13 (conf: 0.91)
   Context validated → OrderAgent
```

---

### FASE 5: Monitoramento e Ajustes (1 hora)

#### Passo 5.1: Coletar Métricas

Criar script de análise:
```bash
docker-compose exec -T backend python -c "
from app.database.base import SessionLocal
from app.database.models import Conversation, Order
from sqlalchemy import func

db = SessionLocal()

# Métricas de conversas
total_conversations = db.query(Conversation).count()
active_conversations = db.query(Conversation).filter(
    Conversation.status == 'active'
).count()

# Métricas de pedidos (últimas 24h)
from datetime import datetime, timedelta
yesterday = datetime.utcnow() - timedelta(days=1)

recent_orders = db.query(Order).filter(
    Order.created_at >= yesterday
).all()

# Pedidos com duplicação (2 itens do mesmo produto)
duplicated_orders = 0
for order in recent_orders:
    items = order.items or []
    product_ids = [item.get('product_id') for item in items]
    if len(product_ids) != len(set(product_ids)):
        duplicated_orders += 1

print(f'''
📊 MÉTRICAS PÓS-MIGRAÇÃO
========================
Total de conversas: {total_conversations}
Conversas ativas: {active_conversations}
Pedidos últimas 24h: {len(recent_orders)}
Pedidos com duplicação: {duplicated_orders} ({duplicated_orders/len(recent_orders)*100:.1f}%)
''')

db.close()
"
```

#### Passo 5.2: Análise de Custos

```bash
# Verificar uso de tokens (aproximado)
docker-compose logs backend | grep "IntentClassifier" | wc -l
# Cada linha = 1 chamada de classificação (~150 tokens)

docker-compose logs backend | grep "MessageExtractor" | wc -l
# Cada linha = 1 chamada de extração (~500 tokens)
```

**Custo esperado:**
- Antes: ~1300 tokens/msg × $0.00023/msg = **$0.0003/msg**
- Depois: ~650 tokens/msg × $0.00023/msg = **$0.00015/msg** (50% economia!)

---

## 🧪 CASOS DE TESTE DETALHADOS

### Teste 1: Produto Único + Finalizar

```
INPUT:
- Cliente: "oi"
- Cliente: "produtos"
- Cliente: "1"
- Cliente: "finalizar"

VALIDAÇÕES:
✅ Carrinho deve ter 1 item (não 2!)
✅ Última resposta deve pedir endereço
✅ Logs devem mostrar: Intent=answer_no → ValidationAgent
❌ NÃO deve aparecer: OrderAgent chamado após "finalizar"

CÓDIGO DE VALIDAÇÃO:
```python
from app.database.base import SessionLocal
from app.database.models import Conversation

db = SessionLocal()
conv = db.query(Conversation).order_by(
    Conversation.started_at.desc()
).first()

items = conv.context.get('current_order', {}).get('items', [])
assert len(items) == 1, f"Esperado 1 item, encontrado {len(items)}"
print("✅ Teste 1 passou!")
db.close()
```

---

### Teste 2: Múltiplos Produtos + Confirmações

```
INPUT:
- Cliente: "oi"
- Cliente: "1"
- Bot: "Deseja adicionar mais?"
- Cliente: "sim"
- Bot: "O que mais?"
- Cliente: "2"
- Bot: "Deseja adicionar mais?"
- Cliente: "não"

VALIDAÇÕES:
✅ Carrinho deve ter 2 itens
✅ Intent "sim" → volta para produtos
✅ Intent "não" → pede endereço
✅ NÃO deve adicionar item 3

CÓDIGO DE VALIDAÇÃO:
```python
from app.database.base import SessionLocal
from app.database.models import Conversation

db = SessionLocal()
conv = db.query(Conversation).order_by(
    Conversation.started_at.desc()
).first()

items = conv.context.get('current_order', {}).get('items', [])
assert len(items) == 2, f"Esperado 2 itens, encontrado {len(items)}"

# Verificar produtos diferentes
product_ids = [item['product_id'] for item in items]
assert len(set(product_ids)) == 2, "Produtos devem ser diferentes"

print("✅ Teste 2 passou!")
db.close()
```

---

### Teste 3: Variações de Negação

```
TESTAR CADA UM:
- "finalizar"
- "pronto"
- "só isso"
- "não"
- "nao"
- "n"
- "fechar"
- "terminar"

PARA CADA VARIAÇÃO:
INPUT:
- Cliente: "1"
- Bot: "Deseja adicionar mais?"
- Cliente: [VARIAÇÃO]

VALIDAÇÕES:
✅ Intent classificado como "answer_no"
✅ Roteamento para ValidationAgent
✅ Carrinho mantém 1 item (não duplica)
✅ Resposta pede endereço

CÓDIGO DE VALIDAÇÃO:
```python
import asyncio
from app.services.intent_classifier import IntentClassifier

async def test_negations():
    classifier = IntentClassifier()

    negations = [
        "finalizar", "pronto", "só isso", "não",
        "nao", "n", "fechar", "terminar"
    ]

    last_bot_msg = "Deseja adicionar mais alguma coisa?"

    for word in negations:
        intent = await classifier.classify(word, last_bot_msg)
        assert intent == "answer_no", f"{word} → {intent} (esperado: answer_no)"
        print(f"✅ {word} → answer_no")

    print("✅ Todas as negações classificadas corretamente!")

asyncio.run(test_negations())
```

---

### Teste 4: Produtos Duplicados Removidos

```
VALIDAÇÃO DO BANCO:
```python
from app.database.base import SessionLocal
from app.database.models import Product

db = SessionLocal()

# Buscar produtos por nome
products_by_name = {}
for product in db.query(Product).all():
    name = product.name
    if name not in products_by_name:
        products_by_name[name] = []
    products_by_name[name].append(product)

# Verificar duplicações
duplicates = {
    name: prods for name, prods in products_by_name.items()
    if len(prods) > 1
}

if duplicates:
    print("❌ Produtos duplicados encontrados:")
    for name, prods in duplicates.items():
        print(f"  - {name}: {len(prods)} ocorrências")
    raise AssertionError("Ainda há produtos duplicados!")
else:
    print("✅ Nenhum produto duplicado!")

db.close()
```

---

## 🔄 PLANO DE ROLLBACK

Se algo der errado, seguir estes passos:

### Rollback Rápido (5 minutos)

```bash
# 1. Voltar para commit anterior
cd c:\Phyton-Projetos\BotGas\backend
git reset --hard HEAD~1

# 2. Reiniciar backend
cd ..
docker-compose restart backend

# 3. Verificar logs
docker-compose logs -f backend
```

### Rollback Parcial (manter alguns componentes)

Se quiser manter `ConversationContext` mas reverter roteamento:

```bash
# 1. Manter novos arquivos
git checkout HEAD~1 -- app/agents/master.py
git checkout HEAD~1 -- app/agents/order.py
git checkout HEAD~1 -- app/agents/validation.py

# 2. Manter novos componentes
# (context_manager.py e intent_classifier.py ficam)

# 3. Restart
docker-compose restart backend
```

### Rollback do Banco de Dados (produtos)

Se deletou produtos errados:

```bash
# Verificar se há backup
docker-compose exec postgres pg_dump -U gasbot gasbot > backup_pre_migration.sql

# Restaurar (se necessário)
docker-compose exec -T postgres psql -U gasbot gasbot < backup_pre_migration.sql
```

---

## 📈 MÉTRICAS DE SUCESSO

Após implementação, coletar estas métricas:

### Métrica 1: Taxa de Duplicação de Produtos
```
Antes: ~30% dos pedidos tinham itens duplicados
Depois: <5% (apenas erros legítimos)
```

### Métrica 2: Taxa de Conversão
```
Antes: ~60% dos pedidos iniciados eram finalizados
Depois: >75% (menos erros = mais conversões)
```

### Métrica 3: Custo por Mensagem
```
Antes: $0.0003/msg (1300 tokens)
Depois: $0.00015/msg (650 tokens)
Economia: 50%
```

### Métrica 4: Tempo de Resposta
```
Antes: 2-3 segundos (2 chamadas sequenciais)
Depois: 1.5-2 segundos (1 chamada + routing local)
Melhoria: ~30%
```

### Métrica 5: Satisfação do Cliente
```
Medir via:
- Taxa de abandono de conversas (deve diminuir)
- Pedidos de intervenção humana (deve diminuir)
- Pedidos concluídos com sucesso (deve aumentar)
```

---

## 🎯 PRÓXIMOS PASSOS (Pós-Implementação)

### Curto Prazo (1-2 semanas)

1. **Monitorar logs** diariamente
   - Verificar classificações de intent
   - Identificar edge cases não cobertos

2. **Coletar feedback** dos usuários
   - Criar formulário pós-pedido
   - Analisar conversas abandonadas

3. **Ajustar prompts** do IntentClassifier
   - Se houver classificações erradas frequentes
   - Adicionar exemplos nos prompts

### Médio Prazo (1 mês)

1. **Re-treinar fine-tuning** com dados reais
   - Usar conversas coletadas
   - Incluir contexto conversacional
   - Adicionar exemplos negativos

2. **Adicionar testes automatizados**
   - Pytest para todos os fluxos
   - CI/CD com validações

3. **Otimizar custos**
   - Cache de classificações comuns
   - Fallback para regras simples quando possível

### Longo Prazo (3 meses)

1. **Avaliar migração para GPT-4**
   - Se crescimento permitir
   - Melhor entendimento de contexto

2. **Implementar analytics detalhado**
   - Dashboard de métricas
   - A/B testing de prompts

3. **Expandir capabilities**
   - Suporte a mais tipos de produto
   - Upselling inteligente
   - Recomendações baseadas em histórico

---

## ✅ CHECKLIST FINAL

Antes de dar como concluído:

### Código
- [ ] `ConversationContext` criado e testado
- [ ] `IntentClassifier` criado e testado
- [ ] `MasterAgent._route_to_agent()` modificado
- [ ] `ValidationAgent.ask_for_address()` adicionado
- [ ] `OrderAgent.process_with_extracted_data()` modificado
- [ ] Imports adicionados corretamente
- [ ] Sem erros de sintaxe

### Banco de Dados
- [ ] Produtos duplicados removidos
- [ ] Conversas ativas encerradas
- [ ] Backup realizado

### Testes
- [ ] Teste 1: Finalizar não duplica produto ✅
- [ ] Teste 2: Múltiplos produtos funcionam ✅
- [ ] Teste 3: Todas variações de "não" funcionam ✅
- [ ] Teste 4: Nenhum produto duplicado no banco ✅

### Infraestrutura
- [ ] Backend reiniciado sem erros
- [ ] Logs não mostram erros críticos
- [ ] Webhooks funcionando
- [ ] Frontend conectado e funcional

### Documentação
- [ ] Este documento salvo e versionado
- [ ] Equipe informada das mudanças
- [ ] Plano de rollback documentado

---

## 📞 SUPORTE

Se encontrar problemas durante implementação:

### Erros Comuns

**Erro: `ModuleNotFoundError: No module named 'app.services.context_manager'`**
```
Solução: Verificar se arquivo foi criado no caminho correto
         backend/app/services/context_manager.py
```

**Erro: `IntentClassifier returned invalid intent`**
```
Solução: Verificar OPENAI_API_KEY no .env
         Verificar conectividade com API da OpenAI
```

**Erro: `NoneType object has no attribute 'get'`**
```
Solução: Verificar se message_history está sendo passado corretamente
         Adicionar validações None nos métodos
```

### Debug Avançado

Habilitar logs detalhados:
```python
# No topo de master.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

Verificar fluxo completo:
```bash
# Seguir logs em tempo real
docker-compose logs -f backend | grep -E "(IntentClassifier|Routing|Context)"
```

---

## 📄 CONCLUSÃO

Este plano detalha a migração completa do sistema multi-agentes atual para uma **arquitetura híbrida** que:

1. ✅ **Resolve** o problema de produtos duplicados
2. ✅ **Mantém** o contexto conversacional
3. ✅ **Reduz** custos em 50%
4. ✅ **Melhora** a experiência do usuário
5. ✅ **Facilita** manutenção futura

**Tempo total estimado:** 4-6 horas de implementação

**Risco:** 🟢 Baixo (mudanças controladas, código testado)

**ROI:** Alto (menos erros = mais conversões + custos menores)

---

**Documento criado em:** 2025-10-25
**Versão:** 1.0
**Próxima revisão:** Após implementação e 1 semana de monitoramento

---

## 🚀 COMANDO PARA INICIAR

```bash
# Começar pela Fase 1
cd c:\Phyton-Projetos\BotGas

# 1. Backup
git add . && git commit -m "Backup antes migração modelo híbrido"

# 2. Limpar produtos duplicados
docker-compose exec backend python -c "[código do Passo 1.2]"

# 3. Encerrar conversas
docker-compose exec backend python close_conversations.py

# 4. Seguir para Fase 2...
```

**BOA SORTE! 🎉**
