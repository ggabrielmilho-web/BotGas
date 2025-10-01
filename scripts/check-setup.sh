#!/bin/bash
# Script de verificação do ambiente - Sessão 1

echo "🔍 VERIFICANDO AMBIENTE GASBOT..."
echo ""

# Verificar Docker
echo "1️⃣ Docker:"
docker --version
echo ""

# Verificar containers rodando
echo "2️⃣ Containers:"
docker-compose ps
echo ""

# Verificar backend
echo "3️⃣ Backend API (http://localhost:8000):"
curl -s http://localhost:8000/health | jq '.' || echo "❌ Backend não respondeu"
echo ""

# Verificar PostgreSQL
echo "4️⃣ PostgreSQL (localhost:5432):"
docker exec gasbot-postgres-1 pg_isready -U gasbot || echo "❌ PostgreSQL não está pronto"
echo ""

# Verificar Redis
echo "5️⃣ Redis (localhost:6379):"
docker exec gasbot-redis-1 redis-cli ping || echo "❌ Redis não respondeu"
echo ""

# Verificar frontend
echo "6️⃣ Frontend (http://localhost:3000):"
curl -s -I http://localhost:3000 | head -1 || echo "❌ Frontend não respondeu"
echo ""

# Verificar Evolution API
echo "7️⃣ Evolution API (http://localhost:8080):"
curl -s -I http://localhost:8080 | head -1 || echo "❌ Evolution não respondeu"
echo ""

echo "✅ Verificação concluída!"
