const API_PROXY_URL = "/api/backend";

export async function apiFetch(
  path: string,
  init: RequestInit = {},
): Promise<Response> {
  const headers = new Headers(init.headers);

  if (!headers.has("Accept")) {
    headers.set("Accept", "application/json");
  }

  const response = await fetch(`${API_PROXY_URL}${path}`, {
    ...init,
    headers,
    credentials: "same-origin",
  });

  if (
    response.status === 401 &&
    typeof window !== "undefined" &&
    window.location.pathname !== "/login"
  ) {
    window.dispatchEvent(new Event("cybersentinel:unauthorized"));
  }

  return response;
}
