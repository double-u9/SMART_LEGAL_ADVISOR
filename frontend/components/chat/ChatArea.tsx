'use client';

import { useRef, useEffect } from 'react';
import { Message } from '@/types';
import MessageBubble from './MessageBubble';
import { Scale, BookOpen, Gavel, FileSearch } from 'lucide-react';

interface ChatAreaProps {
  messages: Message[];
  onSuggestionClick: (text: string) => void;
}

const SUGGESTIONS = [
  { icon: Gavel, text: 'ما هي عقوبة السرقة في القانون العراقي؟' },
  { icon: BookOpen, text: 'اشرح المادة الأولى من القانون المدني العراقي' },
  { icon: FileSearch, text: 'ما هي شروط عقد الزواج في قانون الأحوال الشخصية؟' },
  { icon: Scale, text: 'ما هي أنواع العقوبات في قانون العقوبات العراقي؟' },
];

export default function ChatArea({ messages, onSuggestionClick }: ChatAreaProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center px-4 py-12">
        {/* Hero */}
        <div className="animate-slideUp text-center mb-10">
          <div className="w-20 h-20 mx-auto mb-6 rounded-2xl
            bg-gradient-to-br from-[#D4AF37]/20 to-[#B8941F]/5
            border border-[#D4AF37]/20
            flex items-center justify-center
            animate-pulse-glow"
          >
            <Scale className="w-10 h-10 text-[#D4AF37]" />
          </div>
          <h2 className="text-2xl font-bold text-white font-['Noto_Kufi_Arabic'] mb-2">
            المستشار القانوني الذكي
          </h2>
          <p className="text-gray-400 text-sm max-w-md leading-relaxed">
            مساعدك الذكي في القانون العراقي. اسأل أي سؤال قانوني وسأبحث لك
            في الكتب القانونية الرسمية مع الاستشهاد بالمصادر.
          </p>
        </div>

        {/* Suggestion cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-2xl w-full">
          {SUGGESTIONS.map((s, i) => (
            <button
              key={i}
              onClick={() => onSuggestionClick(s.text)}
              className="group flex items-start gap-3 px-4 py-3 rounded-xl
                glass hover:bg-white/5
                border border-white/5 hover:border-[#D4AF37]/20
                text-right transition-all duration-300
                hover:shadow-lg hover:shadow-[#D4AF37]/5"
              style={{ animationDelay: `${i * 100}ms` }}
            >
              <s.icon className="w-5 h-5 text-gray-500 group-hover:text-[#D4AF37] transition-colors flex-shrink-0 mt-0.5" />
              <span className="text-sm text-gray-400 group-hover:text-gray-200 arabic-text leading-relaxed transition-colors">
                {s.text}
              </span>
            </button>
          ))}
        </div>

        {/* Features */}
        <div className="flex items-center gap-6 mt-10 text-[11px] text-gray-600">
          <span className="flex items-center gap-1">
            <span className="w-1 h-1 rounded-full bg-[#D4AF37]/50" />
            بحث دلالي ذكي
          </span>
          <span className="flex items-center gap-1">
            <span className="w-1 h-1 rounded-full bg-emerald-500/50" />
            استشهادات دقيقة
          </span>
          <span className="flex items-center gap-1">
            <span className="w-1 h-1 rounded-full bg-blue-500/50" />
            محلي وآمن
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6">
      <div className="max-w-4xl mx-auto space-y-6">
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
