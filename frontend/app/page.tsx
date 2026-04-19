"use client";

import { useState, useCallback } from "react";
import ChatInput from "@/components/ChatInput";
import LoadingFlow from "@/components/LoadingFlow";
import DecisionView from "@/components/DecisionView";
import { processRequest, getMockResponse } from "@/lib/api";
import type { CareResponse } from "@/lib/api";

type AppState = "idle" | "loading" | "result" | "error";

export default function HomePage() {
  const [state, setState] = useState<AppState>("idle");
  const [result, setResult] = useState<CareResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [submittedText, setSubmittedText] = useState("");

  const handleSubmit = useCallback(async (text: string, email: string) => {
    setState("loading");
    setSubmittedText(text);
    setResult(null);
    setErrorMessage("");

    // Minimum loading time for the animated steps to feel natural
    const minLoadingTime = new Promise((resolve) => setTimeout(resolve, 5200));

    try {
      // Try real API first, fall back to mock
      let response: CareResponse;

      try {
        const [apiResult] = await Promise.all([
          processRequest({ text, email }),
          minLoadingTime,
        ]);
        response = apiResult;
      } catch {
        // Backend unavailable — use mock data for demo
        await minLoadingTime;
        response = getMockResponse(text);
      }

      setResult(response);
      setState("result");
    } catch {
      setState("error");
      setErrorMessage(
        "Something went wrong. Let's try again."
      );
    }
  }, []);

  const handleRetry = useCallback(() => {
    setState("idle");
    setResult(null);
    setErrorMessage("");
    setSubmittedText("");
  }, []);

  return (
    <main className="min-h-dvh flex flex-col">
      {/* ── Subtle Top Bar ─────────────────────────── */}
      <div className="w-full border-b border-white/[0.04] bg-white/[0.01] backdrop-blur-sm">
        <div className="max-w-4xl mx-auto px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* Logo Icon — Double C with nodes */}
            <svg width="32" height="32" viewBox="0 0 48 48" fill="none" className="flex-shrink-0">
              <defs>
                <linearGradient id="care-g1" x1="12" y1="4" x2="24" y2="44">
                  <stop offset="0%" stopColor="#c084fc" />
                  <stop offset="35%" stopColor="#a855f7" />
                  <stop offset="70%" stopColor="#6d8bf0" />
                  <stop offset="100%" stopColor="#22d3ee" />
                </linearGradient>
                <linearGradient id="care-g2" x1="16" y1="10" x2="28" y2="38">
                  <stop offset="0%" stopColor="#a78bfa" />
                  <stop offset="100%" stopColor="#38bdf8" />
                </linearGradient>
              </defs>
              {/* Outer C arc */}
              <path
                d="M30 8.5C27.2 6.3 23.8 5 20 5C10.6 5 3 12.6 3 22s7.6 17 17 17c3.8 0 7.2-1.3 10-3.5"
                stroke="url(#care-g1)"
                strokeWidth="5"
                strokeLinecap="round"
                fill="none"
              />
              {/* Inner C arc */}
              <path
                d="M30 16c-1.5-2.2-4.2-3.5-7-3.5c-4.7 0-8.5 3.8-8.5 8.5s3.8 8.5 8.5 8.5c2.8 0 5.5-1.3 7-3.5"
                stroke="url(#care-g2)"
                strokeWidth="4"
                strokeLinecap="round"
                fill="none"
              />
              {/* Node dots */}
              <circle cx="33" cy="11" r="3.5" fill="url(#care-g2)" />
              <circle cx="36" cy="22" r="3" fill="url(#care-g2)" opacity="0.8" />
              <circle cx="33" cy="33" r="3.5" fill="url(#care-g1)" />
            </svg>
            {/* Logo Text */}
            <span className="text-lg font-bold tracking-widest care-logo-text">
              CARE
            </span>
          </div>
          <span className="text-[10px] text-[var(--color-text-muted)] tracking-wide hidden sm:inline">
            Customer Autonomous Resolution Engine
          </span>
        </div>
      </div>

      {/* ── Main Content ───────────────────────────── */}
      <div className="flex-1 flex flex-col items-center justify-center px-4 sm:px-6 py-12 sm:py-16">
        <div className="w-full max-w-2xl mx-auto space-y-10">
          {/* ── Header ─────────────────────────────── */}
          {state === "idle" && (
            <div key="idle" className="text-center space-y-4 state-fade-enter">
              <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold text-[var(--color-text-primary)] leading-tight tracking-tight">
                How can I help you today?
              </h1>
              <p className="text-base sm:text-lg text-[var(--color-text-secondary)] max-w-lg mx-auto leading-relaxed">
                CARE analyzes your request and makes the best decision for you.
              </p>

              {/* Quick Actions */}
              <div className="flex flex-wrap justify-center gap-2 pt-4">
                {[
                  "My item arrived damaged",
                  "I want to cancel my order",
                  "I received the wrong item",
                ].map((suggestion) => (
                  <button
                    key={suggestion}
                    onClick={() => {
                      const textarea = document.getElementById(
                        "care-message-input"
                      ) as HTMLTextAreaElement;
                      if (textarea) {
                        const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                          window.HTMLTextAreaElement.prototype,
                          "value"
                        )?.set;
                        nativeInputValueSetter?.call(textarea, suggestion);
                        textarea.dispatchEvent(
                          new Event("input", { bubbles: true })
                        );
                        textarea.focus();
                      }
                    }}
                    className="px-4 py-2 rounded-full text-xs text-[var(--color-text-secondary)] 
                               bg-white/[0.03] border border-white/[0.06]
                               hover:bg-white/[0.06] hover:border-white/[0.1] hover:text-[var(--color-text-primary)]
                               transition-all duration-200"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* ── Loading Header ─────────────────────── */}
          {state === "loading" && (
            <div key="loading" className="text-center space-y-3 state-fade-enter">
              <h2 className="text-xl sm:text-2xl font-semibold text-[var(--color-text-primary)]">
                Looking into this for you…
              </h2>
              <p className="text-sm text-[var(--color-text-secondary)]">
                &ldquo;{submittedText.length > 80
                  ? submittedText.slice(0, 80) + "…"
                  : submittedText}&rdquo;
              </p>
            </div>
          )}

          {/* ── Result Header ──────────────────────── */}
          {state === "result" && (
            <div key="result" className="text-center space-y-2 state-fade-enter">
              <h2 className="text-xl sm:text-2xl font-semibold text-[var(--color-text-primary)]">
                I&apos;ve reviewed your request
              </h2>
              <p className="text-sm text-[var(--color-text-secondary)]">
                &ldquo;{submittedText.length > 80
                  ? submittedText.slice(0, 80) + "…"
                  : submittedText}&rdquo;
              </p>
            </div>
          )}

          {/* ── Chat Input ─────────────────────────── */}
          {(state === "idle" || state === "loading") && (
            <ChatInput
              onSubmit={handleSubmit}
              isLoading={state === "loading"}
            />
          )}

          {/* ── Loading Flow ───────────────────────── */}
          <LoadingFlow isVisible={state === "loading"} />

          {/* ── Decision Result ────────────────────── */}
          {state === "result" && result && <DecisionView data={result} />}

          {/* ── Error State ────────────────────────── */}
          {state === "error" && (
            <div className="fade-in-up w-full max-w-2xl mx-auto">
              <div className="glass-card p-6 md:p-8 text-center space-y-5">
                <div className="w-16 h-16 rounded-full bg-[var(--color-danger-soft)] flex items-center justify-center mx-auto">
                  <span className="text-2xl">😔</span>
                </div>
                <div className="space-y-2">
                  <h3 className="text-lg font-semibold text-[var(--color-text-primary)]">
                    {errorMessage || "Something went wrong. Let's try again."}
                  </h3>
                  <p className="text-sm text-[var(--color-text-secondary)]">
                    Don&apos;t worry — your request wasn&apos;t lost. Give it another try.
                  </p>
                </div>
                <button
                  id="care-retry-button"
                  onClick={handleRetry}
                  className="px-6 py-2.5 rounded-xl text-sm font-medium
                             bg-[var(--color-accent)] text-white
                             hover:brightness-110 active:scale-[0.97]
                             transition-all duration-200
                             shadow-lg shadow-[var(--color-accent)]/20"
                >
                  Try again
                </button>
              </div>
            </div>
          )}

          {/* ── New Request Button (after result) ── */}
          {state === "result" && (
            <div className="text-center fade-in-up" style={{ animationDelay: "0.5s" }}>
              <button
                id="care-new-request-button"
                onClick={handleRetry}
                className="group inline-flex items-center gap-2 px-6 py-2.5 rounded-xl text-sm
                           text-[var(--color-text-secondary)] bg-white/[0.03] border border-white/[0.06]
                           hover:bg-white/[0.06] hover:border-white/[0.1] hover:text-[var(--color-text-primary)]
                           transition-all duration-200"
              >
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 14 14"
                  fill="none"
                  className="transition-transform duration-200 group-hover:-rotate-45"
                >
                  <path
                    d="M7 1v12M1 7h12"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                  />
                </svg>
                Start a new request
              </button>
            </div>
          )}
        </div>
      </div>

      {/* ── Footer ─────────────────────────────────── */}
      <div className="w-full border-t border-white/[0.04] bg-white/[0.01]">
        <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between text-[10px] text-[var(--color-text-muted)]">
          <span>Powered by CARE Engine</span>
          <span>Decisions are transparent and explainable</span>
        </div>
      </div>
    </main>
  );
}
