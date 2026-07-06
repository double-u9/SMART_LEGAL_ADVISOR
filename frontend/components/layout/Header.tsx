'use client';

import { Scale } from 'lucide-react';

export default function Header({ onClear }: { onClear: () => void }) {
  return (
    <header className="glass-strong sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#D4AF37] to-[#B8941F] flex items-center justify-center shadow-lg">
            <Scale className="w-5 h-5 text-[#0A0F1C]" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-white font-['Noto_Kufi_Arabic']">
              المستشار القانوني الذكي
            </h1>
            <p className="text-xs text-gray-400">Smart Legal Advisor • AI-Powered</p>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-3">
          <button
            onClick={onClear}
            className="text-xs px-3 py-1.5 rounded-lg border border-white/10 text-gray-400 hover:text-white hover:border-white/20 transition-all duration-200"
          >
            محادثة جديدة
          </button>
          <div className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-xs text-emerald-400">Ollama محلي</span>
          </div>
        </div>
      </div>
      {/* Gold accent line */}
      <div className="h-[1px] bg-gradient-to-l from-transparent via-[#D4AF37]/30 to-transparent" />
    </header>
  );
}
