import { useState } from "react";
import { useNavigate } from "react-router-dom";

function JobMatch() {
  const navigate = useNavigate();

  const [jobDescription, setJobDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  const handleMatch = async () => {
    setError("");
    setResult(null);

    const token = localStorage.getItem("access_token");
    const resumeId = localStorage.getItem("resume_id");

    if (!token) {
      navigate("/login");
      return;
    }

    if (!resumeId) {
      setError("Please upload your resume first.");
      return;
    }

    if (!jobDescription.trim()) {
      setError("Please enter the job description.");
      return;
    }

    try {
      setLoading(true);

      const response = await fetch(
        "http://127.0.0.1:5000/api/job-matching/",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            resume_id: Number(resumeId),
            job_description: jobDescription.trim(),
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.message || "Job matching failed."
        );
      }

      setResult(data.job_match);

      localStorage.setItem(
        "job_match_result",
        JSON.stringify(data.job_match)
      );
    } catch (error) {
      console.error("Job matching error:", error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
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
              Job Matching
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

      <main className="mx-auto max-w-5xl px-6 py-10">
        {/* Heading */}
        <section className="mb-8">
          <p className="mb-2 text-sm font-medium text-blue-400">
            Career Intelligence
          </p>

          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
            Match your resume with a job
          </h2>

          <p className="mt-3 max-w-3xl text-slate-400">
            Paste a job description and let AI compare it with your
            analyzed resume.
          </p>
        </section>

        {/* Job Description */}
        <section className="rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-xl sm:p-8">
          <label
            htmlFor="jobDescription"
            className="mb-3 block text-sm font-medium text-slate-300"
          >
            Job Description
          </label>

          <textarea
            id="jobDescription"
            value={jobDescription}
            onChange={(event) =>
              setJobDescription(event.target.value)
            }
            placeholder="Paste the complete job description here..."
            rows={12}
            className="w-full resize-y rounded-xl border border-slate-700 bg-slate-950 px-4 py-4 text-sm leading-6 text-white outline-none transition placeholder:text-slate-600 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
          />

          {error && (
            <div className="mt-4 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
              {error}
            </div>
          )}

          <button
            type="button"
            onClick={handleMatch}
            disabled={loading}
            className="mt-5 w-full rounded-xl bg-blue-600 px-5 py-3 font-semibold text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading
              ? "Analyzing Job Match..."
              : "Analyze Job Match"}
          </button>
        </section>

        {/* Result */}
        {result && (
          <section className="mt-8 space-y-6">
            {/* Score */}
            <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6 sm:p-8">
              <p className="text-sm text-slate-400">
                Resume Match Score
              </p>

              <div className="mt-3 flex items-end gap-2">
                <span className="text-5xl font-bold text-blue-400">
                  {result.match_score}
                </span>

                <span className="mb-2 text-lg text-slate-500">
                  / 100
                </span>
              </div>
            </div>

            {/* Skills */}
            <div className="grid gap-6 lg:grid-cols-2">
              <ResultCard
                title="Matched Skills"
                items={result.matched_skills}
              />

              <ResultCard
                title="Missing Skills"
                items={result.missing_skills}
              />

              <ResultCard
                title="Strengths"
                items={result.strengths}
              />

              <ResultCard
                title="Recommendations"
                items={result.recommendations}
              />
            </div>
          </section>
        )}
      </main>
    </div>
  );
}

function ResultCard({ title, items }) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
      <h3 className="mb-4 text-lg font-semibold">
        {title}
      </h3>

      {Array.isArray(items) && items.length > 0 ? (
        <ul className="space-y-3">
          {items.map((item, index) => (
            <li
              key={`${item}-${index}`}
              className="rounded-xl border border-slate-800 bg-slate-950 px-4 py-3 text-sm leading-6 text-slate-300"
            >
              {item}
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-slate-500">
          No information available.
        </p>
      )}
    </div>
  );
}

export default JobMatch;