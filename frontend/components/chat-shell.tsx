"use client";

import { Fragment, useMemo, useState } from "react";

type Citation = {
  title: string;
  url: string;
  snippet: string;
};

type ChatResponse = {
  answer: string;
  citations: Citation[];
  grounded: boolean;
};

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api";

const starterPrompts = [
  "How do I use Docling to parse PDFs?",
  "What are the main Docling pipeline concepts?",
  "How can I extract tables with Docling?",
];

export function ChatShell() {
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState<ChatResponse | null>(null);
  const [submittedQuery, setSubmittedQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const canSubmit = useMemo(() => query.trim().length > 0 && !isLoading, [query, isLoading]);

  async function handleSubmit(nextQuery?: string) {
    const activeQuery = (nextQuery ?? query).trim();

    if (!activeQuery) {
      return;
    }

    setIsLoading(true);
    setError("");
    setSubmittedQuery(activeQuery);

    try {
      const result = await fetch(`${API_BASE_URL}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query: activeQuery }),
      });

      if (!result.ok) {
        throw new Error(`Request failed with status ${result.status}`);
      }

      const data: ChatResponse = await result.json();
      setResponse(data);
      setQuery(activeQuery);
    } catch (submissionError) {
      setResponse(null);
      setError(
        submissionError instanceof Error
          ? submissionError.message
          : "Unable to reach the Docling assistant backend.",
      );
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50">
      <main className="mx-auto flex min-h-screen w-full max-w-6xl flex-col gap-10 px-6 py-10 lg:px-10">
        <section className="rounded-3xl border border-white/10 bg-white/5 p-8 shadow-2xl shadow-cyan-950/20 backdrop-blur">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-3xl space-y-4">
              <span className="inline-flex rounded-full border border-cyan-400/30 bg-cyan-400/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-cyan-200">
                Agentic RAG MVP
              </span>
              <div className="space-y-3">
                <h1 className="text-4xl font-semibold tracking-tight text-white sm:text-5xl">
                  Ask how to use Docling
                </h1>
                <p className="max-w-2xl text-base leading-7 text-slate-300 sm:text-lg">
                  Search indexed Docling documentation through a grounded assistant experience.
                  The backend now fetches docs, chunks content, retrieves relevant passages, and
                  generates answers with citations.
                </p>
              </div>
            </div>

            <div className="grid gap-3 rounded-2xl border border-white/10 bg-slate-900/70 p-4 text-sm text-slate-300 sm:grid-cols-3">
              <StatCard label="Primary sources" value="Official docs" />
              <StatCard label="Secondary sources" value="GitHub examples" />
              <StatCard label="Runtime" value="Local-first" />
            </div>
          </div>
        </section>

        <section className="grid gap-6 lg:grid-cols-[1.4fr_0.9fr]">
          <div className="rounded-3xl border border-white/10 bg-slate-900/80 p-6 shadow-xl shadow-black/20">
            <div className="mb-5 flex items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-semibold text-white">Docling assistant</h2>
                <p className="mt-1 text-sm text-slate-400">
                  Ask a question and get a grounded answer with citations.
                </p>
              </div>
              <span className="rounded-full border border-emerald-400/30 bg-emerald-400/10 px-3 py-1 text-xs font-medium text-emerald-200">
                Backend connected
              </span>
            </div>

            <div className="space-y-4">
              <label className="block">
                <span className="mb-2 block text-sm font-medium text-slate-200">
                  Your Docling question
                </span>
                <textarea
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="Example: How do I convert a PDF into structured markdown with Docling?"
                  className="min-h-36 w-full rounded-2xl border border-white/10 bg-slate-950/80 px-4 py-3 text-sm text-white outline-none transition focus:border-cyan-400/60 focus:ring-2 focus:ring-cyan-400/20"
                />
              </label>

              <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
                <button
                  type="button"
                  onClick={() => handleSubmit()}
                  disabled={!canSubmit}
                  className="inline-flex h-12 items-center justify-center rounded-full bg-cyan-400 px-6 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-400"
                >
                  {isLoading ? "Searching..." : "Ask assistant"}
                </button>
                <p className="text-sm text-slate-400">
                  Endpoint: <code className="rounded bg-white/5 px-2 py-1">{API_BASE_URL}/chat</code>
                </p>
              </div>

              <div className="flex flex-wrap gap-2">
                {starterPrompts.map((prompt) => (
                  <button
                    key={prompt}
                    type="button"
                    onClick={() => {
                      setQuery(prompt);
                      void handleSubmit(prompt);
                    }}
                    className="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-slate-200 transition hover:border-cyan-400/40 hover:bg-cyan-400/10"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <aside className="rounded-3xl border border-white/10 bg-slate-900/80 p-6 shadow-xl shadow-black/20">
            <h2 className="text-xl font-semibold text-white">How this MVP works</h2>
            <div className="mt-4 space-y-4 text-sm leading-6 text-slate-300">
              <StepItem
                step="1"
                title="User asks a Docling question"
                description="The frontend sends the query to the FastAPI backend."
              />
              <StepItem
                step="2"
                title="Backend retrieves relevant Docling chunks"
                description="The FastAPI service searches indexed documentation passages related to the question."
              />
              <StepItem
                step="3"
                title="LLM generates a grounded answer"
                description="Ollama answers from retrieved context, and the UI renders citations plus richer formatting."
              />
            </div>
          </aside>
        </section>

        <section className="rounded-3xl border border-white/10 bg-slate-900/80 p-6 shadow-xl shadow-black/20">
          <div className="flex flex-col gap-2 border-b border-white/10 pb-4">
            <h2 className="text-xl font-semibold text-white">Assistant response</h2>
            <p className="text-sm text-slate-400">
              {submittedQuery
                ? `Showing results for "${submittedQuery}"`
                : "Submit a question to see the response here."}
            </p>
          </div>

          {error ? (
            <div className="mt-6 rounded-2xl border border-rose-400/30 bg-rose-400/10 p-4 text-sm text-rose-100">
              {error}
            </div>
          ) : null}

          {!error && !response && !isLoading ? (
            <EmptyState />
          ) : null}

          {isLoading ? (
            <div className="mt-6 space-y-4">
              <LoadingBlock className="h-5 w-40" />
              <LoadingBlock className="h-4 w-full" />
              <LoadingBlock className="h-4 w-11/12" />
              <LoadingBlock className="h-4 w-10/12" />
            </div>
          ) : null}

          {response ? (
            <div className="mt-6 space-y-6">
              <div className="rounded-2xl border border-white/10 bg-slate-950/70 p-5">
                <div className="mb-3 flex items-center gap-3">
                  <span className="rounded-full border border-cyan-400/30 bg-cyan-400/10 px-3 py-1 text-xs font-medium text-cyan-200">
                    {response.grounded ? "Grounded answer" : "Ungrounded answer"}
                  </span>
                </div>
                <FormattedAnswer answer={response.answer} />
              </div>

              <div>
                <h3 className="text-sm font-semibold uppercase tracking-[0.2em] text-slate-400">
                  Sources
                </h3>
                <div className="mt-3 grid gap-3">
                  {response.citations.map((citation, index) => (
                    <a
                      key={`${citation.url}-${index}`}
                      href={citation.url}
                      target="_blank"
                      rel="noreferrer"
                      className="rounded-2xl border border-white/10 bg-white/5 p-4 transition hover:border-cyan-400/40 hover:bg-cyan-400/5"
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <p className="font-medium text-white">{citation.title}</p>
                          <p className="mt-2 text-sm leading-6 text-slate-300">
                            {citation.snippet}
                          </p>
                        </div>
                        <span className="text-xs text-cyan-200">Open source</span>
                      </div>
                    </a>
                  ))}
                </div>
              </div>
            </div>
          ) : null}
        </section>
      </main>
    </div>
  );
}

type StatCardProps = {
  label: string;
  value: string;
};

function StatCard({ label, value }: StatCardProps) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
      <p className="text-xs uppercase tracking-[0.2em] text-slate-500">{label}</p>
      <p className="mt-2 text-sm font-semibold text-white">{value}</p>
    </div>
  );
}

type StepItemProps = {
  step: string;
  title: string;
  description: string;
};

function StepItem({ step, title, description }: StepItemProps) {
  return (
    <div className="flex gap-4">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-cyan-400/15 text-sm font-semibold text-cyan-200">
        {step}
      </div>
      <div>
        <p className="font-medium text-white">{title}</p>
        <p className="mt-1 text-slate-400">{description}</p>
      </div>
    </div>
  );
}

function FormattedAnswer({ answer }: { answer: string }) {
  const blocks = answer
    .split(/\n{2,}/)
    .map((block) => block.trim())
    .filter(Boolean);

  return (
    <div className="space-y-4 text-sm leading-7 text-slate-200">
      {blocks.map((block, blockIndex) => {
        if (block.includes("```")) {
          const segments = block.split(/```/);

          return (
            <div key={`code-block-${blockIndex}`} className="space-y-3">
              {segments.map((segment, segmentIndex) => {
                const trimmedSegment = segment.trim();

                if (!trimmedSegment) {
                  return null;
                }

                if (segmentIndex % 2 === 1) {
                  const lines = trimmedSegment.split("\n");
                  const firstLine = lines[0]?.trim() ?? "";
                  const language = /^[a-zA-Z0-9#+.-]+$/.test(firstLine) ? firstLine : "";
                  const code = language ? lines.slice(1).join("\n").trim() : trimmedSegment;

                  return (
                    <pre
                      key={`code-${blockIndex}-${segmentIndex}`}
                      className="overflow-x-auto rounded-2xl border border-cyan-400/20 bg-slate-900 px-4 py-3 text-xs leading-6 text-cyan-100"
                    >
                      {language ? (
                        <div className="mb-2 text-[11px] uppercase tracking-[0.2em] text-cyan-300/70">
                          {language}
                        </div>
                      ) : null}
                      <code>{code}</code>
                    </pre>
                  );
                }

                return (
                  <Fragment key={`text-${blockIndex}-${segmentIndex}`}>
                    <FormattedTextBlock text={trimmedSegment} />
                  </Fragment>
                );
              })}
            </div>
          );
        }

        return <FormattedTextBlock key={`block-${blockIndex}`} text={block} />;
      })}
    </div>
  );
}

function renderInlineMarkdown(text: string): React.ReactNode[] {
  const parts: React.ReactNode[] = [];
  let lastIndex = 0;
  
  // Match bold (**text** or __text__), italic (*text* or _text_), and inline code (`text`)
  const regex = /(\*\*|__)(.*?)\1|(\*|_)(.*?)\3|`([^`]+)`/g;
  let match;
  
  while ((match = regex.exec(text)) !== null) {
    // Add text before the match
    if (match.index > lastIndex) {
      parts.push(text.substring(lastIndex, match.index));
    }
    
    // Add the formatted match
    if (match[1]) {
      // Bold (**text** or __text__)
      parts.push(<strong key={match.index} className="font-semibold">{match[2]}</strong>);
    } else if (match[3]) {
      // Italic (*text* or _text_)
      parts.push(<em key={match.index} className="italic">{match[4]}</em>);
    } else if (match[5]) {
      // Inline code (`text`)
      parts.push(
        <code key={match.index} className="rounded bg-cyan-400/10 px-1.5 py-0.5 text-cyan-200">
          {match[5]}
        </code>
      );
    }
    
    lastIndex = regex.lastIndex;
  }
  
  // Add remaining text
  if (lastIndex < text.length) {
    parts.push(text.substring(lastIndex));
  }
  
  return parts.length > 0 ? parts : [text];
}

function FormattedTextBlock({ text }: { text: string }) {
  const lines = text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);

  if (lines.length === 0) {
    return null;
  }

  const isBulletList = lines.every((line) => /^([-*]|\d+\.)\s+/.test(line));

  if (isBulletList) {
    const isOrdered = lines.every((line) => /^\d+\.\s+/.test(line));

    if (isOrdered) {
      return (
        <ol className="list-decimal space-y-2 pl-5">
          {lines.map((line, index) => {
            const content = line.replace(/^\d+\.\s+/, "");
            return <li key={`ordered-${index}`}>{renderInlineMarkdown(content)}</li>;
          })}
        </ol>
      );
    }

    return (
      <ul className="list-disc space-y-2 pl-5">
        {lines.map((line, index) => {
          const content = line.replace(/^[-*]\s+/, "");
          return <li key={`bullet-${index}`}>{renderInlineMarkdown(content)}</li>;
        })}
      </ul>
    );
  }

  // Check for headers
  return (
    <div className="space-y-3">
      {lines.map((line, index) => {
        // Check for markdown headers
        const headerMatch = line.match(/^(#{1,6})\s+(.+)$/);
        if (headerMatch) {
          const level = headerMatch[1].length;
          const content = headerMatch[2];
          
          // Render headers with appropriate sizes
          if (level === 1) {
            return <h1 key={`h1-${index}`} className="text-xl font-bold text-white">{renderInlineMarkdown(content)}</h1>;
          } else if (level === 2) {
            return <h2 key={`h2-${index}`} className="text-lg font-semibold text-white">{renderInlineMarkdown(content)}</h2>;
          } else if (level === 3) {
            return <h3 key={`h3-${index}`} className="text-base font-semibold text-white">{renderInlineMarkdown(content)}</h3>;
          } else {
            return <h4 key={`h4-${index}`} className="text-sm font-semibold text-slate-100">{renderInlineMarkdown(content)}</h4>;
          }
        }
        
        // Check for horizontal rules
        if (/^[-*_]{3,}$/.test(line)) {
          return <hr key={`hr-${index}`} className="border-t border-white/10 my-4" />;
        }
        
        // Regular paragraph
        return <p key={`paragraph-${index}`}>{renderInlineMarkdown(line)}</p>;
      })}
    </div>
  );
}

function EmptyState() {
  return (
    <div className="mt-6 rounded-2xl border border-dashed border-white/10 bg-white/[0.03] p-8 text-center">
      <p className="text-sm font-medium text-white">No answer yet</p>
      <p className="mt-2 text-sm leading-6 text-slate-400">
        Start with one of the suggested prompts or ask your own question about Docling.
      </p>
    </div>
  );
}

type LoadingBlockProps = {
  className: string;
};

function LoadingBlock({ className }: LoadingBlockProps) {
  return <div className={`animate-pulse rounded-full bg-white/10 ${className}`} />;
}

// Made with Bob
