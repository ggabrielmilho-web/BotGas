# 🔧 TECHNICAL SPECIFICATIONS - GASBOT

## 🗄️ DATABASE SCHEMA COMPLETO

```sql
-- TENANTS (Empresas/Distribuidoras)
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_name VARCHAR(255) NOT NULL,
    cnpj VARCHAR(14) UNIQUE,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(255) NOT NULL,
    address JSONB,
    whatsapp_instance_id VARCHAR(255) UNIQUE,
    whatsapp_connected BOOLEAN DEFAULT FALSE,
    trial_ends_at TIMESTAMP,
    subscription_status VARCHAR(50) DEFAULT 'trial',
    subscription_plan VARCHAR(50),
    
    -- Configurações de Pagamento
    payment_methods JSONB DEFAULT '["Dinheiro"]',
    pix_enabled BOOLEAN DEFAULT FALSE,
    pix_key VARCHAR(255),
    pix_name VARCHAR(255),
    payment_instructions TEXT,
    
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- USERS (Usuários do Sistema)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'admin',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(tenant_id, email)
);

-- PRODUCTS (Produtos)
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    category VARCHAR(100),
    image_url VARCHAR(500),
    is_available BOOLEAN DEFAULT TRUE,
    stock_quantity INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- DELIVERY_AREAS (Config Geral de Entrega)
CREATE TABLE delivery_areas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    delivery_mode VARCHAR(50) DEFAULT 'neighborhood',
    free_delivery_minimum DECIMAL(10,2),
    default_fee DECIMAL(10,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- NEIGHBORHOOD_CONFIGS (Configuração por Bairro)
CREATE TABLE neighborhood_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    delivery_area_id UUID REFERENCES delivery_areas(id) ON DELETE CASCADE,
    neighborhood_name VARCHAR(255) NOT NULL,
    city VARCHAR(255) DEFAULT 'São Paulo',
    state VARCHAR(2) DEFAULT 'SP',
    delivery_type VARCHAR(50) DEFAULT 'paid',
    delivery_fee DECIMAL(10,2) DEFAULT 0,
    delivery_time_minutes INTEGER DEFAULT 60,
    zip_codes TEXT[],
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(tenant_id, neighborhood_name)
);

-- RADIUS_CONFIGS (Configuração por Raio/KM)
CREATE TABLE radius_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    delivery_area_id UUID REFERENCES delivery_areas(id) ON DELETE CASCADE,
    center_address VARCHAR(500) NOT NULL,
    center_lat DECIMAL(10,8),
    center_lng DECIMAL(11,8),
    radius_km_start DECIMAL(5,2) NOT NULL,
    radius_km_end DECIMAL(5,2) NOT NULL,
    delivery_fee DECIMAL(10,2) NOT NULL,
    delivery_time_minutes INTEGER DEFAULT 60,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- HYBRID_RULES (Regras para modo híbrido)
CREATE TABLE hybrid_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    delivery_area_id UUID REFERENCES delivery_areas(id) ON DELETE CASCADE,
    priority INTEGER DEFAULT 100,
    rule_type VARCHAR(50),
    config JSONB NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- CUSTOMERS (Clientes via WhatsApp)
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    whatsapp_number VARCHAR(20) NOT NULL,
    name VARCHAR(255),
    addresses JSONB DEFAULT '[]',
    order_count INTEGER DEFAULT 0,
    total_spent DECIMAL(10,2) DEFAULT 0,
    tags TEXT[],
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    last_order_at TIMESTAMP,
    UNIQUE(tenant_id, whatsapp_number)
);

-- ADDRESS_CACHE (Cache de endereços validados)
CREATE TABLE address_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    address_text VARCHAR(500) NOT NULL,
    normalized_address VARCHAR(500),
    coordinates JSONB,
    neighborhood VARCHAR(255),
    city VARCHAR(255),
    state VARCHAR(2),
    zip_code VARCHAR(10),
    delivery_area_id UUID REFERENCES delivery_areas(id),
    delivery_fee DECIMAL(10,2),
    is_deliverable BOOLEAN DEFAULT TRUE,
    validated_at TIMESTAMP DEFAULT NOW(),
    google_place_id VARCHAR(255),
    UNIQUE(tenant_id, address_text)
);

-- ORDERS (Pedidos)
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    customer_id UUID REFERENCES customers(id),
    order_number SERIAL,
    status VARCHAR(50) DEFAULT 'new',
    items JSONB NOT NULL,
    subtotal DECIMAL(10,2) NOT NULL,
    delivery_fee DECIMAL(10,2) DEFAULT 0,
    total DECIMAL(10,2) NOT NULL,
    delivery_address JSONB,
    payment_method VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    delivered_at TIMESTAMP
);

-- CONVERSATIONS (Histórico de Conversas)
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    customer_id UUID REFERENCES customers(id),
    session_id VARCHAR(255) NOT NULL,
    messages JSONB DEFAULT '[]',
    context JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'active',
    started_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP,
    
    -- Sistema de Intervenção Humana
    human_intervention BOOLEAN DEFAULT FALSE,
    intervention_started_at TIMESTAMP,
    intervention_ended_at TIMESTAMP,
    last_bot_message_at TIMESTAMP,
    
    total_messages INTEGER DEFAULT 0
);

-- HUMAN_INTERVENTIONS (Log de intervenções)
CREATE TABLE human_interventions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES conversations(id),
    started_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP,
    reason VARCHAR(255),
    operator_notes TEXT,
    messages_during_intervention JSONB DEFAULT '[]'
);

-- WEBHOOK_LOGS (Logs do Evolution API)
CREATE TABLE webhook_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    event_type VARCHAR(100),
    payload JSONB,
    processed BOOLEAN DEFAULT FALSE,
    error TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- INDEXES
CREATE INDEX idx_orders_tenant_status ON orders(tenant_id, status);
CREATE INDEX idx_customers_whatsapp ON customers(tenant_id, whatsapp_number);
CREATE INDEX idx_conversations_session ON conversations(session_id);
CREATE INDEX idx_conversations_intervention ON conversations(tenant_id, human_intervention);
CREATE INDEX idx_webhook_logs_processed ON webhook_logs(processed, created_at);
CREATE INDEX idx_address_cache_lookup ON address_cache(tenant_id, address_text);
CREATE INDEX idx_neighborhood_lookup ON neighborhood_configs(tenant_id, neighborhood_name);
CREATE INDEX idx_radius_lookup ON radius_configs(tenant_id, radius_km_start, radius_km_end);
CREATE INDEX idx_hybrid_priority ON hybrid_rules(tenant_id, priority);
CREATE INDEX idx_interventions_active ON human_interventions(tenant_id, ended_at);
```

## 🔌 API ENDPOINTS

### Authentication
```
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh
POST   /api/v1/auth/logout
GET    /api/v1/auth/me
```

### Tenant Management
```
GET    /api/v1/tenant
PUT    /api/v1/tenant
POST   /api/v1/tenant/setup
GET    /api/v1/tenant/stats
```

### WhatsApp Integration
```
GET    /api/v1/whatsapp/qr
GET    /api/v1/whatsapp/status
POST   /api/v1/whatsapp/send
POST   /api/v1/whatsapp/disconnect
POST   /api/v1/webhook/evolution
```

### Products
```
GET    /api/v1/products
POST   /api/v1/products
GET    /api/v1/products/{id}
PUT    /api/v1/products/{id}
DELETE /api/v1/products/{id}
POST   /api/v1/products/import
```

### Delivery Configuration
```
GET    /api/v1/delivery/config
PUT    /api/v1/delivery/mode
POST   /api/v1/delivery/neighborhoods
POST   /api/v1/delivery/radius
POST   /api/v1/delivery/hybrid-rules
POST   /api/v1/delivery/validate
```

### Orders
```
GET    /api/v1/orders
GET    /api/v1/orders/{id}
PUT    /api/v1/orders/{id}/status
GET    /api/v1/orders/export
```

### Customers
```
GET    /api/v1/customers
GET    /api/v1/customers/{id}
PUT    /api/v1/customers/{id}
GET    /api/v1/customers/{id}/orders
```

### Conversations & Intervention
```
GET    /api/v1/conversations
GET    /api/v1/conversations/{id}
GET    /api/v1/conversations/{id}/messages
POST   /api/v1/conversations/{id}/intervene
POST   /api/v1/conversations/{id}/resume
POST   /api/v1/conversations/{id}/send
GET    /api/v1/conversations/interventions
```

### Dashboard
```
GET    /api/v1/dashboard/summary
GET    /api/v1/dashboard/revenue
GET    /api/v1/dashboard/orders
GET    /api/v1/dashboard/realtime
```

## 🤖 AGENTES LANGCHAIN - ARQUITETURA

```python
# 1. MASTER AGENT - COM INTERVENÇÃO E ÁUDIO
class MasterAgent:
    def __init__(self):
        self.audio_processor = AudioProcessor()
    
    async def process(self, message, context, tenant_id, customer_phone):
        # Verificar intervenção humana
        conversation = await get_active_conversation(customer_phone, tenant_id)
        
        if conversation.human_intervention:
            time_passed = now() - conversation.intervention_started_at
            if time_passed < timedelta(minutes=5):
                await log_message_during_intervention(message)
                return None
            else:
                await end_human_intervention(conversation)
        
        # Detectar se é intervenção
        if await is_human_intervention(message, tenant_id, customer_phone):
            await start_human_intervention(conversation)
            return None
        
        # Processar áudio se necessário
        if message.get("type") == "audio":
            transcription_result = await self.audio_processor.process_whatsapp_audio(
                message["audio_data"]
            )
            message_text = transcription_result["text"]
        else:
            message_text = message.get("text", "")
        
        # Processar com agentes
        intent = identify_intent(message_text)
        # ... roteamento para agentes específicos

# 2. ATTENDANCE AGENT
class AttendanceAgent:
    """
    Responsável por:
    - Saudações e apresentação
    - Informações gerais
    - Horário de funcionamento
    - Listar produtos disponíveis
    """
    
    async def get_products(self, tenant_id):
        # Cache primeiro
        cached = await redis.get(f"products:{tenant_id}")
        if cached:
            return json.loads(cached)
        
        # Buscar do banco
        products = db.query(Product).filter(
            Product.tenant_id == tenant_id,
            Product.is_available == True
        ).all()
        
        # Salvar cache 5min
        await redis.setex(f"products:{tenant_id}", 300, json.dumps(products))
        return products

# 3. VALIDATION AGENT - SISTEMA HÍBRIDO
class ValidationAgent:
    """
    Valida endereços usando modo escolhido:
    - Por Bairro (cadastro manual)
    - Por Raio/KM (Google Maps)
    - Híbrido (combina os dois)
    """
    
    async def validate_delivery(self, address: str, tenant_id: UUID):
        # Cache de endereço primeiro
        cached = db.query(AddressCache).filter(
            AddressCache.tenant_id == tenant_id,
            AddressCache.address_text == address.lower()
        ).first()
        
        if cached and cached.validated_at > (now() - timedelta(days=30)):
            return cached
        
        # Buscar configuração do tenant
        delivery_config = get_delivery_config(tenant_id)
        
        if delivery_config.delivery_mode == "neighborhood":
            return await self.validate_by_neighborhood(address, tenant_id)
        elif delivery_config.delivery_mode == "radius":
            return await self.validate_by_radius(address, tenant_id)
        elif delivery_config.delivery_mode == "hybrid":
            return await self.validate_hybrid(address, tenant_id)

# 4. ORDER AGENT
class OrderAgent:
    """
    Responsável por:
    - Montar pedido
    - Calcular valores
    - Confirmar itens
    - Gerar resumo
    """
    
    def add_item(self, product_id, quantity, tenant_id):
        product = get_product(product_id, tenant_id)
        return {
            "product": product.name,
            "quantity": quantity,
            "price": product.price,
            "subtotal": product.price * quantity
        }

# 5. PAYMENT AGENT (SIMPLIFICADO)
class PaymentAgent:
    """
    Responsável por:
    - Perguntar forma de pagamento
    - Mostrar chave PIX (se for o caso)
    - Registrar método escolhido
    - Finalizar atendimento
    """
    
    def process_payment_method(self, tenant, method, total):
        if method.lower() == "pix" and tenant.pix_key:
            return f"""
            💰 Total: R$ {total}
            📱 PIX: {tenant.pix_key}
            Nome: {tenant.pix_name}
            """
        elif method.lower() == "dinheiro":
            return "💵 Pagamento em dinheiro na entrega"
        elif method.lower() == "cartão":
            return "💳 Máquina de cartão na entrega"
```

## 🎤 PROCESSAMENTO DE ÁUDIO

```python
# app/services/audio_processor.py
import openai
from typing import Optional
import base64
import tempfile
from pydub import AudioSegment

class AudioProcessor:
    """
    Processa áudios do WhatsApp usando Whisper da OpenAI
    """
    
    def __init__(self):
        self.client = openai.Client()
        
    async def process_whatsapp_audio(self, audio_data: dict) -> str:
        """
        Recebe áudio do Evolution API e transcreve
        """
        # Evolution envia áudio como base64 ou URL
        if audio_data.get("base64"):
            audio_bytes = base64.b64decode(audio_data["base64"])
        elif audio_data.get("url"):
            audio_bytes = await download_audio(audio_data["url"])
        else:
            raise ValueError("Áudio sem dados")
        
        # WhatsApp envia em OGG/OPUS, converter se necessário
        audio_file = await self.prepare_audio(audio_bytes)
        
        # Transcrever com Whisper
        transcription = await self.transcribe(audio_file)
        
        return {
            "text": transcription,
            "type": "audio",
            "duration": audio_data.get("duration"),
            "original_format": "whatsapp_audio"
        }
    
    async def transcribe(self, audio_file) -> str:
        """
        Usa Whisper API da OpenAI para transcrição
        """
        try:
            response = await self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="pt",
                prompt="Transcreva o pedido do cliente. Contexto: distribuidora de gás."
            )
            return response.text
        except Exception as e:
            return "[Áudio não compreendido, peça para repetir]"
```

## 🔄 FLUXO DE CONVERSA TÍPICO

```mermaid
graph TD
    A[Cliente envia mensagem/áudio] --> B[Master Agent]
    B --> C{Intervenção Humana?}
    C -->|Sim| D[Pausa Bot 5min]
    C -->|Não| E{Tipo Mensagem}
    
    E -->|Áudio| F[Whisper Transcreve]
    E -->|Texto| G[Processa Direto]
    
    F --> G
    G --> H{Identificar Intenção}
    
    H -->|Saudação| I[Attendance Agent]
    H -->|Pedido| J[Order Agent]
    H -->|Endereço| K[Validation Agent]
    H -->|Pagamento| L[Payment Agent]
    
    K --> M{Modo Entrega}
    M -->|Bairro| N[Valida por Bairro]
    M -->|Raio| O[Valida por KM]
    M -->|Híbrido| P[Combina Validações]
    
    L --> Q[Mostra PIX/Forma]
    Q --> R[Salva Pedido]
    R --> S[Dashboard]
```

## 🔐 SEGURANÇA

### JWT Configuration
```python
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION = 24 * 60 * 60  # 24 hours
JWT_REFRESH_EXPIRATION = 7 * 24 * 60 * 60  # 7 days

# Token structure
{
    "sub": "user_id",
    "tenant_id": "tenant_uuid",
    "role": "admin",
    "exp": 1234567890
}
```

### Multi-tenant Isolation
```python
# Middleware para toda requisição
async def tenant_middleware(request):
    token = extract_token(request)
    tenant_id = decode_tenant_id(token)
    request.state.tenant_id = tenant_id
    
# Em todas as queries
def get_products(tenant_id: UUID):
    return db.query(Product).filter(
        Product.tenant_id == tenant_id
    ).all()
```

### Rate Limiting
```python
# WhatsApp limits
MAX_MESSAGES_PER_MINUTE = 30
MAX_MESSAGES_PER_DAY = 1000

# API limits
MAX_REQUESTS_PER_MINUTE = 60
MAX_REQUESTS_PER_HOUR = 1000

# Audio limits
MAX_AUDIO_DURATION = 60  # segundos
MAX_AUDIO_SIZE = 10 * 1024 * 1024  # 10MB
```

## 📦 DOCKER SWARM CONFIGURATION

```yaml
# docker-compose.yml (Development)
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://gasbot:password@postgres:5432/gasbot
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
    volumes:
      - ./backend:/app
    command: uvicorn app.main:app --host 0.0.0.0 --reload

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    volumes:
      - ./frontend:/app

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=gasbot
      - POSTGRES_USER=gasbot
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  evolution:
    image: atendai/evolution-api:latest
    ports:
      - "8080:8080"
    environment:
      - NODE_ENV=production
      - DATABASE_URL=postgresql://gasbot:password@postgres:5432/evolution

volumes:
  postgres_data:
  redis_data:
```

```yaml
# docker-stack.yml (Production - Docker Swarm)
version: '3.8'

services:
  backend:
    image: gasbot/backend:latest
    deploy:
      replicas: 2
      restart_policy:
        condition: on-failure
      labels:
        - "traefik.enable=true"
        - "traefik.http.routers.backend.rule=Host(`api.gasbot.com.br`)"
        - "traefik.http.services.backend.loadbalancer.server.port=8000"
        - "traefik.http.routers.backend.tls=true"
        - "traefik.http.routers.backend.tls.certresolver=letsencrypt"
    environment:
      - DATABASE_URL=postgresql://gasbot:${DB_PASSWORD}@postgres:5432/gasbot
      - REDIS_URL=redis://redis:6379
    networks:
      - gasbot-network
      - traefik-public

  frontend:
    image: gasbot/frontend:latest
    deploy:
      replicas: 2
      restart_policy:
        condition: on-failure
      labels:
        - "traefik.enable=true"
        - "traefik.http.routers.frontend.rule=Host(`app.gasbot.com.br`)"
        - "traefik.http.services.frontend.loadbalancer.server.port=3000"
        - "traefik.http.routers.frontend.tls=true"
        - "traefik.http.routers.frontend.tls.certresolver=letsencrypt"
    networks:
      - gasbot-network
      - traefik-public

  postgres:
    image: postgres:15
    deploy:
      placement:
        constraints:
          - node.role == manager
    environment:
      - POSTGRES_DB=gasbot
      - POSTGRES_USER=gasbot
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - gasbot-network

  redis:
    image: redis:7-alpine
    deploy:
      replicas: 1
    volumes:
      - redis_data:/data
    networks:
      - gasbot-network

  evolution:
    image: atendai/evolution-api:latest
    deploy:
      replicas: 1
      labels:
        - "traefik.enable=true"
        - "traefik.http.routers.evolution.rule=Host(`evolution.gasbot.com.br`)"
        - "traefik.http.services.evolution.loadbalancer.server.port=8080"
    networks:
      - gasbot-network
      - traefik-public

networks:
  gasbot-network:
    driver: overlay
    attachable: true
  traefik-public:
    external: true

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
```

## 🚀 DEPLOYMENT CHECKLIST

### Pré-deploy
- [ ] Variáveis de ambiente configuradas
- [ ] SSL/HTTPS configurado via Traefik
- [ ] Backup database configurado
- [ ] Logs centralizados
- [ ] Monitoramento (Uptime)

### Deploy Steps
```bash
# 1. Build images
docker build -t gasbot/backend:latest ./backend
docker build -t gasbot/frontend:latest ./frontend

# 2. Deploy stack
docker stack deploy -c docker-stack.yml gasbot

# 3. Run migrations
docker exec $(docker ps -q -f name=gasbot_backend) alembic upgrade head

# 4. Check health
curl https://api.gasbot.com.br/health
```

### Post-deploy
- [ ] Testar fluxo completo (texto e áudio)
- [ ] Testar intervenção humana
- [ ] Verificar webhooks
- [ ] Testar 3 modos de entrega
- [ ] Monitorar logs primeira hora

## 📚 DEPENDENCIES

# requirements.txt
"""
fastapi==0.109.0
uvicorn==0.27.0
python-dotenv==1.0.0
langchain==0.1.0
langchain-openai==0.0.5
langgraph==0.0.20
redis==5.0.1
celery==5.3.4
sqlalchemy==2.0.25
asyncpg==0.29.0
pydantic==2.5.3
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
aiohttp==3.9.1
googlemaps==4.10.0
psycopg2-binary==2.9.9
alembic==1.13.1
httpx==0.25.0
openai==1.6.0
pydub==0.25.1
"""

# .env.example
"""
# Database
DATABASE_URL=postgresql://gasbot:password@localhost/gasbot
REDIS_URL=redis://localhost:6379

# APIs
OPENAI_API_KEY=sk-...
GOOGLE_MAPS_API_KEY=AIza...
EVOLUTION_API_URL=http://localhost:8080
EVOLUTION_API_KEY=your-evolution-key

# Security
JWT_SECRET_KEY=your-super-secret-key-change-this

# App Config
WEBHOOK_URL=https://api.gasbot.com.br/webhook
TRIAL_DAYS=7
ADDRESS_CACHE_DAYS=30
"""

# app/core/config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    REDIS_URL: str
    
    # APIs
    OPENAI_API_KEY: str
    GOOGLE_MAPS_API_KEY: str
    EVOLUTION_API_URL: str
    EVOLUTION_API_KEY: str
    
    # Security
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # App
    WEBHOOK_URL: str
    TRIAL_DAYS: int = 7
    
    # Cache
    ADDRESS_CACHE_DAYS: int = 30
    
    class Config:
        env_file = ".env"

settings = Settings()