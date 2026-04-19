"use client";

import { useState } from "react";
import type { CareResponse } from "@/lib/api";

interface DetailsPanelProps {
  data: CareResponse;
}

export default function DetailsPanel({ data }: DetailsPanelProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const breakdown = data.confidence_breakdown;
  const steps = data.reasoning_steps ?? [];

  const formatPercent = (value?: number) => {
    if (value === undefined || value === null) return "—";
    return `${Math.round(value * 100)}%`;
  };

  const formatLabel = (key: string) => {
    return key
      .replace(/_/g, " ")
      .replace(/\b\w/g, (c) => c.toUpperCase());
  };

  return (
    <div className="w-full">
      {/* Toggle Button */}
      <button
        id="care-details-toggle"
        onClick={() => setIsExpanded(!isExpanded)}
        className="group flex items-center gap-2 text-sm text-[var(--color-text-secondary)]
                   hover:text-[var(--color-text-primary)] transition-colors duration-200"
      >
        <svg
          width="16"
          height="16"
          viewBox="0 0 16 16"
          fill="none"
          className={`transition-transform duration-300 ${isExpanded ? "rotate-90" : ""}`}
        >
          <path
            d="M6 4l4 4-4 4"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
        <span>
          {isExpanded
            ? "Hide decision details"
            : "See the reasoning behind this decision"}
        </span>
      </button>

      {/* Expandable Content */}
      <div className={`expandable-content ${isExpanded ? "expanded" : ""}`}>
        <div className="mt-5 space-y-6">
          {/* Reasoning Steps */}
          {steps.length > 0 && (
            <div>
              <h4 className="text-xs uppercase tracking-wider text-[var(--color-text-muted)] font-medium mb-3">
                Reasoning Steps
              </h4>
              <div className="space-y-2.5">
                {steps.map((step, i) => (
                  <div
                    key={i}
                    className="relative flex items-start gap-3 pl-1"
                  >
                    {/* Connector dot */}
                    <div className="flex-shrink-0 mt-1.5">
                      <div className="w-2 h-2 rounded-full bg-[var(--color-accent)]/60" />
                    </div>
                    {/* Step text */}
                    <span className="text-sm text-[var(--color-text-secondary)] leading-relaxed">
                      {step}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Explanation */}
          {data.explanation && (
            <div>
              <h4 className="text-xs uppercase tracking-wider text-[var(--color-text-muted)] font-medium mb-3">
                Full Explanation
              </h4>
              <p className="text-sm text-[var(--color-text-secondary)] leading-relaxed bg-white/[0.02] rounded-xl p-4 border border-white/[0.05]">
                {data.explanation}
              </p>
            </div>
          )}

          {/* Confidence Breakdown */}
          {breakdown && (
            <div>
              <h4 className="text-xs uppercase tracking-wider text-[var(--color-text-muted)] font-medium mb-3">
                Confidence Breakdown
              </h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {Object.entries(breakdown).map(([key, value]) => {
                  const isNegative = (value ?? 0) < 0;
                  const absValue = Math.abs(value ?? 0);

                  return (
                    <div
                      key={key}
                      className="bg-white/[0.02] rounded-xl p-3.5 border border-white/[0.05]"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs text-[var(--color-text-muted)]">
                          {formatLabel(key)}
                        </span>
                        <span
                          className={`text-xs font-medium ${
                            isNegative
                              ? "text-[var(--color-danger)]"
                              : "text-[var(--color-text-secondary)]"
                          }`}
                        >
                          {isNegative ? "−" : ""}
                          {formatPercent(absValue)}
                        </span>
                      </div>
                      <div className="confidence-bar">
                        <div
                          className={`confidence-bar-fill ${
                            isNegative
                              ? "bg-[var(--color-danger)]"
                              : "bg-[var(--color-accent)]"
                          }`}
                          style={{ width: `${absValue * 100}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Confidence Reason */}
          {data.confidence_reason && (
            <div className="text-xs text-[var(--color-text-muted)] italic bg-white/[0.02] rounded-lg p-3 border border-white/[0.04]">
              {data.confidence_reason}
            </div>
          )}

          {/* Policy Applied */}
          {data.policy_applied && (
            <div className="flex items-center gap-2 text-xs text-[var(--color-text-muted)]">
              <span className="px-2.5 py-1 rounded-full bg-white/[0.04] border border-white/[0.06]">
                Policy: {data.policy_applied.replace(/_/g, " ")}
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
