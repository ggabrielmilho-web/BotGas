# 📝 SESSÃO 3 - SISTEMA DE AUTENTICAÇÃO JWT MULTI-TENANT

## ✅ STATUS: COMPLETO

## 📁 ARQUIVOS CRIADOS

### 1. backend/app/core/security.py
**Funções de segurança e JWT**
- `verify_password()` - Valida senha com hash
- `get_password_hash()` - Cria hash de senha
- `create_access_token()` - Gera token de acesso (24h)
- `create_refresh_token()` - Gera token de refresh (7 dias)
- `decode_token()` - Decodifica e valida JWT
- `verify_token_type()` - Verifica tipo do token
- `create_token_pair()` - Cria par access + refresh tokens

**Configuração:**
- Algoritmo: HS256
- Access token: 24 horas
- Refresh token: 7 dias
- Hash: bcrypt

---

### 2. backend/app/services/tenant.py
**Serviço de gerenciamento de tenants**

**Métodos principais:**
- `create_tenant()` - Cria tenant + admin user + trial 7 dias
- `get_tenant_by_id()` - Busca tenant por UUID
- `get_tenant_by_cnpj()` - Busca por CNPJ
- `update_tenant()` - Atualiza dados do tenant
- `is_trial_active()` - Verifica se trial está ativo
- `is_subscription_active()` - Verifica subscription (trial ou paga)
- `update_whatsapp_connection()` - Atualiza status WhatsApp
- `get_tenant_stats()` - Retorna estatísticas do tenant

**Features importantes:**
- Trial automático de 7 dias no registro
- Validação de CNPJ único
- Criação automática de usuário admin
- Multi-tenant desde o início

---

### 3. backend/app/middleware/tenant.py
**Middleware e dependencies para isolamento multi-tenant**

**Dependencies:**
- `get_current_user()` - Extrai usuário do JWT
- `get_current_tenant()` - Extrai tenant do usuário
- `verify_subscription()` - Valida subscription ativa
- `get_current_active_user()` - Combinação: user + subscription ativa

**Middleware:**
- `TenantMiddleware` - Adiciona tenant_id ao request.state

**Funções helper:**
- `get_tenant_id_from_request()` - Extrai tenant_id do request
- `ensure_tenant_isolation()` - Garante isolamento entre tenants

**Segurança:**
- Validação automática de JWT em todas rotas protegidas
- Isolamento de dados por tenant_id
- Verificação de usuário ativo
- Verificação de subscription válida

---

### 4. backend/app/api/auth.py
**Endpoints de autenticação**

#### POST /api/v1/auth/register
- Registra novo tenant + admin user
- Cria trial de 7 dias
- Retorna tokens JWT
- **Status:** 201 Created

#### POST /api/v1/auth/login
- Autentica usuário
- Valida credenciais
- Retorna access + refresh tokens
- **Status:** 200 OK

#### POST /api/v1/auth/refresh
- Renova access token usando refresh token
- Retorna novo par de tokens
- **Status:** 200 OK

#### GET /api/v1/auth/me
- Retorna dados do usuário logado
- Requer: Bearer token
- **Status:** 200 OK

#### POST /api/v1/auth/logout
- Logout (client-side remove tokens)
- **Status:** 200 OK

**Validações:**
- Email único
- CNPJ único (opcional)
- Senha mínimo 6 caracteres
- Telefone formato internacional
- CNPJ exatamente 14 dígitos

---

### 5. backend/app/api/tenant.py
**Endpoints de gerenciamento de tenant**

#### GET /api/v1/tenant
- Retorna dados do tenant atual
- Requer: Bearer token
- **Status:** 200 OK

#### PUT /api/v1/tenant
- Atualiza dados do tenant
- Campos permitidos: company_name, phone, email, address, payment_methods, pix_*
- Requer: Bearer token
- **Status:** 200 OK

#### GET /api/v1/tenant/stats
- Retorna estatísticas: pedidos, clientes, produtos
- Info de trial/subscription
- Requer: Bearer token
- **Status:** 200 OK

#### POST /api/v1/tenant/setup
- Marca onboarding como completo
- Requer: Bearer token
- **Status:** 200 OK

---

### 6. backend/app/api/__init__.py
- Package marker para API routes

---

### 7. backend/app/main.py (ATUALIZADO)
**Alterações:**
- Importado `TenantMiddleware`
- Importados routers: `auth`, `tenant`
- Adicionado middleware de tenant
- Registrados routers no app

---

## 🔐 FLUXO DE AUTENTICAÇÃO

```
1. REGISTRO
   POST /api/v1/auth/register
   → Cria Tenant
   → Cria User (admin)
   → Trial 7 dias
   → Retorna tokens JWT

2. LOGIN
   POST /api/v1/auth/login
   → Valida credenciais
   → Retorna access + refresh tokens

3. ACESSO PROTEGIDO
   GET /api/v1/tenant (exemplo)
   Header: Authorization: Bearer {access_token}
   → Middleware extrai tenant_id
   → Dependency valida user
   → Dependency valida tenant
   → Dependency verifica subscription
   → Executa endpoint com isolamento

4. REFRESH TOKEN
   POST /api/v1/auth/refresh
   Body: {refresh_token}
   → Valida refresh token
   → Retorna novo par de tokens
```

---

## 🛡️ ISOLAMENTO MULTI-TENANT

**Garantias:**
1. Todo request tem `tenant_id` no state (via middleware)
2. Toda query ao banco DEVE filtrar por `tenant_id`
3. Dependencies validam tenant automaticamente
4. Impossível acessar dados de outro tenant

**Exemplo de query segura:**
```python
# CORRETO ✅
products = db.query(Product).filter(
    Product.tenant_id == current_tenant.id
).all()

# ERRADO ❌ (vaza dados entre tenants)
products = db.query(Product).all()
```

---

## 🧪 COMO TESTAR

### 1. Registrar novo tenant
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Distribuidora ABC",
    "email": "admin@abc.com",
    "password": "senha123",
    "phone": "+5511999999999",
    "cnpj": "12345678901234"
  }'
```

**Resposta esperada:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

### 2. Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@abc.com",
    "password": "senha123"
  }'
```

### 3. Acessar dados do usuário
```bash
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer {access_token}"
```

### 4. Acessar tenant
```bash
curl -X GET http://localhost:8000/api/v1/tenant \
  -H "Authorization: Bearer {access_token}"
```

### 5. Atualizar tenant (configurar PIX)
```bash
curl -X PUT http://localhost:8000/api/v1/tenant \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "pix_enabled": true,
    "pix_key": "12345678901234",
    "pix_name": "Distribuidora ABC LTDA",
    "payment_methods": ["Dinheiro", "PIX", "Cartão"]
  }'
```

---

## 📊 ESTRUTURA DO TOKEN JWT

**Access Token:**
```json
{
  "sub": "user-uuid",
  "tenant_id": "tenant-uuid",
  "role": "admin",
  "type": "access",
  "exp": 1234567890
}
```

**Refresh Token:**
```json
{
  "sub": "user-uuid",
  "tenant_id": "tenant-uuid",
  "type": "refresh",
  "exp": 1234567890
}
```

---

## ⚙️ VARIÁVEIS DE AMBIENTE NECESSÁRIAS

```env
# Security
JWT_SECRET_KEY=your-super-secret-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Database (já configurado na sessão 2)
DATABASE_URL=postgresql://gasbot:password@localhost/gasbot
```

---

## 🚀 PRÓXIMOS PASSOS (SESSÃO 4)

- [ ] Integrar Evolution API para WhatsApp
- [ ] Criar endpoints de QR Code
- [ ] Implementar webhook do WhatsApp
- [ ] Processador de áudio (Whisper)
- [ ] Gestão de instâncias WhatsApp

---

## ✅ CHECKLIST SESSÃO 3

- [x] Sistema de hashing de senhas (bcrypt)
- [x] Criação e validação de JWT tokens
- [x] Endpoints de registro e login
- [x] Refresh token flow
- [x] Multi-tenant middleware
- [x] Dependencies para proteção de rotas
- [x] Isolamento automático por tenant_id
- [x] Validação de subscription/trial
- [x] Endpoints de gerenciamento de tenant
- [x] Trial automático de 7 dias
- [x] Estatísticas do tenant
- [x] Integração no main.py

---

## 📝 NOTAS IMPORTANTES

1. **Segurança:**
   - SEMPRE use dependencies `get_current_user` e `get_current_tenant` em rotas protegidas
   - NUNCA faça queries sem filtrar por `tenant_id`
   - JWT_SECRET_KEY deve ser alterado em produção

2. **Multi-tenant:**
   - Tenant é criado automaticamente no registro
   - Cada tenant tem trial de 7 dias
   - Isolamento total entre tenants

3. **Trial:**
   - 7 dias gratuitos
   - Verificação automática via `verify_subscription()`
   - Retorna 402 Payment Required se expirado

4. **Próxima sessão:**
   - Vamos integrar WhatsApp via Evolution API
   - Precisaremos do Evolution rodando (porta 8080)
   - Configurar webhooks para receber mensagens
