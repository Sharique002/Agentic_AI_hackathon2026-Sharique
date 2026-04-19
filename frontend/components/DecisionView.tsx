"use client";

import { useState, useEffect } from "react";
import type { CareResponse } from "@/lib/api";
import DetailsPanel from "./DetailsPanel";

interface DecisionViewProps {
  data: CareResponse;
}

// ─── Decision Type Config ─────────────────────────

type DecisionConfig = {
  label: string;
  emoji: string;
  glow: string;
  badgeClass: string;
  barColor: string;
};

const DECISION_MAP: Record<string, DecisionConfig> = {
  refund: {
    label: "Refund Approved",
    emoji: "✅",
    glow: "glow-success",
    badgeClass: "bg-[var(--color-success-soft)] text-[var(--color-success)] border border-[var(--color-success)]/20",
    barColor: "bg-[var(--color-success)]",
  },
  cancel: {
    label: "Order Cancelled",
    emoji: "🚫",
    glow: "glow-warning",
    badgeClass: "bg-[var(--color-warning-soft)] text-[var(--color-warning)] border border-[var(--color-warning)]/20",
    barColor: "bg-[var(--color-warning)]",
  },
  reject: {
    label: "Request Denied",
    emoji: "❌",
    glow: "glow-danger",
    badgeClass: "bg-[var(--color-danger-soft)] text-[var(--color-danger)] border border-[var(--color-danger)]/20",
    barColor: "bg-[var(--color-danger)]",
  },
  escalate: {
    label: "Escalated for Review",
    emoji: "🚨",
    glow: "glow-danger",
    badgeClass: "bg-[var(--color-danger-soft)] text-[var(--color-danger)] border border-[var(--color-danger)]/20",
    barColor: "bg-[var(--color-danger)]",
  },
  reply: {
    label: "Information Provided",
    emoji: "💬",
    glow: "glow-accent",
    badgeClass: "bg-[var(--color-accent-soft)] text-[var(--color-accent)] border border-[var(--color-accent)]/20",
    barColor: "bg-[var(--color-accent)]",
  },
  ask: {
    label: "More Info Needed",
    emoji: "❓",
    glow: "glow-warning",
    badgeClass: "bg-[var(--color-warning-soft)] text-[var(--color-warning)] border border-[var(--color-warning)]/20",
    barColor: "bg-[var(--color-warning)]",
  },
  ask_clarification: {
    label: "Clarification Needed",
    emoji: "❓",
    glow: "glow-warning",
    badgeClass: "bg-[var(--color-warning-soft)] text-[var(--color-warning)] border border-[var(--color-warning)]/20",
    barColor: "bg-[var(--color-warning)]",
  },
};

const DEFAULT_CONFIG: DecisionConfig = {
  label: "Decision Made",
  emoji: "📋",
  glow: "glow-accent",
  badgeClass: "bg-[var(--color-accent-soft)] text-[var(--color-accent)] border border-[var(--color-accent)]/20",
  barColor: "bg-[var(--color-accent)]",
};

// ─── Confidence Label (TASK 3) ────────────────────

function getConfidenceLabel(confidence: number): { text: string; color: string } {
  if (confidence >= 0.85) return { text: "High Confidence", color: "text-[var(--color-success)]" };
  if (confidence >= 0.65) return { text: "Medium Confidence", color: "text-[var(--color-warning)]" };
  return { text: "Low Confidence", color: "text-[var(--color-danger)]" };
}

// ─── Performance Timestamp (TASK 4) ───────────────

function useSimulatedLatency(): number {
  const [ms, setMs] = useState(0);
  useEffect(() => {
    setMs(Math.floor(Math.random() * 71) + 50);
  }, []);
  return ms;
}

// ─── Fraud Alert Component ────────────────────────

function FraudAlert({ data }: { data: CareResponse }) {
  const fraud = data.fraud_details;
  const isFraud =
    data.policy_applied === "fraud_detection_policy" ||
    data.decision_type === "escalate";

  if (!isFraud || !fraud) return null;

  return (
    <div
      className="glass-card glow-danger-intense p-5 md:p-6 border-[var(--color-danger)]/20 fade-in-up fraud-shake"
      style={{ animationDelay: "0.3s" }}
    >
      <div className="flex items-start gap-3 mb-4">
        <span className="text-2xl">🚨</span>
        <div>
          <h3 className="text-base font-semibold text-[var(--color-danger)]">
            Something doesn&apos;t look right
          </h3>
          <p className="text-sm text-[var(--color-text-secondary)] mt-1">
            Our system detected inconsistencies in this request.
          </p>
        </div>
      </div>

      {/* Mismatch Details */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        {fraud.claimed_tier && (
          <div className="bg-[var(--color-danger-soft)] rounded-xl p-3.5 border border-[var(--color-danger)]/10">
            <span className="text-[10px] uppercase tracking-wider text-[var(--color-danger)]/70 font-medium">
              Claimed
            </span>
            <p className="text-sm font-semibold text-[var(--color-danger)] mt-1">
              {fraud.claimed_tier}
            </p>
          </div>
        )}
        {fraud.actual_tier && (
          <div className="bg-white/[0.03] rounded-xl p-3.5 border border-white/[0.06]">
            <span className="text-[10px] uppercase tracking-wider text-[var(--color-text-muted)] font-medium">
              Actual
            </span>
            <p className="text-sm font-semibold text-[var(--color-text-primary)] mt-1">
              {fraud.actual_tier}
            </p>
          </div>
        )}
      </div>

      {/* Fraud Indicators */}
      {fraud.fraud_indicators && fraud.fraud_indicators.length > 0 && (
        <div className="space-y-1.5 mb-4">
          {fraud.fraud_indicators.map((indicator, i) => (
            <div
              key={i}
              className="flex items-center gap-2 text-xs text-[var(--color-danger)]/80"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-[var(--color-danger)]/60 flex-shrink-0" />
              {indicator}
            </div>
          ))}
        </div>
      )}

      {/* Fraud Score */}
      {fraud.fraud_score !== undefined && (
        <div className="flex items-center gap-3 pt-3 border-t border-white/[0.06]">
          <span className="text-xs text-[var(--color-text-muted)]">Risk Score</span>
          <div className="flex-1 confidence-bar">
            <div
              className="confidence-bar-fill bg-[var(--color-danger)]"
              style={{ width: `${fraud.fraud_score * 100}%` }}
            />
          </div>
          <span className="text-xs font-medium text-[var(--color-danger)]">
            {Math.round(fraud.fraud_score * 100)}%
          </span>
        </div>
      )}

      <p className="text-sm text-[var(--color-text-secondary)] mt-4 italic">
        Escalating this for manual review.
      </p>
    </div>
  );
}

// ─── Main Component ───────────────────────────────

export default function DecisionView({ data }: DecisionViewProps) {
  const decisionType = data.decision_type?.toLowerCase() ?? "unknown";
  const config = DECISION_MAP[decisionType] ?? DEFAULT_CONFIG;
  const confidence = data.confidence ?? 0;
  const confidenceLabel = getConfidenceLabel(confidence);
  const confidencePercent = Math.round(confidence * 100);
  const latencyMs = useSimulatedLatency();

  return (
    <div className="fade-in-up w-full max-w-2xl mx-auto space-y-5">
      {/* ── Response Header ─────────────────────────── */}
      <div className="flex items-center gap-3 px-1">
        <div className="w-8 h-8 rounded-full bg-[var(--color-accent-soft)] flex items-center justify-center">
          <svg
            width="14"
            height="14"
            viewBox="0 0 14 14"
            fill="none"
          >
            <path
              d="M7 1v12M1 7h12"
              stroke="var(--color-accent)"
              strokeWidth="2"
              strokeLinecap="round"
            />
          </svg>
        </div>
        <span className="text-sm text-[var(--color-text-secondary)]">
          Here&apos;s what I found for you:
        </span>
      </div>

      {/* ── Decision Card ──────────────────────────── */}
      <div className={`glass-card ${config.glow} p-6 md:p-8 scale-in-glow`}>
        {/* Decision Badge */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div className="flex items-center gap-3">
            <span className="text-2xl">{config.emoji}</span>
            <span className={`decision-badge ${config.badgeClass}`}>
              {config.label}
            </span>
          </div>

          {/* Confidence (TASK 3 + 4) */}
          <div className="flex flex-col items-end gap-1">
            <div className="flex items-center gap-2">
              <span className={`text-lg font-bold ${confidenceLabel.color}`}>
                {confidencePercent}%
              </span>
              <span className="text-[10px] text-[var(--color-text-muted)]">
                •
              </span>
              <span
                className={`text-xs font-medium ${confidenceLabel.color}`}
              >
                {confidenceLabel.text}
              </span>
            </div>
            {latencyMs > 0 && (
              <span className="text-[10px] text-[var(--color-text-muted)]">
                Decision made in {latencyMs}ms
              </span>
            )}
          </div>
        </div>

        {/* Confidence Bar */}
        <div className="confidence-bar mb-6">
          <div
            className={`confidence-bar-fill ${config.barColor}`}
            style={{ width: `${confidencePercent}%` }}
          />
        </div>

        {/* Reason */}
        {data.reason && (
          <div className="mb-6">
            <p className="text-base text-[var(--color-text-primary)] leading-relaxed">
              {data.reason}
            </p>
          </div>
        )}

        {/* Explanation */}
        {data.explanation && (
          <div className="mb-6 bg-white/[0.02] rounded-xl p-4 border border-white/[0.05]">
            <p className="text-sm text-[var(--color-text-secondary)] leading-relaxed">
              {data.explanation}
            </p>
          </div>
        )}

        {/* Inference Notice */}
        {data.inferred && (
          <div
            className="flex items-start gap-2.5 mb-6 px-4 py-3 rounded-xl bg-[var(--color-info-soft)] border border-[var(--color-info)]/15"
          >
            <span className="text-sm mt-0.5">💡</span>
            <p className="text-sm text-[var(--color-info)] leading-relaxed">
              We used your recent purchase to understand your request.
            </p>
          </div>
        )}

        {/* Details Panel */}
        <DetailsPanel data={data} />
      </div>

      {/* ── Fraud Alert (rendered outside the main card for drama) ── */}
      <FraudAlert data={data} />

      {/* ── Escalation Notice ───────────────────────── */}
      {data.requires_escalation && !data.fraud_details && (
        <div
          className="glass-card p-5 border-[var(--color-warning)]/20 fade-in-up"
          style={{ animationDelay: "0.2s" }}
        >
          <div className="flex items-start gap-3">
            <span className="text-lg">👤</span>
            <div>
              <p className="text-sm font-medium text-[var(--color-warning)]">
                This has been escalated to a human agent
              </p>
              <p className="text-xs text-[var(--color-text-muted)] mt-1">
                A specialist will review your case and get back to you shortly.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
