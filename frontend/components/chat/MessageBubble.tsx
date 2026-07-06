'use client';

import { Message } from '@/types';
import { Scale, User } from 'lucide-react';
import { formatDate } from '@/lib/utils';
import ReactMarkdown from 'react-markdown';

interface MessageBubbleProps {
  message: Message;
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';

  return (
    <div
      className={`flex gap-3 animate-fadeIn ${isUser ? 'flex-row-reverse' : ''}`}
    >
      {/* Avatar */}
      <div
        className={`flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center ${
          isUser
            ? 'bg-[#1F2937] border border-white/10'
            : 'bg-gradient-to-br from-[#D4AF37]/20 to-[#B8941F]/10 border border-[#D4AF37]/20'
        }`}
      >
        {isUser ? (
          <User className="w-4 h-4 text-gray-400" />
        ) : (
          <Scale className="w-4 h-4 text-[#D4AF37]" />
        )}
      </div>

      {/* Message content */}
      <div className={`flex-1 max-w-[85%] ${isUser ? 'text-left' : ''}`}>
        <div
          className={`rounded-2xl px-4 py-3 ${
            isUser
              ? 'bg-[#1F2937]/60 border border-white/5'
              : 'bg-[#1a2233] border border-white/[0.06]'
          }`}
        >
          {isUser ? (
            <p className="text-sm text-gray-200 arabic-text leading-relaxed">
              {message.content}
            </p>
          ) : (
            <div className="text-sm text-[#e5e7eb] arabic-text legal-markdown leading-relaxed min-h-[1.5rem]">
              {message.content ? (
                <ReactMarkdown>{message.content}</ReactMarkdown>
              ) : message.isStreaming ? (
                <span className="text-gray-500">جاري الكتابة...</span>
              ) : (
                <span className="text-gray-500">لا توجد إجابة</span>
              )}
              {message.isStreaming && message.content && (
                <span className="typing-cursor" />
              )}
            </div>
          )}
        </div>

        {/* Citations */}
        {message.citations && message.citations.length > 0 && !message.isStreaming && (
          <div className="mt-2 space-y-1.5 animate-slideUp">
            <p className="text-[10px] text-[#D4AF37]/60 font-medium px-1">
              📚 المصادر ({message.citations.length})
            </p>
            {message.citations.map((c, i) => (
              <div
                key={i}
                className="flex items-start gap-2 text-[11px] px-3 py-2 rounded-lg
                  bg-[#D4AF37]/5 border border-[#D4AF37]/10
                  hover:bg-[#D4AF37]/10 transition-colors cursor-default"
              >
                <span className="text-[#D4AF37] font-bold mt-0.5">{i + 1}</span>
                <div className="flex-1 text-gray-400 arabic-text">
                  <span className="text-gray-300">{c.book_name}</span>
                  {c.article_number && (
                    <span className="mx-1">• المادة {c.article_number}</span>
                  )}
                  {c.page_number && (
                    <span className="mx-1">• ص {c.page_number}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Timestamp */}
        <p className={`text-[10px] text-gray-600 mt-1 px-1 ${isUser ? 'text-left' : ''}`}>
          {formatDate(message.timestamp)}
        </p>
      </div>
    </div>
  );
}
