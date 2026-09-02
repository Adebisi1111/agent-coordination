"""
Backend server for Agent Coordination + Technocore integration.

Serves the frontend and provides Technocore API endpoints:
- POST /technocore/generate - Generate a new DID
- POST /technocore/restore - Restore DID from seed
- GET /technocore/messages/{task_id} - Get messages for a task
"""

import json
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from technocore import AgentIdentity, TechnocoreClient, hash_did_for_contract, verify_message


# In-memory store for task rooms (in production, use a database)
task_rooms = {}
message_store = {}


class TechnocoreHandler(SimpleHTTPRequestHandler):
    """HTTP handler for Technocore API endpoints."""
    
    def do_POST(self):
        parsed = urlparse(self.path)
        
        if parsed.path == '/technocore/generate':
            self.handle_generate()
        elif parsed.path == '/technocore/restore':
            self.handle_restore()
        elif parsed.path == '/technocore/post_message':
            self.handle_post_message()
        else:
            self.send_error(404)
    
    def do_GET(self):
        parsed = urlparse(self.path)
        
        if parsed.path.startswith('/technocore/messages/'):
            task_id = parsed.path.split('/messages/')[1]
            self.handle_get_messages(task_id)
        elif parsed.path == '/technocore/health':
            self.handle_health()
        else:
            super().do_GET()
    
    def handle_generate(self):
        """Generate a new Technocore identity."""
        identity = AgentIdentity()
        data = {
            'did': identity.did,
            'seed': identity.seed_hex,
            'address': identity.did  # In this case, the DID is the identifier
        }
        self.send_json_response(200, data)
    
    def handle_restore(self):
        """Restore a Technocore identity from seed."""
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        params = json.loads(body)
        seed = params.get('seed', '')
        
        if not seed or len(seed) != 64:
            self.send_json_response(400, {'error': 'Invalid seed. Must be 64 hex characters.'})
            return
        
        try:
            identity = AgentIdentity(seed_hex=seed)
            data = {
                'did': identity.did,
                'seed': identity.seed_hex,
                'address': identity.did
            }
            self.send_json_response(200, data)
        except Exception as e:
            self.send_json_response(400, {'error': str(e)})
    
    def handle_post_message(self):
        """Post a signed message to a task room."""
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        params = json.loads(body)
        
        task_id = params.get('task_id', '')
        room = params.get('room', '')
        text = params.get('text', '')
        did = params.get('did', '')
        seed = params.get('seed', '')
        nonce = params.get('nonce', 0)
        sig = params.get('sig', '')
        
        if not all([task_id, room, text, did, seed, nonce, sig]):
            self.send_json_response(400, {'error': 'Missing required fields'})
            return
        
        # Verify signature
        if not AgentIdentity.verify(did, room, nonce, text, sig):
            self.send_json_response(400, {'error': 'Invalid signature'})
            return
        
        # Store message
        if task_id not in message_store:
            message_store[task_id] = []
        
        seq = len(message_store[task_id]) + 1
        message = {
            'seq': seq,
            'frm': did,
            'text': text,
            'room': room,
            'nonce': nonce,
            'sig': sig,
            'verified': True
        }
        message_store[task_id].append(message)
        
        self.send_json_response(200, {'seq': seq, 'message': message})
    
    def handle_get_messages(self, task_id):
        """Get messages for a task."""
        messages = message_store.get(task_id, [])
        self.send_json_response(200, {'messages': messages})
    
    def handle_health(self):
        """Health check endpoint."""
        self.send_json_response(200, {'status': 'ok'})
    
    def send_json_response(self, status_code, data):
        """Send a JSON response."""
        response = json.dumps(data).encode()
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(response)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(response)
    
    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


def run_server(port=8000):
    """Run the Technocore backend server."""
    server = HTTPServer(('0.0.0.0', port), TechnocoreHandler)
    print(f'Technocore server running on port {port}')
    server.serve_forever()


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    run_server(port)
