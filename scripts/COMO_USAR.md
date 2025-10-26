# 🚀 Como Usar os Scripts de Teste

Guia rápido para começar a testar os agentes.

---

## ⚡ Início Rápido

### 1. Abra o terminal na raiz do projeto
```bash
cd C:\Phyton-Projetos\BotGas
```

### 2. Execute o chat interativo
```bash
python scripts/test_chat.py
```

### 3. Converse com o bot!
```
Você: Olá
Bot: Olá! Seja bem-vindo...

Você: Quero comprar uma botija
Bot: Claro! Temos os seguintes produtos...

Você: sair
```

---

## 📋 Exemplos de Conversas

### Exemplo 1: Fluxo Completo de Pedido
```bash
python scripts/test_chat.py
```

```
Você: Olá, boa tarde
Bot: Olá! Boa tarde...

Você: Quero comprar uma botija P13
Bot: Ótimo! Para confirmar seu pedido...

Você: Meu endereço é Rua das Flores, 123, Centro, Uberlândia
Bot: Perfeito! Validando seu endereço...

Você: Vou pagar no PIX
Bot: Ótima escolha...
```

### Exemplo 2: Consulta de Informações
```
Você: Quanto custa a botija?
Bot: Temos os seguintes preços...

Você: Qual o horário de funcionamento?
Bot: Funcionamos de segunda...

Você: Vocês entregam no bairro X?
Bot: Para verificar se atendemos...
```

---

## 🧪 Testes Automatizados

### Opção 1: Testes Rápidos
Para executar cenários básicos:

```bash
python scripts/test_prompts.py
```

**Saída esperada:**
```
🧪 BOTGAS - TESTES AUTOMATIZADOS DE AGENTES

📋 Cenário 1/6: Saudação Inicial
💬 Mensagem: "Olá"
🤖 Resposta (attendance): Olá! Seja bem-vindo...

📊 RESUMO DOS TESTES
✅ Testes bem-sucedidos: 12/12
```

### Opção 2: Análise Completa de Performance ⭐ RECOMENDADO
Para análise detalhada de cada agente com scoring:

```bash
python scripts/test_agent_analysis.py
```

**Saída esperada:**
```
🔍 ANÁLISE DE DESEMPENHO DOS AGENTES

==================== AttendanceAgent ====================
📊 PERFORMANCE GERAL: EXCELENTE ✅
🎯 Score Final: 85.3%
✅ Testes Bem-sucedidos: 7/7

[Teste 1/7] Peso: 10%
💬 Mensagem: "Olá"
🤖 Agente Detectado: attendance
📈 Score: 90.0%
💡 Resposta: Olá! Seja bem-vindo...
   📏 Tamanho: 145 caracteres
   😊 Contém emojis: Sim

==================== RESUMO GERAL ====================
🏆 RANKING DE PERFORMANCE:
   1. AttendanceAgent: 85.3% - EXCELENTE ✅
   2. PaymentAgent: 78.5% - BOM 👍
   3. OrderAgent: 72.1% - BOM 👍
   4. ValidationAgent: 65.0% - BOM 👍

📈 ESTATÍSTICAS GERAIS:
   • Total de testes: 18
   • Testes bem-sucedidos: 17/18 (94.4%)
   • Score médio geral: 75.2%

💡 RECOMENDAÇÕES:
   ✅ Agentes com excelente performance:
      - AttendanceAgent (85.3%)

💾 Relatório salvo em: scripts/agent_analysis_20251007_180530.json
```

**Este script é ideal para:**
- Identificar qual agente precisa de melhorias
- Validar mudanças nos prompts
- Gerar relatórios de qualidade
- Monitorar evolução ao longo do tempo

---

## 🐛 Resolução de Problemas

### Erro: "ModuleNotFoundError"
**Execute a partir da raiz:**
```bash
cd C:\Phyton-Projetos\BotGas
python scripts/test_chat.py
```

### Erro: "OpenAI API key not found"
**Verifique o .env:**
```bash
# .env (na raiz)
OPENAI_API_KEY=sk-proj-sua-chave-aqui
```

### Erro: "No module named 'langchain'"
**Instale as dependências:**
```bash
cd backend
pip install -r requirements.txt
```

---

## 💡 Dicas

### Modo Debug
Ative o modo debug para ver o contexto sendo atualizado:
```bash
# No terminal (Windows)
set DEBUG=true
python scripts/test_chat.py

# No terminal (Linux/Mac)
DEBUG=true python scripts/test_chat.py
```

### Resetar Conversa
Durante o chat, digite:
- `limpar` ou `clear` - Reseta a conversa
- `sair` ou `exit` - Encerra o chat

### Testar Agente Específico
Para testar um agente específico, edite `test_prompts.py` e adicione novos cenários na lista `TEST_SCENARIOS`.

---

## 📚 Próximos Passos

1. ✅ Teste o chat interativo
2. ✅ Execute os testes automatizados
3. ✅ Ajuste os prompts dos agentes conforme necessário
4. ✅ Teste via WhatsApp real
5. ✅ Deploy para produção

---

## 🤝 Precisa de Ajuda?

Consulte:
- [README.md](./README.md) - Documentação completa
- `backend/app/agents/` - Código dos agentes
- `.env` - Configurações

Boa sorte com os testes! 🚀
