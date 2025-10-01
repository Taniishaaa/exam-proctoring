import { useParams } from "react-router-dom";
import { useState, useEffect } from "react";

export default function Student() {
  const { roll } = useParams();
  const [phase, setPhase] = useState("time");
  const [time, setTime] = useState("");
  const [examStatus, setExamStatus] = useState("waiting"); // waiting | started | finished | terminated
  const [qnum, setQnum] = useState(1);
  const [question, setQuestion] = useState(null);
  const [answers, setAnswers] = useState({});
  const [status, setStatus] = useState("");

  // --- Handle student time input ---
  const handleSubmitTime = async () => {
  try {
    // Step 1: submit student time
    const res = await fetch("http://localhost:5000/api/student/input-time", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ roll, time }),
    });
    const data = await res.json();

    if (data.ok) {
      setStatus(data.msg);
      setPhase("waiting"); // ✅ Move to waiting room

      // Step 2: auto-register student
      try {
        const regRes = await fetch("http://localhost:5000/api/register-student", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ roll }),
        });
        const regData = await regRes.json();
        if (regData.ok) {
          console.log(`Student ${roll} registered successfully`);
        } else {
          console.warn("Student registration failed:", regData.error);
        }
      } catch (err) {
        console.error("Failed to register student", err);
      }

    } else {
      setStatus(data.error);
    }
  } catch (err) {
    setStatus("❌ Failed to submit time");
  }
};

  

  // --- Poll exam status every 3s ---
  useEffect(() => {
    if (phase === "time") return; // start polling only after submitting time
    let mounted = true;

    const fetchStatus = async () => {
      try {
        const res = await fetch(
          `http://localhost:5000/api/exam-status/${roll}`
        );
        const data = await res.json();
        console.log("[Student] exam-status:", data);
        if (!mounted) return;
        if (data.ok) {
          if (data.terminated) {
            setExamStatus("terminated");
          } else if (data.finished) {
            setExamStatus("finished");
          } else if (data.started) {
            setExamStatus("started");
          } else {
            setExamStatus("waiting");
          }
          if (data.warnings > 0) {
            setStatus(`⚠️ Cheating warning(s): ${data.warnings}`);
          }
        } else {
          console.warn("[Student] exam-status error:", data.error);
        }
      } catch (err) {
        console.error("Failed to get exam status", err);
      }
    };

    fetchStatus(); // immediate check
    const interval = setInterval(fetchStatus, 15000);

    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, [phase, roll]);

  // Fetch questions only if exam started
  useEffect(() => {
    if (examStatus !== "started") return;
    const fetchQuestion = async () => {
      try {
        const res = await fetch(
          `http://localhost:5000/api/get-question/${roll}/${qnum}`
        );
        const data = await res.json();
        if (data.ok) setQuestion(data.q);
        else setStatus(data.error || "No question found");
      } catch (err) {
        setStatus("❌ Failed to load question");
      }
    };
    fetchQuestion();
  }, [qnum, roll, examStatus]);

  const handleAnswer = async (choice) => {
    try {
      const res = await fetch("http://localhost:5000/api/submit-answer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ roll, qnum, choice }),
      });
      const data = await res.json();
      if (data.ok) {
        setAnswers((prev) => ({ ...prev, [qnum]: choice }));
        setStatus(`✅ Answer saved for Q${qnum}`);
      } else {
        setStatus(data.error);
      }
    } catch (err) {
      setStatus("❌ Failed to submit answer");
    }
  };

  const handleFinalSubmit = async () => {
    try {
      const res = await fetch("http://localhost:5000/api/submit-final", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ roll }),
      });
      const data = await res.json();
      setStatus(data.ok ? "🎉 Exam submitted successfully!" : data.error);
    } catch (err) {
      setStatus("❌ Failed to finalize exam");
    }
  };

  // --- UI Render ---
  if (phase === "time") {
    return (
      <div style={{ padding: "20px" }}>
        <h2>Student Registration (Roll {roll})</h2>
        <input
          type="text"
          placeholder="Enter time (HH-MM-SS)"
          value={time}
          onChange={(e) => setTime(e.target.value)}
          style={{ marginRight: "10px" }}
        />
        <button onClick={handleSubmitTime}>Submit Time</button>
        <p>{status}</p>
      </div>
    );
  }

  if (examStatus === "waiting") {
    return <h2>⏳ Waiting for admin to start the exam...</h2>;
  }

  if (examStatus === "terminated") {
    return (
      <div style={{ padding: "20px", color: "red" }}>
        <h2>❌ Exam terminated due to cheating.</h2>
        <p>{status}</p>
      </div>
    );
  }

  if (examStatus === "finished") {
    return <h2>✅ Exam finished. Please wait for results.</h2>;
  }

  // examStatus === "started"
  return (
    <div style={{ padding: "20px", fontFamily: "Arial" }}>
      <h2>Student Exam Window (Roll {roll})</h2>
      {question ? (
        <div>
          <h3>
            Q{question.qnum}: {question.q}
          </h3>
          <ul>
            {question.options.map((opt, i) => (
              <li key={i}>
                <button
                  style={{
                    margin: "5px",
                    padding: "8px",
                    borderRadius: "6px",
                    background:
                      answers[qnum] === i + 1 ? "#28a745" : "#f8f9fa",
                  }}
                  onClick={() => handleAnswer(i + 1)}
                >
                  {i + 1}. {opt}
                </button>
              </li>
            ))}
          </ul>
          <div style={{ marginTop: "10px" }}>
            <button
              onClick={() => setQnum(Math.max(1, qnum - 1))}
              disabled={qnum === 1}
            >
              Previous
            </button>
            <button
              onClick={() => setQnum(qnum + 1)}
              style={{ marginLeft: "10px" }}
            >
              Next
            </button>
          </div>
          <button
            style={{
              marginTop: "20px",
              background: "red",
              color: "white",
              padding: "10px",
            }}
            onClick={handleFinalSubmit}
          >
            Submit Final
          </button>
        </div>
      ) : (
        <p>{status || "⏳ Loading question..."}</p>
      )}
      <p style={{ marginTop: "10px", color: "#555" }}>{status}</p>
    </div>
  );
}
