"""
Flask backend wrapper for your DS project.

- Starts a lightweight XML-RPC server (registers server's functions) *without* the blocking admin input loop.
- Exposes HTTP endpoints the React admin panel can call:
    /api/time-sync        -> triggers Berkeley sync
    /api/start-exam       -> triggers exam start (teacher RPCs + start_mcq)
    /api/start-mcq        -> alias to start_mcq
    /api/get-registry     -> returns registered students
    /api/register-student -> POST roll, url -> calls server.register_student
    /api/cheat/<roll>     -> simulate cheating detection for roll
    /api/logs             -> returns last N lines of server log file (if present)
    /api/stream-logs      -> live SSE log stream for React AdminPanel
"""

from flask import Flask, jsonify, request, Response
import threading
import logging
import random
import time
import traceback
import queue
import datetime
from flask_cors import CORS  # ✅ keep CORS import here
import xmlrpc.client

# Import your existing server module
import server as ds_server
import teacher as ds_teacher

from xmlrpc.server import SimpleXMLRPCServer
from socketserver import ThreadingMixIn


# ----------------- Global log queue + SSE handler -----------------
log_queue = queue.Queue()

class SSELogHandler(logging.Handler):
    def emit(self, record):
        try:
            msg = self.format(record)
            log_queue.put_nowait(msg)
        except Exception:
            pass

sse_handler = SSELogHandler()
sse_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s", "%H:%M:%S"))

# attach handler only once to root logger
logging.getLogger().addHandler(sse_handler)

server_logger = logging.getLogger("server")
backend_logger = logging.getLogger("flask_backend")


# ----------------- Flask app -----------------
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})  # ✅ initialize CORS *after* app is created

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("flask_backend")

# ✅ ensure loggers all output at INFO level
server_logger.setLevel(logging.INFO)
backend_logger.setLevel(logging.INFO)
logging.getLogger().setLevel(logging.INFO)

@app.route('/api/stream-logs')
def stream_logs():
    """Server-Sent Events endpoint for live logs"""
    def event_stream():
        while True:
            try:
                msg = log_queue.get(block=True, timeout=1)
                yield f"data: {msg}\n\n"
            except queue.Empty:
                # keep connection alive
                yield ": keep-alive\n\n"
    return Response(event_stream(), mimetype="text/event-stream")


# ----------------- Lightweight Threading XML-RPC server -----------------
class ThreadingXMLRPCServer(ThreadingMixIn, SimpleXMLRPCServer):
    daemon_threads = True

XMLRPC_HOST = getattr(ds_server, 'SERVER_HOST', '0.0.0.0')
XMLRPC_PORT = getattr(ds_server, 'SERVER_PORT', 9000)

xmlrpc_srv = None

def start_xmlrpc_server():
    global xmlrpc_srv
    xmlrpc_srv = ThreadingXMLRPCServer((XMLRPC_HOST, XMLRPC_PORT), allow_none=True, logRequests=False)

    try:
        xmlrpc_srv.register_function(ds_server.cheating_detection, 'cheating_detection')
        xmlrpc_srv.register_function(ds_server.input_time, 'input_time')
        xmlrpc_srv.register_function(ds_server.get_time, 'get_time')
        xmlrpc_srv.register_function(ds_server.receive_cv, 'receive_cv')
        xmlrpc_srv.register_function(ds_server.start_synchronization, 'start_synchronization')
        xmlrpc_srv.register_function(ds_server.register_student, 'register_student')
        xmlrpc_srv.register_function(ds_server.get_registry, 'get_registry')
        xmlrpc_srv.register_function(ds_server.register_intent, 'register_intent')
        xmlrpc_srv.register_function(ds_server.ok_signal, 'ok_signal')
        xmlrpc_srv.register_function(ds_server.update_isa, 'update_isa')
        xmlrpc_srv.register_function(ds_server.exam_completed, 'exam_completed')
        xmlrpc_srv.register_function(ds_server.accept_backup_result, 'accept_backup_result')

        # MCQ endpoints
        xmlrpc_srv.register_function(ds_server.start_mcq, 'start_mcq')
        xmlrpc_srv.register_function(ds_server.get_mcq_active, 'get_mcq_active')
        xmlrpc_srv.register_function(ds_server.get_question_for_student, 'get_question_for_student')
        xmlrpc_srv.register_function(ds_server.submit_mcq_answer, 'submit_mcq_answer')
        xmlrpc_srv.register_function(ds_server.submit_mcq_final, 'submit_mcq_final')

        # Replication & locks
        xmlrpc_srv.register_function(ds_server.announce_results, 'announce_results')
        xmlrpc_srv.register_function(ds_server.request_read, 'request_read')
        xmlrpc_srv.register_function(ds_server.release_read, 'release_read')
        xmlrpc_srv.register_function(ds_server.request_write, 'request_write')
        xmlrpc_srv.register_function(ds_server.update_chunk_marks, 'update_chunk_marks')
        xmlrpc_srv.register_function(ds_server.release_write, 'release_write')

    except Exception as e:
        logger.error("Failed to register some RPC functions: %s", e)
        traceback.print_exc()

    logger.info(f"Starting XML-RPC server on {XMLRPC_HOST}:{XMLRPC_PORT}")
    thread = threading.Thread(target=xmlrpc_srv.serve_forever, daemon=True)
    thread.start()
    return xmlrpc_srv

# start RPC server when backend starts
start_xmlrpc_server()


# ----------------- REST API endpoints -----------------
@app.route('/api/time-sync', methods=['POST'])
def api_time_sync():
    try:
        ds_server.start_synchronization()
        return jsonify({'ok': True, 'msg': 'Time synchronization started'})
    except Exception as e:
        logger.error('time-sync error: %s', e)
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/get-question/<roll>/<int:qnum>', methods=['GET'])
def api_get_question(roll, qnum):
    try:
        q = ds_server.get_question_for_student(str(roll), int(qnum))
        if not q:
            return jsonify({'ok': False, 'error': 'No question found'}), 404
        return jsonify({'ok': True, 'q': q})
    except Exception as e:
        logger.error("get-question error: %s", e)
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/exam-status', methods=['GET'])
def api_exam_status():
    try:
        return jsonify({
            'ok': True,
            'started': ds_server.exam_started,
            'finished': ds_server.exam_finished
        })
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

@app.route('/api/exam-status/<roll>', methods=['GET'])
def api_exam_status_roll(roll):
    try:
        roll = str(roll)
        return jsonify({
            'ok': True,
            'started': ds_server.exam_started,
            'finished': ds_server.exam_finished,
            'terminated': roll in ds_server.terminated_students,
            'warnings': ds_server.student_flags.get(roll, 0)
        })
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/finish-exam', methods=['POST'])
def api_finish_exam():
    try:
        ds_server.exam_finished = True
        return jsonify({'ok': True, 'msg': 'Exam finished'})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/submit-answer', methods=['POST'])
def api_submit_answer():
    data = request.get_json() or {}
    roll = str(data.get('roll'))
    qnum = int(data.get('qnum', 0))
    choice = int(data.get('choice', 0))
    if not roll or not qnum:
        return jsonify({'ok': False, 'error': 'roll and qnum required'}), 400
    try:
        ds_server.submit_mcq_answer(roll, qnum, choice)
        return jsonify({'ok': True})
    except Exception as e:
        logger.error("submit-answer error: %s", e)
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/submit-final', methods=['POST'])
def api_submit_final():
    data = request.get_json() or {}
    roll = str(data.get('roll'))
    if not roll:
        return jsonify({'ok': False, 'error': 'roll required'}), 400
    try:
        ds_server.submit_mcq_final(roll)
        return jsonify({'ok': True})
    except Exception as e:
        logger.error("submit-final error: %s", e)
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/start-exam', methods=['POST'])
def api_start_exam():
    """
    Starts the MCQ on the server, flips flags, and spawns:
     - a timer thread that waits `duration` seconds then finalizes the exam
     - a cheating-simulator thread that every 10s selects a random roll 1..5 and calls cheating_detection
    The request may optionally send JSON: {"duration": 30} to override duration (seconds).
    """
    try:
        # optional duration from request body (seconds)
        data = request.get_json(silent=True) or {}
        if isinstance(data.get("duration"), (int, float)):
            duration = float(data["duration"])
        else:
            duration = float(getattr(ds_server, "EXAM_DURATION", 30))

        # Start MCQ on server
        ds_server.start_mcq()
        ds_server.exam_started = True
        ds_server.exam_finished = False

        # Tell teacher & students (best-effort)
        try:
            ds_server.teacher_proxy.start_exam()
        except Exception:
            logger.warning('teacher.start_exam RPC failed')

        try:
            ds_server.teacher_proxy.phase_complete('Exam Started')
        except Exception:
            pass

        with ds_server.students_lock:
            for r, url in ds_server.students_registry.items():
                try:
                    ds_server.new_proxy(url).phase_complete('Exam Started')
                except Exception:
                    pass

        logger.info(f"[flask_backend] Exam started (duration={duration}s). Spawning timer & cheating threads.")

        # --- Timer thread: after `duration` seconds, finalize the exam ---
        def _exam_timer_thread(dur):
            try:
                time.sleep(dur)
                logger.info("[flask_backend] Exam timer expired — auto-finalizing exam now.")
                try:
                    ds_server.exam_completed()
                except Exception as e:
                    logger.error(f"[flask_backend] ERROR calling ds_server.exam_completed(): {e}")
                ds_server.exam_finished = True
            except Exception as e:
                logger.error(f"[flask_backend] Timer thread error: {e}", exc_info=True)

        threading.Thread(target=_exam_timer_thread, args=(duration,), daemon=True).start()

        # --- Cheating simulator thread ---
        def _cheating_simulator_thread():
            try:
                while True:
                    if getattr(ds_server, "exam_finished", False):
                        logger.info("[flask_backend] Cheating simulator stopping (exam_finished=True).")
                        break
                    time.sleep(10)  # wait exactly 10 seconds
                    roll = str(random.randint(1, 5))
                    logger.info(f"[flask_backend] Cheating simulator selecting roll={roll}")
                    try:
                        ds_server.cheating_detection(roll)
                    except Exception as e:
                        logger.warning(f"[flask_backend] cheating_detection call failed for {roll}: {e}")
            except Exception as e:
                logger.error(f"[flask_backend] Cheating simulator thread crashed: {e}", exc_info=True)

        threading.Thread(target=_cheating_simulator_thread, daemon=True).start()

        return jsonify({'ok': True, 'msg': f'Exam started (duration={duration}s)'})
    except Exception as e:
        logger.error('start-exam error: %s', e, exc_info=True)
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/start-mcq', methods=['POST'])
def api_start_mcq():
    try:
        ds_server.start_mcq()
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/register-student', methods=['POST'])
def api_register_student():
    data = request.get_json() or {}
    roll = str(data.get('roll'))
    # In UI version we don't really need url; just generate dummy one
    url = data.get('url') or f"http://127.0.0.1:900{roll}"
    if not roll:
        return jsonify({'ok': False, 'error': 'roll required'}), 400
    try:
        ds_server.register_student(roll, url)
        return jsonify({'ok': True, 'msg': f"Student {roll} registered"})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/get-registry', methods=['GET'])
def api_get_registry():
    try:
        return jsonify({'ok': True, 'registry': ds_server.get_registry()})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/cheat/<roll>', methods=['POST'])
def api_cheat(roll):
    try:
        msg = ds_server.cheating_detection(roll)
        return jsonify({'ok': True, 'msg': msg})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/logs', methods=['GET'])
def api_logs():
    n = int(request.args.get('n', 200))
    candidates = ['server.log', 'results.log']
    for fname in candidates:
        try:
            with open(fname, 'r', encoding='utf-8') as fh:
                lines = fh.readlines()
                return jsonify({'ok': True, 'lines': lines[-n:]})
        except FileNotFoundError:
            continue
        except Exception as e:
            return jsonify({'ok': False, 'error': str(e)}), 500
    return jsonify({'ok': False, 'error': 'no log file found'}), 404


@app.route('/api/registry-count', methods=['GET'])
def api_registry_count():
    try:
        reg = ds_server.get_registry()
        return jsonify({'ok': True, 'count': len(reg), 'registry': reg})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/')
def index():
    return (
        "<h2>DS Project Admin</h2>"
        "<p>Use the React frontend later. Quick test endpoints:</p>"
        "<ul>"
        "<li>POST /api/time-sync</li>"
        "<li>POST /api/start-exam</li>"
        "<li>POST /api/register-student {'roll','url'}</li>"
        "</ul>"
    )


# Start teacher server in background when backend launches
teacher_thread = threading.Thread(target=ds_teacher.run_teacher, daemon=True)
teacher_thread.start()


@app.route('/api/teacher/input-time', methods=['POST'])
def api_teacher_input_time():
    data = request.get_json() or {}
    t = data.get("time")
    if not t:
        return jsonify({'ok': False, 'error': 'time required'}), 400
    try:
        ds_teacher.local_time = datetime.datetime.strptime(t, "%H-%M-%S")
        ds_teacher.logger.info(f"[Teacher] Local time set to {ds_teacher.local_time.strftime('%H-%M-%S')}")
        return jsonify({'ok': True, 'msg': f"Teacher time set to {t}"})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/teacher/release-results', methods=['POST'])
def api_teacher_release_results():
    try:
        success = ds_teacher.release_results()
        if success:
            return jsonify({'ok': True, 'msg': 'Results released to students'})
        return jsonify({'ok': False, 'error': 'Failed to release results'})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/student/input-time', methods=['POST'])
def api_student_input_time():
    data = request.get_json() or {}
    roll = str(data.get("roll"))
    t = data.get("time")
    if not roll or not t:
        return jsonify({'ok': False, 'error': 'roll and time required'}), 400
    try:
        dt = datetime.datetime.strptime(t, "%H-%M-%S")
        if not hasattr(ds_server, "student_times"):
            ds_server.student_times = {}
        ds_server.student_times[roll] = dt
        ds_server.logger.info(f"[Student {roll}] Local time set to {dt.strftime('%H-%M-%S')}")
        return jsonify({'ok': True, 'msg': f"Student {roll} time set to {t}"})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/server/input-time', methods=['POST'])
def api_server_input_time():
    data = request.get_json() or {}
    t = data.get("time")
    if not t:
        return jsonify({'ok': False, 'error': 'time required'}), 400
    try:
        ds_server.local_time = datetime.datetime.strptime(t, "%H-%M-%S")
        ds_server.logger.info(f"[Server] Local time set to {ds_server.local_time.strftime('%H-%M-%S')}")
        return jsonify({'ok': True, 'msg': f"Server time set to {t}"})
    except Exception as e:
        ds_server.logger.error(f"server/input-time failed: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


# ----------------- Run Flask -----------------
if __name__ == '__main__':
    logger.info('Starting Flask backend on http://0.0.0.0:5000')
    app.run(host='0.0.0.0', port=5000, debug=False)
