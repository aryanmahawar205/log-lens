import { type FilterState } from '../context/FilterContext';

const API_BASE_URL = 'http://localhost:8000/api/v1/analytics';

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
  const url = `${API_BASE_URL}${endpoint}${queryString}`;

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
