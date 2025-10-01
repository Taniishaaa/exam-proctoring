import { useState } from "react";

export default function Teacher() {
  const [time, setTime] = useState("");
  const [status, setStatus] = useState("");

  const handleSubmitTime = async () => {
    const res = await fetch("http://localhost:5000/api/teacher/input-time", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ time }),
    });
    const data = await res.json();
    setStatus(data.msg || data.error);
  };

  const handleReleaseResults = async () => {
    const res = await fetch("http://localhost:5000/api/teacher/release-results", {
      method: "POST",
    });
    const data = await res.json();
    setStatus(data.msg || data.error);
  };

  return (
    <div style={{ padding: "20px", fontFamily: "Arial" }}>
      <h2>Teacher Dashboard</h2>
      <div>
        <input
          type="text"
          placeholder="Enter time (HH-MM-SS)"
          value={time}
          onChange={(e) => setTime(e.target.value)}
          style={{ marginRight: "10px" }}
        />
        <button onClick={handleSubmitTime}>Submit Time</button>
      </div>
      <div style={{ marginTop: "20px" }}>
        <button onClick={handleReleaseResults}>Release Results</button>
      </div>
      <p>{status}</p>
    </div>
  );
}
