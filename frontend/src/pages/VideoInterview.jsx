import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
const API_URL = import.meta.env.VITE_API_URL;

function VideoInterview() {
  const navigate = useNavigate();

  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const recordingChunksRef = useRef([]);
  const recordingStartTimeRef = useRef(null);

  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const silenceTimerRef = useRef(null);
  const speechDetectedRef = useRef(false);

  const [started, setStarted] = useState(false);
  const [error, setError] = useState("");

  const [interviewId, setInterviewId] = useState(null);
  const [question, setQuestion] = useState("");
  const [loadingQuestion, setLoadingQuestion] = useState(false);
  const [questionError, setQuestionError] = useState("");
  const [currentQuestionId, setCurrentQuestionId] = useState(null);

  const [interviewStage, setInterviewStage] = useState(
    "candidate_introduction"
  );
  const [selectedResume, setSelectedResume] = useState("");
  const [cameraEnabled, setCameraEnabled] = useState(false);
  const [microphoneEnabled, setMicrophoneEnabled] = useState(false);
  const [cameraPreference, setCameraPreference] = useState(true);
  const [mediaError, setMediaError] = useState("");
  const [aiSpeaking, setAiSpeaking] = useState(false);

 const startInterview = async () => {
  try {
    setError("");
    setLoadingQuestion(true);

    const token = localStorage.getItem("access_token");
    const resumeId = localStorage.getItem("resume_id");
    const jobDescription =
      localStorage.getItem("job_description") || "";

    if (!token) {
      navigate("/login");
      return;
    }

    if (!resumeId) {
      setError("Please upload and analyze your resume first.");
      return;
    }

    // Create interview
    const response = await fetch(
  `${API_URL}/api/questions/start`,
      {

        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          resume_id: Number(resumeId),
          job_description: jobDescription,
        }),
      }
    );

   const data = await response.json();

console.log("START INTERVIEW RESPONSE:", {
  status: response.status,
  data: data,
});

if (!response.ok) {
  throw new Error(
    data.message ||
    data.msg ||
    "Failed to start interview."
  );
}

    console.log("Interview started:", data);

  const welcomeMessage =
  "Welcome to the interview. Please introduce yourself and tell me a little about your background.";

    setInterviewId(data.interview.id);
    setQuestion(welcomeMessage);
    setInterviewStage("candidate_introduction");
    setStarted(true);
    console.log("Interview started:", data);
  
  } catch (err) {
    console.error("START INTERVIEW ERROR:", err);

    stopMedia();

    setError(
      err.message || "Unable to start the interview."
    );
  } finally {
    setLoadingQuestion(false);
  }
};

  const stopMedia = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => {
        track.stop();
      });

      streamRef.current = null;
    }
  };
const enableCameraAndMicrophone = async () => {
  try {
    setMediaError("");

    const stream = await navigator.mediaDevices.getUserMedia({
      video: cameraPreference,
      audio: true,
    });

    streamRef.current = stream;

    if (videoRef.current) {
      videoRef.current.srcObject = stream;
    }

    setCameraEnabled(stream.getVideoTracks().length > 0);
    setMicrophoneEnabled(stream.getAudioTracks().length > 0);
  } catch (err) {
    console.error("MEDIA PERMISSION ERROR:", err);

    setMediaError(
      "Microphone access is required to start the interview."
    );

    setCameraEnabled(false);
    setMicrophoneEnabled(false);
  }
};
   
  const startRecording = () => {
  if (!streamRef.current) {
    return;
  }

  recordingChunksRef.current = [];

  const preferredMimeType = cameraEnabled ? "video/webm" : "audio/webm";
  const mimeType = MediaRecorder.isTypeSupported(preferredMimeType) ? preferredMimeType : "webm";

  const mediaRecorder = new MediaRecorder(streamRef.current, { mimeType });

  mediaRecorderRef.current = mediaRecorder;

  mediaRecorder.ondataavailable = (event) => {
    if (event.data && event.data.size > 0) {
      recordingChunksRef.current.push(event.data);
    }
  };

  mediaRecorder.onstart = () => {
    recordingStartTimeRef.current = Date.now();
    console.log("Recording started");
  };

  mediaRecorder.start();
  startSilenceDetection();
};


const stopRecording = () => {
  return new Promise((resolve) => {
    const mediaRecorder = mediaRecorderRef.current;
    if (!mediaRecorder) { resolve(null); return; }

    mediaRecorder.onstop = () => {
      const recordingBlob = new Blob(recordingChunksRef.current, { type: "video/webm" });
      const duration = recordingStartTimeRef.current
        ? (Date.now() - recordingStartTimeRef.current) / 1000
        : 0;

      console.log("Recording stopped");
      console.log("Recording duration:", duration);
      console.log("Recording size:", recordingBlob.size);

      recordingChunksRef.current = [];
      mediaRecorderRef.current = null;
      recordingStartTimeRef.current = null;

      if (audioContextRef.current) {
        audioContextRef.current.close().catch(() => {});
        audioContextRef.current = null;
      }
      analyserRef.current = null;
      speechDetectedRef.current = false;

      if (silenceTimerRef.current) {
        clearTimeout(silenceTimerRef.current);
        silenceTimerRef.current = null;
      }

      resolve({ blob: recordingBlob, duration });
    };

    if (mediaRecorder.state !== "inactive") mediaRecorder.stop();
  });
};

const uploadIntroductionRecording = async (recordingData) => {
  if (!recordingData || !interviewId) {
    return;
  }

  try {
    setQuestionError("");
    setLoadingQuestion(true);

    const token = localStorage.getItem("access_token");

    const formData = new FormData();

    formData.append(
      "recording",
      recordingData.blob,
      cameraEnabled ? "candidate-introduction.webm" : "candidate-introduction-audio.webm"
    );

    formData.append(
      "interview_id",
      String(interviewId)
    );

    formData.append(
      "duration",
      String(recordingData.duration)
    );

    const response = await fetch(
      `${API_URL}/api/recordings/introduction`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      }
    );

    const data = await response.json();

console.log("INTRODUCTION BACKEND RESPONSE:", data);

if (!response.ok) {
  throw new Error(
    data.processing_error ||
    data.message ||
    "Failed to process introduction recording"
  );
}

    console.log(
      "Introduction processed:",
      data
    );

    setQuestion(
      data.first_question.question
    );

    setCurrentQuestionId(
      data.first_question.id
    );

    setInterviewStage(
      data.interview.stage
    );

  } catch (err) {
    console.error(
      "INTRODUCTION UPLOAD ERROR:",
      err
    );

    setQuestionError(
      err.message ||
      "Failed to process your introduction."
    );
  } finally {
    setLoadingQuestion(false);
  }
};

const uploadAnswerRecording = async (blob, duration) => {
  try {
    const token = localStorage.getItem("access_token");

    const formData = new FormData();
    formData.append("interview_id", interviewId);
    formData.append("question_id", currentQuestionId);
    formData.append("duration", duration);
    formData.append("recording", blob, cameraEnabled ? "answer.webm" : "answer-audio.webm");

    setLoadingQuestion(true);

    const response = await fetch(
  `${API_URL}/api/recordings/upload`,
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
      throw new Error(data.message || "Failed to process answer");
    }

    console.log("Answer processed:", data);

    if (data.next_question) {
      setQuestion(data.next_question.question);
      setCurrentQuestionId(data.next_question.id);
      setInterviewStage("technical_interview");
    }
  } catch (error) {
    console.error("Answer upload error:", error);
    setError(error.message);
  } finally {
    setLoadingQuestion(false);
  }
};



  const startSilenceDetection = () => {
    if (!mediaRecorderRef.current || !streamRef.current) return;

    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (!AudioContext) {
      console.warn("AudioContext is not supported in this browser.");
      return;
    }

    const audioContext = new AudioContext();
    audioContextRef.current = audioContext;

    const analyser = audioContext.createAnalyser();
    analyser.fftSize = 2048;
    analyserRef.current = analyser;

    const source = audioContext.createMediaStreamSource(streamRef.current);
    source.connect(analyser);

    const dataArray = new Uint8Array(analyser.fftSize);
    let silenceStart = null;
    let speechDetected = false;

    const checkAudio = () => {
      if (!mediaRecorderRef.current) return;

      analyser.getByteTimeDomainData(dataArray);
      let sum = 0;
      for (let i = 0; i < dataArray.length; i++) {
        const normalized = (dataArray[i] - 128) / 128;
        sum += normalized * normalized;
      }

      const volume = Math.sqrt(sum / dataArray.length);
      const speechThreshold = 0.02;
      const silenceDuration = 2000;

      if (volume > speechThreshold) {
        speechDetected = true;
        silenceStart = null;
      } else if (speechDetected) {
        if (!silenceStart) silenceStart = Date.now();

        if (Date.now() - silenceStart >= silenceDuration) {
          console.log("2 seconds silence detected");

          stopRecording().then((recordingData) => {
            if (!recordingData) return;

            if (interviewStage === "candidate_introduction") {
              uploadIntroductionRecording(recordingData);
            } else {
              uploadAnswerRecording(recordingData.blob, recordingData.duration);
            }
          });
          return;
        }
      }

      requestAnimationFrame(checkAudio);
    };

    checkAudio();
  };

  const handleEndInterview = () => {
    stopMedia();
    setStarted(false);
    navigate("/dashboard");
  };

  
  useEffect(() => {
  if (!started || !question || loadingQuestion) {
  return;
}

  if (!question) {
    return;
  }

  if (!("speechSynthesis" in window)) {
    console.warn("Speech synthesis is not supported in this browser.");
    
    if (streamRef.current && !mediaRecorderRef.current) {
      startRecording();
    }

    return;
  }

  window.speechSynthesis.cancel();

  const utterance = new SpeechSynthesisUtterance(question);

utterance.lang = "en-IN";
utterance.rate = 0.9;
utterance.pitch = 1;
utterance.volume = 1;

  utterance.onstart = () => {
    console.log("AI started speaking");
    setAiSpeaking(true);
  };

  utterance.onend = () => {
    console.log("AI finished speaking");
    setAiSpeaking(false);

    if (streamRef.current && !mediaRecorderRef.current) {
      console.log("Starting user recording...");
      startRecording();
    }
  };

  utterance.onerror = (event) => {
    console.error("AI SPEECH ERROR:", event);
    setAiSpeaking(false);

    if (streamRef.current && !mediaRecorderRef.current) {
      startRecording();
    }
  };

  window.speechSynthesis.speak(utterance);

  return () => {
    window.speechSynthesis.cancel();
    setAiSpeaking(false);
  };
}, [started, interviewStage, question, loadingQuestion]);



useEffect(() => {
  const resumeId = localStorage.getItem("resume_id");
  const resumeFilename = localStorage.getItem("resume_filename");

  if (resumeId) {
    setSelectedResume(
      `${resumeId}|${resumeFilename || "Uploaded Resume"}`
    );
  }
}, []);

useEffect(() => {
  const attachCamera = async () => {
    const video = videoRef.current;
    const stream = streamRef.current;

    console.log("CAMERA DEBUG:", {
      cameraEnabled,
      started,
      videoExists: !!video,
      streamExists: !!stream,
      videoTracks: stream ? stream.getVideoTracks().length : 0,
      videoTrackState: stream?.getVideoTracks?.()[0]?.readyState,
    });

    if (!cameraEnabled || !started || !video || !stream) {
      return;
    }

    const videoTrack = stream.getVideoTracks()[0];

    if (!videoTrack) {
      console.error("NO VIDEO TRACK FOUND");
      return;
    }

    console.log("VIDEO TRACK:", {
      readyState: videoTrack.readyState,
      enabled: videoTrack.enabled,
      muted: videoTrack.muted,
    });

    video.srcObject = stream;

    video.onloadedmetadata = async () => {
      console.log("VIDEO METADATA LOADED");

      try {
        await video.play();
        console.log("CAMERA PREVIEW PLAYING");
      } catch (error) {
        console.error("CAMERA PLAY ERROR:", error);
      }
    };

    if (video.readyState >= 1) {
      try {
        await video.play();
        console.log("CAMERA PREVIEW PLAYING DIRECTLY");
      } catch (error) {
        console.error("CAMERA DIRECT PLAY ERROR:", error);
      }
    }
  };

  attachCamera();
}, [cameraEnabled, started]);

useEffect(() => {
  return () => {
    stopMedia();
  };
}, []);

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-950/90">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5">
          <div>
            <h1 className="text-xl font-bold tracking-tight">
              AI Video Interview
            </h1>

            <p className="text-xs text-slate-500">
              Realistic AI-powered interview practice
            </p>
          </div>

          {!started && (
            <button
              onClick={() => navigate("/dashboard")}
              className="rounded-xl border border-slate-700 px-4 py-2 text-sm font-medium text-slate-300 transition hover:border-slate-500 hover:bg-slate-900"
            >
              ← Dashboard
            </button>
          )}
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-10">
        {!started ? (
          <>
            {/* Intro */}
            <section className="mb-8">
              <p className="mb-2 text-sm font-medium text-green-400">
                Interview Workspace
              </p>

              <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
                Ready for your AI interview?
              </h2>

              <p className="mt-3 max-w-2xl text-slate-400">
                Your interview will use your resume and job profile to
                generate relevant questions and evaluate your answers
                dynamically.
              </p>
            </section>

            {/* Setup */}
            <section className="rounded-3xl border border-slate-800 bg-slate-900 p-8">
              <div className="grid gap-8 md:grid-cols-2">
                {/* Interview information */}
                <div>
                  <h3 className="text-xl font-semibold">
                    Interview Overview
                  </h3>

                  <div className="mt-6 space-y-4">
                    <div className="rounded-2xl border border-slate-800 bg-slate-950 p-4">
                      <p className="text-sm text-slate-500">
                        Interview Type
                      </p>

                      <p className="mt-1 font-medium">
                        AI Video Interview
                      </p>
                    </div>

                    <div className="rounded-2xl border border-slate-800 bg-slate-950 p-4">
                      <p className="text-sm text-slate-500">
                        Question Mode
                      </p>

                      <p className="mt-1 font-medium">
                        Dynamic & Adaptive
                      </p>
                    </div>

                    <div className="rounded-2xl border border-slate-800 bg-slate-950 p-4">
                      <p className="text-sm text-slate-500">
                        Answer Evaluation
                      </p>

                      <p className="mt-1 font-medium">
                        AI-powered
                      </p>
                    </div>
                  </div>
                </div>

                {/* Requirements */}
                {/* Interview Setup */}
<div>
  <h3 className="text-xl font-semibold">
    Before you start
  </h3>

  <div className="mt-6 space-y-4">

    {/* Resume */}
    <div className="rounded-2xl border border-slate-800 bg-slate-950 p-4">
      <div className="mb-3 flex items-center justify-between">
        <div>
          <p className="text-sm text-slate-500">
            Resume
          </p>

          <p className="mt-1 font-medium text-slate-200">
            Select the resume for this interview
          </p>
        </div>

        <span
          className={
            selectedResume
              ? "text-sm text-green-400"
              : "text-sm text-slate-500"
          }
        >
          {selectedResume ? "Ready" : "Required"}
        </span>
      </div>

      <select
        value={selectedResume}
        onChange={(e) => setSelectedResume(e.target.value)}
        className="w-full rounded-xl border border-slate-700 bg-slate-900 px-4 py-3 text-sm text-slate-200 outline-none transition focus:border-green-400"
      >
        <option value="">
          Select your resume
        </option>

        {selectedResume && (
          <option value={selectedResume}>
            {selectedResume.split("|")[1]}
          </option>
        )}
      </select>
    </div>

    {/* Camera Preference */}
    <div className="rounded-2xl border border-slate-800 bg-slate-950 p-4">
      <div className="mb-4">
        <p className="text-sm text-slate-500">Camera Preference</p>
        <p className="mt-1 font-medium text-slate-200">Choose whether you want to use your camera during the interview.</p>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <button type="button" onClick={() => { setCameraPreference(true); setMediaError(""); }} className={`rounded-xl px-4 py-3 text-sm font-semibold transition ${cameraPreference ? "bg-green-500 text-slate-950" : "border border-slate-700 bg-slate-900 text-slate-300 hover:border-slate-600"}`}>Camera ON</button>
        <button type="button" onClick={() => { setCameraPreference(false); setMediaError(""); }} className={`rounded-xl px-4 py-3 text-sm font-semibold transition ${!cameraPreference ? "bg-green-500 text-slate-950" : "border border-slate-700 bg-slate-900 text-slate-300 hover:border-slate-600"}`}>Camera OFF</button>
      </div>
      <p className="mt-3 text-xs text-slate-500">Camera OFF will use microphone-only interview mode.</p>
    </div>

    {/* Camera */}
<div className="rounded-2xl border border-slate-800 bg-slate-950 p-4">
  <div className="mb-4 flex items-center justify-between">
    <div>
      <p className="text-sm text-slate-500">
        Camera
      </p>

      <p className="mt-1 font-medium text-slate-200">
        {cameraEnabled
          ? "Camera is ready"
          : "Camera is not connected"}
      </p>
    </div>

    <span
      className={
        cameraEnabled
          ? "rounded-full bg-green-500/10 px-3 py-1 text-xs text-green-400"
          : "rounded-full bg-slate-800 px-3 py-1 text-xs text-slate-400"
      }
    >
      {cameraEnabled ? "ON" : "OFF"}
    </span>
  </div>

  {cameraEnabled && (
    <div className="overflow-hidden rounded-xl border border-slate-800 bg-black">
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        className="aspect-video w-full object-cover"
      />

      <div className="border-t border-slate-800 px-3 py-2 text-xs text-slate-400">
        Live camera preview
      </div>
    </div>
  )}
</div>
    

    {/* Microphone */}
    <div className="rounded-2xl border border-slate-800 bg-slate-950 p-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-slate-500">
            Microphone
          </p>

          <p className="mt-1 font-medium text-slate-200">
            {microphoneEnabled
              ? "Microphone is ready"
              : "Microphone is not connected"}
          </p>
        </div>

        <span
          className={
            microphoneEnabled
              ? "rounded-full bg-green-500/10 px-3 py-1 text-xs text-green-400"
              : "rounded-full bg-slate-800 px-3 py-1 text-xs text-slate-400"
          }
        >
          {microphoneEnabled ? "ON" : "OFF"}
        </span>
      </div>
    </div>

    {/* Enable Devices */}
    {!cameraEnabled || !microphoneEnabled ? (
      <button
        type="button"
        onClick={enableCameraAndMicrophone}
        className="w-full rounded-xl border border-green-500/30 bg-green-500/10 px-4 py-3 text-sm font-semibold text-green-400 transition hover:bg-green-500/20"
      >
        {cameraPreference ? "Enable Camera & Microphone" : "Enable Microphone Only"}
      </button>
    ) : (
      <div className="rounded-xl border border-green-500/20 bg-green-500/5 px-4 py-3 text-sm text-green-400">
        ✓ {cameraPreference ? "Camera and microphone are ready" : "Microphone is ready — camera is off"}
      </div>
    )}

    {/* Media Error */}
    {mediaError && (
      <div className="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
        {mediaError}
      </div>
    )}

  </div>
</div>
              </div>

              {/* Error */}
              {error && (
                <div className="mt-6 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
                  {error}
                </div>
              )}

              {/* Start */}
              <div className="mt-8 border-t border-slate-800 pt-8">
                <button
  onClick={startInterview}
  disabled={
    !selectedResume ||
    !microphoneEnabled ||
    loadingQuestion
  }
  className={`w-full rounded-2xl px-6 py-4 text-sm font-bold transition ${
    selectedResume &&
    microphoneEnabled &&
    !loadingQuestion
      ? "bg-green-500 text-slate-950 hover:bg-green-400"
      : "cursor-not-allowed bg-slate-800 text-slate-500"
  }`}
>
  {loadingQuestion
    ? "Starting Interview..."
    : "Start Interview →"}
</button>
              </div>
            </section>
          </>
        ) : (
          /* Active Interview */
         <section>
  {/* Interview Status */}
  <div className="mb-6 flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
    <div>
      <p className="text-sm font-medium text-green-400">
        Interview in progress
      </p>

      <h2 className="mt-1 text-2xl font-bold">
        {cameraEnabled ? "Camera & microphone are active" : "Microphone interview mode is active"}
      </h2>
    </div>

    <div className="flex items-center gap-2 rounded-full border border-green-500/30 bg-green-500/10 px-4 py-2 text-sm text-green-400">
      <span className="h-2 w-2 rounded-full bg-green-400" />
      Live
    </div>
  </div>

  {/* Candidate Media */}
  {cameraEnabled ? (
    <div className="relative overflow-hidden rounded-3xl border border-slate-800 bg-black shadow-2xl">
      <video ref={videoRef} autoPlay playsInline muted className="aspect-video w-full object-cover" />
      <div className="absolute bottom-5 left-5 rounded-xl border border-white/10 bg-black/60 px-4 py-2 text-sm text-slate-200 backdrop-blur">Candidate Camera</div>
    </div>
  ) : (
    <div className="flex aspect-video items-center justify-center rounded-3xl border border-slate-800 bg-slate-900 shadow-2xl">
      <div className="text-center">
        <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-slate-800 text-2xl">🎙️</div>
        <p className="font-semibold text-slate-200">Camera is Off</p>
        <p className="mt-1 text-sm text-slate-500">Your microphone is active. The AI interview will continue normally.</p>
      </div>
    </div>
  )}

  {/* AI Interviewer */}
  <div className="mt-6 rounded-3xl border border-slate-800 bg-slate-900 p-6">
    <div className="mb-4 flex items-center justify-between">
      <div>
        <p className="text-sm font-medium text-green-400">
  AI Interviewer
</p>

{aiSpeaking && (
  <p className="mt-1 text-xs text-green-400">
    ● AI is speaking...
  </p>
)}

        <h3 className="mt-1 text-lg font-semibold">
          {interviewStage === "candidate_introduction"
            ? "Introduction"
            : "Interview Question"}
        </h3>
      </div>

      <span className="rounded-full border border-slate-700 bg-slate-950 px-3 py-1 text-xs text-slate-400">
        {interviewStage === "candidate_introduction"
          ? "Getting Started"
          : "Technical"}
      </span>
    </div>

    {/* Loading */}
    {loadingQuestion ? (
      <div className="flex items-center gap-3 text-slate-400">
        <div className="h-4 w-4 animate-spin rounded-full border-2 border-slate-600 border-t-green-400" />

        <span>
          AI is preparing your interview...
        </span>
      </div>
    ) : question ? (
      <div className="rounded-2xl border border-slate-800 bg-slate-950 p-5">
        <p className="text-lg leading-8 text-slate-200">
          {question}
        </p>
      </div>
    ) : (
      <p className="text-slate-400">
        Waiting for the AI interviewer...
      </p>
    )}

    {/* Question Error */}
    {questionError && (
      <div className="mt-4 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
        {questionError}
      </div>
    )}
  </div>

  {/* Interview Controls */}
  <div className="mt-6 flex justify-center">
    <button
      onClick={handleEndInterview}
      className="rounded-2xl border border-red-500/40 bg-red-500/10 px-8 py-4 text-sm font-bold text-red-300 transition hover:bg-red-500/20"
    >
      End Interview
    </button>
  </div>
</section>
        )}
      </main>
    </div>
  );
}

export default VideoInterview;
