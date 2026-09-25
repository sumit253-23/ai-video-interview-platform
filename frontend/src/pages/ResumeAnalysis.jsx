import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

function ResumeAnalysis() {
  const navigate = useNavigate();

  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const savedAnalysis = localStorage.getItem("resume_analysis");

    if (savedAnalysis) {
      try {
        setAnalysis(JSON.parse(savedAnalysis));
      } catch (error) {
        console.error("Failed to read resume analysis:", error);
      }
    }

    setLoading(false);
  }, []);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950 text-white">
        <p className="text-slate-400">
          Loading analysis...
        </p>
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950 px-6 text-white">
        <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900 p-8 text-center">
          <h2 className="text-xl font-semibold">
            No Resume Analysis Found
          </h2>

          <p className="mt-3 text-sm text-slate-400">
            Upload and analyze your resume before viewing the analysis.
          </p>

          <button
            onClick={() => navigate("/resume")}
            className="mt-6 rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold transition hover:bg-blue-500"
          >
            Go to Resume
          </button>
        </div>
      </div>
    );
  }

  const renderList = (items) => {
    if (!Array.isArray(items) || items.length === 0) {
      return (
        <p className="text-sm text-slate-500">
          No information available.
        </p>
      );
    }

    return (
      <div className="flex flex-wrap gap-2">
        {items.map((item, index) => {
          // Handle object items such as:
          // { name: "...", description: "..." }
          if (
            typeof item === "object" &&
            item !== null
          ) {
            return (
              <div
                key={`${item.name || "item"}-${index}`}
                className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3"
              >
                {item.name && (
                  <p className="text-sm font-semibold text-slate-200">
                    {item.name}
                  </p>
                )}

                {item.description && (
                  <p className="mt-1 text-sm leading-6 text-slate-400">
                    {item.description}
                  </p>
                )}
              </div>
            );
          }

          return (
            <span
              key={`${item}-${index}`}
              className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-300"
            >
              {String(item)}
            </span>
          );
        })}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      {/* Header */}
      <header className="border-b border-slate-800">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
          <div>
            <h1 className="text-xl font-bold">
              AI Interview
            </h1>

            <p className="text-xs text-slate-500">
              Resume Intelligence
            </p>
          </div>

          <button
            onClick={() => navigate("/dashboard")}
            className="rounded-xl border border-slate-700 px-4 py-2 text-sm text-slate-300 transition hover:border-slate-600 hover:bg-slate-900"
          >
            Dashboard
          </button>
        </div>
      </header>

      {/* Main */}
      <main className="mx-auto max-w-6xl px-6 py-10">
        {/* Heading */}
        <section className="mb-8">
          <p className="mb-2 text-sm font-medium text-blue-400">
            AI Resume Analysis
          </p>

          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
            Your Resume Insights
          </h2>

          <p className="mt-3 max-w-3xl text-slate-400">
            AI-generated insights from your uploaded resume. These
            insights will also be used to personalize your interview
            experience.
          </p>
        </section>

        {/* Summary */}
        <section className="mb-6 rounded-2xl border border-slate-800 bg-slate-900 p-6 sm:p-8">
          <div className="mb-4 flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-500/10">
              🧠
            </div>

            <div>
              <h3 className="font-semibold">
                Profile Summary
              </h3>

              <p className="text-xs text-slate-500">
                AI-generated overview
              </p>
            </div>
          </div>

          <p className="text-sm leading-7 text-slate-300">
            {typeof analysis.summary === "string"
              ? analysis.summary
              : "No summary available."}
          </p>
        </section>

        {/* Skills */}
        <section className="grid gap-6 lg:grid-cols-2">
          {/* Skills */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
            <h3 className="mb-4 text-lg font-semibold">
              Skills
            </h3>

            {renderList(analysis.skills)}
          </div>

          {/* Programming Languages */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
            <h3 className="mb-4 text-lg font-semibold">
              Programming Languages
            </h3>

            {renderList(analysis.programming_languages)}
          </div>

          {/* Frameworks */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
            <h3 className="mb-4 text-lg font-semibold">
              Frameworks & Technologies
            </h3>

            {renderList(analysis.frameworks)}
          </div>

          {/* Projects */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
            <h3 className="mb-4 text-lg font-semibold">
              Projects
            </h3>

            {renderList(analysis.projects)}
          </div>

          {/* CS Fundamentals */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
            <h3 className="mb-4 text-lg font-semibold">
              CS Fundamentals
            </h3>

            {renderList(analysis.cs_fundamentals)}
          </div>

          {/* DSA */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
            <h3 className="mb-4 text-lg font-semibold">
              DSA Topics
            </h3>

            {renderList(analysis.dsa_topics)}
          </div>
        </section>

        {/* Continue */}
        <section className="mt-8 rounded-2xl border border-blue-500/20 bg-blue-500/5 p-6">
          <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-center">
            <div>
              <h3 className="text-lg font-semibold">
                Ready for the next step?
              </h3>

              <p className="mt-1 text-sm text-slate-400">
                Use your resume insights to prepare for a personalized
                AI interview.
              </p>
            </div>

            <button
              onClick={() => navigate("/dashboard")}
              className="rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold transition hover:bg-blue-500"
            >
              Continue →
            </button>
          </div>
        </section>
      </main>
    </div>
  );
}

export default ResumeAnalysis;