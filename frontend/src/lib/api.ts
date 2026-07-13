// 薄 API client：一律打同源相對 /api（dev 靠 Vite proxy、prod 靠 nginx 反代）。
// 支援子路徑部署（BASE_URL）。錯誤丟出由呼叫端接住 toast。
// 見 reference/frontend/frontend-backend-integration.md §5、§6。
const BASE = import.meta.env.BASE_URL.replace(/\/$/, "");

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init,
  });
  if (!res.ok) {
    // 後端錯誤回 { detail: "..." }（FastAPI 預設）
    let msg = `HTTP ${res.status}`;
    try {
      msg = (await res.json()).detail ?? msg;
    } catch {
      /* 非 JSON */
    }
    throw new Error(msg);
  }
  return res.status === 204 ? (undefined as T) : res.json();
}

export const api = {
  get: <T>(p: string) => request<T>(`/api${p}`),
  post: <T>(p: string, body?: unknown) =>
    request<T>(`/api${p}`, { method: "POST", body: JSON.stringify(body) }),
  put: <T>(p: string, body?: unknown) =>
    request<T>(`/api${p}`, { method: "PUT", body: JSON.stringify(body) }),
  del: <T>(p: string) => request<T>(`/api${p}`, { method: "DELETE" }),
};

// multipart POST（檔案上傳，如 OCR 圖片）。不要手動設 Content-Type，讓瀏覽器帶 boundary。
export async function postForm<T>(path: string, form: FormData): Promise<T> {
  const res = await fetch(`${BASE}/api${path}`, { method: "POST", body: form });
  if (!res.ok) {
    let msg = `HTTP ${res.status}`;
    try {
      msg = (await res.json()).detail ?? msg;
    } catch {
      /* 非 JSON */
    }
    throw new Error(msg);
  }
  return res.json();
}

// JSON in → 二進位 out（如 TTS 回傳 audio）。回傳 blob + 回應標頭（讓呼叫端讀 X-TTS-Engine 等）。
export async function postBlob(
  path: string,
  body: unknown
): Promise<{ blob: Blob; headers: Headers }> {
  const res = await fetch(`${BASE}/api${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    let msg = `HTTP ${res.status}`;
    try {
      msg = (await res.json()).detail ?? msg;
    } catch {
      /* 非 JSON */
    }
    throw new Error(msg);
  }
  return { blob: await res.blob(), headers: res.headers };
}

// 串流 POST：讀 res.body 的 ReadableStream，逐段回呼 onToken（LLM 逐字輸出）。
// 見 frontend-backend-integration.md §5。錯誤（含非 2xx）會丟出，由呼叫端 toast。
export async function postStream(
  path: string,
  body: unknown,
  onToken: (chunk: string) => void,
  signal?: AbortSignal
): Promise<void> {
  const res = await fetch(`${BASE}/api${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  });
  if (!res.ok || !res.body) {
    let msg = `HTTP ${res.status}`;
    try {
      msg = (await res.json()).detail ?? msg;
    } catch {
      /* 非 JSON */
    }
    throw new Error(msg);
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    onToken(decoder.decode(value, { stream: true }));
  }
}
