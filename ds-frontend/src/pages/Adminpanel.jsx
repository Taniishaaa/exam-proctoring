// src/pages/AdminPanel.jsx
import { useEffect, useState, useRef } from "react";

export default function AdminPanel() {
  const [logs, setLogs] = useState([]);
  const logEndRef = useRef(null);

  // Admin-specific states
  const [time, setTime] = useState("");
  const [status, setStatus] = useState("");

  // Auto scroll to bottom whenever logs update
  useEffect(() => {
    if (logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [logs]);

  // Connect to SSE for live logs
  useEffect(() => {
    const evtSource = new EventSource("http://localhost:5000/api/stream-logs");

    evtSource.onmessage = (e) => {
      setLogs((prev) => [...prev, e.data].slice(-500)); // keep last 500 lines
    };

    evtSource.onerror = () => {
      console.error("SSE connection lost.");
      evtSource.close();
    };

    return () => evtSource.close();
  }, []);

  // Handlers for admin time input
const handleSubmitTime = async () => {
  try {
    const res = await fetch("http://localhost:5000/api/server/input-time", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ time }),
    });
    const data = await res.json();
    setStatus(data.msg || data.error);
  } catch (err) {
    setStatus("❌ Failed to submit time");
    console.error(err);
  }
};


// Inside AdminPanel.jsx

const handleTimeSync = async () => {
  try {
    const res = await fetch("http://localhost:5000/api/time-sync", {
      method: "POST",
    });
    const data = await res.json();
    setStatus(data.msg || data.error);
  } catch (err) {
    setStatus("❌ Failed to start time sync");
    console.error(err);
  }
};


const handleStartExam = async () => {
  try {
    const res = await fetch("http://localhost:5000/api/start-exam", {
      method: "POST",
    });
    const data = await res.json();
    setStatus(data.msg || data.error);
  } catch (err) {
    setStatus("❌ Failed to start exam");
    console.error(err);
  }
};

const handleFinishExam = async () => {
  try {
    const res = await fetch("http://localhost:5000/api/finish-exam", {
      method: "POST",
    });
    const data = await res.json();
    setStatus(data.msg || data.error);
  } catch (err) {
    setStatus("❌ Failed to finish exam");
    console.error(err);
  }
};



  return (
    <div style={{ padding: "20px", fontFamily: "Arial, sans-serif" }}>
      <h2>Admin Panel</h2>

      {/* Control Buttons */}
      <div style={{ marginBottom: "20px", display: "flex", flexWrap: "wrap", gap: "10px" }}>
        <button>Register Students</button>
        <button onClick={handleTimeSync}>Start Time Sync</button>
        <button onClick={handleStartExam}>Start Exam</button>
        <button onClick={handleFinishExam}>Finish Exam</button>
        <button>Start ISA</button>
        <button>Create Replication</button>
        <button>Consistency Demo</button>
        <button style={{ background: "red", color: "white" }}>Exit</button>
      </div>

      {/* Time Input Feature for Admin */}
      <div style={{ marginBottom: "20px" }}>
        <h3>Set Exam Time</h3>
        <input
          type="text"
          placeholder="Enter time (HH:MM:SS)"
          value={time}
          onChange={(e) => setTime(e.target.value)}
          style={{ marginRight: "10px" }}
        />
        <button onClick={handleSubmitTime}>Submit Time</button>
        <p>{status}</p>
      </div>

      {/* Terminal-style Log Viewer */}
      <h3>Server Logs</h3>
      <div
        style={{
          background: "#000",
          color: "#0f0",
          padding: "10px",
          height: "400px",
          overflowY: "auto",
          borderRadius: "6px",
          fontFamily: "monospace",
          fontSize: "14px",
          whiteSpace: "pre",
        }}
      >
        {logs.map((line, i) => (
          <div key={i}>{line}</div>
        ))}
        <div ref={logEndRef} />
      </div>
    </div>
  );
}
