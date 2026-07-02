const host = window.location.hostname;
const protocol = window.location.protocol;

const BASE_HOST = host.includes("github.dev")
  ? `${protocol}//${host.replace("-3000.", "-8000.")}`
  : `${protocol}//${host}:8000`;

export const API_BASE =
  import.meta.env.VITE_API_URL || `${BASE_HOST}/api/v1/analytics`;

export const SYSTEM_API_BASE =
  API_BASE.replace("/analytics", "/system");