"use client";

import { useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  ShieldAlert,
  Sparkles,
} from "lucide-react";

import AIErrorState from "@/components/ai/AIErrorState";
import AIHeader from "@/components/ai/AIHeader";
import AILoadingState from "@/components/ai/AILoadingState";
import AIResultCard from "@/components/ai/AIResultCard";
import RiskMeter from "@/components/ai/RiskMeter";

import { checkScam } from "@/features/ai/services/ai.service";

import type {
  ScamCheckRequest,
  ScamCheckResponse,
} from "@/features/ai/types";

export default function ScamCheckPage() {
  const [form, setForm] =
    useState<ScamCheckRequest>({
      content: "",
    });

  const [result, setResult] =
    useState<ScamCheckResponse | null>(null);

  const [loading, setLoading] =
    useState(false);

  const [error, setError] = useState("");

  async function runScamCheck() {
    const response = await checkScam(form);
    setResult(response);
  }

  async function handleSubmit(
    event: React.FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    try {
      setLoading(true);
      setError("");

      await runScamCheck();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to analyze content."
      );

      setResult(null);
    } finally {
      setLoading(false);
    }
  }

  async function retry() {
    try {
      setLoading(true);
      setError("");

      await runScamCheck();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to analyze content."
      );

      setResult(null);
    } finally {
      setLoading(false);
    }
  }

  const redFlags = Array.isArray(
    result?.red_flags
  )
    ? result.red_flags
    : [];

  const positiveSignals = Array.isArray(
    result?.positive_signals
  )
    ? result.positive_signals
    : [];

  const recommendations = Array.isArray(
    result?.recommendations
  )
    ? result.recommendations
    : [];

  return (
    <main className="min-h-screen bg-[#071512]">
      <section className="mx-auto max-w-7xl px-4 py-8 sm:px-6 sm:py-10 lg:px-8">
        <AIHeader
          badge="Rental Scam Checker"
          title="Detect suspicious rental listings"
          description="Paste property descriptions, WhatsApp chats, emails or payment requests. AI will estimate the scam risk and explain the warning signs."
          icon={
            <ShieldAlert className="h-7 w-7" />
          }
        />

        <div className="mt-8 grid items-start gap-8 lg:grid-cols-[400px_minmax(0,1fr)]">
          <section className="relative overflow-hidden rounded-[30px] border border-[#205C46]/40 bg-[#0D211B] p-6 shadow-[0_20px_60px_rgba(0,0,0,0.24)] lg:sticky lg:top-6">
            <div className="absolute -right-16 -top-16 h-52 w-52 rounded-full bg-[#D4A34F]/8 blur-3xl" />

            <div className="relative">
              <div className="flex items-start gap-4">
                <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-[16px] border border-[#D4A34F]/20 bg-[#D4A34F]/10 text-[#F0C86A]">
                  <ShieldAlert className="h-6 w-6" />
                </div>

                <div>
                  <p className="text-xs font-bold uppercase tracking-[0.18em] text-[#D4A34F]">
                    Scam Detection
                  </p>

                  <h2 className="mt-1 text-xl font-bold text-[#FBFAF7]">
                    Analyze Rental Content
                  </h2>

                  <p className="mt-2 text-sm leading-6 text-[#9EAEA7]">
                    Paste any suspicious listing,
                    conversation, email or payment
                    request for analysis.
                  </p>
                </div>
              </div>

              <form
                onSubmit={handleSubmit}
                className="mt-7 space-y-5"
              >
                <div className="space-y-2">
                  <div className="flex items-center justify-between gap-4">
                    <label
                      htmlFor="scam-content"
                      className="text-sm font-semibold text-[#D6E0DB]"
                    >
                      Rental content
                    </label>

                    <span className="text-xs font-medium text-[#7F9189]">
                      {form.content.length} characters
                    </span>
                  </div>

                  <textarea
                    id="scam-content"
                    rows={14}
                    value={form.content}
                    onChange={(event) =>
                      setForm({
                        content:
                          event.target.value,
                      })
                    }
                    placeholder="Paste the rental listing, owner message, payment request or advertisement here..."
                    className="w-full resize-none rounded-[22px] border border-[#205C46]/40 bg-[#10271F] px-4 py-4 text-sm leading-7 text-[#FBFAF7] outline-none transition placeholder:text-[#6F8179] hover:border-[#205C46]/70 focus:border-[#D4A34F] focus:ring-4 focus:ring-[#D4A34F]/10"
                    required
                  />
                </div>

                <div className="rounded-[20px] border border-amber-400/20 bg-amber-400/10 p-4">
                  <div className="flex items-start gap-3">
                    <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-amber-300" />

                    <p className="text-sm leading-6 text-amber-100">
                      Do not include passwords, OTPs,
                      bank details or other sensitive
                      personal information.
                    </p>
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={
                    loading ||
                    form.content.trim().length === 0
                  }
                  className="inline-flex min-h-12 w-full items-center justify-center gap-2 rounded-2xl bg-[#D4A34F] px-5 font-bold text-[#071512] shadow-[0_12px_30px_rgba(212,163,79,0.22)] transition hover:bg-[#F0C86A] disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <ShieldAlert className="h-4 w-4" />

                  {loading
                    ? "Analyzing..."
                    : "Check Scam Risk"}
                </button>
              </form>
            </div>
          </section>

          <section className="min-w-0">
            {loading ? (
              <AILoadingState
                title="Analyzing rental details"
                description="AI is checking the content for suspicious patterns, fraud signals, payment pressure, identity concerns, and common rental scam tactics."
              />
            ) : error ? (
              <AIErrorState
                title="Analysis failed"
                message={error}
                onRetry={retry}
                retrying={loading}
              />
            ) : result ? (
              <div className="space-y-6">
                <AIResultCard
                  title="Scam Analysis"
                  description="Review the complete assessment before sharing documents, visiting the property, or making any payment."
                  icon={
                    <ShieldAlert className="h-5 w-5" />
                  }
                >
                  <div className="space-y-8">
                    <RiskMeter
                      risk={result.risk_level}
                      score={result.risk_score}
                    />

                    <ResultSection
                      title="Why this risk was assigned"
                      description="Signals detected in the information you provided."
                      icon={
                        <AlertTriangle className="h-5 w-5" />
                      }
                    >
                      {redFlags.length > 0 ? (
                        <ul className="space-y-3">
                          {redFlags.map(
                            (flag, index) => (
                              <li
                                key={`${flag}-${index}`}
                                className="flex items-start gap-3 rounded-[18px] border border-amber-400/20 bg-amber-400/10 p-4 text-sm leading-7 text-amber-100"
                              >
                                <span className="mt-2.5 h-2 w-2 shrink-0 rounded-full bg-amber-300" />

                                <span>{flag}</span>
                              </li>
                            )
                          )}
                        </ul>
                      ) : (
                        <EmptyResultMessage>
                          No specific scam indicators
                          were returned.
                        </EmptyResultMessage>
                      )}
                    </ResultSection>

                    {positiveSignals.length > 0 && (
                      <ResultSection
                        title="Positive Signals"
                        description="Signals that reduce the apparent scam risk."
                        icon={
                          <CheckCircle2 className="h-5 w-5" />
                        }
                      >
                        <ul className="space-y-3">
                          {positiveSignals.map(
                            (signal, index) => (
                              <li
                                key={`${signal}-${index}`}
                                className="flex items-start gap-3 rounded-[18px] border border-emerald-400/20 bg-emerald-400/10 p-4 text-sm leading-7 text-emerald-100"
                              >
                                <CheckCircle2 className="mt-1 h-4 w-4 shrink-0 text-emerald-300" />

                                <span>{signal}</span>
                              </li>
                            )
                          )}
                        </ul>
                      </ResultSection>
                    )}

                    <ResultSection
                      title="Safety Tips"
                      description="Recommended steps before continuing with the rental."
                      icon={
                        <CheckCircle2 className="h-5 w-5" />
                      }
                    >
                      {recommendations.length > 0 ? (
                        <ul className="space-y-3">
                          {recommendations.map(
                            (tip, index) => (
                              <li
                                key={`${tip}-${index}`}
                                className="flex items-start gap-3 rounded-[18px] border border-emerald-400/20 bg-emerald-400/10 p-4 text-sm leading-7 text-emerald-100"
                              >
                                <CheckCircle2 className="mt-1 h-4 w-4 shrink-0 text-emerald-300" />

                                <span>{tip}</span>
                              </li>
                            )
                          )}
                        </ul>
                      ) : (
                        <EmptyResultMessage>
                          No additional safety tips
                          were returned.
                        </EmptyResultMessage>
                      )}
                    </ResultSection>

                    <section className="relative overflow-hidden rounded-[24px] border border-[#D4A34F]/20 bg-[#D4A34F]/10 p-5">
                      <div className="absolute -right-12 -top-12 h-36 w-36 rounded-full bg-[#D4A34F]/10 blur-3xl" />

                      <div className="relative">
                        <div className="flex items-center gap-3">
                          <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-[#D4A34F]/20 bg-[#D4A34F]/10 text-[#F0C86A]">
                            <Sparkles className="h-5 w-5" />
                          </div>

                          <h3 className="font-bold text-[#FBFAF7]">
                            AI Summary
                          </h3>
                        </div>

                        <p className="mt-4 text-sm leading-7 text-[#D6E0DB]">
                          {result.summary ||
                            "No summary was returned."}
                        </p>

                        {result.disclaimer && (
                          <p className="mt-4 border-t border-[#D4A34F]/15 pt-4 text-xs leading-6 text-[#9EAEA7]">
                            {result.disclaimer}
                          </p>
                        )}
                      </div>
                    </section>
                  </div>
                </AIResultCard>
              </div>
            ) : (
              <section className="relative flex min-h-[520px] flex-col items-center justify-center overflow-hidden rounded-[30px] border border-dashed border-[#D4A34F]/25 bg-[#0D211B] px-6 py-12 text-center shadow-[0_20px_60px_rgba(0,0,0,0.24)]">
                <div className="absolute left-1/2 top-1/2 h-64 w-64 -translate-x-1/2 -translate-y-1/2 rounded-full bg-[#D4A34F]/5 blur-3xl" />

                <div className="relative flex flex-col items-center">
                  <div className="flex h-24 w-24 items-center justify-center rounded-[28px] border border-[#D4A34F]/25 bg-[#D4A34F]/10 text-[#F0C86A]">
                    <ShieldAlert className="h-10 w-10" />
                  </div>

                  <p className="mt-6 text-xs font-bold uppercase tracking-[0.2em] text-[#D4A34F]">
                    Rental Safety Analysis
                  </p>

                  <h2 className="mt-3 text-3xl font-bold text-[#FBFAF7]">
                    No Analysis Yet
                  </h2>

                  <p className="mt-4 max-w-lg text-sm leading-7 text-[#9EAEA7] sm:text-base">
                    Paste a rental conversation,
                    listing, email or payment request
                    to receive an AI-generated scam
                    assessment.
                  </p>

                  <div className="mt-7 inline-flex items-center gap-2 rounded-full border border-[#205C46]/40 bg-[#10271F] px-4 py-2 text-sm font-semibold text-[#D6E0DB]">
                    <Sparkles className="h-4 w-4 text-[#F0C86A]" />
                    Smart fraud signal detection
                  </div>
                </div>
              </section>
            )}
          </section>
        </div>
      </section>
    </main>
  );
}

interface ResultSectionProps {
  title: string;
  description: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}

function ResultSection({
  title,
  description,
  icon,
  children,
}: ResultSectionProps) {
  return (
    <section>
      <div className="flex items-start gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-[#D4A34F]/20 bg-[#D4A34F]/10 text-[#F0C86A]">
          {icon}
        </div>

        <div>
          <h3 className="text-lg font-bold text-[#FBFAF7]">
            {title}
          </h3>

          <p className="mt-1 text-sm leading-6 text-[#9EAEA7]">
            {description}
          </p>
        </div>
      </div>

      <div className="mt-4">
        {children}
      </div>
    </section>
  );
}

function EmptyResultMessage({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <p className="rounded-[18px] border border-[#205C46]/30 bg-[#10271F] p-4 text-sm leading-6 text-[#9EAEA7]">
      {children}
    </p>
  );
}