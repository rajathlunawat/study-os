/* ═══════════════════════════════════════════════════════════════
   StudyOS — API Client
   
   All requests go through NEXT_PUBLIC_API_URL. No localhost.
   Set this env var in Vercel dashboard or .env.local.
   ═══════════════════════════════════════════════════════════════ */

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';

/* ─── Types ─── */
export interface Source {
  id: string;
  title: string;
  file_type: string;
  status: string;
  uploaded_at?: string;
}

export interface ChatResponse {
  reply: string;
  sources_used?: string[];
}

export interface ApiError {
  message: string;
  status: number;
}

/* ─── Fetch Wrapper ─── */
async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${BASE_URL}${endpoint}`;

  const defaultHeaders: HeadersInit = {
    'Content-Type': 'application/json',
  };

  const response = await fetch(url, {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  });

  if (!response.ok) {
    const errorBody = await response.text().catch(() => 'Unknown error');
    const error: ApiError = {
      message: errorBody || `HTTP ${response.status}`,
      status: response.status,
    };
    throw error;
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

/* ─── API Methods ─── */
export const api = {
  /** Upload a document (PDF, TXT, DOCX) */
  uploadDocument: async (file: File, category: string): Promise<Source> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('category', category);

    const url = `${BASE_URL}/documents/upload`;
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorBody = await response.text().catch(() => 'Upload failed');
      throw { message: errorBody, status: response.status } as ApiError;
    }

    return response.json() as Promise<Source>;
  },

  /** List all uploaded documents */
  getDocuments: (): Promise<Source[]> => {
    return apiFetch<Source[]>('/documents');
  },

  /** Delete a document by ID */
  deleteDocument: (id: string): Promise<void> => {
    return apiFetch<void>(`/documents/${id}`, { method: 'DELETE' });
  },

  /** Send a chat message for RAG-based answer */
  chat: (message: string, documentIds: string[]): Promise<ChatResponse> => {
    return apiFetch<ChatResponse>('/chat', {
      method: 'POST',
      body: JSON.stringify({ message, document_ids: documentIds }),
    });
  },

  /** Health check */
  health: (): Promise<{ status: string; message: string }> => {
    return apiFetch('/health');
  },
};
