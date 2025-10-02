# 🚀 COMO RODAR O GASBOT

## 📋 PRÉ-REQUISITOS

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+
- Docker (opcional, mas recomendado)

---

## 🐳 OPÇÃO 1: COM DOCKER (RECOMENDADO)

### 1. Clonar e configurar
```bash
cd c:\Phyton-Projetos\BotGas

# Copiar .env de exemplo
cp .env.example .env

# Editar .env com suas chaves
# - OPENAI_API_KEY
# - GOOGLE_MAPS_API_KEY
# - EVOLUTION_API_URL
# - EVOLUTION_API_KEY
# - JWT_SECRET_KEY
```

### 2. Iniciar todos os serviços
```bash
docker-compose up -d
```

Isso vai iniciar:
- PostgreSQL (porta 5432)
- Redis (porta 6379)
- Backend FastAPI (porta 8000)
- Frontend Next.js (porta 3000)
- Evolution API (porta 8080)

### 3. Rodar migrations
```bash
docker exec gasbot_backend alembic upgrade head
```

### 4. Acessar
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Evolution API**: http://localhost:8080

---

## 💻 OPÇÃO 2: MODO DESENVOLVIMENTO (SEM DOCKER)

### 1. PostgreSQL e Redis
```bash
# Instalar PostgreSQL
# Windows: https://www.postgresql.org/download/windows/
# Criar banco de dados
psql -U postgres
CREATE DATABASE gasbot;
CREATE USER gasbot WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE gasbot TO gasbot;

# Instalar Redis
# Windows: https://github.com/microsoftarchive/redis/releases
```

### 2. Backend
```bash
cd backend

# Criar ambiente virtual
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Instalar dependências
pip install -r requirements.txt

# Configurar .env
cp .env.example .env
# Editar .env com suas configurações

# Rodar migrations
alembic upgrade head

# Iniciar servidor
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend (em outro terminal)
```bash
cd frontend

# Instalar dependências
npm install

# Configurar .env.local
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Iniciar dev server
npm run dev
```

### 4. Evolution API (opcional, para WhatsApp)
```bash
docker run -d \
  --name evolution-api \
  -p 8080:8080 \
  -e NODE_ENV=production \
  atendai/evolution-api:latest
```

---

## 🧪 TESTANDO O SISTEMA

### 1. Criar conta
```bash
# Acessar
http://localhost:3000

# Ou via API
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "teste@gasbot.com",
    "password": "senha123",
    "full_name": "Admin Teste",
    "company_name": "Distribuidora Teste",
    "phone": "11999999999"
  }'
```

### 2. Login e obter token
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "teste@gasbot.com",
    "password": "senha123"
  }'

# Copiar o access_token retornado
```

### 3. Testar endpoints do dashboard
```bash
# Definir token
TOKEN="seu_token_aqui"

# Ver resumo
curl http://localhost:8000/api/v1/dashboard/summary \
  -H "Authorization: Bearer $TOKEN"

# Ver pedidos
curl http://localhost:8000/api/v1/dashboard/orders \
  -H "Authorization: Bearer $TOKEN"

# Ver conversas
curl http://localhost:8000/api/v1/dashboard/conversations \
  -H "Authorization: Bearer $TOKEN"
```

### 4. Testar WebSocket
```javascript
// No console do navegador (F12)
const ws = new WebSocket('ws://localhost:8000/api/v1/conversations/ws/YOUR_TENANT_ID');

ws.onopen = () => {
  console.log('Conectado!');
  ws.send('ping');
};

ws.onmessage = (event) => {
  console.log('Mensagem recebida:', event.data);
};
```

---

## 📊 ACESSAR DASHBOARD

### 1. Login
```
http://localhost:3000/dashboard
```

### 2. Funcionalidades disponíveis
- **Pedidos**: Ver e gerenciar pedidos
- **Conversas**: Histórico de conversas (com áudios!)
- **Intervenções**: Sistema de intervenção humana

---

## 🔍 VERIFICAR LOGS

### Docker
```bash
# Backend
docker logs -f gasbot_backend

# Frontend
docker logs -f gasbot_frontend

# PostgreSQL
docker logs gasbot_postgres

# Redis
docker logs gasbot_redis
```

### Modo Dev
```bash
# Backend: Logs aparecem no terminal do uvicorn
# Frontend: Logs aparecem no terminal do npm run dev
```

---

## 🗄️ BANCO DE DADOS

### Acessar PostgreSQL
```bash
# Docker
docker exec -it gasbot_postgres psql -U gasbot -d gasbot

# Local
psql -U gasbot -d gasbot
```

### Queries úteis
```sql
-- Ver tenants
SELECT * FROM tenants;

-- Ver pedidos
SELECT * FROM orders ORDER BY created_at DESC LIMIT 10;

-- Ver conversas
SELECT * FROM conversations ORDER BY started_at DESC LIMIT 10;

-- Ver intervenções ativas
SELECT * FROM human_interventions WHERE ended_at IS NULL;
```

---

## 🔧 TROUBLESHOOTING

### Backend não inicia
```bash
# Verificar se PostgreSQL está rodando
docker ps | grep postgres
# ou
psql -U postgres -l

# Verificar migrations
alembic current
alembic upgrade head
```

### Frontend não carrega API
```bash
# Verificar CORS no backend
# Verificar .env.local do frontend
cat frontend/.env.local

# Deve ter:
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### WebSocket não conecta
```bash
# Verificar se o servidor está rodando
curl http://localhost:8000/health

# Verificar token JWT
# Decodificar em https://jwt.io

# Verificar tenant_id no token
```

### Áudio não toca
```bash
# Verificar se o arquivo está em formato suportado
# WhatsApp usa OGG/OPUS

# Verificar transcrição no banco
SELECT audio_transcription FROM conversations
WHERE messages->>'message_type' = 'audio';
```

---

## 📦 DEPENDÊNCIAS IMPORTANTES

### Backend
```txt
fastapi==0.109.0
uvicorn==0.27.0
langchain==0.1.0
openai==1.6.0
sqlalchemy==2.0.25
redis==5.0.1
```

### Frontend
```json
{
  "next": "^14.0.0",
  "react": "^18.2.0",
  "@radix-ui/react-tabs": "^1.0.4",
  "axios": "^1.6.0"
}
```

---

## 🎯 FLUXO COMPLETO DE TESTE

1. ✅ Iniciar serviços (Docker ou manual)
2. ✅ Criar conta via frontend
3. ✅ Fazer login
4. ✅ Configurar empresa (onboarding)
5. ✅ Adicionar produtos
6. ✅ Configurar áreas de entrega
7. ✅ Conectar WhatsApp (QR Code)
8. ✅ Simular pedido via WhatsApp
9. ✅ Ver pedido no dashboard
10. ✅ Iniciar intervenção
11. ✅ Enviar mensagem manual
12. ✅ Retomar bot

---

## 🚨 PROBLEMAS COMUNS

### "ModuleNotFoundError: No module named 'app'"
```bash
# Certificar que está no diretório correto
cd backend
python -c "import app; print('OK')"
```

### "Cannot find module '@/components/ui/tabs'"
```bash
# Reinstalar dependências do frontend
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### "WebSocket connection failed"
```bash
# Verificar se o backend suporta WebSocket
# Uvicorn deve estar rodando com --ws auto (padrão)
```

### "CORS policy error"
```bash
# Adicionar origem no backend/app/main.py
allow_origins=["http://localhost:3000"]
```

---

## 📞 SUPORTE

Se tiver problemas:
1. Verificar logs
2. Verificar .env
3. Verificar portas em uso
4. Reiniciar serviços
5. Verificar dependências

---

## ✅ CHECKLIST DE SETUP

- [ ] PostgreSQL rodando
- [ ] Redis rodando
- [ ] Backend rodando (porta 8000)
- [ ] Frontend rodando (porta 3000)
- [ ] .env configurado
- [ ] Migrations executadas
- [ ] Consegue fazer login
- [ ] Dashboard carrega
- [ ] WebSocket conecta

**Pronto para usar! 🎉**
