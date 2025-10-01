# 🤖 CLAUDE CODE - CONTEXTO E INSTRUÇÕES

## 🎯 PROMPT MASTER PARA CLAUDE CODE

```
Você está desenvolvendo o GasBot, um sistema SaaS de atendimento automatizado via WhatsApp para distribuidoras de gás e água. 

CONTEXTO:
- Sistema multi-tenant com dashboard web
- Backend Python/FastAPI com agentes LangChain
- Frontend Next.js 14 com Tailwind
- Deploy via Docker Swarm em VPS existente
- Integração WhatsApp via Evolution API
- Suporte a áudio via Whisper
- Sistema de intervenção humana
- Cache inteligente de endereços
- Prazo: MVP funcional em 7-10 dias

SUA TAREFA ATUAL: [INSERIR TAREFA ESPECÍFICA]

PRINCÍPIOS:
1. Código funcional > Código perfeito
2. Sempre implemente tratamento de erros
3. Use tipos (TypeScript/Pydantic)
4. Comente apenas lógica complexa
5. Faça logs informativos
6. Pense em multi-tenant desde início
7. Cache sempre que possível

PADRÕES DO PROJETO:
- Endpoints: /api/v1/{recurso}
- Auth: JWT Bearer token
- Database: PostgreSQL com SQLAlchemy
- Cache: Redis com TTL de 5min para produtos
- Validação: Pydantic models
- Testes: Pytest + Jest
```

## 📁 ESTRUTURA DE SESSÕES CLAUDE CODE

### SESSÃO 1: Setup Base
```
TAREFA: Criar estrutura base do projeto com Docker
ARQUIVOS CRIAR:
- docker-compose.yml (desenvolvimento)
- docker-stack.yml (produção swarm)
- backend/Dockerfile
- backend/app/main.py
- backend/app/core/config.py
- backend/requirements.txt
- frontend/Dockerfile
- frontend/package.json
- .env.example

RESULTADO ESPERADO:
- Backend rodando na porta 8000
- Frontend rodando na porta 3000
- PostgreSQL e Redis configurados
- Ambiente pronto para desenvolvimento
```

### SESSÃO 2: Database e Models
```
TAREFA: Criar schema do banco e models SQLAlchemy
ARQUIVOS CRIAR:
- backend/app/database/base.py
- backend/app/database/models.py
- backend/app/database/schemas.py
- backend/alembic.ini
- backend/app/database/session.py

CONTEXTO ANTERIOR: Setup base completo
IMPORTANTE: Incluir tabelas de cache e intervenção humana
DEPENDÊNCIAS: PostgreSQL rodando
```

### SESSÃO 3: Sistema de Autenticação
```
TAREFA: Implementar auth JWT multi-tenant
ARQUIVOS CRIAR:
- backend/app/api/auth.py
- backend/app/core/security.py
- backend/app/services/tenant.py
- backend/app/middleware/tenant.py

CONTEXTO ANTERIOR: Models criados
PRÉ-REQUISITO: Database funcionando
```

### SESSÃO 4: Evolution API Integration
```
TAREFA: Integrar Evolution API para WhatsApp
ARQUIVOS CRIAR:
- backend/app/services/evolution.py
- backend/app/services/audio_processor.py
- backend/app/webhooks/whatsapp.py
- backend/app/api/whatsapp.py

CONTEXTO ANTERIOR: Auth implementado
IMPORTANTE: Suporte a áudio e texto
CRÍTICO: QR Code e gestão de instâncias
```

### SESSÃO 5: Agentes LangChain
```
TAREFA: Criar sistema de agentes IA com intervenção humana
ARQUIVOS CRIAR:
- backend/app/agents/base.py
- backend/app/agents/master.py
- backend/app/agents/attendance.py
- backend/app/agents/validation.py
- backend/app/agents/order.py
- backend/app/agents/payment.py
- backend/app/services/intervention.py

CONTEXTO ANTERIOR: WhatsApp conectado
CRÍTICO: Sistema de pause para intervenção humana
IMPORTANTE: Cache de produtos e endereços
```

### SESSÃO 6: Sistema de Entrega Flexível
```
TAREFA: Implementar 3 modos de entrega
ARQUIVOS CRIAR:
- backend/app/services/delivery_modes.py
- backend/app/services/neighborhood_delivery.py
- backend/app/services/radius_delivery.py
- backend/app/services/hybrid_delivery.py
- backend/app/services/address_cache.py

CONTEXTO ANTERIOR: Agentes criados
FEATURES: Bairros cadastrados, raio/KM, modo híbrido
```

### SESSÃO 7: Frontend - Onboarding
```
TAREFA: Criar fluxo de onboarding completo
ARQUIVOS CRIAR:
- frontend/src/app/onboarding/page.tsx
- frontend/src/components/SetupWizard.tsx
- frontend/src/components/QRCodeScanner.tsx
- frontend/src/components/DeliveryConfig.tsx
- frontend/src/components/PaymentConfig.tsx
- frontend/src/services/api.ts

CONTEXTO ANTERIOR: Backend APIs prontas
DESIGN: Shadcn/ui + Tailwind
IMPORTANTE: 3 modos de configuração de entrega
```

### SESSÃO 8: Frontend - Dashboard
```
TAREFA: Dashboard com pedidos real-time e intervenção
ARQUIVOS CRIAR:
- frontend/src/app/dashboard/page.tsx
- frontend/src/components/OrdersList.tsx
- frontend/src/components/ChatHistory.tsx
- frontend/src/components/InterventionPanel.tsx
- frontend/src/components/AudioMessage.tsx
- frontend/src/hooks/useWebSocket.ts

CONTEXTO ANTERIOR: Onboarding completo
FEATURE: WebSocket para real-time
CRÍTICO: Interface de intervenção humana
```

### SESSÃO 9: Sistema de Trial
```
TAREFA: Trial 7 dias gratuito
ARQUIVOS CRIAR:
- backend/app/services/trial.py
- backend/app/tasks/trial.py
- frontend/src/components/TrialBanner.tsx

CONTEXTO ANTERIOR: Sistema base completo
LÓGICA: Verificação de expiração do trial
IMPORTANTE: Sem cobrança automática no MVP
```

### SESSÃO 10: Deploy Production (Docker Swarm)
```
TAREFA: Preparar para produção com Docker Swarm
ARQUIVOS CRIAR:
- docker-stack.yml
- .env.production
- scripts/deploy-swarm.sh
- scripts/backup.sh
- traefik/config.yml

CONTEXTO ANTERIOR: MVP completo
SERVIDOR: VPS com Docker Swarm + Traefik
IMPORTANTE: Configurar labels do Traefik
```

### SESSÃO 11: Testes e Documentação
```
TAREFA: Testes críticos e docs
ARQUIVOS CRIAR:
- backend/tests/test_agents.py
- backend/tests/test_audio.py
- backend/tests/test_intervention.py
- backend/tests/test_api.py
- frontend/__tests__/
- README.md
- docs/API.md

CONTEXTO ANTERIOR: Sistema funcionando
COBERTURA: Fluxos críticos + features especiais
```

## 🔄 TEMPLATE DE ATUALIZAÇÃO ENTRE SESSÕES

```markdown
## RESUMO DA SESSÃO ANTERIOR
- **Sessão:** [NÚMERO]
- **Tarefa:** [O QUE FOI FEITO]
- **Arquivos criados:** [LISTAR]
- **Status:** ✅ Completo / ⚠️ Parcial / ❌ Bloqueado

## PONTOS IMPORTANTES
- [Decisões técnicas tomadas]
- [Problemas encontrados]
- [Soluções implementadas]

## FEATURES ESPECIAIS IMPLEMENTADAS
- [ ] Processamento de áudio
- [ ] Intervenção humana
- [ ] Cache de endereços
- [ ] Entrega flexível (3 modos)

## PRÓXIMOS PASSOS
- [ ] [Tarefa 1]
- [ ] [Tarefa 2]

## VARIÁVEIS DE AMBIENTE NECESSÁRIAS
```env
NOVA_VAR=valor
```

## COMANDOS PARA RODAR
```bash
# Comando necessário
```
```

## 🚨 TROUBLESHOOTING COMUM

### Problema: Evolution API não conecta
```python
# Verificar:
1. Evolution está rodando? (porta 8080)
2. API Key está correta?
3. Webhook URL é acessível externamente?
```

### Problema: Áudio não transcrevendo
```python
# Verificar:
1. OPENAI_API_KEY configurada?
2. Formato do áudio suportado?
3. Verificar logs do audio_processor
```

### Problema: Intervenção humana não pausando bot
```python
# Verificar:
1. Flag human_intervention está True?
2. Timer de 5min está funcionando?
3. WebSocket conectado pro real-time?
```

### Problema: Multi-tenant misturando dados
```python
# Sempre filtrar por tenant_id:
query.filter(Model.tenant_id == current_tenant.id)
```

## 📈 MÉTRICAS DE PROGRESSO

| Módulo | Status | Sessões | Prioridade |
|--------|--------|---------|------------|
| Setup Base | ⏳ | 1 | P0 |
| Database | ⏳ | 2 | P0 |
| Auth | ⏳ | 3 | P0 |
| WhatsApp + Áudio | ⏳ | 4 | P0 |
| Agentes IA | ⏳ | 5 | P0 |
| Sistema Entrega | ⏳ | 6 | P0 |
| Onboarding | ⏳ | 7 | P1 |
| Dashboard | ⏳ | 8 | P1 |
| Trial | ⏳ | 9 | P2 |
| Deploy | ⏳ | 10 | P1 |
| Testes | ⏳ | 11 | P2 |

Legenda: ✅ Completo | 🔄 Em progresso | ⏳ Pendente | ❌ Bloqueado

## 🎯 FEATURES CRÍTICAS DO MVP
1. ✅ Processamento de texto e áudio
2. ✅ Intervenção humana (5min pause)
3. ✅ Cache de endereços (economia 80%)
4. ✅ Entrega flexível (bairro/raio/híbrido)
5. ✅ Pagamento simples (só mostra PIX)
6. ✅ Multi-tenant desde início
7. ✅ Trial 7 dias sem cartão