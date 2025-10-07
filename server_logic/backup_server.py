# backup_server.py (updated with info-level logging, drop-in ready)
import datetime
import threading
import xmlrpc.client
import http.client
from xmlrpc.server import SimpleXMLRPCServer
from socketserver import ThreadingMixIn
import logging

# ---------------- CONFIG ----------------
BACKUP_HOST = "127.0.0.1"
BACKUP_PORT = 9003
MAIN_SERVER_URL = "http://127.0.0.1:9000/"
RPC_TIMEOUT = 5.0

# ---------------- LOGGING ----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | BACKUP | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("backup")

# ---------------- HELPER ----------------
class TimeoutTransport(xmlrpc.client.Transport):
    def __init__(self, timeout=RPC_TIMEOUT):
        super().__init__()
        self._timeout = timeout
    def make_connection(self, host):
        return http.client.HTTPConnection(host, timeout=self._timeout)

def new_proxy(url: str, timeout=RPC_TIMEOUT):
    return xmlrpc.client.ServerProxy(
        url, allow_none=True, transport=TimeoutTransport(timeout)
    )

main_proxy = new_proxy(MAIN_SERVER_URL)

class ThreadingXMLRPCServer(ThreadingMixIn, SimpleXMLRPCServer):
    daemon_threads = True

# ---------------- STATE ----------------
student_flags = {}               # cheating flags
mcq_lock = threading.Lock()
mcq_submitted_students = set()
mcq_final_scores = {}

# Same MCQ questions as in main server
MCQ_QUESTIONS = {
    1: {"answer": 2},  # Berkeley
    2: {"answer": 2},  # Ricart-Agrawala
    3: {"answer": 2},  # openpyxl
    4: {"answer": 3},  # 300s
    5: {"answer": 2},  # XML-RPC
    6: {"answer": 2},  # 80%
    7: {"answer": 4},  # 0%
    8: {"answer": 3},  # 100
    9: {"answer": 3},  # Server
    10: {"answer": 2}, # heap
}

# ---------------- BACKUP LOGIC ----------------
def submit_mcq_final(roll: str, answers: dict):
    """
    Called by main when >3 students submit at the same time.
    Backup grades using forwarded answers and pushes result back to main.
    """
    roll = str(roll)
    logger.info(f"[Backup] Received redirected submit for roll={roll}")

    with mcq_lock:
        if roll in mcq_submitted_students:
            logger.info(f"[Backup] roll={roll} already processed here; ignoring.")
            return True

        raw = 0
        # Convert string keys from XML-RPC back to int for grading
        for qnum_str, given in answers.items():
            qnum = int(qnum_str)
            if qnum in MCQ_QUESTIONS and int(given) == MCQ_QUESTIONS[qnum]["answer"]:
                raw += 10

        # Apply cheating penalties
        flags = student_flags.get(roll, 0)
        if flags >= 2:
            final = 0
        elif flags == 1:
            final = int(raw * 0.8)
        else:
            final = raw

        mcq_final_scores[roll] = final
        mcq_submitted_students.add(roll)

    logger.info(f"[Backup] Finalized roll={roll} final={final}")

    try:
        main_proxy.accept_backup_result(roll, int(final))
        logger.info(f"[Backup] Sent result back to main for roll={roll}")
    except Exception as e:
        logger.error(f"[Backup] ERROR pushing to main: {e}")

    return True

# ---------------- SERVER ----------------
def run_server():
    srv = ThreadingXMLRPCServer((BACKUP_HOST, BACKUP_PORT),
                                allow_none=True, logRequests=False)
    srv.register_function(submit_mcq_final, "submit_mcq_final")
    logger.info(f"[Backup] Running on {BACKUP_HOST}:{BACKUP_PORT} ...")
    srv.serve_forever()

if __name__ == "__main__":
    run_server()
