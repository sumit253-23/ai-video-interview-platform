import { useState } from "react";
import { useNavigate } from "react-router-dom";

function ResumeUpload() {
  const navigate = useNavigate();

  const [selectedFile, setSelectedFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [resumeId, setResumeId] = useState(
  localStorage.getItem("resume_id")
  );

  const [analyzing, setAnalyzing] = useState(false);
  const [analysisDone, setAnalysisDone] = useState(false);

  const handleFileChange = (event) => {
    const file = event.target.files?.[0];

    if (!file) return;

    if (file.type !== "application/pdf") {
      alert("Please select a PDF file.");
      return;
    }

    setSelectedFile(file);
  };

  const handleDrop = (event) => {
    event.preventDefault();
    setDragActive(false);

    const file = event.dataTransfer.files?.[0];

    if (!file) return;

    if (file.type !== "application/pdf") {
      alert("Please upload a PDF file.");
      return;
    }

    setSelectedFile(file);
  };

  const handleUpload = async () => {
  if (!selectedFile) {
    alert("Please select your resume first.");
    return;
  }

  const token = localStorage.getItem("access_token");

  if (!token) {
    alert("Your session has expired. Please login again.");
    navigate("/login");
    return;
  }

  try {
    const formData = new FormData();

    formData.append("resume", selectedFile);

    const response = await fetch(
      "http://127.0.0.1:5000/api/resume/upload",
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      }
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error(
        data.message || "Resume upload failed."
      );
    }

    localStorage.setItem(
      "resume_id",
      String(data.resume.id)
    );

    localStorage.setItem(
      "resume_filename",
      data.resume.filename
    ); 

    setResumeId(String(data.resume.id));
    setAnalysisDone(false);


    alert("Resume uploaded successfully.");

    console.log("Resume upload response:", data);
  } catch (error) {
    console.error("Resume upload error:", error);
    alert(error.message);
  }
};

const handleAnalyze = async () => {
  const storedResumeId =
    resumeId || localStorage.getItem("resume_id");

  if (!storedResumeId) {
    alert("Please upload your resume first.");
    return;
  }

  const token = localStorage.getItem("access_token");

  if (!token) {
    alert("Your session has expired. Please login again.");
    navigate("/login");
    return;
  }

  try {
    setAnalyzing(true);

    const response = await fetch(
      `http://127.0.0.1:5000/api/resume/${storedResumeId}/analyze`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error(
        data.message || "Resume analysis failed."
      );
    }

    localStorage.setItem(
      "resume_analysis",
      JSON.stringify(data.analysis)
    );

    setAnalysisDone(true);
    navigate("/resume-analysis");
    

    console.log("Resume analysis response:", data);
  } catch (error) {
    console.error("Resume analysis error:", error);
    alert(error.message);
  } finally {
    setAnalyzing(false);
  }
};

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      {/* Header */}
      <header className="border-b border-slate-800">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-5">
          <div>
            <h1 className="text-xl font-bold">AI Interview</h1>
            <p className="text-xs text-slate-500">
              Resume Analysis
            </p>
          </div>

          <button
            onClick={() => navigate("/dashboard")}
            className="rounded-xl border border-slate-700 px-4 py-2 text-sm text-slate-300 transition hover:border-slate-600 hover:bg-slate-900"
          >
            Back to Dashboard
          </button>
        </div>
      </header>

      {/* Main */}
      <main className="mx-auto max-w-3xl px-6 py-12">
        <div className="mb-8">
          <p className="mb-2 text-sm font-medium text-blue-400">
            Resume Setup
          </p>

          <h2 className="text-3xl font-bold tracking-tight">
            Upload your resume
          </h2>

          <p className="mt-3 text-slate-400">
            Upload your latest resume in PDF format. Our AI will analyze
            your profile and prepare it for personalized interview
            practice.
          </p>
        </div>

        {/* Upload Card */}
        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-xl sm:p-8">
          <label
            htmlFor="resume"
            onDragOver={(event) => {
              event.preventDefault();
              setDragActive(true);
            }}
            onDragLeave={() => setDragActive(false)}
            onDrop={handleDrop}
            className={`flex min-h-72 cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed px-6 text-center transition ${
              dragActive
                ? "border-blue-500 bg-blue-500/10"
                : "border-slate-700 bg-slate-950/50 hover:border-slate-600 hover:bg-slate-950"
            }`}
          >
            <div className="mb-5 flex h-16 w-16 items-center justify-center rounded-2xl bg-blue-500/10 text-3xl">
              📄
            </div>

            <h3 className="text-lg font-semibold">
              {selectedFile
                ? selectedFile.name
                : "Drop your resume here"}
            </h3>

            <p className="mt-2 text-sm text-slate-500">
              {selectedFile
                ? `${(selectedFile.size / 1024 / 1024).toFixed(2)} MB`
                : "or click to browse from your computer"}
            </p>

            <span className="mt-5 rounded-lg border border-slate-700 px-4 py-2 text-sm text-slate-300">
              Choose PDF
            </span>

            <input
              id="resume"
              type="file"
              accept=".pdf,application/pdf"
              onChange={handleFileChange}
              className="hidden"
            />
          </label>

          {/* Selected file */}
          {selectedFile && (
            <div className="mt-5 flex items-center justify-between rounded-xl border border-slate-800 bg-slate-950 px-4 py-3">
              <div className="min-w-0">
                <p className="truncate text-sm font-medium text-white">
                  {selectedFile.name}
                </p>

                <p className="mt-1 text-xs text-slate-500">
                  PDF document
                </p>
              </div>

              <button
                type="button"
                onClick={() => setSelectedFile(null)}
                className="ml-4 text-sm text-red-400 transition hover:text-red-300"
              >
                Remove
              </button>
            </div>
          )}

          {/* Upload button */}
          <button
            type="button"
            onClick={handleUpload}
            disabled={!selectedFile}
            className="mt-6 w-full rounded-xl bg-blue-600 px-5 py-3 font-semibold text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-40"
          >
            Upload Resume
          </button>

           {resumeId && (
  <button
    type="button"
    onClick={handleAnalyze}
    disabled={analyzing}
    className="mt-3 w-full rounded-xl border border-blue-500/40 bg-blue-500/10 px-5 py-3 font-semibold text-blue-300 transition hover:bg-blue-500/20 disabled:cursor-not-allowed disabled:opacity-50"
  >
    {analyzing
      ? "Analyzing Resume..."
      : analysisDone
      ? "Resume Analyzed ✓"
      : "Analyze Resume"}
  </button>
)}

          <p className="mt-4 text-center text-xs text-slate-600">
            Only PDF files are supported.
          </p>
        </div>
      </main>
    </div>
  );
}

export default ResumeUpload;