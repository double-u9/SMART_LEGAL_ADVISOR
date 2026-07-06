'use client';

import { useState } from 'react';
import { useChat } from '@/hooks/useChat';
import Header from '@/components/layout/Header';
import ChatArea from '@/components/chat/ChatArea';
import ChatInput from '@/components/chat/ChatInput';
import CitationPanel from '@/components/citations/CitationPanel';
import { BookOpen } from 'lucide-react';

export default function HomePage() {
  const { messages, isLoading, statusText, activeCitations, sendMessage, clearChat } = useChat();
  const [citationPanelOpen, setCitationPanelOpen] = useState(false);

  const hasCitations = activeCitations.length > 0;

  return (
    <div className="flex flex-col h-screen">
      <Header onClear={clearChat} />

      <div className="flex flex-1 overflow-hidden relative">
        {/* Main chat area */}
        <div className="flex flex-col flex-1">
          <ChatArea
            messages={messages}
            onSuggestionClick={sendMessage}
          />
          <ChatInput
            onSend={sendMessage}
            isLoading={isLoading}
            statusText={statusText}
          />
        </div>

        {/* Citation toggle button */}
        {hasCitations && !citationPanelOpen && (
          <button
            onClick={() => setCitationPanelOpen(true)}
            className="fixed bottom-20 left-4 z-40 flex items-center gap-2 px-3 py-2 rounded-xl
              glass border border-[#D4AF37]/20 text-[#D4AF37]
              hover:bg-[#D4AF37]/10 transition-all duration-200
              animate-fadeIn shadow-lg"
          >
            <BookOpen className="w-4 h-4" />
            <span className="text-xs font-medium">
              المصادر ({activeCitations.length})
            </span>
          </button>
        )}

        {/* Citation panel */}
        <CitationPanel
          citations={activeCitations}
          isOpen={citationPanelOpen}
          onClose={() => setCitationPanelOpen(false)}
        />
      </div>
    </div>
  );
}
