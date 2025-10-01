# 📝 SESSÃO 4 - INTEGRAÇÃO EVOLUTION API + WHATSAPP + ÁUDIO

## ✅ STATUS: COMPLETO

## 📁 ARQUIVOS CRIADOS

### 1. backend/.env
**Arquivo de configuração com credenciais**
- Evolution API URL: `https://api.carvalhoia.com`
- Evolution API Key: `03fd4f2fc18afc835d3e83d343eae714`
- OpenAI API Key: Configurada para Whisper
- ⚠️ **IMPORTANTE:** Arquivo protegido no .gitignore

### 2. backend/.env.example
**Template de configuração**
- Exemplo para outros desenvolvedores
- Sem credenciais reais

### 3. backend/.gitignore
**Proteção de arquivos sensíveis**
- .env protegido
- Credenciais nunca vão pro GitHub

---

### 4. backend/app/services/evolution.py
**Serviço de integração com Evolution API v2.3.1**

**Métodos principais:**

#### Gerenciamento de Instâncias
- `create_instance()` - Cria instância WhatsApp
- `get_instance_status()` - Status da conexão
- `get_qr_code()` - Gera QR Code para conexão
- `logout_instance()` - Desconecta WhatsApp
- `delete_instance()` - Remove instância completamente

#### Envio de Mensagens
- `send_text_message()` - Envia texto
- `send_audio_message()` - Envia áudio
- `send_media_message()` - Envia imagem/vídeo/documento
- `download_media()` - Baixa mídia de mensagem

#### Funcionalidades Extras
- `set_presence()` - Define status (online, digitando, gravando)
- `mark_message_read()` - Marca mensagem como lida
- `get_profile_picture()` - Busca foto de perfil

**Features:**
- Cliente HTTP async com httpx
- Tratamento de erros completo
- Logs informativos
- Suporte completo Evolution API v2

---

### 5. backend/app/services/audio_processor.py
**Processador de áudio com OpenAI Whisper**

**Métodos principais:**
- `download_audio()` - Baixa áudio de URL
- `transcribe_audio()` - Transcreve com Whisper
- `process_whatsapp_audio()` - Pipeline completo (download + transcrição)
- `process_base64_audio()` - Processa áudio base64

**Features especiais:**
- ✅ Transcrição em português (language="pt")
- ✅ Prompt contextual para gás/água
- ✅ Limite de 25MB (limite do Whisper)
- ✅ Formato verbose_json com duração
- ✅ Tratamento de erros gracioso
- ✅ Arquivos temporários com limpeza automática

**Exemplo de resultado:**
```json
{
  "text": "Boa tarde, quero 2 botijões de 13kg",
  "language": "pt",
  "duration": 3.5,
  "success": true
}
```

---

### 6. backend/app/api/whatsapp.py
**Endpoints de WhatsApp**

#### GET /api/v1/whatsapp/qr
Gera QR Code para conectar WhatsApp
- Cria instância se não existir
- Retorna QR Code em base64
- Formato de instância: `tenant_{uuid}`

**Response:**
```json
{
  "qr_code": "data:image/png;base64,...",
  "instance_name": "tenant_abc-123",
  "status": "waiting_scan"
}
```

#### GET /api/v1/whatsapp/status
Verifica status da conexão
- Retorna estado da conexão
- Atualiza status no banco
- Mostra número conectado

**Response:**
```json
{
  "connected": true,
  "instance_name": "tenant_abc-123",
  "state": "open",
  "phone_number": "5511999999999"
}
```

#### POST /api/v1/whatsapp/send
Envia mensagem de texto
- Valida se WhatsApp conectado
- Retorna message_id

**Request:**
```json
{
  "phone_number": "5511999999999",
  "message": "Olá! Seu pedido foi confirmado."
}
```

#### POST /api/v1/whatsapp/disconnect
Desconecta WhatsApp
- Faz logout da instância
- Atualiza status no banco

#### DELETE /api/v1/whatsapp/instance
Deleta instância completamente
- Remove tudo do Evolution
- ⚠️ Ação irreversível

---

### 7. backend/app/webhooks/whatsapp.py
**Webhook para receber mensagens do Evolution**

#### POST /api/v1/webhook/evolution
Recebe todos eventos do Evolution API

**Eventos suportados:**

##### MESSAGES_UPSERT (Nova mensagem)
Processa mensagens recebidas:
- ✅ Texto simples
- ✅ Áudio (com transcrição automática via Whisper)
- ✅ Imagens/vídeos (log, processamento futuro)
- ✅ Ignora mensagens do próprio bot (fromMe)

**Fluxo de processamento:**
1. Recebe webhook do Evolution
2. Identifica tenant pela instância
3. Cria/busca cliente (Customer)
4. Cria/busca conversa (Conversation)
5. Verifica intervenção humana
6. Processa mensagem:
   - Texto → Salva direto
   - Áudio → Transcreve + Salva
7. Salva no banco com timestamp
8. TODO: Enviar para agentes IA (Sessão 5)

##### CONNECTION_UPDATE (Status de conexão)
Atualiza status de conexão no banco:
- `open` → conectado
- `close` → desconectado

##### QRCODE_UPDATED (QR Code atualizado)
Log de atualização de QR Code

**Helpers implementados:**
- `get_tenant_from_instance()` - Extrai tenant do nome da instância
- `get_or_create_customer()` - Cria cliente se não existir
- `get_or_create_conversation()` - Gerencia conversas
- `process_text_message()` - Processa texto
- `process_audio_message()` - Processa áudio

**Logs de webhook:**
Todos webhooks são salvos na tabela `webhook_logs` para debug.

---

### 8. backend/app/main.py (ATUALIZADO)
**Alterações:**
- Importado router `whatsapp`
- Importado router `whatsapp_webhook`
- Registrados ambos os routers

---

## 🔄 FLUXO COMPLETO DE MENSAGEM

```
1. CLIENTE ENVIA MENSAGEM NO WHATSAPP
   ↓
2. EVOLUTION API RECEBE
   ↓
3. EVOLUTION ENVIA WEBHOOK
   POST https://seu-gasbot.com/api/v1/webhook/evolution
   ↓
4. WEBHOOK HANDLER
   - Identifica tenant
   - Busca/cria customer
   - Busca/cria conversation
   - Verifica intervenção humana
   ↓
5. SE FOR TEXTO
   - Salva direto no banco
   ↓
6. SE FOR ÁUDIO
   - Baixa áudio do Evolution
   - Transcreve com Whisper
   - Salva transcrição + áudio_url
   ↓
7. TODO: ENVIAR PARA AGENTES IA
   (Sessão 5)
   ↓
8. BOT RESPONDE
   POST /api/v1/whatsapp/send
   ↓
9. EVOLUTION ENVIA NO WHATSAPP
```

---

## 🧪 COMO TESTAR

### 1. Conectar WhatsApp

```bash
# 1. Gerar QR Code
curl -X GET http://localhost:8000/api/v1/whatsapp/qr \
  -H "Authorization: Bearer {access_token}"

# Response terá o QR code em base64
# Cole no navegador: data:image/png;base64,{qr_code}
```

### 2. Verificar Status

```bash
curl -X GET http://localhost:8000/api/v1/whatsapp/status \
  -H "Authorization: Bearer {access_token}"
```

### 3. Enviar Mensagem de Teste

```bash
curl -X POST http://localhost:8000/api/v1/whatsapp/send \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "5511999999999",
    "message": "Olá! Teste do GasBot 🤖"
  }'
```

### 4. Testar Recebimento (manualmente)

1. Escaneie o QR Code com seu WhatsApp
2. Envie mensagem de texto para o número conectado
3. Envie mensagem de áudio
4. Verifique os logs:

```bash
# Ver logs do backend
docker logs gasbot-backend

# Verificar no banco
SELECT * FROM conversations ORDER BY started_at DESC LIMIT 1;
SELECT * FROM webhook_logs ORDER BY created_at DESC LIMIT 5;
```

---

## 🔐 CONFIGURAÇÃO DO WEBHOOK NA VPS

Quando subir na VPS, você precisará:

### 1. Atualizar .env em produção

```env
WEBHOOK_URL=https://gasbot.seudominio.com/api/v1/webhook/evolution
```

### 2. Configurar webhook no Evolution

Existem 2 formas:

**Opção A: Via criação de instância (automático)**
O webhook já é configurado quando cria a instância via código.

**Opção B: Via Evolution Manager (manual)**
1. Acesse: https://api.carvalhoia.com/manager
2. Vá em Settings → Webhooks
3. Configure:
   - URL: `https://gasbot.seudominio.com/api/v1/webhook/evolution`
   - Events: `MESSAGES_UPSERT`, `CONNECTION_UPDATE`, `QRCODE_UPDATED`

### 3. SSL/HTTPS obrigatório

Evolution API exige HTTPS para webhooks. Certifique-se que:
- Traefik está configurado com Let's Encrypt
- Certificado SSL válido
- Porta 443 aberta

---

## 📊 ESTRUTURA DAS MENSAGENS NO BANCO

### Conversation.messages (JSONB)

```json
[
  {
    "role": "user",
    "content": "Boa tarde, quero 2 botijões de 13kg",
    "timestamp": "2024-10-01T14:30:00",
    "type": "audio",
    "audio_url": "https://evolution.../media/abc123.ogg",
    "transcription_success": true,
    "duration": 3.5
  },
  {
    "role": "assistant",
    "content": "Olá! Entendi que você quer 2 botijões de 13kg...",
    "timestamp": "2024-10-01T14:30:05",
    "type": "text"
  }
]
```

---

## ⚙️ VARIÁVEIS DE AMBIENTE (COMPLETAS)

```env
# Database
DATABASE_URL=postgresql://gasbot:password@postgres:5432/gasbot
REDIS_URL=redis://redis:6379

# Evolution API
EVOLUTION_API_URL=https://api.carvalhoia.com
EVOLUTION_API_KEY=03fd4f2fc18afc835d3e83d343eae714

# OpenAI
OPENAI_API_KEY=sk-proj-...

# Security
JWT_SECRET_KEY=gasbot-super-secret-key-change-in-production-2024
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Google Maps (opcional)
GOOGLE_MAPS_API_KEY=

# App Config
WEBHOOK_URL=https://gasbot.seudominio.com/api/v1/webhook/evolution
TRIAL_DAYS=7
ADDRESS_CACHE_DAYS=30
ENVIRONMENT=production
```

---

## 🚀 PRÓXIMOS PASSOS (SESSÃO 5)

- [ ] Criar agentes LangChain/LangGraph
- [ ] Agente Mestre (orquestrador)
- [ ] Agente Atendimento
- [ ] Agente Validação de Endereço
- [ ] Agente Pedidos
- [ ] Agente Pagamento
- [ ] Sistema de intervenção humana (pause 5min)
- [ ] Integrar agentes com webhook

---

## ✅ CHECKLIST SESSÃO 4

- [x] Credenciais Evolution e OpenAI configuradas
- [x] .env protegido no .gitignore
- [x] Serviço Evolution API completo
- [x] Processador de áudio com Whisper
- [x] Endpoints WhatsApp (QR, status, send, disconnect)
- [x] Webhook para receber mensagens
- [x] Processamento de texto
- [x] Processamento de áudio com transcrição
- [x] Criação automática de customers
- [x] Gestão de conversations
- [x] Logs de webhooks
- [x] Atualização automática de status
- [x] Integração no main.py

---

## 📝 NOTAS IMPORTANTES

### 1. Formato de Instâncias
- Sempre use: `tenant_{uuid}`
- Exemplo: `tenant_550e8400-e29b-41d4-a716-446655440000`
- Isso garante isolamento multi-tenant

### 2. Números de Telefone
- Formato internacional obrigatório
- Exemplo: `5511999999999` (Brasil)
- Sem espaços, traços ou parênteses

### 3. Áudio
- Whisper suporta vários formatos (ogg, mp3, wav, etc)
- Limite: 25MB
- Transcrição em português (pt)
- Prompt contextual melhora precisão

### 4. Webhook
- HTTPS obrigatório em produção
- URL deve ser acessível publicamente
- Evolution envia POST para cada evento
- Eventos são processados de forma assíncrona

### 5. Intervenção Humana
- Sistema de pausa já está implementado
- Verificação em `conversation.human_intervention`
- Timer de 5min será implementado na Sessão 5

### 6. Segurança
- .env NUNCA vai pro GitHub
- API Key do Evolution é global
- Cada tenant tem instância separada
- Multi-tenant garantido pelo nome da instância

---

## 🐛 TROUBLESHOOTING

### Problema: QR Code não aparece
```bash
# Verificar se Evolution está acessível
curl https://api.carvalhoia.com

# Verificar logs
docker logs gasbot-backend
```

### Problema: Webhook não chega
```bash
# 1. Verificar webhook_logs
SELECT * FROM webhook_logs ORDER BY created_at DESC LIMIT 10;

# 2. Testar endpoint manualmente
curl -X POST http://localhost:8000/api/v1/webhook/evolution \
  -H "Content-Type: application/json" \
  -d '{"event": "test"}'

# 3. Verificar se URL é HTTPS (obrigatório)
```

### Problema: Áudio não transcreve
```bash
# 1. Verificar OpenAI Key
echo $OPENAI_API_KEY

# 2. Testar Whisper diretamente
# (código de teste em Python)

# 3. Verificar logs
grep "Transcription" logs/backend.log
```

### Problema: Mensagens duplicadas
- Evolution pode reenviar webhooks
- Implementar deduplicação por message_id (futuro)

---

## 📈 MÉTRICAS DE SUCESSO

- ✅ Conexão WhatsApp funcional
- ✅ QR Code gerado corretamente
- ✅ Mensagens de texto recebidas e salvas
- ✅ Áudios transcritos com sucesso
- ✅ Customers criados automaticamente
- ✅ Conversations gerenciadas
- ✅ Webhooks logados
- ✅ Status sincronizado

---

## 🎯 PRÓXIMA SESSÃO

**Sessão 5: Agentes LangChain**
- Criar sistema de agentes inteligentes
- Processar mensagens automaticamente
- Sistema de intervenção humana
- Contexto de conversa com Redis
- Orquestração com LangGraph
