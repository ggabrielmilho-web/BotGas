# 🤖 BotGas

Sistema SaaS de Atendimento Automatizado via WhatsApp para Distribuidoras de Gás e Água

## 🎯 Visão Geral

GasBot é uma plataforma multi-tenant que automatiza atendimento ao cliente via WhatsApp usando IA, permitindo que distribuidoras gerenciem pedidos, entregas e pagamentos de forma inteligente.

## ✨ Features Principais

- 🤖 **Agentes IA** - Sistema de agentes LangChain para atendimento inteligente
- 🎤 **Transcrição de Áudio** - Suporte completo a mensagens de voz via Whisper
- 👤 **Intervenção Humana** - Sistema de pause de 5min para atendimento manual
- 📍 **Entrega Flexível** - 3 modos: por bairro, raio/km ou híbrido
- 💰 **Pagamento Simples** - Mostra PIX sem validação complexa
- 💾 **Cache Inteligente** - Economia de 80% em chamadas de API externa

## 🛠️ Stack Tecnológica

### Backend
- Python 3.11
- FastAPI
- LangChain + LangGraph
- PostgreSQL
- Redis
- Celery

### Frontend
- Next.js 14
- React 18
- Tailwind CSS
- Shadcn/ui
- React Query

### Infraestrutura
- Docker + Docker Swarm
- Traefik (Proxy Reverso)
- Evolution API (WhatsApp)

## 🚀 Instalação e Uso

### Pré-requisitos

- Docker Desktop ou Docker Engine
- PostgreSQL (via Docker)
- Node.js 18+ (para desenvolvimento local)
- Python 3.11+ (para desenvolvimento local)

### Configuração Rápida

1. Clone o repositório:
```bash
git clone https://github.com/ggabrielmilho-web/BotGas.git
cd BotGas
```

2. Configure as variáveis de ambiente:
```bash
cp .env.example .env
# Edite o .env com suas chaves de API
```

3. Suba os containers:
```bash
docker-compose up -d
```

4. Acesse:
- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- API Health: http://localhost:8000/health

## 📁 Estrutura do Projeto

```
BotGas/
├── backend/              # API Python/FastAPI
│   ├── app/
│   │   ├── agents/      # Agentes LangChain
│   │   ├── api/         # Endpoints
│   │   ├── core/        # Configurações
│   │   ├── database/    # Models e migrations
│   │   ├── services/    # Lógica de negócio
│   │   └── webhooks/    # Evolution API handlers
│   └── requirements.txt
├── frontend/            # Dashboard Next.js
│   ├── src/
│   │   ├── app/        # App Router
│   │   ├── components/ # Componentes React
│   │   └── services/   # API calls
│   └── package.json
├── docker-compose.yml   # Desenvolvimento
├── docker-stack.yml     # Produção Swarm
└── docs/               # Documentação

```

## 🔐 Variáveis de Ambiente

```env
# Database
DATABASE_URL=postgresql://gasbot:password@localhost:5432/gasbot
REDIS_URL=redis://localhost:6379

# APIs
OPENAI_API_KEY=sk-...
GOOGLE_MAPS_API_KEY=AIza...
EVOLUTION_API_URL=http://localhost:8080
EVOLUTION_API_KEY=your-key

# Security
JWT_SECRET_KEY=your-secret-key

# App Config
WEBHOOK_URL=http://localhost:8000/webhook
TRIAL_DAYS=7
```

## 📊 Status do Projeto

| Sessão | Módulo | Status | Última Atualização |
|--------|--------|--------|-------------------|
| 1 | Setup Base | ✅ Completo | Docker + FastAPI + Next.js |
| 2 | Database e Models | ✅ Completo | PostgreSQL + SQLAlchemy + 14 tabelas |
| 3 | Autenticação JWT Multi-tenant | ✅ Completo | Sistema completo de auth + isolamento |
| 4 | **Evolution API + WhatsApp** | ✅ **Completo** | Integração completa + Áudio + Webhooks |
| 5 | Agentes LangChain | 🔄 Pendente | 5 agentes IA + Intervenção Humana |
| 6 | Sistema de Entrega | 🔄 Pendente | 3 modos + Cache endereços |
| 7 | Frontend Onboarding | 🔄 Pendente | Wizard setup + QR Code |
| 8 | Dashboard | 🔄 Pendente | Pedidos real-time + Chat |
| 9 | Trial System | 🔄 Pendente | Gestão de assinaturas |
| 10 | Deploy Produção | 🔄 Pendente | Docker Swarm + Traefik |

### 🎉 Última Sessão Completa: Sessão 4

**Implementações da Sessão 4:**
- ✅ Integração completa Evolution API v2.3.1
- ✅ Endpoints WhatsApp (QR Code, status, send, disconnect)
- ✅ Webhook para receber mensagens do Evolution
- ✅ Processador de áudio com OpenAI Whisper
- ✅ Transcrição automática de áudios em português
- ✅ Processamento de mensagens (texto e áudio)
- ✅ Criação automática de customers e conversations
- ✅ Multi-tenant por instância (tenant_{uuid})
- ✅ Logs de webhooks para debug
- ✅ Teste de integração validado

**Endpoints disponíveis:**
```
GET  /api/v1/whatsapp/qr          # Gerar QR Code
GET  /api/v1/whatsapp/status      # Status conexão
POST /api/v1/whatsapp/send        # Enviar mensagem
POST /api/v1/whatsapp/disconnect  # Desconectar
DELETE /api/v1/whatsapp/instance  # Deletar instância
POST /api/v1/webhook/evolution    # Receber mensagens
```

📄 [Ver documentação completa da Sessão 4](SESSION_4_SUMMARY.md)
📖 [Guia de setup Ngrok para testes locais](SETUP_NGROK.md)

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor, abra uma issue ou pull request.

## 📄 Licença

Este projeto está sob licença privada.

## 📞 Contato

Para mais informações, entre em contato através do GitHub.

---

🤖 **Desenvolvido com FastAPI + Next.js + LangChain**
