# trigger.py
import xmlrpc.client
s = xmlrpc.client.ServerProxy("http://127.0.0.1:9000/", allow_none=True)
print(s.exam_completed())
