/* ═══════════════════════════════════════════════════════════════
   StudyOS — API Client
   
   All requests go through NEXT_PUBLIC_API_URL. No localhost.
   Set this env var in Vercel dashboard or .env.local.
   ═══════════════════════════════════════════════════════════════ */

const BASE_URL = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, '') || 'http://localhost:8000/api';

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

export interface PredictionResponse {
  readiness_score: number;
  readiness_band: string;
  pass_probability: number;
  prediction_backend: string;
  insights: string[];
}

export interface StudyTask {
  id: string;
  title: string;
  description: string | null;
  scheduled_date: string;
  completed: boolean;
}

export interface UserStats {
  id: number;
  quiz_accuracy: number;
  flashcard_mastery: number;
  task_completion: number;
  consistency_score: number;
  study_streak: number;
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

  /** Get Exam Readiness Prediction */
  getPrediction: (): Promise<PredictionResponse> => {
    return apiFetch<PredictionResponse>('/predict');
  },

  /** Generate Study Plan Tasks */
  generatePlanner: (topic: string, targetDate: string, hoursPerDay: number = 2): Promise<{message: string}> => {
    return apiFetch<{message: string}>('/planner/generate', {
      method: 'POST',
      body: JSON.stringify({
        topic,
        target_date: targetDate,
        hours_per_day: hoursPerDay
      }),
    });
  },

  /** Get all generated study tasks */
  getTasks: (): Promise<StudyTask[]> => {
    return apiFetch<StudyTask[]>('/planner/tasks');
  },

  /** Update task completion status */
  updateTask: (taskId: string, completed: boolean): Promise<{status: string}> => {
    return apiFetch<{status: string}>(`/planner/tasks/${taskId}`, {
      method: 'PATCH',
      body: JSON.stringify({ completed }),
    });
  },
  
  /** Get user stats */
  getStats: (): Promise<UserStats> => {
    return apiFetch<UserStats>('/stats');
  },

  /** Health check */
  health: (): Promise<{ status: string; message: string }> => {
    return apiFetch('/health');
  },
};
