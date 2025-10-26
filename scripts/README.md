# Scripts de Teste - BotGas Agents

## 🎯 Objetivo

Testar os agentes de IA (GPT-4) do BotGas **sem usar WhatsApp/Evolution API**, diretamente via terminal.

Útil para:
- Testar mudanças nos prompts dos agentes
- Validar fluxo de conversação
- Debug de respostas dos agentes
- Desenvolver novos agentes

---

## 📋 Scripts Disponíveis

### 1. `test_chat.py` - Chat Interativo
Conversa em tempo real com o MasterAgent via terminal.

**Como usar:**
```bash
cd scripts
python test_chat.py
```

**O que faz:**
- Inicia conversa interativa no terminal
- Você digita mensagens e recebe respostas do GPT-4
- Mantém histórico da conversa
- Mostra qual agente está respondendo
- `Ctrl+C` ou digite "sair" para encerrar

**Exemplo de uso:**
```
Você: Olá, quero comprar uma botija de gás
Bot (AttendanceAgent): Olá! Claro, posso te ajudar...
Você: Quanto custa?
Bot (AttendanceAgent): A botija P13 custa R$ 95,00...
```

---

### 2. `test_prompts.py` - Testes Automatizados
Executa cenários pré-definidos para testar todos os agentes.

**Como usar:**
```bash
cd scripts
python test_prompts.py
```

**Cenários testados:**
1. Saudação inicial
2. Consulta de produtos e preços
3. Pedido de produto
4. Validação de endereço
5. Finalização de pedido
6. Pergunta sobre horário de funcionamento

**Saída:**
Mostra as respostas de cada agente para cada cenário.

---

## ⚙️ Requisitos

### 1. OpenAI API Key
Os scripts precisam da chave da API OpenAI configurada:

```bash
# Certifique-se que o .env na raiz tem:
OPENAI_API_KEY=sk-proj-...
```

### 2. Python 3.11+
Os scripts rodam **fora do Docker**, diretamente no seu Python local.

### 3. Dependências Python
Instale as mesmas dependências do backend:

```bash
cd backend
pip install -r requirements.txt
```

Ou instale apenas as necessárias:
```bash
pip install openai langchain sqlalchemy python-dotenv
```

---

## 🔧 Como Funcionam

### Contexto Simulado
Os scripts criam um `AgentContext` em memória com:
- `tenant_id`: UUID fake da distribuidora
- `customer_phone`: Número de telefone de teste
- `conversation_id`: ID da conversa simulada
- `session_data`: Contexto vazio (será preenchido durante conversa)
- `message_history`: Histórico de mensagens

### Sem Banco de Dados
- **Não salvam** nada no PostgreSQL
- **Não enviam** mensagens via WhatsApp
- **Não chamam** Evolution API
- Apenas testam a lógica dos agentes e GPT-4

### Tenant Simulado
Os scripts usam dados mock de uma distribuidora:
```python
tenant_mock = {
    "company_name": "Distribuidora Teste",
    "phone": "5534999999999",
    "address": {"street": "Rua Teste, 123", "city": "Uberlândia"}
}
```

---

## ⚠️ Notas Importantes

### O que os scripts NÃO fazem:
- ❌ Não alteram código dos agentes
- ❌ Não modificam banco de dados
- ❌ Não enviam mensagens reais
- ❌ Não afetam o sistema em produção
- ❌ Não criam registros de conversas

### O que os scripts FAZEM:
- ✅ Consomem créditos da OpenAI API (custo por token)
- ✅ Imprimem logs no terminal
- ✅ Testam prompts e respostas dos agentes
- ✅ Validam fluxo de conversação

### Segurança:
- **Pode deletar a pasta `scripts/`** a qualquer momento sem afetar o sistema
- Nenhuma dependência no código principal
- Scripts 100% isolados

---

## 📝 Exemplos de Testes

### Teste de Fluxo Completo
```bash
python test_chat.py

# Simule um cliente:
> Olá
> Quero comprar uma botija
> Meu endereço é Rua A, 100, Centro, Uberlândia
> Pode entregar agora
> Vou pagar no PIX
```

### Teste de Validação de Endereço
```bash
python test_prompts.py

# Verifica se ValidationAgent está validando corretamente
```

---

## 🐛 Troubleshooting

### Erro: "ModuleNotFoundError: No module named 'app'"
**Solução:** Execute os scripts a partir da raiz do projeto:
```bash
cd C:\Phyton-Projetos\BotGas
python scripts/test_chat.py
```

### Erro: "OpenAI API key not found"
**Solução:** Configure a chave no `.env` da raiz:
```bash
OPENAI_API_KEY=sk-proj-sua-chave-aqui
```

### Erro: "No module named 'langchain'"
**Solução:** Instale as dependências:
```bash
pip install -r backend/requirements.txt
```

---

## 📚 Próximos Passos

Depois de testar os agentes aqui, você pode:
1. Ajustar os prompts em `backend/app/agents/`
2. Testar novamente com os scripts
3. Quando estiver satisfeito, testar via WhatsApp real
4. Deployar para produção

---

## 📞 Dúvidas?

Consulte a documentação dos agentes em:
- `backend/app/agents/README.md`
- `backend/app/agents/master.py` (orquestrador)
- Cada agente individual (attendance.py, validation.py, etc)
