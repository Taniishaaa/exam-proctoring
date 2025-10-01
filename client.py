# client.py (updated)
import xmlrpc.client
import random
import time
import datetime
from xmlrpc.server import SimpleXMLRPCServer
import threading
from socketserver import ThreadingMixIn
import logging

# ---------------- CONFIG ----------------
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 9000
TEACHER_HOST = "127.0.0.1"
TEACHER_PORT = 9001

# ---------------- LOGGING ----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | CLIENT | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("client")

class ThreadingXMLRPCServer(ThreadingMixIn, SimpleXMLRPCServer):
    daemon_threads = True

roll_numbers = ["1", "2", "3", "4", "5"]

server_proxy = xmlrpc.client.ServerProxy(f"http://{SERVER_HOST}:{SERVER_PORT}/", allow_none=True)
teacher_proxy = xmlrpc.client.ServerProxy(f"http://{TEACHER_HOST}:{TEACHER_PORT}/", allow_none=True)

local_time = None
exam_start_event = threading.Event()

# ---------------- TIME SYNC ----------------
def input_time():
    global local_time
    user_input = input("[Client] (Step 1) Enter current local client time (HH-MM-SS): ")
    local_time = datetime.datetime.strptime(user_input, "%H-%M-%S")
    logger.info(f"[Client] Local time set to {local_time.strftime('%H-%M-%S')}")
    return True

def calculate_cv(server_time_str):
    global local_time
    server_time = datetime.datetime.strptime(server_time_str, "%H-%M-%S")
    cv = (local_time - server_time).total_seconds()
    logger.info(f"[Client] Calculated CV = {cv} seconds; sending to Server")
    try:
        server_proxy.receive_cv("Client", cv)
    except Exception as e:
        logger.warning(f"[Client] Cannot send CV: {e}")
    return True

def apply_adjustment(adj):
    global local_time
    local_time = local_time + datetime.timedelta(seconds=adj)
    logger.info(f"[Client] Adjusted local time: {local_time.strftime('%H-%M-%S')}")
    logger.info(f"[Client] Final synchronized time: {local_time.strftime('%H-%M-%S')}")
    return True

# ---------------- EXAM ----------------
def start_exam():
    logger.info("[Client] Received exam start signal from Server.")
    exam_start_event.set()
    return True

def phase_complete(phase_name: str):
    logger.info("\n" + "="*40)
    logger.info(f"PHASE COMPLETE: {phase_name}")
    logger.info("="*40 + "\n")
    return True

def run_client_server():
    server = ThreadingXMLRPCServer(("0.0.0.0", 9002), allow_none=True, logRequests=False)
    server.register_function(input_time, "input_time")
    server.register_function(calculate_cv, "calculate_cv")
    server.register_function(apply_adjustment, "apply_adjustment")
    server.register_function(start_exam, "start_exam")
    server.register_function(phase_complete, "phase_complete")
    logger.info("[Client] XML-RPC server running on port 9002...")
    server.serve_forever()

def exam_timer():
    exam_duration = 30  # seconds
    interval = 10       # seconds
    start_time = time.time()
    active_rolls = roll_numbers.copy()

    while time.time() - start_time < exam_duration and active_rolls:
        roll = random.choice(active_rolls)
        response = None
        try:
            response = server_proxy.cheating_detection(roll)
        except Exception as e:
            logger.warning(f"[Client] cheating_detection RPC failed: {e}")

        if response is None:
            try:
                active_rolls.remove(roll)
            except Exception:
                pass
            time.sleep(interval)
            continue

        logger.info(f"[Client] Reporting cheating attempt by roll no: {roll}")
        logger.info(f"[Client] Server response: {response}")
        time.sleep(interval)

    logger.info("[Client] Exam finished. Notifying server for exam completion...")
    try:
        server_proxy.exam_completed()
    except Exception as e:
        logger.warning(f"[Client] exam_completed RPC failed: {e}")

# ---------------- MAIN ----------------
if __name__ == "__main__":
    t = threading.Thread(target=run_client_server, daemon=True)
    t.start()

    try:
        server_proxy.input_time()
    except Exception:
        pass
    try:
        teacher_proxy.input_time()
    except Exception:
        pass
    input_time()

    try:
        server_proxy.start_synchronization()
    except Exception as e:
        logger.warning(f"[Client] starting synchronization failed: {e}")

    logger.info("[Client] Waiting for exam start signal from Server...")
    exam_start_event.wait()
    exam_timer()
