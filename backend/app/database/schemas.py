"""
Pydantic Schemas for Request/Response Validation
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ============================================================================
# TENANT SCHEMAS
# ============================================================================

class TenantBase(BaseModel):
    company_name: str
    cnpj: Optional[str] = None
    phone: str
    email: EmailStr
    address: Optional[Dict[str, Any]] = None


class TenantCreate(TenantBase):
    pass


class TenantUpdate(BaseModel):
    company_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[Dict[str, Any]] = None
    payment_methods: Optional[List[str]] = None
    pix_enabled: Optional[bool] = None
    pix_key: Optional[str] = None
    pix_name: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class TenantResponse(TenantBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    whatsapp_connected: bool
    subscription_status: str
    trial_ends_at: Optional[datetime] = None
    created_at: datetime


# ============================================================================
# USER SCHEMAS
# ============================================================================

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: str = 'admin'


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    is_active: bool
    created_at: datetime


# ============================================================================
# PRODUCT SCHEMAS
# ============================================================================

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: Decimal = Field(..., gt=0)
    category: Optional[str] = None
    image_url: Optional[str] = None
    is_available: bool = True
    stock_quantity: Optional[int] = None


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = Field(None, gt=0)
    category: Optional[str] = None
    image_url: Optional[str] = None
    is_available: Optional[bool] = None
    stock_quantity: Optional[int] = None


class ProductResponse(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime


# ============================================================================
# DELIVERY AREA SCHEMAS
# ============================================================================

class NeighborhoodConfigBase(BaseModel):
    neighborhood_name: str
    city: str = 'São Paulo'
    state: str = 'SP'
    delivery_type: str = 'paid'
    delivery_fee: Decimal = Field(default=0, ge=0)
    delivery_time_minutes: int = 60
    zip_codes: Optional[List[str]] = None
    is_active: bool = True
    notes: Optional[str] = None


class NeighborhoodConfigCreate(NeighborhoodConfigBase):
    pass


class NeighborhoodConfigResponse(NeighborhoodConfigBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    delivery_area_id: UUID
    created_at: datetime


class RadiusConfigBase(BaseModel):
    center_address: str
    center_lat: Optional[Decimal] = Field(None, ge=-90, le=90)
    center_lng: Optional[Decimal] = Field(None, ge=-180, le=180)
    radius_km_start: Decimal = Field(..., ge=0)
    radius_km_end: Decimal = Field(..., gt=0)
    delivery_fee: Decimal = Field(..., ge=0)
    delivery_time_minutes: int = 60
    is_active: bool = True


class RadiusConfigCreate(RadiusConfigBase):
    pass


class RadiusConfigResponse(RadiusConfigBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    delivery_area_id: UUID
    created_at: datetime


class DeliveryAreaBase(BaseModel):
    delivery_mode: str = Field(default='neighborhood', pattern='^(neighborhood|radius|hybrid)$')
    free_delivery_minimum: Optional[Decimal] = Field(None, ge=0)
    default_fee: Decimal = Field(default=0, ge=0)


class DeliveryAreaCreate(DeliveryAreaBase):
    pass


class DeliveryAreaResponse(DeliveryAreaBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime


# ============================================================================
# CUSTOMER SCHEMAS
# ============================================================================

class CustomerBase(BaseModel):
    whatsapp_number: str
    name: Optional[str] = None
    addresses: Optional[List[Dict[str, Any]]] = []
    tags: Optional[List[str]] = None
    notes: Optional[str] = None


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    addresses: Optional[List[Dict[str, Any]]] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None


class CustomerResponse(CustomerBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    order_count: int
    total_spent: Decimal
    created_at: datetime
    last_order_at: Optional[datetime] = None


# ============================================================================
# ORDER SCHEMAS
# ============================================================================

class OrderItemSchema(BaseModel):
    product_id: UUID
    product_name: str
    quantity: int = Field(..., gt=0)
    price: Decimal = Field(..., gt=0)
    subtotal: Decimal = Field(..., gt=0)


class OrderBase(BaseModel):
    items: List[OrderItemSchema]
    delivery_address: Dict[str, Any]
    payment_method: str
    notes: Optional[str] = None


class OrderCreate(OrderBase):
    customer_id: UUID
    subtotal: Decimal = Field(..., gt=0)
    delivery_fee: Decimal = Field(default=0, ge=0)
    total: Decimal = Field(..., gt=0)


class OrderUpdate(BaseModel):
    status: Optional[str] = Field(None, pattern='^(new|confirmed|preparing|delivering|delivered|cancelled)$')
    notes: Optional[str] = None


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    customer_id: UUID
    order_number: int
    status: str
    items: List[Dict[str, Any]]
    subtotal: Decimal
    delivery_fee: Decimal
    total: Decimal
    delivery_address: Dict[str, Any]
    payment_method: str
    notes: Optional[str] = None
    created_at: datetime
    delivered_at: Optional[datetime] = None


# ============================================================================
# CONVERSATION SCHEMAS
# ============================================================================

class ConversationMessage(BaseModel):
    role: str  # user, assistant, system
    content: str
    timestamp: datetime
    message_type: Optional[str] = 'text'  # text, audio, image
    audio_transcription: Optional[str] = None


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    customer_id: UUID
    session_id: str
    messages: List[Dict[str, Any]]
    status: str
    human_intervention: bool
    started_at: datetime
    ended_at: Optional[datetime] = None


# ============================================================================
# ADDRESS CACHE SCHEMAS
# ============================================================================

class AddressCacheCreate(BaseModel):
    address_text: str
    normalized_address: Optional[str] = None
    coordinates: Optional[Dict[str, Any]] = None
    neighborhood: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    delivery_fee: Optional[Decimal] = None
    is_deliverable: bool = True
    google_place_id: Optional[str] = None


class AddressCacheResponse(AddressCacheCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    validated_at: datetime


# ============================================================================
# WEBHOOK LOG SCHEMAS
# ============================================================================

class WebhookLogCreate(BaseModel):
    event_type: str
    payload: Dict[str, Any]
    tenant_id: Optional[UUID] = None


class WebhookLogResponse(WebhookLogCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    processed: bool
    error: Optional[str] = None
    created_at: datetime


# ============================================================================
# DASHBOARD SCHEMAS
# ============================================================================

class DashboardSummary(BaseModel):
    """Resumo do dashboard com métricas principais"""
    orders_today: int
    revenue_today: float
    pending_orders: int
    active_conversations: int
    active_interventions: int
    total_customers: int


# ============================================================================
# AUTH SCHEMAS
# ============================================================================

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: Optional[str] = None


class TokenPayload(BaseModel):
    sub: UUID
    tenant_id: UUID
    role: str
    exp: int


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    company_name: str
    phone: str
