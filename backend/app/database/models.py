"""
SQLAlchemy Models for GasBot
"""
import uuid
from datetime import datetime
from sqlalchemy import (
    Boolean, Column, DateTime, String, Text, Integer,
    Numeric, ForeignKey, ARRAY, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.base import Base


# ============================================================================
# TENANTS (Empresas/Distribuidoras)
# ============================================================================

class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_name = Column(String(255), nullable=False)
    cnpj = Column(String(14), unique=True)
    phone = Column(String(20), nullable=False)
    email = Column(String(255), nullable=False)
    address = Column(JSON)

    # WhatsApp
    whatsapp_instance_id = Column(String(255), unique=True)
    whatsapp_connected = Column(Boolean, default=False)

    # Subscription
    trial_ends_at = Column(DateTime)
    subscription_status = Column(String(50), default='trial')
    subscription_plan = Column(String(50))

    # Payment Config
    payment_methods = Column(JSON, default=['Dinheiro'])
    pix_enabled = Column(Boolean, default=False)
    pix_key = Column(String(255))
    pix_name = Column(String(255))
    payment_instructions = Column(Text)

    # Metadata
    settings = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="tenant", cascade="all, delete-orphan")
    delivery_areas = relationship("DeliveryArea", back_populates="tenant", cascade="all, delete-orphan")
    customers = relationship("Customer", back_populates="tenant", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="tenant", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="tenant", cascade="all, delete-orphan")


# ============================================================================
# USERS (Usuários do Sistema)
# ============================================================================

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    email = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(String(50), default='admin')
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant", back_populates="users")


# ============================================================================
# PRODUCTS (Produtos)
# ============================================================================

class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    price = Column(Numeric(10, 2), nullable=False)
    category = Column(String(100))
    image_url = Column(String(500))
    is_available = Column(Boolean, default=True)
    stock_quantity = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant", back_populates="products")


# ============================================================================
# DELIVERY AREAS (Configuração de Entrega)
# ============================================================================

class DeliveryArea(Base):
    __tablename__ = "delivery_areas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    delivery_mode = Column(String(50), default='neighborhood')  # neighborhood, radius, hybrid
    free_delivery_minimum = Column(Numeric(10, 2))
    default_fee = Column(Numeric(10, 2), default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant", back_populates="delivery_areas")
    neighborhood_configs = relationship("NeighborhoodConfig", back_populates="delivery_area", cascade="all, delete-orphan")
    radius_configs = relationship("RadiusConfig", back_populates="delivery_area", cascade="all, delete-orphan")
    hybrid_rules = relationship("HybridRule", back_populates="delivery_area", cascade="all, delete-orphan")


class NeighborhoodConfig(Base):
    __tablename__ = "neighborhood_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    delivery_area_id = Column(UUID(as_uuid=True), ForeignKey("delivery_areas.id", ondelete="CASCADE"), nullable=False)
    neighborhood_name = Column(String(255), nullable=False)
    city = Column(String(255), default='São Paulo')
    state = Column(String(2), default='SP')
    delivery_type = Column(String(50), default='paid')  # free, paid, not_available
    delivery_fee = Column(Numeric(10, 2), default=0)
    delivery_time_minutes = Column(Integer, default=60)
    zip_codes = Column(ARRAY(Text))
    is_active = Column(Boolean, default=True)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    delivery_area = relationship("DeliveryArea", back_populates="neighborhood_configs")


class RadiusConfig(Base):
    __tablename__ = "radius_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    delivery_area_id = Column(UUID(as_uuid=True), ForeignKey("delivery_areas.id", ondelete="CASCADE"), nullable=False)
    center_address = Column(String(500), nullable=False)
    center_lat = Column(Numeric(10, 8))
    center_lng = Column(Numeric(11, 8))
    radius_km_start = Column(Numeric(5, 2), nullable=False)
    radius_km_end = Column(Numeric(5, 2), nullable=False)
    delivery_fee = Column(Numeric(10, 2), nullable=False)
    delivery_time_minutes = Column(Integer, default=60)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    delivery_area = relationship("DeliveryArea", back_populates="radius_configs")


class HybridRule(Base):
    __tablename__ = "hybrid_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    delivery_area_id = Column(UUID(as_uuid=True), ForeignKey("delivery_areas.id", ondelete="CASCADE"), nullable=False)
    priority = Column(Integer, default=100)
    rule_type = Column(String(50))
    config = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    delivery_area = relationship("DeliveryArea", back_populates="hybrid_rules")


# ============================================================================
# CUSTOMERS (Clientes via WhatsApp)
# ============================================================================

class Customer(Base):
    __tablename__ = "customers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    whatsapp_number = Column(String(20), nullable=False)
    name = Column(String(255))
    addresses = Column(JSON, default=[])
    order_count = Column(Integer, default=0)
    total_spent = Column(Numeric(10, 2), default=0)
    tags = Column(ARRAY(Text))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_order_at = Column(DateTime)

    # Relationships
    tenant = relationship("Tenant", back_populates="customers")
    orders = relationship("Order", back_populates="customer", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="customer", cascade="all, delete-orphan")


# ============================================================================
# ADDRESS CACHE (Cache de endereços validados)
# ============================================================================

class AddressCache(Base):
    __tablename__ = "address_cache"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    address_text = Column(String(500), nullable=False)
    normalized_address = Column(String(500))
    coordinates = Column(JSON)
    neighborhood = Column(String(255))
    city = Column(String(255))
    state = Column(String(2))
    zip_code = Column(String(10))
    delivery_area_id = Column(UUID(as_uuid=True), ForeignKey("delivery_areas.id"))
    delivery_fee = Column(Numeric(10, 2))
    is_deliverable = Column(Boolean, default=True)
    validated_at = Column(DateTime, default=datetime.utcnow)
    google_place_id = Column(String(255))


# ============================================================================
# DELIVERY DRIVERS (Motoboys)
# ============================================================================

class DeliveryDriver(Base):
    __tablename__ = "delivery_drivers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=False)
    is_active = Column(Boolean, default=True)
    total_deliveries = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant")


# ============================================================================
# ORDERS (Pedidos)
# ============================================================================

class Order(Base):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"))
    order_number = Column(Integer, autoincrement=True)
    status = Column(String(50), default='new')  # new, confirmed, preparing, delivering, delivered, cancelled
    items = Column(JSON, nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)
    delivery_fee = Column(Numeric(10, 2), default=0)
    total = Column(Numeric(10, 2), nullable=False)
    delivery_address = Column(JSON)
    payment_method = Column(String(50))
    notes = Column(Text)
    driver_name = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    delivered_at = Column(DateTime)

    # Relationships
    tenant = relationship("Tenant", back_populates="orders")
    customer = relationship("Customer", back_populates="orders")


# ============================================================================
# CONVERSATIONS (Histórico de Conversas)
# ============================================================================

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"))
    session_id = Column(String(255), nullable=False)
    messages = Column(JSON, default=[])
    context = Column(JSON, default={})
    status = Column(String(50), default='active')  # active, completed, abandoned
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime)

    # Human Intervention
    human_intervention = Column(Boolean, default=False)
    intervention_started_at = Column(DateTime)
    intervention_ended_at = Column(DateTime)
    last_bot_message_at = Column(DateTime)

    total_messages = Column(Integer, default=0)

    # Relationships
    tenant = relationship("Tenant", back_populates="conversations")
    customer = relationship("Customer", back_populates="conversations")
    interventions = relationship("HumanIntervention", back_populates="conversation", cascade="all, delete-orphan")


# ============================================================================
# HUMAN INTERVENTIONS (Log de intervenções)
# ============================================================================

class HumanIntervention(Base):
    __tablename__ = "human_interventions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"))
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime)
    reason = Column(String(255))
    operator_notes = Column(Text)
    messages_during_intervention = Column(JSON, default=[])

    # Relationships
    conversation = relationship("Conversation", back_populates="interventions")


# ============================================================================
# WEBHOOK LOGS (Logs do Evolution API)
# ============================================================================

class WebhookLog(Base):
    __tablename__ = "webhook_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"))
    event_type = Column(String(100))
    payload = Column(JSON)
    processed = Column(Boolean, default=False)
    error = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
