#  Distributed Systems — Online Exam Proctoring Portal

This project is a **Distributed Systems-based Online Examination Portal** that demonstrates key distributed concepts such as **clock synchronization**, **mutual exclusion**, **replication**, **consistency control**, and **fault tolerance** — all within a unified **Flask web application**.

---

## Features Overview

### 1. Berkeley Clock Synchronization
- Admin initiates time synchronization.
- Teacher and all 5 Students submit local times.
- The server runs the **Berkeley algorithm** to compute the average offset and synchronize all participants.
- Displays adjusted times on Admin panel.

---

### 2. Exam Conduction Module
- Admin starts the exam.
- Students receive a **10-question MCQ test**, each with a **30-second timer**.
- Auto-submission when time expires or on manual submission.
- Results are recorded in `results.xlsx`.

---

### 3. Cheating Detection Simulation
- The server randomly flags students during the exam.
- **1 Warning** → 50% marks retained.  
- **2 Warnings** → Exam terminated, marks = 0.
- Live cheating monitor visible to Admin.

---

### 4. ISA Marks Entry — Ricart–Agrawala Mutual Exclusion
- Once exam ends, Admin triggers the **ISA phase**.
- Students are prompted to enter ISA marks.
- **Ricart–Agrawala algorithm** ensures that only one student accesses the critical section at a time.
- Deferred OKs and queue ordering handle simultaneous requests safely.
- Avoids deadlocks between manual and auto submissions.

---

### 5. Replication and Chunking
- Exam results are **split into 2 chunks**, each having **3 replicas**.
- Metadata (paths, replicas) stored in `replication_metadata.json`.
- Ensures **fault tolerance** and **data availability**.

---

### 6. Consistency Demo — Read/Write Locks
- Admin starts the **Consistency Demo**.
- All students are prompted with:
  - 🔹 Read Marks
  - 🔹 Write Marks
  - 🔹 Exit Demo
- Demonstrates **read-write lock synchronization**:
  - Multiple readers allowed concurrently.
  - Writer requires exclusive access.
- Updates propagate to all replicas and `results.xlsx` for **strong consistency**.
- Waiting students see a “Please Wait” screen until locks are released.

---

### 7. Backup Server Handling
- Main server handles up to 3 concurrent submissions.
- Overflow requests are automatically redirected to the **Backup Server**.
- Logs and load stats visible on Admin dashboard.

---

## Tech Stack

| Component | Technology |
|------------|-------------|
| Backend | Flask (Python) |
| Frontend | HTML, CSS, JS |
| Database | OpenPyXL (Excel-based) |
| Data Storage | Replicated `.xlsx` files |
| Algorithms | Berkeley Sync, Ricart–Agrawala, Read/Write Locks |
| Architecture | Multi-Process Distributed Simulation |

---

## System Roles

| Role | Description |
|------|-------------|
| **Admin** | Controls synchronization, starts exam, initiates ISA & consistency demos |
| **Teacher** | Observes synced times and results |
| **Student (1–5)** | Takes exam, enters ISA, participates in consistency demo |
| **Backup Server** | Handles overflow auto-submissions |

---

## 🖥️ How to Run the Project

### Prerequisites
- Python 3.10+
- Install dependencies:
  ```bash
  pip install flask openpyxl
  ```

---

### Steps to Run
2. **Run Flask server:**
   ```bash
   python app.py
   ```

3. **Open the web app:**
   - Admin Panel → http://127.0.0.1:5000/admin  
   - Teacher Panel → http://127.0.0.1:5000/teacher  
   - Students →  
     - http://127.0.0.1:5000/student/1  
     - http://127.0.0.1:5000/student/2  
     - http://127.0.0.1:5000/student/3  
     - http://127.0.0.1:5000/student/4  
     - http://127.0.0.1:5000/student/5

4. **Workflow**
   - Start with **Time Sync** (Admin panel).
   - Then **Start Exam**.
   - After exam → **Start ISA Phase**.
   - Once ISA marks are done → **Create Replicas**.
   - Then **Start Consistency Demo**.

---

## 🧠 Use Cases

| Concept | Demonstrated By |
|----------|------------------|
| **Clock Synchronization** | Berkeley Algorithm |
| **Distributed Coordination** | Teacher–Students–Server communication |
| **Mutual Exclusion** | Ricart–Agrawala algorithm |
| **Replication** | Chunk-based multi-replica architecture |
| **Consistency Models** | Read/Write locks with demo UI |
| **Fault Tolerance** | Backup server for overflow |
| **Real-time Monitoring** | Admin panel with live logs & load stats |

---


## 🧩 Future Enhancements
- Convert multi-tab simulation into **Dockerized microservices**.
- Use **PostgreSQL** or **MongoDB** for persistent storage.
- Add **real-time websockets** for instant lock notifications.

---

