'use client';

import { Citation } from '@/types';
import { BookOpen, ChevronLeft, ChevronRight, X } from 'lucide-react';
import { useState } from 'react';

interface CitationPanelProps {
  citations: Citation[];
  isOpen: boolean;
  onClose: () => void;
}

export default function CitationPanel({ citations, isOpen, onClose }: CitationPanelProps) {
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-y-0 left-0 w-80 z-50 glass-strong shadow-2xl
      animate-slideRight flex flex-col"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/5">
        <div className="flex items-center gap-2">
          <BookOpen className="w-4 h-4 text-[#D4AF37]" />
          <h3 className="text-sm font-semibold text-white font-['Noto_Kufi_Arabic']">
            المصادر القانونية
          </h3>
          <span className="text-[10px] bg-[#D4AF37]/10 text-[#D4AF37] px-1.5 py-0.5 rounded-full">
            {citations.length}
          </span>
        </div>
        <button
          onClick={onClose}
          className="w-7 h-7 rounded-lg flex items-center justify-center
            hover:bg-white/5 text-gray-400 hover:text-white transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Citations list */}
      <div className="flex-1 overflow-y-auto px-3 py-3 space-y-2">
        {citations.length === 0 ? (
          <div className="text-center py-10 text-gray-500 text-sm">
            <BookOpen className="w-8 h-8 mx-auto mb-3 opacity-30" />
            <p>لم يتم العثور على مصادر بعد</p>
          </div>
        ) : (
          citations.map((c, i) => (
            <div
              key={i}
              className="rounded-lg border border-white/5 overflow-hidden
                hover:border-[#D4AF37]/20 transition-all duration-200"
            >
              <button
                onClick={() => setExpandedIdx(expandedIdx === i ? null : i)}
                className="w-full flex items-center justify-between px-3 py-2.5
                  bg-[#1F2937]/50 hover:bg-[#1F2937]/80 transition-colors text-right"
              >
                <div className="flex-1">
                  <p className="text-xs font-medium text-gray-200 arabic-text">
                    {c.book_name || 'مصدر'}
                  </p>
                  <p className="text-[10px] text-gray-500 mt-0.5">
                    {c.article_number && `المادة ${c.article_number}`}
                    {c.page_number && ` • ص ${c.page_number}`}
                  </p>
                </div>
                <div className="flex items-center gap-1.5">
                  {c.confidence > 0 && (
                    <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${
                      c.confidence > 0.7
                        ? 'bg-emerald-500/10 text-emerald-400'
                        : c.confidence > 0.4
                        ? 'bg-yellow-500/10 text-yellow-400'
                        : 'bg-red-500/10 text-red-400'
                    }`}>
                      {Math.round(c.confidence * 100)}%
                    </span>
                  )}
                  {expandedIdx === i ? (
                    <ChevronRight className="w-3 h-3 text-gray-500" />
                  ) : (
                    <ChevronLeft className="w-3 h-3 text-gray-500" />
                  )}
                </div>
              </button>

              {expandedIdx === i && c.relevant_text && (
                <div className="px-3 py-2.5 border-t border-white/5 bg-[#0A0F1C]/50">
                  <p className="text-[11px] text-gray-400 arabic-text leading-relaxed">
                    {c.relevant_text}
                  </p>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
