# 🤖 Como Ativar Agentes de IA REAIS no BotGas

## 📊 Status da Implementação

### ✅ **COMPLETO** - Agentes com IA Real Implementados

| Agente | Status | Métodos Disponíveis |
|--------|--------|-------------------|
| **BaseAgent** | ✅ | `_parse_llm_response()`, `_format_full_context()`, `_format_history_text()` |
| **MasterAgent** | ✅ | `_build_system_prompt_ai()`, `_execute_decision()`, `process_with_ai_routing()` |
| **OrderAgent** | ✅ | `_build_system_prompt_ai()`, `_execute_decision_ai()`, `process_with_ai()` |
| **ValidationAgent** | ✅ | `_build_system_prompt_ai()`, `_execute_decision_ai()`, `process_with_ai()` |
| **PaymentAgent** | ⏳ | Pendente - usar como referência OrderAgent |
| **AttendanceAgent** | ⏳ | Pendente - mais simples (LLM responde diretamente) |

---

## 🎯 O Que Foi Implementado

### **Antes (Sistema Antigo)**
```python
def _detect_intent(self, message: str) -> str:
    """IF/ELSE com listas de palavras"""
    if "oi" in message or "olá" in message:
        return "greeting"
    if "produto" in message or "preço" in message:
        return "product_inquiry"
    # ... 30 linhas de IF/ELSE
```

### **Depois (Sistema Novo - IA Real)**
```python
async def process_with_ai_routing(self, message, context, db):
    """LLM decide roteamento"""
    system_prompt = self._build_system_prompt_ai(context, db)
    response = await self._call_llm([
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Mensagem: {message}")
    ])
    decision = self._parse_llm_response(response)
    return await self._execute_decision(decision, context, db, message)
```

---

## 🚀 Como Ativar o Novo Sistema

### **Opção 1: Ativar Apenas MasterAgent (Recomendado para Teste)**

Edite `backend/app/api/v1/webhook.py`:

```python
# Encontre o método que chama o MasterAgent
# Troque:
response = await master_agent.process(message, context, db)

# Por:
response = await master_agent.process_with_ai_routing(message, context, db)
```

### **Opção 2: Ativar Agentes Individuais**

No MasterAgent, após decidir qual agente chamar, use os novos métodos:

```python
# Em _execute_decision() do MasterAgent
if agente_nome == "OrderAgent":
    agent = OrderAgent()
    # Trocar:
    # return await agent.process(message_text, context)
    # Por:
    from app.database.base import get_db
    db = next(get_db())
    return await agent.process_with_ai(message_text, context, db)

elif agente_nome == "ValidationAgent":
    agent = ValidationAgent()
    from app.database.base import get_db
    db = next(get_db())
    return await agent.process_with_ai(message_text, context, db)
```

### **Opção 3: Sistema Híbrido (A/B Test)**

Criar flag de controle:

```python
# backend/app/core/config.py
USE_AI_AGENTS = os.getenv("USE_AI_AGENTS", "false").lower() == "true"

# backend/app/agents/master.py
if settings.USE_AI_AGENTS:
    return await self.process_with_ai_routing(message, context, db)
else:
    return await self.process(message, context, db)  # Sistema antigo
```

Adicionar no `.env`:
```bash
USE_AI_AGENTS=true
```

---

## 🧪 Como Testar

### **Teste 1: Roteamento Inteligente**
```
Cliente: "pode seguir"

Contexto: Após confirmar endereço
Esperado: MasterAgent → PaymentAgent (NÃO adiciona produto)
```

### **Teste 2: Variações Linguísticas**
```
Cliente: "beleza" (confirmando)
Cliente: "só isso" (finalizando)
Cliente: "morada 15" (endereço número 15)

Esperado: Sistema entende todas variações naturalmente
```

### **Teste 3: Fluxo Completo**
```
1. "oi" → AttendanceAgent saúda
2. "produtos" → AttendanceAgent lista
3. "quero o 1" → OrderAgent adiciona
4. "finalizar" → OrderAgent NÃO adiciona produto, pede endereço
5. "Rua ABC 123 Centro" → ValidationAgent valida
6. "pode seguir" → PaymentAgent (NÃO adiciona produto!)
7. "pix" → PaymentAgent finaliza
```

---

## 📈 Benefícios do Novo Sistema

### **Redução de Código**
- ❌ **Antes:** ~800 linhas de IF/ELSE
- ✅ **Depois:** ~300 linhas de prompts + lógica de execução
- 🎯 **Redução:** 62% menos código

### **Manutenção**
- ❌ **Antes:** Adicionar variação = modificar código + testar + deploy
- ✅ **Depois:** Adicionar variação = ajustar prompt (5 minutos)

### **Generalização**
- ❌ **Antes:** "pode seguir" não reconhecido
- ✅ **Depois:** LLM entende contexto automaticamente

### **Custo de API**
- Pedidos/mês: 1000
- Tokens/pedido: ~2600
- Custo/pedido: $0.00065
- **Total/mês: ~$0.65** (irrelevante!)

---

## 🔧 Próximos Passos

### **Para Completar a Implementação:**

1. **Implementar PaymentAgent.process_with_ai()**
   - Copiar estrutura do OrderAgent
   - System prompt com formas de pagamento aceitas
   - Detectar PIX, dinheiro, cartão

2. **Implementar AttendanceAgent.process_with_ai()**
   - Mais simples: LLM responde diretamente
   - System prompt com informações da empresa
   - Listar produtos quando solicitado

3. **Atualizar Endpoint Principal**
   - Modificar webhook para chamar `process_with_ai_routing()`
   - Adicionar flag de controle (A/B test)

4. **Testes Integrados**
   - Testar fluxo completo
   - Validar custos de API
   - Medir performance (tempo de resposta)

5. **Monitoramento**
   - Logs estruturados com decisões do LLM
   - Métricas de custo por pedido
   - Taxa de sucesso por agente

---

## 🆘 Troubleshooting

### **Problema: "LLM não retorna JSON válido"**
**Solução:** Método `_parse_llm_response()` já trata isso. Tenta extrair JSON de:
1. Resposta direta
2. Entre ```json e ```
3. Qualquer bloco { ... }

### **Problema: "Roteamento incorreto"**
**Solução:** Revisar system prompt do MasterAgent. Adicionar mais exemplos de casos difíceis.

### **Problema: "Custo muito alto"**
**Solução:**
- Usar `gpt-4o-mini` (mais barato)
- Reduzir histórico (de 10 para 5 mensagens)
- Cache de respostas comuns

---

## 📞 Suporte

Para dúvidas ou problemas:
1. Verificar logs: `docker-compose logs -f backend`
2. Procurar por `🤖`, `🛒`, `📍` nos logs (indicam decisões dos agentes)
3. Revisar este documento

---

**Última atualização:** 2025-10-28
**Versão:** 1.0 - Implementação Inicial
**Branch:** `feature/real-ai-agents`
**Commits:** 5 (base, master, order, validation, docs)
