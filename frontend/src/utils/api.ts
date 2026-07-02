import { type FilterState } from '../context/FilterContext';
import { API_BASE, SYSTEM_API_BASE } from "../config/api";

/**
 * Builds query parameters string from a filters object and any additional parameters.
 */
export function buildQueryString(filters: FilterState, additionalParams: Record<string, string | number | boolean> = {}): string {
  const params = new URLSearchParams();

  // Add global filters
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== '') {
      params.append(key, String(value));
    }
  });

  // Add specific endpoint parameters
  Object.entries(additionalParams).forEach(([key, value]) => {
    if (value !== undefined && value !== '') {
      params.append(key, String(value));
    }
  });

  const query = params.toString();
  return query ? `?${query}` : '';
}

/**
 * Core API fetching utility that throws errors for non-2xx responses.
 */
export async function fetchApi<T>(endpoint: string, filters: FilterState = {}, additionalParams: Record<string, string | number | boolean> = {}): Promise<T> {
  const queryString = buildQueryString(filters, additionalParams);

  // Handle system endpoints that are not under analytics prefix
  let url;
  if (endpoint.startsWith('/system/')) {
    url = `${SYSTEM_API_BASE}${endpoint.replace("/system", "")}${queryString}`;
  } else {
    url = `${API_BASE}${endpoint}${queryString}`;
  }

  console.log('API Request:', url);
  const response = await fetch(url);

  if (!response.ok) {
    let errorMessage = 'An error occurred while fetching data';
    try {
      const errorData = await response.json();
      errorMessage = errorData.detail || errorMessage;
    } catch {
      // If we can't parse JSON error, fall back to status text
      errorMessage = `${response.status} ${response.statusText}`;
    }
    throw new Error(errorMessage);
  }

  return response.json();
}
