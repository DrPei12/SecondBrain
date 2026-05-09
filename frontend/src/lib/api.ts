export const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const API_KEY = process.env.NEXT_PUBLIC_SECOND_BRAIN_API_KEY || '';

export function apiUrl(path: string) {
  return `${API_URL}${path.startsWith('/') ? path : `/${path}`}`;
}

export function apiFetch(path: string, init: RequestInit = {}) {
  const headers = new Headers(init.headers);
  if (API_KEY) {
    headers.set('X-API-Key', API_KEY);
  }

  return fetch(apiUrl(path), {
    ...init,
    headers,
  });
}
