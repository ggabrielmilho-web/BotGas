# 🤖 GASBOT - PROJECT OVERVIEW
> Sistema SaaS de Atendimento Automatizado para Distribuidoras via WhatsApp

## 🎯 CONTEXTO RÁPIDO
- **Produto:** Chatbot WhatsApp para distribuidoras de gás/água
- **Stack:** Python (FastAPI) + Next.js + PostgreSQL + LangChain
- **Deploy:** Docker Swarm + Traefik
- **Prazo:** MVP em 7-10 dias
- **Monetização:** SaaS R$ 200-300/mês

## 📁 ESTRUTURA DO PROJETO
```
gasbot/
├── backend/
│   ├── app/
│   │   ├── agents/          # Agentes LangChain
│   │   ├── api/             # Endpoints FastAPI
│   │   ├── core/            # Configurações
│   │   ├── database/        # Models e migrations
│   │   ├── services/        # Lógica de negócio
│   │   └── webhooks/        # Evolution API handlers
│   ├── tests/
│   ├── Dockerfile           # Dockerfile do backend
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/            # Next.js App Router
│   │   ├── components/     # Componentes React
│   │   ├── lib/           # Utils e configs
│   │   └── services/      # API calls
│   ├── Dockerfile          # Dockerfile do frontend
│   └── package.json
├── scripts/
│   ├── deploy-swarm.sh     # Script de deploy
│   └── backup.sh           # Script de backup
├── docker-compose.yml      # Para desenvolvimento local
├── docker-stack.yml        # Para produção (Swarm)
├── .env.example            # Variáveis de ambiente exemplo
└── docs/
    ├── PROJECT_OVERVIEW.md
    ├── CLAUDE_CONTEXT.md
    ├── TECHNICAL_SPECS.md
    └── CURRENT_SESSION.md
```

## 🔄 FLUXO PRINCIPAL
1. Cliente escaneia QR Code → WhatsApp conectado
2. Mensagem (texto/áudio) chega → Evolution API → Webhook
3. Backend processa → Agentes decidem resposta
4. Resposta enviada → Cliente recebe no WhatsApp
5. Dashboard mostra pedidos em tempo real

## 🎨 FEATURES MVP

### ONBOARDING (Prioridade 1)
- [ ] Tela de cadastro empresa
- [ ] Setup produtos e preços
- [ ] Configuração áreas de entrega (bairros/raio/híbrido)
- [ ] QR Code Evolution API
- [ ] Configuração formas de pagamento e PIX

### AGENTES IA (Prioridade 1)
- [ ] Agente Mestre (orquestrador)
- [ ] Agente Atendimento
- [ ] Agente Validação Endereço (com cache)
- [ ] Agente Pedidos
- [ ] Agente Pagamento (apenas coleta método, não valida)
- [ ] Processamento de áudio (Whisper)
- [ ] Sistema de intervenção humana

### DASHBOARD (Prioridade 2)
- [ ] Lista pedidos real-time
- [ ] Sistema de intervenção manual
- [ ] Métricas básicas
- [ ] Histórico conversas (com transcrições de áudio)
- [ ] Gestão produtos
- [ ] Configuração áreas de entrega

### SISTEMA (Prioridade 3)
- [ ] Trial 7 dias gratuito
- [ ] Multi-tenant
- [ ] Cache de endereços
- [ ] Logs e monitoramento

## 🔑 DECISÕES TÉCNICAS IMPORTANTES

### BACKEND
- **FastAPI** - Performance e async nativo
- **LangChain + LangGraph** - Orquestração de agentes
- **PostgreSQL** - Dados relacionais + cache de endereços
- **Redis** - Cache e filas de mensagens
- **Celery** - Processamento assíncrono
- **OpenAI Whisper** - Transcrição de áudios

### FRONTEND
- **Next.js 14** - App Router e Server Components
- **Tailwind + Shadcn** - UI rápida e bonita
- **React Query** - Estado e cache
- **Zod** - Validação de schemas

### INTEGRAÇÕES
- **Evolution API** - WhatsApp não-oficial
- **OpenAI GPT-4-mini** - Processamento de linguagem
- **OpenAI Whisper** - Transcrição de áudio
- **Google Maps API** - Validação de endereços (com cache)

## ⚠️ PONTOS CRÍTICOS
1. **Rate Limits WhatsApp** - Implementar queue
2. **Contexto de Conversa** - Redis para sessões
3. **Multi-tenant** - Isolamento por tenant_id
4. **Intervenção Humana** - Sistema de pause de 5min
5. **Cache Endereços** - Economia de 80% Google Maps API
6. **Áudio** - Suporte completo para mensagens de voz
7. **Flexibilidade Entrega** - 3 modos (bairro/raio/híbrido)

## 📊 MODELO DE DADOS SIMPLIFICADO
```sql
tenants (empresas)
├── products (produtos)
├── delivery_areas (config de entrega)
├── neighborhood_configs (bairros)
├── radius_configs (raios/km)
├── orders (pedidos)
├── customers (clientes)
├── conversations (conversas)
├── address_cache (cache endereços)
└── human_interventions (logs intervenção)
```

## 🚀 COMANDOS ÚTEIS
```bash
# Backend
cd backend && uvicorn app.main:app --reload

# Frontend
cd frontend && npm run dev

# Docker Swarm Deploy
docker stack deploy -c docker-stack.yml gasbot

# Migrations
alembic upgrade head

# Tests
pytest tests/
```

## 💡 FEATURES DIFERENCIAIS
1. **Processamento de Áudio** - Atende "véinhas" que mandam áudio
2. **Intervenção Humana** - Dono pode intervir por 5min quando quiser
3. **Cache Inteligente** - Economiza 80% em APIs externas
4. **Entrega Flexível** - Por bairro, raio ou híbrido
5. **Sem Validação de Pagamento** - Simples, mostra PIX e pronto

## 📝 STATUS ATUAL
- **Fase:** Documentação finalizada
- **Próximo passo:** Iniciar desenvolvimento
- **Bloqueios:** Nenhum
- **Última atualização:** Documentação completa com todas features