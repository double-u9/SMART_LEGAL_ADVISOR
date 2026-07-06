import { SSEEvent, Citation } from '@/types';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function fetchQueryStream(
  question: string,
  onToken: (token: string) => void,
  onCitation: (citation: Citation) => void,
  onStatus: (status: string) => void,
  onDone: () => void,
  onError: (error: string) => void,
  filters?: Record<string, string>,
): Promise<void> {
  try {
    const response = await fetch(`${BASE_URL}/api/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, filters, stream: true }),
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      onError(err.detail || `خطأ في الخادم: ${response.status}`);
      return;
    }

    const reader = response.body?.getReader();
    if (!reader) {
      onError('فشل في قراءة الاستجابة');
      return;
    }

    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed || !trimmed.startsWith('data: ')) continue;

        const jsonStr = trimmed.slice(6);
        try {
          const event: SSEEvent = JSON.parse(jsonStr);
          switch (event.type) {
            case 'token':
              onToken(event.content as string);
              break;
            case 'citation':
              onCitation(event.content as Citation);
              break;
            case 'status':
              onStatus(event.content as string);
              break;
            case 'done':
              onDone();
              return;
          }
        } catch {
          // Skip malformed events
        }
      }
    }
    onDone();
  } catch (error) {
    onError(error instanceof Error ? error.message : 'خطأ غير متوقع');
  }
}

export async function fetchHealth() {
  const res = await fetch(`${BASE_URL}/api/health`);
  return res.json();
}

export async function fetchBooks() {
  const res = await fetch(`${BASE_URL}/api/books`);
  return res.json();
}

export async function triggerIngestion(datasetPath?: string) {
  const res = await fetch(`${BASE_URL}/api/ingest/dataset`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ dataset_path: datasetPath }),
  });
  return res.json();
}
