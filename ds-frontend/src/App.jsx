// src/App.jsx
import { useState } from "react";
import { Routes, Route, useNavigate } from "react-router-dom";
import Admin from "./pages/Adminpanel";
import Teacher from "./pages/Teacher"; // ✅ add this
import Client from "./pages/Client";
import Student from "./pages/Student"; // ✅ import Student

function Landing({ studentCount, setStudentCount }) {
  const navigate = useNavigate();

  const handleRegisterTeacher = () => {
    // Either open in new tab
    window.open("/teacher", "_blank");
    // Or just navigate in same tab:
    // navigate("/teacher");
  };

  const handleRegisterClient = () => {
    // Either open in new tab
    window.open("/client", "_blank");
    // Or just navigate in same tab:
    // navigate("/teacher");
  };

  const handleRegisterStudent = () => {
    const nextRoll = studentCount + 1;
    setStudentCount(nextRoll);
    window.open(`/student/${nextRoll}`, "_blank"); // Student.jsx will come later
  };

  const handleAdminPanel = () => {
    window.open("/admin", "_blank");
  };

  return (
    <div style={{
      display: "flex", flexDirection: "column", justifyContent: "center",
      alignItems: "center", height: "100vh", backgroundColor: "#f0f0f0",
      fontFamily: "Arial, sans-serif"
    }}>
      <h1 style={{ fontSize: "28px", fontWeight: "bold", marginBottom: "20px" }}>
        Distributed Systems Exam Portal
      </h1>
      <div style={{ display: "flex", flexDirection: "column", gap: "12px", width: "220px" }}>
        <button
          onClick={handleRegisterTeacher}
          style={{ padding: "10px", backgroundColor: "#007bff", color: "white", border: "none", borderRadius: "6px", cursor: "pointer" }}
        >
          Register as Teacher
        </button>

        <button
          onClick={handleRegisterStudent}
          style={{ padding: "10px", backgroundColor: "#28a745", color: "white", border: "none", borderRadius: "6px", cursor: "pointer" }}
        >
          Register as Student
        </button>
        <button
          onClick={handleAdminPanel}
          style={{ padding: "10px", backgroundColor: "#343a40", color: "white", border: "none", borderRadius: "6px", cursor: "pointer" }}
        >
          Admin Panel
        </button>
      </div>
    </div>
  );
}

export default function App() {
  const [studentCount, setStudentCount] = useState(0);

  return (
    <Routes>
      <Route path="/" element={<Landing studentCount={studentCount} setStudentCount={setStudentCount} />} />
      <Route path="/admin" element={<Admin />} />
      <Route path="/teacher" element={<Teacher />} />
      <Route path="/client" element={<Client />} />
      <Route path="/student/:roll" element={<Student />} />
      {/* Later you’ll add <Route path="/student/:roll" element={<Student />} /> */}
    </Routes>
  );
}
