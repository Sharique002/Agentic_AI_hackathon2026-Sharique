"use client";

import { useState, useRef, useEffect } from "react";

interface ChatInputProps {
  onSubmit: (text: string, email: string) => void;
  isLoading: boolean;
}

export default function ChatInput({ onSubmit, isLoading }: ChatInputProps) {
  const [text, setText] = useState("");
  const [email, setEmail] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current;
    if (el) {
      el.style.height = "auto";
      el.style.height = Math.min(el.scrollHeight, 200) + "px";
    }
  }, [text]);

  const handleSubmit = () => {
    if (!text.trim() || isLoading) return;
    onSubmit(text.trim(), email.trim());
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="fade-in-up w-full max-w-2xl mx-auto">
      <div className="glass-card p-6 md:p-8 space-y-5">
        {/* Textarea */}
        <div className="relative">
          <textarea
            id="care-message-input"
            ref={textareaRef}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Describe your issue…"
            disabled={isLoading}
            rows={3}
            className="w-full bg-white/[0.03] border border-white/[0.08] rounded-2xl px-5 py-4 
                       text-[var(--color-text-primary)] text-base leading-relaxed
                       placeholder:text-[var(--color-text-muted)] 
                       focus:border-[var(--color-accent)]/40 focus:bg-white/[0.05]
                       transition-all duration-300 resize-none
                       disabled:opacity-50 disabled:cursor-not-allowed
                       input-focus-glow"
          />
          {/* Character hint */}
          <div className="absolute bottom-3 right-4 text-xs text-[var(--color-text-muted)] opacity-60">
            {text.length > 0 && `${text.length} chars`}
          </div>
        </div>

        {/* Email + Submit Row */}
        <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-end">
          {/* Email Input */}
          <div className="flex-1">
            <label
              htmlFor="care-email-input"
              className="block text-xs text-[var(--color-text-muted)] mb-1.5 ml-1"
            >
              Your email (optional)
            </label>
            <input
              id="care-email-input"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              disabled={isLoading}
              className="w-full bg-white/[0.03] border border-white/[0.08] rounded-xl px-4 py-3 
                         text-sm text-[var(--color-text-primary)]
                         placeholder:text-[var(--color-text-muted)]
                         focus:border-[var(--color-accent)]/40 focus:bg-white/[0.05]
                         transition-all duration-300
                         disabled:opacity-50 disabled:cursor-not-allowed
                         input-focus-glow"
            />
          </div>

          {/* Submit Button */}
          <button
            id="care-resolve-button"
            onClick={handleSubmit}
            disabled={!text.trim() || isLoading}
            className="group relative px-7 py-3 rounded-xl font-medium text-sm
                       bg-[var(--color-accent)] text-white
                       hover:brightness-110 hover:scale-[1.03]
                       active:scale-[0.97] active:brightness-95
                       disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:brightness-100 disabled:hover:scale-100
                       transition-all duration-200 ease-out
                       shadow-lg shadow-[var(--color-accent)]/20
                       hover:shadow-xl hover:shadow-[var(--color-accent)]/40
                       whitespace-nowrap"
          >
            <span className="relative z-10 flex items-center justify-center gap-2">
              {isLoading ? (
                <>
                  <span className="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Processing…
                </>
              ) : (
                <>
                  Resolve this
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 16 16"
                    fill="none"
                    className="transition-transform duration-200 group-hover:translate-x-0.5"
                  >
                    <path
                      d="M3 8h10M9 4l4 4-4 4"
                      stroke="currentColor"
                      strokeWidth="1.5"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </>
              )}
            </span>
          </button>
        </div>

        {/* Hint */}
        <p className="text-xs text-[var(--color-text-muted)] text-center opacity-60">
          Press <kbd className="px-1.5 py-0.5 rounded bg-white/[0.06] text-[var(--color-text-secondary)] text-[10px] font-mono">Enter</kbd> to send
          · <kbd className="px-1.5 py-0.5 rounded bg-white/[0.06] text-[var(--color-text-secondary)] text-[10px] font-mono">Shift+Enter</kbd> for new line
        </p>
      </div>
    </div>
  );
}
