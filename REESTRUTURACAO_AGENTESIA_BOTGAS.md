# 🤖 REESTRUTURAÇÃO: AGENTES DE IA REAIS - BOTGAS

> **Documento Técnico para Migração de TypeBot para Sistema Multi-Agentes REAL com IA**
> Data: 2025-10-27
> Versão: 1.0
> Autor: Claude Code Analysis

---

## 📊 SUMÁRIO EXECUTIVO

### Problema Atual
O sistema foi implementado como **TypeBot com IF/ELSE** mascarado de "multi-agentes":
- ❌ 98% das decisões são hardcoded (listas de palavras-chave)
- ❌ LLM só é usado para extrair dados (MessageExtractor)
- ❌ Agentes NÃO pensam, apenas executam IF/ELSE
- ❌ Contexto conversacional é ignorado
- ❌ Não entende variações linguísticas ("pode seguir", "beleza", etc)

### Solução Proposta
Implementar **agentes DE VERDADE** que usam LLM para tomar decisões:
- ✅ MasterAgent usa IA para decidir roteamento (não IF/ELSE)
- ✅ Cada agente usa IA para decisões (não listas de palavras)
- ✅ Contexto completo sempre disponível
- ✅ Entende variações linguísticas naturalmente
- ✅ Prompts bem estruturados substituem código hardcoded

### Resultado Esperado
- ✅ Sistema realmente inteligente
- ✅ 80% menos código para manter
- ✅ Fácil ajustar comportamento (editar prompts, não código)
- ✅ Generaliza para novos casos automaticamente
- ✅ Custo: ~$0.65/mês para 1000 pedidos (irrelevante)

### Tempo Estimado
**15-20 horas** de implementação

### Risco
🟡 **MÉDIO** - Refatoração grande, mas estrutura de dados mantida

---

## ✅ CHECKLIST DE IMPLEMENTAÇÃO

Use este checklist para acompanhar o progresso da implementação:

---

### 📋 PRÉ-REQUISITOS

- [ ] Ler este documento completo
- [ ] Entender o problema atual (sistema = TypeBot com IF/ELSE)
- [ ] Entender a solução (agentes REAIS com LLM)
- [ ] Backend rodando sem erros
- [ ] Acesso ao container Docker funcionando
- [ ] Git configurado para commits

---

### 🗂️ FASE 1: PREPARAÇÃO E BACKUP (1h)

**Objetivo:** Garantir segurança antes de mudanças grandes

#### Passo 1.1: Análise da Estrutura Atual
- [ ] Ler código do BaseAgent atual (`app/agents/base.py`)
- [ ] Listar todos os métodos com IF/ELSE hardcoded
- [ ] Identificar onde LLM NÃO está sendo usado
- [ ] Documentar dependências entre agentes

#### Passo 1.2: Backup Completo
- [ ] Criar branch: `git checkout -b feature/real-ai-agents`
- [ ] Commit de backup: `git add . && git commit -m "Backup antes reestruturação agentes IA"`
- [ ] Confirmar commit: `git log -1`
- [ ] **Tag de segurança:** `git tag backup-before-ai-agents`

#### Passo 1.3: Preparar Ambiente
- [ ] Verificar variável `OPENAI_API_KEY` no `.env`
- [ ] Testar chamada simples ao OpenAI:
  ```python
  from langchain_openai import ChatOpenAI
  llm = ChatOpenAI(model="gpt-4o-mini")
  response = await llm.ainvoke("teste")
  ```
- [ ] Confirmar: resposta recebida sem erros

#### Passo 1.4: Criar Diretório de Testes
- [ ] Criar: `backend/tests/agents/` (se não existir)
- [ ] Criar arquivo: `test_prompts.py` (para testar prompts isoladamente)

---

### 🔧 FASE 2: REFATORAR BaseAgent (2h)

**Objetivo:** Criar base sólida para agentes REAIS com IA

#### Passo 2.1: Limpar Código Antigo
- [ ] Abrir: `backend/app/agents/base.py`
- [ ] **DELETAR** método `_detect_intent()` (linhas 120-154)
  - ❌ É puro IF/ELSE com listas de palavras
  - ✅ Será substituído por LLM
- [ ] **MANTER** métodos úteis:
  - ✅ `_build_messages()` - formata histórico
  - ✅ `_call_llm()` - chama OpenAI
  - ✅ `_build_system_prompt()` - base para prompts

#### Passo 2.2: Adicionar Novos Métodos

**Método 1: Parse de Resposta JSON**
- [ ] Adicionar ao BaseAgent:
```python
def _parse_llm_response(self, response_text: str) -> dict:
    """
    Parse resposta JSON do LLM

    LLM deve retornar JSON estruturado.
    Este método extrai e valida o JSON.
    """
    import json
    import re

    try:
        # Tentar parse direto
        return json.loads(response_text)
    except json.JSONDecodeError:
        # Se falhar, buscar JSON entre ```json e ```
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))

        # Se ainda falhar, buscar qualquer { ... }
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))

        # Falha total
        logger.error(f"Não foi possível parsear JSON: {response_text}")
        return {"erro": "resposta_invalida", "texto": response_text}
```
- [ ] Validar: código compila sem erros

**Método 2: Formatar Contexto Completo**
- [ ] Adicionar ao BaseAgent:
```python
def _format_full_context(self, context: AgentContext) -> str:
    """
    Formata contexto completo para o prompt

    Inclui:
    - Dados da sessão
    - Estado do carrinho
    - Histórico de mensagens
    - Informações do cliente
    """
    # Carrinho
    current_order = context.session_data.get("current_order", {})
    items = current_order.get("items", [])
    cart_summary = f"{len(items)} item(s) - R$ {current_order.get('total', 0):.2f}" if items else "vazio"

    # Stage
    stage = context.session_data.get("stage", "início")

    # Endereço
    has_address = bool(context.session_data.get("delivery_address"))

    # Histórico
    history_text = self._format_history_text(context.message_history[-5:])

    return f"""
CONTEXTO ATUAL:
- Stage: {stage}
- Carrinho: {cart_summary}
- Endereço validado: {has_address}
- Cliente: {context.customer_phone}

HISTÓRICO RECENTE (últimas 5 mensagens):
{history_text}
"""

def _format_history_text(self, messages: list) -> str:
    """Formata histórico para texto legível"""
    if not messages:
        return "(nenhuma mensagem anterior)"

    text = ""
    for msg in messages:
        role = "Cliente" if msg.get("role") == "user" else "Bot"
        content = msg.get("content", "")[:100]
        text += f"- {role}: {content}...\n"

    return text
```
- [ ] Validar: código compila sem erros

#### Passo 2.3: Atualizar Método `process()`
- [ ] Modificar método `process()` no BaseAgent para incluir contexto completo:
```python
async def process(self, message: str, context: AgentContext) -> AgentResponse:
    """
    Processo REAL com IA

    1. Monta system prompt com contexto completo
    2. Chama LLM
    3. Parse resposta JSON
    4. Executa decisão
    """
    # System prompt (cada agente implementa)
    system_prompt = self._build_system_prompt(context)

    # Mensagens
    messages = [
        SystemMessage(content=system_prompt),
        *self._build_messages(message, context, system_prompt=None)[1:],  # Pular o system
        HumanMessage(content=message)
    ]

    # Chamar LLM
    response = await self._call_llm(messages)

    # Parse JSON
    decision = self._parse_llm_response(response)

    # Executar (cada agente implementa)
    return await self._execute_decision(decision, context)

@abstractmethod
async def _execute_decision(self, decision: dict, context: AgentContext) -> AgentResponse:
    """Cada agente implementa como executar a decisão do LLM"""
    pass
```
- [ ] Validar: BaseAgent compila sem erros

#### Passo 2.4: Testar BaseAgent Isoladamente
- [ ] Criar teste em `tests/agents/test_base_agent.py`:
```python
import asyncio
from app.agents.base import BaseAgent, AgentContext, AgentResponse

class TestAgent(BaseAgent):
    def _build_system_prompt(self, context):
        return "Você é um agente de teste. Responda em JSON: {\"resposta\": \"ok\"}"

    async def _execute_decision(self, decision, context):
        return AgentResponse(text=decision.get("resposta", "erro"), intent="test")

async def test():
    agent = TestAgent()
    context = AgentContext(
        tenant_id="test-id",
        customer_phone="5511999999999",
        conversation_id="test-conv",
        session_data={},
        message_history=[]
    )

    response = await agent.process("teste", context)
    print(f"Resposta: {response.text}")
    assert response.text == "ok", "BaseAgent não funcionou corretamente"
    print("✅ BaseAgent funcionando!")

asyncio.run(test())
```
- [ ] Executar: `docker-compose exec backend python tests/agents/test_base_agent.py`
- [ ] ✅ Confirmar: "BaseAgent funcionando!"

---

### 🧠 FASE 3: IMPLEMENTAR MasterAgent REAL (3h)

**Objetivo:** MasterAgent usa IA para decidir roteamento (não IF/ELSE)

#### Passo 3.1: Revisar Código Atual
- [ ] Abrir: `backend/app/agents/master.py`
- [ ] Identificar bloco de roteamento (_route_to_agent)
- [ ] Documentar todas as condições IF/ELSE atuais
- [ ] Total de linhas com IF/ELSE: ______ linhas

#### Passo 3.2: Criar System Prompt do MasterAgent
- [ ] No método `_build_system_prompt()` do MasterAgent, implementar:

```python
def _build_system_prompt(self, context: AgentContext) -> str:
    """System prompt para MasterAgent decidir roteamento"""

    # Buscar dados do tenant
    from app.database.base import get_db
    db = next(get_db())

    try:
        from app.database.models import Tenant
        tenant = db.query(Tenant).filter(Tenant.id == context.tenant_id).first()
        company_name = tenant.company_name if tenant else "Distribuidora"
    finally:
        db.close()

    # Contexto formatado
    ctx = self._format_full_context(context)

    return f"""Você é o ORQUESTRADOR do sistema de atendimento via WhatsApp da {company_name}.

Sua ÚNICA responsabilidade é decidir QUAL agente especializado deve processar a mensagem do cliente.

{ctx}

AGENTES DISPONÍVEIS:
1. **AttendanceAgent**: Saudações, apresentar produtos, dúvidas gerais sobre a empresa
2. **OrderAgent**: Adicionar/remover itens do carrinho, gerenciar pedido
3. **ValidationAgent**: Validar endereço de entrega (após cliente fornecer)
4. **PaymentAgent**: Coletar forma de pagamento e finalizar pedido

ANÁLISE NECESSÁRIA:
1. O que o cliente está pedindo AGORA?
2. Qual o CONTEXTO da conversa (o que foi discutido antes)?
3. Se o bot fez uma pergunta, o cliente está RESPONDENDO ela?
4. Qual agente é mais ADEQUADO para esta situação?

REGRAS IMPORTANTES:
- Se stage="confirming_order" E cliente CONFIRMA (sim/ok/pode/beleza/etc) → PaymentAgent (próximo é pagamento)
- Se stage="building_order" E cliente CONFIRMA adicionar mais → AttendanceAgent (mostrar produtos)
- Se stage="awaiting_address" → ValidationAgent
- Se stage="payment" → PaymentAgent
- Se cliente menciona PRODUTO → OrderAgent
- Se cliente menciona ENDEREÇO → ValidationAgent
- Se cliente SAÚDA ou pede INFO → AttendanceAgent

ATENÇÃO: CONTEXTO > palavras isoladas
- "pode seguir" após confirmar endereço = ir para pagamento
- "pode seguir" sem contexto = pedir esclarecimento

RESPONDA **APENAS** EM JSON (não adicione texto antes ou depois):
{{
    "raciocinio": "breve explicação da sua decisão (1 frase)",
    "agente": "AttendanceAgent" | "OrderAgent" | "ValidationAgent" | "PaymentAgent",
    "contexto_adicional": {{
        "cliente_confirmando": true/false,
        "cliente_finalizando": true/false,
        "cliente_corrigindo": true/false
    }}
}}"""
```
- [ ] Salvar arquivo
- [ ] Validar: código compila sem erros

#### Passo 3.3: Implementar _execute_decision()
- [ ] No MasterAgent, adicionar método:

```python
async def _execute_decision(self, decision: dict, context: AgentContext, db) -> AgentResponse:
    """
    Executa decisão do LLM: roteia para agente escolhido
    """
    agente_nome = decision.get("agente", "AttendanceAgent")
    raciocinio = decision.get("raciocinio", "")

    logger.info(f"MasterAgent decidiu: {agente_nome} | Razão: {raciocinio}")

    # Importar agentes
    from app.agents.attendance import AttendanceAgent
    from app.agents.order import OrderAgent
    from app.agents.validation import ValidationAgent
    from app.agents.payment import PaymentAgent

    # Instanciar agente escolhido
    if agente_nome == "AttendanceAgent":
        agent = AttendanceAgent()
    elif agente_nome == "OrderAgent":
        agent = OrderAgent()
    elif agente_nome == "ValidationAgent":
        agent = ValidationAgent()
    elif agente_nome == "PaymentAgent":
        agent = PaymentAgent()
    else:
        # Fallback
        logger.warning(f"Agente desconhecido: {agente_nome}. Usando AttendanceAgent.")
        agent = AttendanceAgent()

    # Chamar agente escolhido
    return await agent.process(message, context)
```
- [ ] **IMPORTANTE:** Modificar método `process()` do MasterAgent para passar `db`:
  - Atualizar chamadas para `_execute_decision(decision, context, db)`
- [ ] Salvar arquivo
- [ ] Validar: código compila sem erros

#### Passo 3.4: Remover Lógica de Roteamento Hardcoded
- [ ] Comentar (não deletar ainda) todo o método `_route_to_agent()` antigo
- [ ] Adicionar comentário: `# TODO: Deletar após validação do novo sistema`
- [ ] Atualizar método `process()` principal do MasterAgent para usar novo fluxo:

```python
async def process(self, message: dict, context: AgentContext, db) -> AgentResponse:
    """
    Process message with AI-powered routing
    """

    # 1. Verificar intervenção humana (manter lógica existente)
    intervention_check = await self._check_human_intervention(context, db)
    if intervention_check:
        return intervention_check

    # 2. Processar áudio se necessário (manter lógica existente)
    if message.get("type") == "audio":
        message_text = await self._process_audio(message, context)
    else:
        message_text = message.get("content", "")

    # 3. NOVO: LLM decide roteamento
    system_prompt = self._build_system_prompt(context)
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Mensagem do cliente: {message_text}")
    ]

    response = await self._call_llm(messages)
    decision = self._parse_llm_response(response)

    # 4. Executar decisão
    return await self._execute_decision(decision, context, db)
```
- [ ] Salvar arquivo
- [ ] Validar: código compila sem erros

#### Passo 3.5: Testar MasterAgent
- [ ] Criar teste: `tests/agents/test_master_routing.py`
- [ ] Testar casos:
  - [ ] "oi" → AttendanceAgent
  - [ ] "quero um P13" → OrderAgent
  - [ ] "Rua ABC 123" → ValidationAgent
  - [ ] "vou pagar no pix" → PaymentAgent
- [ ] Executar testes
- [ ] ✅ Confirmar: todos passaram

---

### 📦 FASE 4: IMPLEMENTAR OrderAgent REAL (2h)

**Objetivo:** OrderAgent usa IA para gerenciar carrinho (não listas de palavras)

#### Passo 4.1: Criar System Prompt
- [ ] Abrir: `backend/app/agents/order.py`
- [ ] Modificar `_build_system_prompt()`:

```python
def _build_system_prompt(self, context: AgentContext) -> str:
    """System prompt para OrderAgent"""

    # Buscar produtos e tenant
    from app.database.base import get_db
    from app.database.models import Product, Tenant

    db = next(get_db())
    try:
        tenant = db.query(Tenant).filter(Tenant.id == context.tenant_id).first()
        products = db.query(Product).filter(
            Product.tenant_id == context.tenant_id,
            Product.is_available == True
        ).all()

        # Formatar produtos
        products_text = ""
        for i, p in enumerate(products, 1):
            products_text += f"{i}. {p.name} - R$ {p.price:.2f}\n"

        # Carrinho atual
        current_order = context.session_data.get("current_order", {})
        items = current_order.get("items", [])

        cart_text = ""
        if items:
            for item in items:
                cart_text += f"- {item['quantity']}x {item['product_name']} (R$ {item['subtotal']:.2f})\n"
            cart_text += f"Total: R$ {current_order.get('total', 0):.2f}"
        else:
            cart_text = "Carrinho vazio"

        # Última pergunta
        last_bot_question = ""
        for msg in reversed(context.message_history):
            if msg.get("role") == "assistant":
                last_bot_question = msg.get("content", "")
                break

    finally:
        db.close()

    # Contexto
    ctx = self._format_full_context(context)

    return f"""Você gerencia o CARRINHO DE COMPRAS de pedidos de gás via WhatsApp.

{ctx}

PRODUTOS DISPONÍVEIS:
{products_text}

CARRINHO ATUAL:
{cart_text}

ÚLTIMA PERGUNTA QUE VOCÊ FEZ:
"{last_bot_question}"

RESPONSABILIDADES:
1. Adicionar produtos ao carrinho
2. Remover produtos do carrinho
3. Mostrar resumo do pedido
4. Detectar quando cliente quer finalizar

REGRAS DE INTERPRETAÇÃO:
1. Se você perguntou "Deseja adicionar mais?" e cliente diz não/finalizar/pronto/só isso:
   → NÃO adicione produto
   → Ação = "finalizar"

2. Se cliente menciona produto (por nome ou número da lista):
   → Adicione ao carrinho

3. Se cliente diz sim/ok/pode SEM você ter perguntado nada:
   → Peça esclarecimento

4. Entenda variações naturais:
   - "quero um P13" = adicionar Botijão P13
   - "pode seguir" após você perguntar = confirmação
   - "só isso" / "mais nada" = finalizar
   - "1" = produto número 1 da lista
   - "dois p13" = 2x Botijão P13

RESPONDA **APENAS** EM JSON:
{{
    "acao": "adicionar" | "remover" | "mostrar_resumo" | "finalizar" | "esclarecer",
    "produto_nome": "nome do produto ou null",
    "quantidade": número ou null,
    "mensagem_cliente": "texto amigável da resposta",
    "proximo_passo": "pedir_endereco" | "continuar_comprando" | "esclarecer"
}}

IMPORTANTE: Seja natural e amigável na mensagem_cliente."""
```
- [ ] Salvar arquivo
- [ ] Validar: compila sem erros

#### Passo 4.2: Implementar _execute_decision()
- [ ] Adicionar método no OrderAgent:

```python
async def _execute_decision(self, decision: dict, context: AgentContext) -> AgentResponse:
    """Executa decisão do LLM para gerenciar carrinho"""

    from app.database.base import get_db
    from app.database.models import Product

    db = next(get_db())

    try:
        acao = decision.get("acao")
        mensagem = decision.get("mensagem_cliente", "")
        proximo_passo = decision.get("proximo_passo")

        current_order = context.session_data.get("current_order", {
            "items": [],
            "subtotal": 0.0,
            "delivery_fee": 0.0,
            "total": 0.0
        })

        # ADICIONAR produto
        if acao == "adicionar":
            produto_nome = decision.get("produto_nome")
            quantidade = decision.get("quantidade", 1)

            # Buscar produto
            product = db.query(Product).filter(
                Product.tenant_id == context.tenant_id,
                Product.name.ilike(f"%{produto_nome}%"),
                Product.is_available == True
            ).first()

            if not product:
                return AgentResponse(
                    text=f"Desculpe, não encontrei '{produto_nome}' em nosso catálogo.",
                    intent="product_not_found",
                    should_end=False
                )

            # Adicionar ao carrinho
            item = {
                "product_id": str(product.id),
                "product_name": product.name,
                "quantity": quantidade,
                "unit_price": float(product.price),
                "subtotal": float(product.price) * quantidade
            }
            current_order["items"].append(item)

            # Recalcular totais
            current_order["subtotal"] = sum(i["subtotal"] for i in current_order["items"])
            current_order["total"] = current_order["subtotal"] + current_order.get("delivery_fee", 0)

            return AgentResponse(
                text=mensagem,
                intent="item_added",
                context_updates={"current_order": current_order},
                should_end=False
            )

        # FINALIZAR
        elif acao == "finalizar":
            if not current_order.get("items"):
                return AgentResponse(
                    text="Seu carrinho está vazio. O que você gostaria de pedir?",
                    intent="empty_cart",
                    should_end=False
                )

            return AgentResponse(
                text=mensagem,
                intent="ready_for_address",
                next_agent="validation",
                context_updates={
                    "current_order": current_order,
                    "stage": "awaiting_address"
                },
                should_end=False
            )

        # MOSTRAR RESUMO
        elif acao == "mostrar_resumo":
            summary = self._build_order_summary(current_order)
            return AgentResponse(
                text=f"{mensagem}\n\n{summary}",
                intent="show_summary",
                should_end=False
            )

        # ESCLARECER
        else:
            return AgentResponse(
                text=mensagem,
                intent="clarification_needed",
                should_end=False
            )

    finally:
        db.close()

def _build_order_summary(self, order: dict) -> str:
    """Constrói resumo do pedido"""
    if not order.get("items"):
        return "Carrinho vazio."

    summary = "📋 **Seu Pedido:**\n\n"
    for item in order["items"]:
        summary += f"- {item['quantity']}x {item['product_name']}\n"
        summary += f"  💰 R$ {item['subtotal']:.2f}\n\n"

    summary += f"**Total:** R$ {order.get('total', 0):.2f}"
    return summary
```
- [ ] Salvar arquivo
- [ ] Validar: compila sem erros

#### Passo 4.3: Remover Código Antigo
- [ ] Comentar métodos antigos com IF/ELSE:
  - `_parse_order_intent()`
  - `_extract_product_and_quantity()`
  - Listas de palavras (PRODUCT_SYNONYMS, etc)
- [ ] Adicionar comentário: `# TODO: Deletar após validação`

#### Passo 4.4: Testar OrderAgent
- [ ] Testar casos:
  - [ ] "quero um P13" → adiciona produto
  - [ ] "2" → adiciona produto 2
  - [ ] "finalizar" após "Deseja mais?" → NÃO adiciona produto
  - [ ] "pode seguir" após confirmar → finaliza
- [ ] ✅ Todos testes passaram

---

### 📍 FASE 5: IMPLEMENTAR ValidationAgent REAL (2h)

**Objetivo:** ValidationAgent usa IA para extrair/validar endereço

#### Passo 5.1: System Prompt
- [ ] Implementar `_build_system_prompt()` no ValidationAgent
- [ ] Incluir:
  - Modo de entrega (neighborhood/radius/hybrid)
  - Instruções para extrair endereço
  - Exemplos de variações
- [ ] Código completo no documento (seção "PROMPTS DOS AGENTES")

#### Passo 5.2: _execute_decision()
- [ ] Implementar lógica:
  - Se endereço completo → validar com Google Maps
  - Se incompleto → pedir dados faltantes
  - Retornar taxa + tempo se válido

#### Passo 5.3: Remover Código Antigo
- [ ] Comentar método `_extract_address()` (regex patterns)
- [ ] Manter apenas:
  - ✅ `validate_delivery()` (Google Maps)
  - ✅ Cache de endereços

#### Passo 5.4: Testar
- [ ] "Rua ABC 123 Centro" → valida endereço
- [ ] "morada 15" → extrai corretamente
- [ ] "Rua ABC" (sem número) → pede número
- [ ] ✅ Testes OK

---

### 💳 FASE 6: IMPLEMENTAR PaymentAgent REAL (2h)

**Objetivo:** PaymentAgent usa IA para detectar forma de pagamento

#### Passo 6.1: System Prompt
- [ ] Implementar prompt no PaymentAgent
- [ ] Incluir:
  - Formas aceitas (PIX, dinheiro, cartão)
  - Detecção de troco
  - Finalização de pedido

#### Passo 6.2: _execute_decision()
- [ ] Detectar forma de pagamento
- [ ] Se PIX → mostrar chave
- [ ] Se dinheiro → perguntar troco
- [ ] Criar pedido no banco
- [ ] Enviar confirmação

#### Passo 6.3: Remover Código Antigo
- [ ] Comentar `_detect_payment_method()` (IF/ELSE)
- [ ] Manter apenas lógica de criar pedido no banco

#### Passo 6.4: Testar
- [ ] "vou pagar no pix" → mostra PIX
- [ ] "dinheiro" → pergunta troco
- [ ] "100 reais" → detecta troco de R$100
- [ ] ✅ Testes OK

---

### 👋 FASE 7: IMPLEMENTAR AttendanceAgent REAL (2h)

**Objetivo:** AttendanceAgent responde naturalmente com IA

#### Passo 7.1: System Prompt
- [ ] Implementar prompt completo
- [ ] Incluir:
  - Lista de produtos
  - Informações da empresa
  - Tom de voz (amigável, brasileiro)

#### Passo 7.2: _execute_decision()
- [ ] LLM responde diretamente
- [ ] Formatar produtos se solicitado
- [ ] Guiar para próximos passos

#### Passo 7.3: Remover Código Antigo
- [ ] Deletar métodos:
  - `_handle_greeting()` (template fixo)
  - `_handle_product_inquiry()` (formata lista)
  - `_handle_help()` (template fixo)
- [ ] Manter apenas `_handle_general()` (já usa LLM)

#### Passo 7.4: Testar
- [ ] "oi" → saudação natural
- [ ] "produtos" → lista formatada
- [ ] "quanto custa o P13" → resposta clara
- [ ] ✅ Testes OK

---

### 🧪 FASE 8: TESTES INTEGRADOS (4h)

**Objetivo:** Validar sistema completo funcionando

#### Passo 8.1: Fluxo Completo - Caso Feliz
- [ ] Iniciar conversa: "oi"
  - ✅ AttendanceAgent saúda
- [ ] "produtos"
  - ✅ AttendanceAgent lista produtos
- [ ] "quero o 1"
  - ✅ OrderAgent adiciona P13
- [ ] "finalizar"
  - ✅ OrderAgent NÃO adiciona produto
  - ✅ Pede endereço
- [ ] "Rua ABC, 123, Centro"
  - ✅ ValidationAgent valida
- [ ] "pode seguir"
  - ✅ PaymentAgent pede pagamento (não adiciona produto!)
- [ ] "pix"
  - ✅ PaymentAgent mostra chave PIX
  - ✅ Pedido criado no banco

#### Passo 8.2: Variações Linguísticas
- [ ] Testar "beleza" em vez de "ok"
- [ ] Testar "tá bom" em vez de "sim"
- [ ] Testar "só isso" em vez de "finalizar"
- [ ] Testar "na maquininha" em vez de "cartão"
- [ ] ✅ Todas variações funcionam

#### Passo 8.3: Casos de Erro
- [ ] Cliente pede produto inexistente
  - ✅ Sistema informa que não existe
- [ ] Cliente fornece endereço incompleto
  - ✅ Sistema pede dados faltantes
- [ ] Cliente não responde forma de pagamento
  - ✅ Sistema repete pergunta

#### Passo 8.4: Validar Logs
- [ ] MasterAgent logando decisões:
  ```
  MasterAgent decidiu: OrderAgent | Razão: Cliente mencionou produto
  ```
- [ ] Cada agente logando ações:
  ```
  OrderAgent: Ação = adicionar | Produto = Botijão P13
  ```
- [ ] ✅ Logs claros e úteis

#### Passo 8.5: Verificar Custo de API
- [ ] Executar 10 pedidos completos
- [ ] Calcular tokens usados
- [ ] Custo total: R$ ____
- [ ] Custo por pedido: R$ ____
- [ ] ✅ Custo aceitável (<R$ 0.01 por pedido)

---

### 📊 FASE 9: MONITORAMENTO E AJUSTES (2h)

**Objetivo:** Garantir qualidade e performance

#### Passo 9.1: Criar Dashboard de Métricas
- [ ] Adicionar endpoint: `/api/v1/agents/metrics`
- [ ] Métricas:
  - Total de decisões por agente
  - Tempo médio de resposta
  - Taxa de sucesso (pedidos finalizados)
  - Custo acumulado de API

#### Passo 9.2: Logs Estruturados
- [ ] Cada decisão de agente salva em log:
```python
{
    "timestamp": "2025-10-27T10:30:00",
    "agent": "MasterAgent",
    "decision": "OrderAgent",
    "reasoning": "Cliente mencionou produto",
    "tokens_used": 450,
    "cost_usd": 0.00007
}
```

#### Passo 9.3: Ajustes de Prompts
- [ ] Se detecção incorreta > 5%:
  - Revisar prompt do agente
  - Adicionar exemplos
  - Ajustar temperatura
- [ ] Documentar ajustes realizados

#### Passo 9.4: Comparação com Sistema Antigo
- [ ] Métrica: Taxa de duplicação de produtos
  - Antes: ____%
  - Depois: ____%
- [ ] Métrica: Tempo de atendimento
  - Antes: ____ segundos
  - Depois: ____ segundos
- [ ] Métrica: Taxa de conversão
  - Antes: ____%
  - Depois: ____%

---

### 🚀 FASE 10: DEPLOY E ROLLOUT (1 dia)

**Objetivo:** Colocar em produção com segurança

#### Passo 10.1: Preparar Deploy
- [ ] Merge branch `feature/real-ai-agents` em `develop`
- [ ] Testes finais em staging
- [ ] Documentação atualizada
- [ ] README com novo fluxo

#### Passo 10.2: Rollout Gradual
- [ ] **10%**: Ativar novo sistema para 10% dos clientes
- [ ] Monitorar por 2 dias
- [ ] Métricas OK? Sim [ ] Não [ ]
- [ ] **50%**: Expandir para 50%
- [ ] Monitorar por 2 dias
- [ ] Métricas OK? Sim [ ] Não [ ]
- [ ] **100%**: Ativar para todos

#### Passo 10.3: Deletar Código Antigo
- [ ] Após 1 semana de 100% estável
- [ ] Deletar métodos comentados:
  - `_detect_intent()` do BaseAgent
  - Métodos de parse hardcoded
  - Listas de palavras-chave
- [ ] Commit: "Cleanup: Remove old IF/ELSE logic"

#### Passo 10.4: Documentação Final
- [ ] Atualizar `technical-specs.md`
- [ ] Documentar prompts em arquivo separado
- [ ] Criar guia de ajuste de prompts
- [ ] Video demo do novo sistema

---

## 📈 MÉTRICAS DE SUCESSO

### Antes (Sistema Antigo - TypeBot)
- Linhas de código com IF/ELSE: ~800 linhas
- % de IA real: 2% (só MessageExtractor)
- Variações linguísticas: Lista fixa de ~50 palavras
- Taxa de erro (produto duplicado): 30%
- Tempo de desenvolvimento para novo caso: 2-4 horas

### Depois (Agentes IA Reais) - Esperado
- Linhas de código com IF/ELSE: ~50 linhas (80% menos)
- % de IA real: 95%
- Variações linguísticas: Infinitas (LLM entende)
- Taxa de erro (produto duplicado): <5%
- Tempo de desenvolvimento para novo caso: 15 min (editar prompt)

### Custo de API
- Pedidos/mês: 1000
- Tokens/pedido: ~2600
- Custo/pedido: $0.00065
- **Total/mês: $0.65** (irrelevante!)

---

## 🔄 PLANO DE ROLLBACK

### Se algo der errado:

#### Rollback Rápido (5 min)
```bash
# Voltar para tag de backup
git reset --hard backup-before-ai-agents
docker-compose restart backend
```

#### Rollback Parcial
- Manter MasterAgent novo
- Reverter agentes específicos problemáticos
- Deploy incremental

#### Logs de Erro
- Se taxa de erro > 10%: rollback automático
- Se latência > 5s: investigar + rollback se necessário
- Se custo > $10/dia: pausar e revisar prompts

---

## 📞 SUPORTE E DEBUG

### Problemas Comuns

**Erro: "LLM não retorna JSON válido"**
```
Solução: Ajustar prompt para ser mais claro
- Adicionar: "RESPONDA APENAS EM JSON (sem texto antes ou depois)"
- Melhorar _parse_llm_response() para ser mais tolerante
```

**Erro: "Roteamento incorreto"**
```
Solução: Revisar system prompt do MasterAgent
- Adicionar mais exemplos de casos difíceis
- Aumentar clareza das instruções
- Reduzir temperatura (mais determinístico)
```

**Erro: "Custo de API muito alto"**
```
Solução:
- Reduzir histórico passado (de 10 para 5 mensagens)
- Usar modelos menores para casos simples
- Cache de respostas comuns
```

### Debug de Decisões
```python
# Adicionar logs detalhados:
logger.debug(f"Prompt enviado: {system_prompt}")
logger.debug(f"Resposta LLM: {response}")
logger.debug(f"Decisão parseada: {decision}")
```

---

## ✅ CHECKLIST FINAL

### Código
- [ ] BaseAgent refatorado sem IF/ELSE
- [ ] MasterAgent usa IA para roteamento
- [ ] OrderAgent usa IA para decisões
- [ ] ValidationAgent usa IA para extração
- [ ] PaymentAgent usa IA para detecção
- [ ] AttendanceAgent usa IA para respostas
- [ ] Código antigo comentado/deletado
- [ ] Sem warnings ou erros

### Testes
- [ ] Testes unitários de cada agente
- [ ] Teste de fluxo completo
- [ ] Teste de variações linguísticas
- [ ] Teste de casos de erro
- [ ] Teste de performance/custo

### Infraestrutura
- [ ] Deploy em staging OK
- [ ] Rollout gradual planejado
- [ ] Métricas configuradas
- [ ] Logs estruturados
- [ ] Plano de rollback documentado

### Documentação
- [ ] `technical-specs.md` atualizado
- [ ] Prompts documentados
- [ ] Guia de ajustes
- [ ] README atualizado
- [ ] Changelog

---

## 🎯 RESUMO EXECUTIVO PARA NOVO CHAT

**Contexto:**
Sistema atual é TypeBot mascarado de agentes (98% IF/ELSE, 2% IA). Precisamos transformar em agentes REAIS que usam LLM para decisões.

**Objetivo:**
Cada agente usa IA para PENSAR e DECIDIR (não IF/ELSE). MasterAgent usa IA para rotear. Contexto completo sempre disponível.

**Estrutura:**
- ✅ Database/Models: manter 100%
- ✅ Integrações (WhatsApp, Google Maps): manter 100%
- ❌ Agentes atuais: refatorar completamente
- ✅ Services: manter

**Tempo:** 15-20 horas
**Risco:** Médio (refatoração grande)
**Custo API:** ~$0.65/mês (irrelevante)

**Prioridades:**
1. MasterAgent (orquestrador) é o mais crítico
2. OrderAgent (onde está o problema de duplicação)
3. Demais agentes

**Validação de Sucesso:**
Cliente diz "pode seguir" após confirmar endereço → Sistema pede pagamento (NÃO adiciona produto)

---

## 🚀 COMANDO PARA INICIAR

```bash
# 1. Entrar no diretório
cd c:\Phyton-Projetos\BotGas

# 2. Criar branch
git checkout -b feature/real-ai-agents

# 3. Backup
git add . && git commit -m "Backup antes reestruturação agentes IA"
git tag backup-before-ai-agents

# 4. Começar pela Fase 2 (BaseAgent)
# Seguir checklist passo a passo
```

---

**Documento criado em:** 2025-10-27
**Versão:** 1.0
**Próxima revisão:** Após implementação completa

**BOA SORTE! 🎉**
