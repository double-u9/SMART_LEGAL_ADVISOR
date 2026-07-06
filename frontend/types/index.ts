export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: Citation[];
  timestamp: Date;
  isStreaming?: boolean;
}

export interface Citation {
  book_name: string;
  chapter: string;
  article_number: string;
  page_number: string;
  relevant_text: string;
  confidence: number;
  chunk_id?: string;
  source_file?: string;
}

export interface QueryRequest {
  question: string;
  filters?: Record<string, string>;
  stream?: boolean;
}

export interface QueryResponse {
  answer: string;
  citations: Citation[];
  query: string;
  confidence: number;
}

export interface SSEEvent {
  type: 'status' | 'token' | 'citation' | 'done';
  content: string | Citation | Record<string, unknown>;
}

export interface HealthStatus {
  status: string;
  services: Record<string, { status: string }>;
  config: Record<string, string>;
}
