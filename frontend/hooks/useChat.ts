'use client';

import { useState, useCallback, useRef } from 'react';
import { Message, Citation } from '@/types';
import { fetchQueryStream } from '@/services/api';
import { generateId } from '@/lib/utils';

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [statusText, setStatusText] = useState('');
  const [activeCitations, setActiveCitations] = useState<Citation[]>([]);
  const abortRef = useRef(false);

  const sendMessage = useCallback(async (text: string) => {
    if (!text.trim() || isLoading) return;

    // Add user message
    const userMsg: Message = {
      id: generateId(),
      role: 'user',
      content: text.trim(),
      timestamp: new Date(),
    };

    // Add placeholder assistant message
    const assistantId = generateId();
    const assistantMsg: Message = {
      id: assistantId,
      role: 'assistant',
      content: '',
      citations: [],
      timestamp: new Date(),
      isStreaming: true,
    };

    setMessages(prev => [...prev, userMsg, assistantMsg]);
    setIsLoading(true);
    setStatusText('جاري البحث في الكتب القانونية...');
    setActiveCitations([]);
    abortRef.current = false;

    const citations: Citation[] = [];

    await fetchQueryStream(
      text.trim(),
      // onToken
      (token) => {
        if (abortRef.current) return;
        setMessages(prev =>
          prev.map(m =>
            m.id === assistantId
              ? { ...m, content: m.content + token }
              : m
          )
        );
      },
      // onCitation
      (citation) => {
        citations.push(citation);
        setActiveCitations([...citations]);
        setMessages(prev =>
          prev.map(m =>
            m.id === assistantId
              ? { ...m, citations: [...citations] }
              : m
          )
        );
      },
      // onStatus
      (status) => {
        setStatusText(status);
      },
      // onDone
      () => {
        setMessages(prev =>
          prev.map(m =>
            m.id === assistantId
              ? { ...m, isStreaming: false }
              : m
          )
        );
        setIsLoading(false);
        setStatusText('');
      },
      // onError
      (error) => {
        setMessages(prev =>
          prev.map(m =>
            m.id === assistantId
              ? { ...m, content: `❌ ${error}`, isStreaming: false }
              : m
          )
        );
        setIsLoading(false);
        setStatusText('');
      },
    );
  }, [isLoading]);

  const clearChat = useCallback(() => {
    setMessages([]);
    setActiveCitations([]);
    setStatusText('');
    abortRef.current = true;
    setIsLoading(false);
  }, []);

  return {
    messages,
    isLoading,
    statusText,
    activeCitations,
    sendMessage,
    clearChat,
  };
}
