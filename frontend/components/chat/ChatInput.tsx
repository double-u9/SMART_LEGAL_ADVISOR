'use client';

import { useState, useRef, KeyboardEvent } from 'react';
import { Send, Loader2 } from 'lucide-react';

interface ChatInputProps {
  onSend: (text: string) => void;
  isLoading: boolean;
  statusText: string;
}

export default function ChatInput({ onSend, isLoading, statusText }: ChatInputProps) {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = () => {
    if (!input.trim() || isLoading) return;
    onSend(input);
    setInput('');
    if (textareaRef.current) {
      textareaRef.current.style.height = '52px';
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleInput = () => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = '52px';
    const scrollHeight = el.scrollHeight;
    el.style.height = Math.min(scrollHeight, 160) + 'px';
  };

  return (
    <div className="sticky bottom-0 z-40 glass-strong">
      <div className="h-[1px] bg-gradient-to-l from-transparent via-[#D4AF37]/20 to-transparent" />

      {/* Status bar */}
      {statusText && (
        <div className="px-4 py-2 flex items-center gap-2 text-xs text-[#D4AF37] border-b border-white/5">
          <Loader2 className="w-3 h-3 animate-spin" />
          <span>{statusText}</span>
        </div>
      )}

      <div className="max-w-4xl mx-auto px-4 py-3">
        <div className="relative flex items-end gap-2">
          <textarea
            ref={textareaRef}
            id="chat-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onInput={handleInput}
            onKeyDown={handleKeyDown}
            placeholder="اطرح سؤالك القانوني هنا..."
            disabled={isLoading}
            rows={1}
            className="flex-1 min-h-[52px] max-h-[160px] px-4 py-3 rounded-xl
              bg-[#1F2937]/80 border border-white/10
              text-white placeholder-gray-500
              resize-none focus:outline-none focus-glow
              arabic-text text-sm leading-relaxed
              transition-all duration-200
              disabled:opacity-50 disabled:cursor-not-allowed"
          />

          <button
            onClick={handleSubmit}
            disabled={!input.trim() || isLoading}
            className="flex-shrink-0 w-11 h-11 rounded-xl
              bg-gradient-to-br from-[#D4AF37] to-[#B8941F]
              text-[#0A0F1C] flex items-center justify-center
              hover:shadow-lg hover:shadow-[#D4AF37]/20
              disabled:opacity-30 disabled:cursor-not-allowed
              transition-all duration-200 hover:scale-105 active:scale-95"
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5 rotate-180" />
            )}
          </button>
        </div>

        <p className="text-[10px] text-gray-600 mt-2 text-center">
          المستشار القانوني الذكي يستخدم الذكاء الاصطناعي. تأكد دائمًا من المعلومات مع محامٍ متخصص.
        </p>
      </div>
    </div>
  );
}
