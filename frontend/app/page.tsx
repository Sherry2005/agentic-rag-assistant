
"use client";

import { useState } from "react";

type Source = {
  id?: number;
  source?: string;
  title?: string;
  page?: number | null;
  section?: string | null;
};

type Answer = {
  answer: string;
  sources?: Source[];
};

export default function Home() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<Answer | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function askQuestion(q: string) {
    if (!q.trim() || loading) return;

    setLoading(true);
    setError("");
    setAnswer(null);
    setQuestion(q);

    try {
      const API_URL =
        process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

      const response = await fetch(`${API_URL}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q }),
      });

      if (!response.ok) {
        throw new Error(`API returned status ${response.status}`);
      }

      const data = await response.json();
      setAnswer(data);
    } catch {
      setError(
        "Could not connect to the API. Make sure your FastAPI backend is running on port 8000."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-[#f5f7fb] text-slate-900">
      <header className="border-b border-slate-200 bg-white px-6 py-5">
        <div className="mx-auto flex max-w-5xl items-center justify-between">
          <div>
            <h1 className="text-xl font-bold tracking-tight">
              Research Assistant
            </h1>
            <p className="mt-1 text-sm text-slate-500">
              Ask questions. Get evidence-backed answers.
            </p>
          </div>
          <span className="rounded-full bg-emerald-50 px-3 py-1.5 text-xs font-medium text-emerald-700">
            RAG Assistant
          </span>
        </div>
      </header>

      <section className="mx-auto max-w-3xl px-5 py-12">
        <div className="mb-8">
          <p className="text-sm font-semibold uppercase tracking-widest text-indigo-600">
            Your knowledge workspace
          </p>
          <h2 className="mt-3 text-3xl font-bold tracking-tight sm:text-4xl">
            What would you like to research?
          </h2>
          <p className="mt-3 leading-7 text-slate-600">
            Ask about renewable energy policies, solar incentives, and SREC
            markets using your indexed documents.
          </p>
        </div>

        <div className="mb-5 grid gap-3 sm:grid-cols-2">
          {[
            "What are Solar Renewable Energy Certificates?",
            "What trends affect SREC markets?",
            "What federal renewable energy policies are relevant?",
            "Explain solar carve-out programs.",
          ].map((example) => (
            <button
              key={example}
              onClick={() => askQuestion(example)}
              disabled={loading}
              className="rounded-xl border border-slate-200 bg-white p-4 text-left text-sm leading-6 transition hover:border-indigo-300 hover:bg-indigo-50 disabled:opacity-50"
            >
              {example}
              <span className="ml-2 text-indigo-600">→</span>
            </button>
          ))}
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            askQuestion(question);
          }}
          className="rounded-2xl border border-slate-200 bg-white p-3 shadow-sm"
        >
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask a question about your documents..."
            rows={3}
            className="w-full resize-y border-0 bg-transparent p-3 text-sm outline-none placeholder:text-slate-400"
          />
          <div className="flex items-center justify-between border-t border-slate-100 pt-3">
            <span className="px-2 text-xs text-slate-400">
              Answers retrieved from your knowledge base
            </span>
            <button
              type="submit"
              disabled={loading || !question.trim()}
              className="rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? "Researching..." : "Ask question →"}
            </button>
          </div>
        </form>

        {error && (
          <div className="mt-5 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            {error}
          </div>
        )}

        {answer && (
          <article className="mt-8 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-widest text-indigo-600">
              Answer
            </p>
            <h3 className="mt-2 text-lg font-semibold">{answer.answer}</h3>

            {!!answer.sources?.length && (
              <div className="mt-6 border-t border-slate-100 pt-5">
                <h4 className="mb-3 font-semibold">Sources</h4>
                <div className="space-y-3">
                  {answer.sources.map((source, index) => (
                    <div
                      key={`${source.id ?? index}-${source.source ?? ""}`}
                      className="rounded-lg bg-slate-50 p-3 text-sm"
                    >
                      <p className="font-medium">
                        {source.title || source.source || `Source ${index + 1}`}
                      </p>
                      <p className="mt-1 text-slate-500">
                        {source.page != null ? `Page ${source.page}` : ""}
                        {source.page != null && source.section ? " · " : ""}
                        {source.section || ""}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </article>
        )}
      </section>
    </main>
  );
}
