/**
 * API Client for GasBot
 * Centralized HTTP client with auth and error handling
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface RequestOptions extends RequestInit {
  requiresAuth?: boolean;
}

class ApiError extends Error {
  constructor(public status: number, message: string, public data?: any) {
    super(message);
    this.name = 'ApiError';
  }
}

/**
 * Get auth token from localStorage
 */
function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('auth_token');
}

/**
 * Set auth token in localStorage
 */
export function setAuthToken(token: string): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem('auth_token', token);
}

/**
 * Remove auth token from localStorage
 */
export function clearAuthToken(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem('auth_token');
}

/**
 * Base fetch wrapper with auth and error handling
 */
async function fetchApi<T>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const { requiresAuth = true, headers, ...restOptions } = options;

  const url = `${API_BASE_URL}${endpoint}`;

  const requestHeaders: HeadersInit = {
    'Content-Type': 'application/json',
    ...headers,
  };

  // Add auth token if required
  if (requiresAuth) {
    const token = getAuthToken();
    if (token) {
      requestHeaders['Authorization'] = `Bearer ${token}`;
    }
  }

  try {
    const response = await fetch(url, {
      ...restOptions,
      headers: requestHeaders,
    });

    // Handle non-JSON responses
    const contentType = response.headers.get('content-type');
    if (!contentType || !contentType.includes('application/json')) {
      if (!response.ok) {
        throw new ApiError(response.status, `HTTP error! status: ${response.status}`);
      }
      return {} as T;
    }

    const data = await response.json();

    if (!response.ok) {
      throw new ApiError(
        response.status,
        data.detail || data.message || 'Request failed',
        data
      );
    }

    return data;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }

    // Network or other errors
    throw new ApiError(
      0,
      error instanceof Error ? error.message : 'Network error',
      error
    );
  }
}

// ============================================================================
// AUTH API
// ============================================================================

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: {
    id: string;
    email: string;
    full_name: string;
    tenant_id: string;
  };
}

export interface RegisterRequest {
  company_name: string;
  email: string;
  password: string;
  phone: string;
  cnpj?: string;
}

export const authApi = {
  login: (data: LoginRequest) =>
    fetchApi<LoginResponse>('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify(data),
      requiresAuth: false,
    }),

  register: (data: RegisterRequest) =>
    fetchApi<LoginResponse>('/api/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
      requiresAuth: false,
    }),

  me: () => fetchApi<LoginResponse['user']>('/api/v1/auth/me'),
};

// ============================================================================
// TENANT API
// ============================================================================

export interface TenantData {
  id: string;
  company_name: string;
  cnpj?: string;
  phone: string;
  email: string;
  whatsapp_connected: boolean;
  whatsapp_instance_id?: string;
  trial_ends_at?: string;
  subscription_status: string;
}

export interface UpdateTenantRequest {
  company_name?: string;
  phone?: string;
  pix_enabled?: boolean;
  pix_key?: string;
  pix_name?: string;
  payment_methods?: string[];
  payment_instructions?: string;
}

export const tenantApi = {
  get: () => fetchApi<TenantData>('/api/v1/tenant'),

  update: (data: UpdateTenantRequest) =>
    fetchApi<TenantData>('/api/v1/tenant', {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
};

// ============================================================================
// WHATSAPP API
// ============================================================================

export interface QRCodeResponse {
  qr_code: string;
  instance_id: string;
  status: string;
}

export interface WhatsAppStatusResponse {
  connected: boolean;
  instance_id?: string;
  phone_number?: string;
}

export const whatsappApi = {
  getQRCode: () => fetchApi<QRCodeResponse>('/api/v1/whatsapp/qr'),

  getStatus: () => fetchApi<WhatsAppStatusResponse>('/api/v1/whatsapp/status'),

  disconnect: () =>
    fetchApi<{ success: boolean }>('/api/v1/whatsapp/disconnect', {
      method: 'POST',
    }),
};

// ============================================================================
// PRODUCTS API
// ============================================================================

export interface Product {
  id: string;
  name: string;
  description?: string;
  price: number;
  category?: string;
  image_url?: string;
  is_available: boolean;
  stock_quantity?: number;
}

export interface CreateProductRequest {
  name: string;
  description?: string;
  price: number;
  category?: string;
  is_available?: boolean;
}

export const productsApi = {
  list: () => fetchApi<Product[]>('/api/v1/products'),

  create: (data: CreateProductRequest) =>
    fetchApi<Product>('/api/v1/products', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  update: (id: string, data: Partial<CreateProductRequest>) =>
    fetchApi<Product>(`/api/v1/products/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  delete: (id: string) =>
    fetchApi<{ success: boolean }>(`/api/v1/products/${id}`, {
      method: 'DELETE',
    }),
};

// ============================================================================
// DELIVERY API
// ============================================================================

export interface DeliveryConfig {
  id: string;
  delivery_mode: 'neighborhood' | 'radius' | 'hybrid';
  free_delivery_minimum?: number;
  default_fee?: number;
}

export interface Neighborhood {
  id: string;
  neighborhood_name: string;
  city: string;
  state: string;
  delivery_type: 'free' | 'paid' | 'not_available';
  delivery_fee: number;
  delivery_time_minutes: number;
  is_active: boolean;
}

export interface RadiusConfig {
  id: string;
  center_address: string;
  center_lat?: number;
  center_lng?: number;
  radius_km_start: number;
  radius_km_end: number;
  delivery_fee: number;
  delivery_time_minutes: number;
  is_active: boolean;
}

export interface CreateNeighborhoodRequest {
  neighborhood_name: string;
  city?: string;
  state?: string;
  delivery_type: 'free' | 'paid' | 'not_available';
  delivery_fee: number;
  delivery_time_minutes?: number;
}

export interface CreateRadiusConfigRequest {
  center_address: string;
  radius_km_start: number;
  radius_km_end: number;
  delivery_fee: number;
  delivery_time_minutes?: number;
}

export interface HybridSetupRequest {
  center_address: string;
  main_neighborhoods: Array<{
    name: string;
    fee: number;
    time: number;
    delivery_type?: string;
  }>;
  radius_tiers: Array<{
    start: number;
    end: number;
    fee: number;
    time: number;
  }>;
}

export const deliveryApi = {
  getConfig: () => fetchApi<DeliveryConfig>('/api/v1/delivery/config'),

  updateMode: (mode: 'neighborhood' | 'radius' | 'hybrid', freeDeliveryMin?: number) =>
    fetchApi<{ success: boolean; config: DeliveryConfig }>('/api/v1/delivery/mode', {
      method: 'PUT',
      body: JSON.stringify({
        delivery_mode: mode,
        free_delivery_minimum: freeDeliveryMin,
      }),
    }),

  // Neighborhoods
  listNeighborhoods: () => fetchApi<Neighborhood[]>('/api/v1/delivery/neighborhoods'),

  createNeighborhood: (data: CreateNeighborhoodRequest) =>
    fetchApi<{ success: boolean; neighborhood: Neighborhood }>('/api/v1/delivery/neighborhoods', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  bulkCreateNeighborhoods: (neighborhoods: any[]) =>
    fetchApi<{ success: boolean; neighborhoods: Neighborhood[] }>('/api/v1/delivery/neighborhoods/bulk', {
      method: 'POST',
      body: JSON.stringify({ neighborhoods }),
    }),

  updateNeighborhood: (id: string, data: Partial<CreateNeighborhoodRequest>) =>
    fetchApi<{ success: boolean; neighborhood: Neighborhood }>(`/api/v1/delivery/neighborhoods/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  deleteNeighborhood: (id: string) =>
    fetchApi<{ success: boolean }>(`/api/v1/delivery/neighborhoods/${id}`, {
      method: 'DELETE',
    }),

  // Radius configs
  listRadiusConfigs: () => fetchApi<RadiusConfig[]>('/api/v1/delivery/radius'),

  createRadiusConfig: (data: CreateRadiusConfigRequest) =>
    fetchApi<{ success: boolean; config: RadiusConfig }>('/api/v1/delivery/radius', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  bulkCreateRadiusConfigs: (centerAddress: string, tiers: any[]) =>
    fetchApi<{ success: boolean; configs: RadiusConfig[] }>('/api/v1/delivery/radius/bulk', {
      method: 'POST',
      body: JSON.stringify({
        center_address: centerAddress,
        radius_tiers: tiers,
      }),
    }),

  updateRadiusConfig: (id: string, data: Partial<CreateRadiusConfigRequest>) =>
    fetchApi<{ success: boolean; config: RadiusConfig }>(`/api/v1/delivery/radius/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  deleteRadiusConfig: (id: string) =>
    fetchApi<{ success: boolean }>(`/api/v1/delivery/radius/${id}`, {
      method: 'DELETE',
    }),

  // Hybrid setup
  setupHybrid: (data: HybridSetupRequest) =>
    fetchApi<{ success: boolean; message: string }>('/api/v1/delivery/hybrid/setup', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  getStats: () =>
    fetchApi<{
      total_neighborhoods: number;
      deliverable_neighborhoods: number;
      radius_configs: number;
      cached_addresses: number;
    }>('/api/v1/delivery/hybrid/stats'),
};

// ============================================================================
// DASHBOARD API
// ============================================================================

export const dashboardApi = {
  getSummary: () => fetchApi<any>('/api/v1/dashboard/summary'),

  getConversations: () => fetchApi<any[]>('/api/v1/dashboard/conversations'),

  getOrders: () => fetchApi<any[]>('/api/v1/dashboard/orders'),
};

// ============================================================================
// Generic HTTP methods
// ============================================================================

export const httpApi = {
  get: <T>(url: string) => fetchApi<T>(url, { method: 'GET' }),
  post: <T>(url: string, data?: any) => fetchApi<T>(url, { method: 'POST', body: data ? JSON.stringify(data) : undefined }),
  put: <T>(url: string, data?: any) => fetchApi<T>(url, { method: 'PUT', body: data ? JSON.stringify(data) : undefined }),
  delete: <T>(url: string) => fetchApi<T>(url, { method: 'DELETE' }),
};

// Default export com todas as APIs
const api = {
  auth: authApi,
  tenant: tenantApi,
  whatsapp: whatsappApi,
  products: productsApi,
  delivery: deliveryApi,
  dashboard: dashboardApi,
  // Generic HTTP methods
  get: httpApi.get,
  post: httpApi.post,
  put: httpApi.put,
  delete: httpApi.delete,
}

export { api, ApiError };
