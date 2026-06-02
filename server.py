import http.server
import socketserver
import threading
import os
import config
import diagnostics

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()

def start_server(port=8080):
    os.chdir(config.REPORT_DIR)
    handler = CustomHTTPRequestHandler
    socketserver.TCPServer.allow_reuse_address = True

    try:
        httpd = socketserver.TCPServer(("", port), handler)
        server_thread = threading.Thread(target=httpd.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        diagnostics.log_info(f"Local Server Active: http://localhost:{port}/index.html")
    except Exception as e:
        diagnostics.log_warning(f"Port {port} is occupied. Server is likely already running.")
