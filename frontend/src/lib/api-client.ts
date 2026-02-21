/**
 * API Client configuration for backend communication
 * ESTÁNDAR NOUGRAM: Transforma automáticamente strings Decimal a Dinero
 */
import { logger } from './logger';
import { transformAPIResponse } from './money-transformer';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export type ApiResponse<T> = {
  data?: T;
  error?: string;
} & (T extends object ? Partial<T> : {});

/**
 * Get auth token from localStorage
 */
function getAuthToken(): string | null {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('auth_token');
  }
  return null;
}

/**
 * Translate error messages using the new i18n system
 * This function is kept for backward compatibility but now uses the error handler
 */
import { getErrorMessage, fallbackTranslate } from './error-handler';

function translateError(errorMessage: string | unknown): string {
  // Use the new error handler with fallback translations
  return getErrorMessage(errorMessage, fallbackTranslate);
}

/**
 * Retry a failed request with exponential backoff
 */
async function retryRequest<T>(
  endpoint: string,
  options: RequestInit,
  maxRetries: number = 3,
  delay: number = 1000
): Promise<ApiResponse<T>> {
  let lastError: Error | null = null;
  
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      const response = await apiRequestInternal<T>(endpoint, options, undefined);
      
      // Don't retry on 4xx errors (client errors) except 408 (timeout) and 429 (rate limit)
      if (response.error && !response.error.includes('timeout') && !response.error.includes('rate limit')) {
        const statusMatch = response.error.match(/status: (\d+)/);
        if (statusMatch) {
          const status = parseInt(statusMatch[1]);
          if (status >= 400 && status < 500 && status !== 408 && status !== 429) {
            return response; // Don't retry client errors
          }
        }
      }
      
      if (!response.error) {
        return response;
      }
      
      lastError = new Error(response.error);
    } catch (error) {
      lastError = error instanceof Error ? error : new Error('Unknown error');
    }
    
    // Wait before retrying (exponential backoff)
    if (attempt < maxRetries - 1) {
      const waitTime = delay * Math.pow(2, attempt);
      await new Promise(resolve => setTimeout(resolve, waitTime));
    }
  }
  
  return { 
    error: lastError?.message || 'La solicitud falló después de varios intentos' 
  } as ApiResponse<T>;
}

/**
 * Internal API request function (without retry logic)
 * ESTÁNDAR NOUGRAM: Transforma automáticamente strings Decimal a Dinero
 */
async function apiRequestInternal<T>(
  endpoint: string,
  options: RequestInit = {},
  currency?: string  // Opcional: moneda para transformación si no viene en la respuesta
): Promise<ApiResponse<T>> {
  try {
    const token = getAuthToken();
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const url = `${API_URL}${endpoint}`;
    logger.debug(`[API] ${options.method || 'GET'} ${url}`, { headers, body: options.body });

    const response = await fetch(url, {
      ...options,
      headers,
    });

    logger.debug(`[API] Response status: ${response.status}`, response);

    if (!response.ok) {
      if (response.status === 401) {
        if (typeof window !== 'undefined') {
          localStorage.removeItem('auth_token');
          window.location.href = '/';
        }
        return { error: 'No autorizado. Por favor, inicia sesión nuevamente.' } as ApiResponse<T>;
      }
      
      const error = await response.json().catch(() => ({ 
        detail: `Error ${response.status}: ${response.statusText}` 
      }));
      
      // Log full error for 422 validation errors to help debug
      if (response.status === 422) {
        logger.error('[API] Validation error (422):', error);
        // Handle Pydantic validation errors - they have a 'detail' array
        if (error.detail && Array.isArray(error.detail)) {
          const validationErrors = error.detail.map((err: any) => {
            const field = err.loc ? err.loc.join('.') : 'campo';
            const msg = err.msg || 'Error de validación';
            return `${field}: ${msg}`;
          }).join(', ');
          return { error: `Error de validación: ${validationErrors}` } as ApiResponse<T>;
        }
      }
      
      const errorMessage = error.detail || error.message || `Error ${response.status}`;
      return { error: translateError(errorMessage) } as ApiResponse<T>;
    }

    // Handle 204 No Content responses
    if (response.status === 204) {
      return {} as ApiResponse<T>;
    }

    const data = await response.json();
    
    // ESTÁNDAR NOUGRAM: Transformar strings Decimal a Dinero automáticamente
    const transformedData = transformAPIResponse<T>(data, currency);
    
    logger.debug(`[API] Response data (transformed):`, transformedData);
    return {
      ...(transformedData && typeof transformedData === 'object' ? (transformedData as object) : {}),
      data: transformedData,
    } as ApiResponse<T>;
  } catch (error) {
    if (error instanceof TypeError && error.message === 'Failed to fetch') {
      return { 
        error: 'Error de conexión. El servidor backend no está disponible. Verifica que el backend esté corriendo en http://localhost:8000' 
      } as ApiResponse<T>;
    }
    return { 
      error: translateError(error instanceof Error ? error.message : 'Error de red') 
    } as ApiResponse<T>;
  }
}

/**
 * Make API request to backend with automatic retry for network errors
 * ESTÁNDAR NOUGRAM: Transforma automáticamente strings Decimal a Dinero
 */
export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {},
  retry: boolean = true,
  currency?: string  // Opcional: moneda para transformación si no viene en la respuesta
): Promise<ApiResponse<T>> {
  const method = (options.method || 'GET').toUpperCase();
  // Never retry non-idempotent requests to avoid duplicate creates/updates.
  const shouldRetry = retry && method === 'GET';

  if (shouldRetry) {
    return retryRequest(endpoint, options);
  }
  return apiRequestInternal(endpoint, options, currency);
}

/**
 * Download PDF file from API
 */
export async function downloadPDF(
  endpoint: string,
  filename: string
): Promise<void> {
  try {
    const token = getAuthToken();
    const headers: Record<string, string> = {};
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_URL}${endpoint}`, {
      method: 'GET',
      headers,
    });

    if (!response.ok) {
      if (response.status === 401) {
        if (typeof window !== 'undefined') {
          localStorage.removeItem('auth_token');
          window.location.href = '/';
        }
        throw new Error('Unauthorized. Please login again.');
      }
      const error = await response.json().catch(() => ({ message: 'An error occurred' }));
      throw new Error(error.detail || error.message || 'Failed to download PDF');
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  } catch (error) {
    throw error;
  }
}

/**
 * Download DOCX file from API
 */
export async function downloadDOCX(
  endpoint: string,
  filename: string
): Promise<void> {
  try {
    const token = getAuthToken();
    const headers: Record<string, string> = {};
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_URL}${endpoint}`, {
      method: 'GET',
      headers,
    });

    if (!response.ok) {
      if (response.status === 401) {
        if (typeof window !== 'undefined') {
          localStorage.removeItem('auth_token');
          window.location.href = '/';
        }
        throw new Error('Unauthorized. Please login again.');
      }
      const error = await response.json().catch(() => ({ message: 'An error occurred' }));
      throw new Error(error.detail || error.message || 'Failed to download DOCX');
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  } catch (error) {
    logger.error(`Error downloading DOCX from ${endpoint}:`, error);
    throw error;
  }
}

/**
 * Convenience wrapper functions for common HTTP methods
 */
export async function apiGet<T>(endpoint: string, retry: boolean = true): Promise<ApiResponse<T>> {
  return apiRequest<T>(endpoint, { method: 'GET' }, retry);
}

export async function apiPost<T>(endpoint: string, data?: any, retry: boolean = true): Promise<ApiResponse<T>> {
  return apiRequest<T>(endpoint, {
    method: 'POST',
    body: data ? JSON.stringify(data) : undefined,
  }, retry);
}

export async function apiPut<T>(endpoint: string, data?: any, retry: boolean = true): Promise<ApiResponse<T>> {
  return apiRequest<T>(endpoint, {
    method: 'PUT',
    body: data ? JSON.stringify(data) : undefined,
  }, retry);
}

export async function apiPatch<T>(endpoint: string, data?: any, retry: boolean = true): Promise<ApiResponse<T>> {
  return apiRequest<T>(endpoint, {
    method: 'PATCH',
    body: data ? JSON.stringify(data) : undefined,
  }, retry);
}

export async function apiDelete<T>(endpoint: string, retry: boolean = true): Promise<ApiResponse<T>> {
  return apiRequest<T>(endpoint, { method: 'DELETE' }, retry);
}

/**
 * Get auth token (exported for convenience)
 */
export function getToken(): string | null {
  return getAuthToken();
}

/**
 * Clear auth token (used on logout flows)
 */
export function clearToken(): void {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('auth_token');
  }
}

/**
 * API Error class for better error handling
 */
export class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public data?: any
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export default apiRequest;