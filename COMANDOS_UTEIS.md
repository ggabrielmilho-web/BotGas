# 🛠️ COMANDOS ÚTEIS - GASBOT

## 🐳 DOCKER

### Comandos Básicos
```bash
# Iniciar todos os serviços
docker-compose up -d

# Ver logs de todos os serviços
docker-compose logs -f

# Ver logs de um serviço específico
docker-compose logs -f backend
docker-compose logs -f frontend

# Parar todos os serviços
docker-compose down

# Parar e remover volumes (cuidado, apaga o banco!)
docker-compose down -v

# Rebuild de uma imagem
docker-compose build backend
docker-compose build frontend

# Restart de um serviço
docker-compose restart backend
```

### Ver Status
```bash
# Listar containers rodando
docker ps

# Ver uso de recursos
docker stats

# Inspecionar um container
docker inspect gasbot_backend
```

### Executar Comandos em Containers
```bash
# Entrar no container do backend
docker exec -it gasbot_backend bash

# Entrar no container do PostgreSQL
docker exec -it gasbot_postgres psql -U gasbot -d gasbot

# Rodar migration
docker exec gasbot_backend alembic upgrade head

# Criar nova migration
docker exec gasbot_backend alembic revision -m "description"
```

---

## 🐍 BACKEND (Python/FastAPI)

### Desenvolvimento Local
```bash
cd backend

# Ativar ambiente virtual
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Rodar servidor
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Rodar servidor com logs detalhados
uvicorn app.main:app --reload --log-level debug
```

### Migrations (Alembic)
```bash
# Ver versão atual
alembic current

# Ver histórico de migrations
alembic history

# Criar nova migration
alembic revision -m "add new table"

# Aplicar migrations
alembic upgrade head

# Reverter última migration
alembic downgrade -1

# Reverter todas
alembic downgrade base

# Auto-gerar migration baseada nos models
alembic revision --autogenerate -m "auto migration"
```

### Testes
```bash
# Rodar todos os testes
pytest

# Rodar com coverage
pytest --cov=app --cov-report=html

# Rodar testes específicos
pytest tests/test_agents.py
pytest tests/test_audio.py -v

# Rodar com output detalhado
pytest -v -s
```

### Python Shell
```bash
# Abrir Python shell com contexto do app
python
>>> from app.database.base import get_db
>>> from app.database.models import Tenant
>>> # Fazer queries...
```

---

## ⚛️ FRONTEND (Next.js/React)

### Desenvolvimento Local
```bash
cd frontend

# Instalar dependências
npm install

# Rodar dev server
npm run dev

# Build para produção
npm run build

# Rodar produção local
npm run start

# Lint
npm run lint

# Limpar cache
rm -rf .next node_modules package-lock.json
npm install
```

### TypeScript
```bash
# Verificar tipos
npx tsc --noEmit

# Gerar tipos a partir da API
# (Se tiver OpenAPI schema)
npx openapi-typescript http://localhost:8000/openapi.json -o src/types/api.ts
```

### Testes
```bash
# Rodar testes
npm test

# Rodar com coverage
npm test -- --coverage

# Watch mode
npm test -- --watch
```

---

## 🗄️ BANCO DE DADOS (PostgreSQL)

### Comandos SQL Úteis
```bash
# Conectar ao banco
psql -U gasbot -d gasbot

# Ou via Docker
docker exec -it gasbot_postgres psql -U gasbot -d gasbot
```

```sql
-- Listar tabelas
\dt

-- Descrever tabela
\d tenants
\d orders

-- Ver todas as databases
\l

-- Ver conexões ativas
SELECT * FROM pg_stat_activity;

-- Matar conexão
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE pid = 12345;

-- Tamanho do banco
SELECT pg_size_pretty(pg_database_size('gasbot'));

-- Tamanho de tabelas
SELECT
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Ver últimos 10 pedidos
SELECT
  id, order_number, status, total, created_at
FROM orders
ORDER BY created_at DESC
LIMIT 10;

-- Ver conversas ativas
SELECT
  id, customer_id, human_intervention, started_at
FROM conversations
WHERE status = 'active'
ORDER BY started_at DESC;

-- Ver intervenções ativas
SELECT * FROM human_interventions WHERE ended_at IS NULL;

-- Limpar cache de endereços antigos
DELETE FROM address_cache
WHERE validated_at < NOW() - INTERVAL '30 days';

-- Estatísticas de pedidos por tenant
SELECT
  t.company_name,
  COUNT(o.id) as total_orders,
  SUM(o.total) as total_revenue
FROM tenants t
LEFT JOIN orders o ON o.tenant_id = t.id
GROUP BY t.id, t.company_name;
```

### Backup e Restore
```bash
# Backup
docker exec gasbot_postgres pg_dump -U gasbot gasbot > backup.sql

# Ou com compressão
docker exec gasbot_postgres pg_dump -U gasbot gasbot | gzip > backup.sql.gz

# Restore
docker exec -i gasbot_postgres psql -U gasbot gasbot < backup.sql

# Ou de arquivo comprimido
gunzip -c backup.sql.gz | docker exec -i gasbot_postgres psql -U gasbot gasbot
```

---

## 🔴 REDIS

### Comandos Redis
```bash
# Conectar ao Redis
docker exec -it gasbot_redis redis-cli

# Ou localmente
redis-cli
```

```redis
# Listar todas as chaves
KEYS *

# Ver chaves de produtos
KEYS products:*

# Ver valor de uma chave
GET products:tenant_id

# Ver TTL (tempo de vida)
TTL products:tenant_id

# Deletar chave
DEL products:tenant_id

# Limpar tudo (cuidado!)
FLUSHALL

# Ver info do Redis
INFO

# Monitor em tempo real
MONITOR
```

---

## 🔍 DEBUGGING

### Ver logs em tempo real
```bash
# Backend
docker-compose logs -f backend

# Ver apenas erros
docker-compose logs backend | grep ERROR

# Últimas 100 linhas
docker-compose logs --tail=100 backend
```

### cURL - Testar API
```bash
# Health check
curl http://localhost:8000/health

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"teste@gasbot.com","password":"senha123"}'

# Obter resumo do dashboard (com token)
curl http://localhost:8000/api/v1/dashboard/summary \
  -H "Authorization: Bearer YOUR_TOKEN"

# Ver pedidos
curl http://localhost:8000/api/v1/dashboard/orders \
  -H "Authorization: Bearer YOUR_TOKEN"

# Criar produto
curl -X POST http://localhost:8000/api/v1/products \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Gás 13kg","price":100.00}'
```

### WebSocket - Testar no navegador
```javascript
// Abrir console do navegador (F12)
const ws = new WebSocket('ws://localhost:8000/api/v1/conversations/ws/YOUR_TENANT_ID');

ws.onopen = () => console.log('Conectado!');
ws.onmessage = (e) => console.log('Mensagem:', e.data);
ws.onerror = (e) => console.error('Erro:', e);
ws.onclose = () => console.log('Desconectado');

// Enviar ping
ws.send('ping');

// Fechar
ws.close();
```

---

## 🧹 LIMPEZA

### Limpar Docker
```bash
# Remover containers parados
docker container prune

# Remover imagens não utilizadas
docker image prune

# Remover tudo não utilizado
docker system prune -a

# Ver uso de espaço
docker system df
```

### Limpar Node Modules
```bash
cd frontend
rm -rf node_modules package-lock.json .next
npm install
```

### Limpar Python Cache
```bash
cd backend
find . -type d -name __pycache__ -exec rm -r {} +
find . -type f -name "*.pyc" -delete
```

---

## 📊 MONITORAMENTO

### Ver processos
```bash
# Processos do Docker
docker stats

# CPU e memória
top
htop  # Se instalado
```

### Verificar portas em uso
```bash
# Windows
netstat -ano | findstr :8000
netstat -ano | findstr :3000

# Linux/Mac
lsof -i :8000
lsof -i :3000
```

### Verificar conectividade
```bash
# Ping ao backend
curl http://localhost:8000/health

# Testar PostgreSQL
docker exec gasbot_postgres pg_isready -U gasbot

# Testar Redis
docker exec gasbot_redis redis-cli ping
```

---

## 🚀 DEPLOY

### Build para produção
```bash
# Backend
docker build -t gasbot/backend:latest ./backend

# Frontend
docker build -t gasbot/frontend:latest ./frontend

# Tag para registry
docker tag gasbot/backend:latest registry.com/gasbot/backend:latest
docker push registry.com/gasbot/backend:latest
```

### Docker Swarm
```bash
# Inicializar swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-stack.yml gasbot

# Ver serviços
docker service ls

# Ver logs de um serviço
docker service logs -f gasbot_backend

# Escalar serviço
docker service scale gasbot_backend=3

# Atualizar serviço
docker service update --image gasbot/backend:new gasbot_backend

# Remover stack
docker stack rm gasbot
```

---

## 🔐 SEGURANÇA

### Gerar secret key
```bash
# Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# OpenSSL
openssl rand -base64 32
```

### Verificar dependências
```bash
# Backend
pip check
pip list --outdated

# Frontend
npm outdated
npm audit
npm audit fix
```

---

## 📝 GIT

### Comandos úteis
```bash
# Status
git status

# Ver diferenças
git diff

# Adicionar tudo
git add .

# Commit
git commit -m "feat: add dashboard"

# Push
git push origin main

# Pull
git pull origin main

# Ver log bonito
git log --oneline --graph --all

# Desfazer último commit (mantém alterações)
git reset --soft HEAD~1

# Limpar alterações locais
git checkout .
git clean -fd
```

---

## 💡 DICAS

### Aliases úteis (adicionar ao .bashrc ou .zshrc)
```bash
# Docker
alias dc='docker-compose'
alias dcu='docker-compose up -d'
alias dcd='docker-compose down'
alias dcl='docker-compose logs -f'

# Python
alias py='python'
alias venv='source venv/bin/activate'

# Git
alias gs='git status'
alias ga='git add .'
alias gc='git commit -m'
alias gp='git push'
alias gl='git log --oneline --graph'
```

### Variáveis de ambiente rápidas
```bash
# Exportar token (após login)
export TOKEN="eyJ0eXAi..."

# Usar em requests
curl http://localhost:8000/api/v1/dashboard/summary \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🎯 WORKFLOW DIÁRIO

```bash
# 1. Puxar atualizações
git pull origin main

# 2. Subir ambiente
docker-compose up -d

# 3. Ver logs
docker-compose logs -f

# 4. Fazer alterações no código...

# 5. Testar
curl http://localhost:8000/health

# 6. Commit
git add .
git commit -m "feat: nova feature"
git push origin main

# 7. Parar ambiente
docker-compose down
```

---

## 📚 LINKS ÚTEIS

- **FastAPI Docs**: http://localhost:8000/docs
- **Frontend**: http://localhost:3000
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379
- **Evolution API**: http://localhost:8080

---

**Happy Coding! 🚀**
