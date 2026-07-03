/* ═══════════════════════════════════════════════════════════════
   StudyOS — API Client
   
   All requests go through NEXT_PUBLIC_API_URL. No localhost.
   Set this env var in Vercel dashboard or .env.local.
   ═══════════════════════════════════════════════════════════════ */

const BASE_URL = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, '') || 'http://localhost:8000/api';

/* ─── Types ─── */
export interface Subject {
  id: string;
  name: string;
  created_at: string;
}

export interface Source {
  id: string;
  subject_id: string;
  title: string;
  file_type: string;
  status: string;
  uploaded_at?: string;
}

export interface ChatMessage {
  id: string;
  subject_id: string;
  role: 'user' | 'ai';
  content: string;
  timestamp: string;
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
  subject_id: string;
  title: string;
  description: string | null;
  scheduled_date: string;
  completed: boolean;
}

export interface UserStats {
  id: number;
  subject_id: string;
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

export interface LibraryBook {
  key: string;
  title: string;
  author: string;
  year?: number;
  cover_url?: string | null;
}

export interface LibrarySearchResponse {
  books: LibraryBook[];
}

export interface YouTubeSearchResponse {
  id?: string;
  title?: string;
  uploader?: string;
  view_count?: number;
  error?: string;
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
  /** Get all subjects */
  getSubjects: (): Promise<Subject[]> => {
    return apiFetch<Subject[]>('/subjects');
  },

  /** Add a new subject */
  addSubject: (name: string): Promise<Subject> => {
    return apiFetch<Subject>('/subjects', {
      method: 'POST',
      body: JSON.stringify({ name }),
    });
  },

  /** Delete a subject */
  deleteSubject: (id: string): Promise<void> => {
    return apiFetch<void>(`/subjects/${id}`, { method: 'DELETE' });
  },

  /** Upload a document (PDF, TXT, DOCX) to a subject */
  uploadDocument: async (file: File, category: string, subjectId: string): Promise<Source> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('category', category);
    formData.append('subject_id', subjectId);

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

  /** List all uploaded documents for a subject */
  getDocuments: (subjectId: string): Promise<Source[]> => {
    return apiFetch<Source[]>(`/documents?subject_id=${subjectId}`);
  },

  /** Delete a document by ID */
  deleteDocument: (id: string): Promise<void> => {
    return apiFetch<void>(`/documents/${id}`, { method: 'DELETE' });
  },

  /** Get chat history for a subject */
  getChatHistory: (subjectId: string): Promise<ChatMessage[]> => {
    return apiFetch<ChatMessage[]>(`/chat/${subjectId}`);
  },

  /** Send a chat message for RAG-based answer */
  chat: (subjectId: string, message: string, documentIds: string[]): Promise<ChatResponse> => {
    return apiFetch<ChatResponse>('/chat', {
      method: 'POST',
      body: JSON.stringify({ subject_id: subjectId, message, document_ids: documentIds }),
    });
  },

  /** Get Exam Readiness Prediction for a subject */
  getPrediction: (subjectId: string): Promise<PredictionResponse> => {
    return apiFetch<PredictionResponse>(`/predict?subject_id=${subjectId}`);
  },

  /** Generate Study Plan Tasks for a subject */
  generatePlanner: (subjectId: string, topic: string, targetDate: string, hoursPerDay: number = 2): Promise<{message: string}> => {
    return apiFetch<{message: string}>('/planner/generate', {
      method: 'POST',
      body: JSON.stringify({
        subject_id: subjectId,
        topic,
        target_date: targetDate,
        hours_per_day: hoursPerDay
      }),
    });
  },

  /** Get all generated study tasks for a subject */
  getTasks: (subjectId: string): Promise<StudyTask[]> => {
    return apiFetch<StudyTask[]>(`/planner/tasks?subject_id=${subjectId}`);
  },

  /** Update task completion status */
  updateTask: (taskId: string, completed: boolean): Promise<{status: string}> => {
    return apiFetch<{status: string}>(`/planner/tasks/${taskId}`, {
      method: 'PATCH',
      body: JSON.stringify({ completed }),
    });
  },
  
  /** Get user stats for a subject */
  getStats: (subjectId: string): Promise<UserStats> => {
    return apiFetch<UserStats>(`/stats?subject_id=${subjectId}`);
  },

  /** Health check */
  health: (): Promise<{ status: string; message: string }> => {
    return apiFetch('/health');
  },

  /** Search library books */
  searchLibrary: (query: string): Promise<LibrarySearchResponse> => {
    return apiFetch<LibrarySearchResponse>(`/library/search?q=${encodeURIComponent(query)}`);
  },

  /** Ask a doubt to the library AI */
  askLibraryDoubt: (doubt: string): Promise<{answer: string}> => {
    return apiFetch<{answer: string}>('/library/doubt', {
      method: 'POST',
      body: JSON.stringify({ doubt }),
    });
  },

  /** Search YouTube videos */
  searchYouTube: (query: string): Promise<YouTubeSearchResponse> => {
    return apiFetch<YouTubeSearchResponse>(`/youtube/search?q=${encodeURIComponent(query)}`);
  },
};
