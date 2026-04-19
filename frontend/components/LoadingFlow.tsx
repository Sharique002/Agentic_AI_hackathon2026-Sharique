"use client";

import { useState, useEffect } from "react";

const LOADING_STEPS = [
  {
    label: "Reading through your message…",
    icon: "🧠",
    duration: 1200,
  },
  {
    label: "Pulling up your order history…",
    icon: "📋",
    duration: 1400,
  },
  {
    label: "Cross-referencing our policies…",
    icon: "📜",
    duration: 1100,
  },
  {
    label: "Deciding the best outcome for you…",
    icon: "⚡",
    duration: 1000,
  },
];

interface LoadingFlowProps {
  isVisible: boolean;
}

export default function LoadingFlow({ isVisible }: LoadingFlowProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<number[]>([]);

  useEffect(() => {
    if (!isVisible) {
      setCurrentStep(0);
      setCompletedSteps([]);
      return;
    }

    let stepIndex = 0;

    const advanceStep = () => {
      if (stepIndex < LOADING_STEPS.length - 1) {
        setCompletedSteps((prev) => [...prev, stepIndex]);
        stepIndex++;
        setCurrentStep(stepIndex);

        setTimeout(advanceStep, LOADING_STEPS[stepIndex].duration);
      }
    };

    const timeout = setTimeout(advanceStep, LOADING_STEPS[0].duration);

    return () => {
      clearTimeout(timeout);
    };
  }, [isVisible]);

  if (!isVisible) return null;

  return (
    <div className="fade-in-up w-full max-w-2xl mx-auto">
      <div className="glass-card p-6 md:p-8">
        {/* Header */}
        <div className="flex items-center gap-3 mb-6">
          <div className="flex gap-1.5">
            <span className="typing-dot" />
            <span className="typing-dot" />
            <span className="typing-dot" />
          </div>
          <span className="text-sm text-[var(--color-text-secondary)]">
            CARE is thinking…
          </span>
        </div>

        {/* Steps */}
        <div className="space-y-4">
          {LOADING_STEPS.map((step, index) => {
            const isActive = index === currentStep;
            const isCompleted = completedSteps.includes(index);
            const isPending = index > currentStep;

            return (
              <div
                key={index}
                className={`
                  relative flex items-center gap-4 py-3 px-4 rounded-xl
                  transition-all duration-500 ease-in-out
                  ${isActive ? "bg-[var(--color-accent-soft)] border border-[var(--color-accent)]/20" : ""}
                  ${isCompleted ? "opacity-60" : ""}
                  ${isPending ? "opacity-25" : ""}
                `}
                style={{
                  animationDelay: `${index * 150}ms`,
                }}
              >
                {/* Icon / Checkmark */}
                <div
                  className={`
                    flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center text-base
                    transition-all duration-500
                    ${isCompleted ? "bg-[var(--color-success-soft)]" : ""}
                    ${isActive ? "bg-[var(--color-accent-soft)] pulse-ring" : ""}
                    ${isPending ? "bg-white/[0.04]" : ""}
                  `}
                >
                  {isCompleted ? (
                    <svg
                      width="16"
                      height="16"
                      viewBox="0 0 16 16"
                      fill="none"
                      className="text-[var(--color-success)]"
                    >
                      <path
                        d="M3 8.5l3 3 7-7"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                  ) : (
                    <span>{step.icon}</span>
                  )}
                </div>

                {/* Label */}
                <span
                  className={`
                    text-sm font-medium transition-colors duration-300
                    ${isActive ? "text-[var(--color-text-primary)]" : ""}
                    ${isCompleted ? "text-[var(--color-text-secondary)]" : ""}
                    ${isPending ? "text-[var(--color-text-muted)]" : ""}
                  `}
                >
                  {step.label}
                </span>

                {/* Active indicator */}
                {isActive && (
                  <div className="ml-auto flex gap-1">
                    <span className="typing-dot" />
                    <span className="typing-dot" />
                    <span className="typing-dot" />
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Bottom progress line */}
        <div className="mt-6 progress-line h-0.5 rounded-full bg-white/[0.04]" />
      </div>
    </div>
  );
}
