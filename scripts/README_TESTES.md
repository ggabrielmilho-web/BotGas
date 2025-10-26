# 🧪 Scripts de Teste dos Agentes - BotGas

Este diretório contém scripts para testar o desempenho e funcionamento dos agentes de IA do BotGas.

---

## 📁 Arquivos Disponíveis

### 1. `test_agents_via_evolution.py` ⭐ **RECOMENDADO**

**Script que envia mensagens REAIS via Evolution API para testar os agentes.**

✅ **Vantagens:**
- Testa o fluxo completo real (Evolution → Webhook → Agentes → WhatsApp)
- Não precisa de dependências Python locais
- Você pode ver as respostas diretamente no WhatsApp
- Valida todo o sistema de ponta a ponta

⚠️ **Atenção:**
- Envia mensagens REAIS para o WhatsApp
- Requer confirmação antes de executar
- Aguarda 8 segundos entre cada mensagem

**Como usar:**
```bash
python scripts/test_agents_via_evolution.py
```

O script vai:
1. Pedir confirmação (digite "SIM" para continuar)
2. Enviar 9 mensagens de teste via Evolution API
3. Aguardar 8 segundos entre cada mensagem
4. Gerar relatório JSON com os resultados
5. Mostrar resumo no terminal

**Depois do teste:**
- Verifique as respostas no WhatsApp (número `5534996554613`)
- Acesse o Dashboard: http://localhost:3000/dashboard
- Veja o relatório JSON gerado em `scripts/evolution_test_YYYYMMDD_HHMMSS.json`

---

### 2. `test_chat.py`

**Chat interativo no terminal para conversar diretamente com os agentes.**

⚠️ **Requer:**
- Instalação local de todas as dependências Python do backend
- Configuração do ambiente Python

**Como usar:**
```bash
# Instalar dependências (uma vez)
pip install -r backend/requirements.txt

# Executar chat
python scripts/test_chat.py
```

Permite conversar no terminal como se fosse WhatsApp.

---

### 3. `test_prompts.py`

**Testes automatizados dos prompts dos agentes.**

⚠️ **Requer:**
- Instalação local de todas as dependências Python do backend

**Como usar:**
```bash
python scripts/test_prompts.py
```

Executa testes predefinidos e mostra as respostas de cada agente.

---

### 4. `test_agent_analysis.py`

**Análise avançada com scoring dos agentes.**

⚠️ **Requer:**
- Instalação local de todas as dependências Python do backend
- Python < 3.13 (devido a dependências de áudio)

**Como usar:**
```bash
python scripts/test_agent_analysis.py
```

Gera relatório com pontuação de desempenho de cada agente.

---

### 5. `test_agent_simple.py`

**Script simplificado que tenta simular webhooks (NÃO RECOMENDADO).**

❌ **Problemas:**
- Não funciona corretamente com a estrutura atual
- Requer configuração complexa de tenant/instância
- Não valida o fluxo real

**Status:** Obsoleto - Use `test_agents_via_evolution.py` ao invés.

---

## 🎯 Qual Script Usar?

### Para testes rápidos e completos:
→ **`test_agents_via_evolution.py`** ⭐

### Para desenvolver/debugar prompts:
→ **`test_chat.py`** (requer setup local)

### Para análise de performance:
→ **`test_agent_analysis.py`** (requer setup local)

---

## 📊 Exemplo de Uso Completo

```bash
# 1. Executar testes via Evolution API
python scripts/test_agents_via_evolution.py

# 2. Verificar respostas no WhatsApp (5534996554613)

# 3. Acessar Dashboard para ver conversas
# http://localhost:3000/dashboard

# 4. Analisar relatório JSON gerado
cat scripts/evolution_test_20251007_184530.json
```

---

## 📝 Formato dos Testes

Todos os scripts testam as seguintes categorias:

### Saudações e Atendimento
- "Olá"
- "Boa tarde"
- "Quanto custa a botija de gás?"
- "Quais produtos vocês tem?"

### Pedidos
- "Quero comprar uma botija"
- "Preciso de um P13"

### Endereço
- "Rua das Flores, 123, Centro, Uberlândia"

### Pagamento
- "Aceita PIX?"
- "Posso pagar no cartão?"

---

## 🔧 Configuração

### Evolution API (test_agents_via_evolution.py)
```python
EVOLUTION_API_URL = "https://api.carvalhoia.com"
EVOLUTION_API_KEY = "03fd4f2fc18afc835d3e83d343eae714"
INSTANCE_NAME = "carvalhoia"
TEST_PHONE = "5534996554613"
```

### Backend Local (outros scripts)
```python
BACKEND_URL = "http://localhost:8000"
OPENAI_API_KEY = "sua-chave-aqui"  # Do .env do backend
```

---

## 📦 Relatórios Gerados

Cada execução gera um arquivo JSON com timestamp:

```json
{
  "timestamp": "20251007_184530",
  "phone": "5534996554613",
  "instance": "carvalhoia",
  "total_tests": 9,
  "sent": 9,
  "failed": 0,
  "results": [
    {
      "category": "Saudações e Atendimento",
      "message": "Olá",
      "sent": true,
      "timestamp": "2025-10-07T18:45:30.123456"
    }
  ]
}
```

---

## ❓ Troubleshooting

### Erro: Evolution API não responde
- Verifique se a API está online: https://api.carvalhoia.com
- Confirme a API key está correta
- Verifique se a instância "carvalhoia" está ativa

### Erro: ModuleNotFoundError
- Instale as dependências: `pip install -r backend/requirements.txt`
- Ou use o script recomendado que não precisa de dependências

### Erro: WhatsApp não recebe mensagens
- Verifique se o número de teste está correto
- Confirme se o WhatsApp está conectado
- Veja logs do backend: `docker logs -f botgas-backend-1`

---

## 🚀 Próximos Passos

Após executar os testes:

1. **Analise as respostas** no WhatsApp
2. **Verifique o Dashboard** para ver intents detectadas
3. **Ajuste os prompts** dos agentes se necessário
4. **Execute novamente** para validar melhorias

---

**Dúvidas?** Consulte a documentação completa em `COMO_USAR.md`
