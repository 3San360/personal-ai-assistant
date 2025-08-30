import http.server
import socketserver
import json
from urllib.parse import urlparse, parse_qs

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/v1/health/':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response = {"status": "ok", "message": "Personal AI Assistant API is running"}
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        if self.path == '/api/v1/chat/message':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response = {"message": "Chat endpoint is working", "response": "Hello! This is a test response."}
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == "__main__":
    PORT = 5000
    with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:
        print(f"🚀 Simple Personal AI Assistant API Server running on port {PORT}")
        print(f"🌐 Health endpoint: http://localhost:{PORT}/api/v1/health/")
        httpd.serve_forever()
