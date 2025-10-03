from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.middleware.tenant import TenantMiddleware

# Import routers
from app.api import auth, tenant, whatsapp, delivery, dashboard, conversations, trial, products
from app.webhooks import whatsapp as whatsapp_webhook

app = FastAPI(
    title="GasBot API",
    description="Sistema SaaS de Atendimento Automatizado para Distribuidoras via WhatsApp",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tenant middleware for multi-tenant isolation
app.add_middleware(TenantMiddleware)

# Include routers
app.include_router(auth.router)
app.include_router(tenant.router)
app.include_router(whatsapp.router)
app.include_router(delivery.router)
app.include_router(dashboard.router)
app.include_router(conversations.router)
app.include_router(trial.router)
app.include_router(products.router)
app.include_router(whatsapp_webhook.router)

@app.get("/")
async def root():
    return {"message": "GasBot API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)