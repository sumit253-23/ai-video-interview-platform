import { useNavigate } from "react-router-dom";

function Dashboard() {
  const navigate = useNavigate();

  const user = JSON.parse(localStorage.getItem("user") || "null");

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
    navigate("/login");
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-950/90">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5">
          <div>
            <h1 className="text-xl font-bold tracking-tight">
              AI Interview
            </h1>

            <p className="text-xs text-slate-500">
              Interview Preparation Platform
            </p>
          </div>

          <button
            onClick={handleLogout}
            className="rounded-xl border border-slate-700 px-4 py-2 text-sm font-medium text-slate-300 transition hover:border-red-500/50 hover:bg-red-500/10 hover:text-red-300"
          >
            Logout
          </button>
        </div>
      </header>

      {/* Main */}
      <main className="mx-auto max-w-7xl px-6 py-10">
        {/* Welcome */}
        <section className="mb-10">
          <p className="mb-2 text-sm font-medium text-blue-400">
            Your Interview Workspace
          </p>

          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
            Welcome{user?.name ? `, ${user.name}` : ""}
          </h2>

          <p className="mt-3 max-w-2xl text-slate-400">
            Prepare for technical interviews with AI-powered resume
            analysis, job matching, and realistic interview practice.
          </p>
        </section>

        {/* Quick Actions */}
        <section className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">

          {/* Resume */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6 transition hover:border-slate-700">
            <div className="mb-5 flex h-12 w-12 items-center justify-center rounded-xl bg-blue-500/10 text-xl">
              📄
            </div>

            <h3 className="text-lg font-semibold">
              Resume Analysis
            </h3>

            <p className="mt-2 text-sm leading-6 text-slate-400">
              Upload your resume and get AI-powered insights about your
              skills, experience, and profile.
            </p>

            <button
              className="mt-5 text-sm font-semibold text-blue-400 transition hover:text-blue-300"
              onClick={() => navigate("/resume")}
            >
              Open Resume →
            </button>
          </div>

          {/* Job Match */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6 transition hover:border-slate-700">
            <div className="mb-5 flex h-12 w-12 items-center justify-center rounded-xl bg-purple-500/10 text-xl">
              🎯
            </div>

            <h3 className="text-lg font-semibold">
              Job Match
            </h3>

            <p className="mt-2 text-sm leading-6 text-slate-400">
              Compare your resume with a job description and understand
              how well your profile matches the role.
            </p>

            <button
              className="mt-5 text-sm font-semibold text-purple-400 transition hover:text-purple-300"
              onClick={() => navigate("/job-match")}
            >
              Match a Job →
            </button>
          </div>

          {/* Interview */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6 transition hover:border-slate-700">
            <div className="mb-5 flex h-12 w-12 items-center justify-center rounded-xl bg-green-500/10 text-xl">
              🎥
            </div>

            <h3 className="text-lg font-semibold">
              AI Interview
            </h3>

            <p className="mt-2 text-sm leading-6 text-slate-400">
              Practice realistic AI-powered interviews with dynamic
              questions and answer evaluation.
            </p>

            <button
              className="mt-5 text-sm font-semibold text-green-400 transition hover:text-green-300"
              onClick={() => navigate("/video-interview")}
            >
              Start Interview →
            </button>
          </div>
        </section>

        {/* Progress */}
        <section className="mt-10 rounded-2xl border border-slate-800 bg-slate-900 p-6">
          <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
            <div>
              <h3 className="text-lg font-semibold">
                Interview Preparation
              </h3>

              <p className="mt-1 text-sm text-slate-400">
                Your preparation workspace will appear here.
              </p>
            </div>

            <span className="w-fit rounded-full border border-slate-700 bg-slate-950 px-3 py-1 text-xs text-slate-400">
              Getting Started
            </span>
          </div>
        </section>
      </main>
    </div>
  );
}

export default Dashboard;