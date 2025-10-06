# 🧪 Roteiro de Testes - Sistema de Agentes BotGas

## Objetivo
Testar todos os fluxos de conversa do sistema de agentes AI e identificar pontos de falha.

---

## ✅ Como Testar

1. Envie cada mensagem pelo WhatsApp
2. Aguarde a resposta do bot
3. Anote o resultado (✅ funcionou / ❌ falhou / ⚠️ comportamento estranho)
4. No dashboard, verifique se a conversa aparece corretamente

---

## 📋 Casos de Teste

### 1. Saudação e Menu Inicial
**Objetivo:** Verificar se o bot responde adequadamente a saudações

| Mensagem | Resposta Esperada | Status |
|----------|-------------------|--------|
| "Oi" | Menu com opções (produtos, pedidos, atendente) | ⬜ |
| "Olá" | Menu com opções | ⬜ |
| "Bom dia" | Saudação + menu | ⬜ |
| "Boa tarde" | Saudação + menu | ⬜ |
| "Alô" | Menu com opções | ⬜ |

**Agente responsável:** AttendanceAgent
**Intent:** greeting

---

### 2. Consulta de Produtos
**Objetivo:** Verificar se o bot lista produtos corretamente

| Mensagem | Resposta Esperada | Status |
|----------|-------------------|--------|
| "Quais produtos?" | Lista com produtos e preços | ⬜ |
| "Preços" | Lista com produtos e preços | ⬜ |
| "Quanto custa?" | Lista com produtos e preços | ⬜ |
| "Cardápio" | Lista com produtos e preços | ⬜ |
| "O que vocês vendem?" | Lista com produtos | ⬜ |

**Agente responsável:** AttendanceAgent
**Intent:** product_inquiry

---

### 3. Início de Pedido
**Objetivo:** Verificar se o bot processa corretamente a intenção de fazer pedido

| Mensagem | Resposta Esperada | Status |
|----------|-------------------|--------|
| "Quero fazer um pedido" | Solicita qual produto ou mostra menu | ⬜ |
| "Quero 1 botijão" | Confirma produto e solicita endereço | ⬜ |
| "Uma botija por favor" | Confirma produto e solicita endereço | ⬜ |
| "Quero comprar gás" | Mostra opções de gás disponíveis | ⬜ |
| "Preciso de 2 botijões P13" | Confirma 2x P13 e solicita endereço | ⬜ |

**Agente responsável:** OrderAgent
**Intent:** make_order

---

### 4. Fornecimento de Endereço
**Objetivo:** Verificar se o bot valida e aceita endereços

| Mensagem | Resposta Esperada | Status |
|----------|-------------------|--------|
| "Rua das Flores, 123" | Confirma endereço e solicita complemento/bairro | ⬜ |
| "Av. Principal, 500 - Centro" | Confirma endereço completo | ⬜ |
| "Meu endereço é [endereço completo]" | Valida e confirma | ⬜ |
| "Não sei meu endereço" | Orienta como encontrar ou sugere atendente | ⬜ |

**Agente responsável:** ValidationAgent
**Intent:** provide_address
**Stage:** awaiting_address

---

### 5. Confirmação de Pedido
**Objetivo:** Verificar se o bot confirma corretamente o pedido completo

| Mensagem | Resposta Esperada | Status |
|----------|-------------------|--------|
| "Sim, pode confirmar" | Confirma pedido e mostra resumo | ⬜ |
| "Confirmar" | Confirma e avança para pagamento | ⬜ |
| "Não, cancelar" | Cancela pedido educadamente | ⬜ |
| "Quero mudar o endereço" | Permite alteração | ⬜ |

**Agente responsável:** OrderAgent
**Stage:** confirming_order

---

### 6. Fluxo de Pagamento
**Objetivo:** Verificar se o bot processa opções de pagamento

| Mensagem | Resposta Esperada | Status |
|----------|-------------------|--------|
| "Quero pagar com PIX" | Fornece dados PIX | ⬜ |
| "Vou pagar em dinheiro" | Confirma e pergunta se precisa troco | ⬜ |
| "Cartão" | Informa opções de cartão | ⬜ |
| "Preciso de troco" | Solicita valor do troco | ⬜ |

**Agente responsável:** PaymentAgent
**Intent:** payment
**Stage:** payment

---

### 7. Solicitação de Atendente Humano
**Objetivo:** Verificar se o bot detecta quando cliente pede atendente

| Mensagem | Resposta Esperada | Status |
|----------|-------------------|--------|
| "Quero falar com atendente" | Ativa intervenção humana | ⬜ |
| "Falar com uma pessoa" | Ativa intervenção humana | ⬜ |
| "Não estou entendendo" | Sugere atendente ou repete explicação | ⬜ |
| "Isso não é o que eu quero" | Sugere atendente | ⬜ |

**Agente responsável:** MasterAgent
**Funcionalidade:** Human Intervention

---

### 8. Mensagens de Áudio (Transcrição)
**Objetivo:** Verificar se o bot processa áudios corretamente

| Tipo de Áudio | Resposta Esperada | Status |
|---------------|-------------------|--------|
| Áudio com "Oi" | Responde como se fosse texto | ⬜ |
| Áudio com pedido | Processa pedido normalmente | ⬜ |
| Áudio longo | Transcreve e processa | ⬜ |
| Áudio com ruído | Tenta transcrever ou informa erro | ⬜ |

**Funcionalidade:** Audio Processor + MasterAgent

---

### 9. Perguntas Gerais
**Objetivo:** Verificar se o bot responde dúvidas variadas

| Mensagem | Resposta Esperada | Status |
|----------|-------------------|--------|
| "Qual seu horário de funcionamento?" | Informa horários | ⬜ |
| "Onde vocês ficam?" | Informa endereço da empresa | ⬜ |
| "Qual o telefone?" | Fornece telefone da empresa | ⬜ |
| "Fazem entrega?" | Confirma que sim e explica processo | ⬜ |

**Agente responsável:** AttendanceAgent
**Intent:** general / help

---

### 10. Fluxo Completo (End-to-End)
**Objetivo:** Testar o fluxo completo de um pedido

**Sequência de mensagens:**
1. "Oi" → Aguarda menu
2. "Quero fazer um pedido" → Aguarda opções
3. "1 botijão P13" → Aguarda solicitação de endereço
4. "Rua Exemplo, 100 - Centro" → Aguarda confirmação
5. "Sim, confirmar" → Aguarda opções de pagamento
6. "PIX" → Aguarda dados PIX e confirmação final

**Status:** ⬜

---

## 📊 Como Reportar Problemas

Quando encontrar um erro, anote:

1. **Mensagem enviada:** [texto exato]
2. **Resposta recebida:** [texto ou "erro: ..." ]
3. **Resposta esperada:** [o que deveria acontecer]
4. **Erro nos logs:** [se houver traceback no terminal]
5. **Conversa no dashboard:** [aparece corretamente? sim/não]

---

## 🔍 Verificações no Dashboard

Durante os testes, verifique:

- [ ] Mensagens aparecem em tempo real (3 segundos)
- [ ] Contador de "Conversas Ativas" aumenta
- [ ] Histórico mostra role correto (user/assistant)
- [ ] Intent é registrado nas mensagens do bot
- [ ] Context é atualizado conforme conversa evolui

---

## 🐛 Erros Conhecidos Corrigidos

### ✅ Erro: `AttributeError: 'NoneType' object has no attribute 'get'`
- **Onde:** AttendanceAgent ao acessar `tenant.address`
- **Causa:** Tenant sem endereço cadastrado
- **Correção:** Verificação segura antes de acessar address.get()
- **Status:** CORRIGIDO

---

## 📝 Próximos Passos Após Testes

Depois de executar todos os testes:

1. Identificar quais agentes falharam
2. Verificar logs para erros específicos
3. Corrigir código dos agentes problemáticos
4. Adicionar tratamento de erros onde necessário
5. Melhorar prompts dos agentes para respostas melhores

---

## 🚀 Comandos Úteis

```bash
# Ver logs do backend em tempo real
docker logs -f botgas-backend-1

# Ver apenas erros de agentes
docker logs botgas-backend-1 2>&1 | grep -A 10 "Error processing message"

# Ver últimas mensagens no PostgreSQL
docker exec botgas-postgres-1 psql -U gasbot -d gasbot -c \
  "SELECT jsonb_pretty(messages::jsonb) FROM conversations
   WHERE id = 'CONVERSATION_ID';"

# Reiniciar backend após correções
docker restart botgas-backend-1
```

---

**Data de criação:** 2025-10-06
**Versão:** 1.0
**Última atualização:** Correção do AttendanceAgent (tenant.address None)
