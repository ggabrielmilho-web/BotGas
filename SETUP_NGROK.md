# 🌐 Setup Ngrok para Testes Locais

## 📝 O que é Ngrok?

Ngrok cria um túnel público (HTTPS) para seu localhost, permitindo que o Evolution API (na VPS) envie webhooks para seu backend local.

---

## 🚀 Como usar

### 1. Instalar Ngrok

**Windows:**
```bash
# Download: https://ngrok.com/download
# Extrair o executável para uma pasta (ex: C:\ngrok)
```

**Linux/Mac:**
```bash
brew install ngrok
# ou
snap install ngrok
```

### 2. Autenticar com seu token

```bash
ngrok config add-authtoken 33Tdc2ajy5OdcSIfqcaAS3fsE4p_3BcUoPszPQnRDVxr2DMJh
```

### 3. Iniciar túnel

**Opção A: Comando simples**
```bash
ngrok http 8000
```

**Opção B: Usando arquivo de config (recomendado)**
```bash
# Já está configurado no arquivo ngrok.yml
ngrok start gasbot
```

### 4. Copiar URL gerada

Ngrok vai mostrar algo assim:
```
Session Status                online
Account                       Seu Nome (Plan: Free)
Version                       3.x.x
Region                        United States (us)
Latency                       50ms
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://abc123.ngrok-free.app -> http://localhost:8000
```

**Copie a URL:** `https://abc123.ngrok-free.app`

### 5. Atualizar .env

```env
# backend/.env
WEBHOOK_URL=https://abc123.ngrok-free.app/api/v1/webhook/evolution
```

### 6. Reiniciar backend

```bash
# Ctrl+C no backend atual
# Rodar novamente:
cd backend
uvicorn app.main:app --reload
```

---

## 🔍 Ver webhooks em tempo real

Acesse: **http://localhost:4040**

Interface web do ngrok mostra:
- ✅ Todas requisições HTTP
- ✅ Headers completos
- ✅ Payloads JSON
- ✅ Tempo de resposta
- ✅ Status codes

Muito útil para debug!

---

## ⚠️ Importante

### URL muda toda vez
Na versão free, a URL do ngrok muda quando você reinicia.

**Solução:**
- Atualize o `.env` sempre que iniciar ngrok
- Ou assine o plano pago para URL fixa

### Sempre rode ngrok antes de testar webhook
```bash
# Ordem correta:
1. Inicia backend (porta 8000)
2. Inicia ngrok (túnel para 8000)
3. Atualiza .env com nova URL
4. Reinicia backend
5. Testa WhatsApp
```

---

## 🧪 Testar se está funcionando

### 1. Teste manual do túnel
```bash
# Em outro terminal:
curl https://sua-url.ngrok-free.app/health
```

Deve retornar:
```json
{"status": "healthy", "version": "1.0.0"}
```

### 2. Conectar WhatsApp
1. `GET /api/v1/whatsapp/qr`
2. Escanear QR Code
3. Enviar mensagem para o número conectado
4. Ver webhook chegando no ngrok (localhost:4040)
5. Ver mensagem salva no banco

---

## 🐛 Troubleshooting

### Ngrok não inicia
```bash
# Verificar se porta 8000 está livre
netstat -ano | findstr :8000

# Matar processo se necessário
taskkill /PID <PID> /F
```

### Webhook não chega
1. Verificar ngrok rodando: `http://localhost:4040`
2. Verificar .env atualizado
3. Verificar backend rodando
4. Testar URL manualmente com curl

### "Tunnel not found"
Você precisa autenticar primeiro:
```bash
ngrok config add-authtoken 33Tdc2ajy5OdcSIfqcaAS3fsE4p_3BcUoPszPQnRDVxr2DMJh
```

---

## 💡 Dicas

1. **Mantenha ngrok aberto** enquanto testa
2. **Use a interface web** (localhost:4040) para debug
3. **Copie/cole URLs** - evite erros de digitação
4. **Reinicie backend** após mudar WEBHOOK_URL

---

## 🎯 Workflow completo

```bash
# Terminal 1: Backend
cd c:\Phyton-Projetos\BotGas\backend
uvicorn app.main:app --reload

# Terminal 2: Ngrok
cd c:\Phyton-Projetos\BotGas
ngrok start gasbot

# 1. Copiar URL do ngrok
# 2. Atualizar backend/.env
# 3. Ctrl+C no backend (Terminal 1)
# 4. Rodar backend novamente
# 5. Testar WhatsApp

# Terminal 3: Ver logs ngrok
# Abrir navegador: http://localhost:4040
```

---

## 📚 Referências

- [Ngrok Docs](https://ngrok.com/docs)
- [Ngrok Dashboard](https://dashboard.ngrok.com/)
- [Evolution API Webhooks](https://doc.evolution-api.com/v2/webhooks)
