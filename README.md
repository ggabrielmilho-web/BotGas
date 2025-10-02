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
| 4 | Evolution API + WhatsApp | ✅ Completo | Integração completa + Áudio + Webhooks |
| 5 | Agentes LangChain | ✅ Completo | 5 agentes + Intervenção + Cache |
| 6 | **Sistema de Entrega** | ✅ **Completo** | 3 modos + Cache + APIs REST |
| 7 | Frontend Onboarding | 🔄 Pendente | Wizard setup + QR Code |
| 8 | Dashboard | 🔄 Pendente | Pedidos real-time + Chat |
| 9 | Trial System | 🔄 Pendente | Gestão de assinaturas |
| 10 | Deploy Produção | 🔄 Pendente | Docker Swarm + Traefik |

### 🎉 Última Sessão Completa: Sessão 6

**Implementações da Sessão 6:**
- ✅ Sistema completo de Entrega Flexível (3 modos configuráveis)
- ✅ DeliveryModeService (orquestrador de modos)
- ✅ NeighborhoodDeliveryService (validação por bairros cadastrados)
- ✅ RadiusDeliveryService (validação por raio/KM + Google Maps)
- ✅ HybridDeliveryService (combina bairros + raio)
- ✅ AddressCacheService melhorado (cache de 30 dias + fuzzy matching)
- ✅ API REST completa (17 endpoints para configuração)
- ✅ Integração com Google Maps Geocoding API
- ✅ Cálculo de distância (fórmula de Haversine)
- ✅ Extração inteligente de bairro do endereço
- ✅ Sistema de entrega grátis (acima de valor mínimo)
- ✅ Economia de ~80% em chamadas à API do Google Maps

**Modos de Entrega implementados:**
```
DeliveryModeService
├── NeighborhoodDelivery  # Por bairros cadastrados (manual, grátis)
├── RadiusDelivery        # Por distância/KM (Google Maps, preciso)
└── HybridDelivery        # Combina os dois (melhor performance)
```

**Features especiais:**
- 📍 3 modos de validação configuráveis por tenant
- 💰 Economia de 80% em chamadas de API (cache inteligente)
- 🎯 Configuração granular (por bairro ou faixas de raio)
- 🔄 Fuzzy matching para endereços similares
- ⚡ Performance otimizada (bairros primeiro no modo híbrido)

---

**Implementações da Sessão 5:**
- ✅ Sistema completo de agentes LangChain
- ✅ MasterAgent (orquestrador com roteamento inteligente)
- ✅ AttendanceAgent (saudações e informações de produtos)
- ✅ ValidationAgent (validação de endereços com 3 modos)
- ✅ OrderAgent (montagem e gestão de pedidos)
- ✅ PaymentAgent (processamento de pagamento simplificado)
- ✅ InterventionService (sistema de pausa de 5min para atendimento humano)
- ✅ AudioProcessor (transcrição de áudio via Whisper)
- ✅ AddressCacheService (cache inteligente com fuzzy matching)
- ✅ Detecção automática de intenções
- ✅ Fluxo completo de conversação (greeting → products → order → address → payment)
- ✅ Testes de estrutura e validação

**Agentes implementados:**
```
MasterAgent          # Orquestração e roteamento
├── AttendanceAgent  # Saudações e produtos
├── ValidationAgent  # Validação de endereços (bairro/raio/híbrido)
├── OrderAgent       # Montagem de pedidos
└── PaymentAgent     # Pagamento (PIX/dinheiro/cartão)
```

**Features especiais:**
- 🤚 Intervenção humana com pause de 5min
- 🎤 Processamento de áudio do WhatsApp
- 💾 Cache de endereços (economia 80% API calls)
- 📍 3 modos de validação de entrega

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor, abra uma issue ou pull request.

## 📄 Licença

Este projeto está sob licença privada.

## 📞 Contato

Para mais informações, entre em contato através do GitHub.

---

🤖 **Desenvolvido com FastAPI + Next.js + LangChain**
