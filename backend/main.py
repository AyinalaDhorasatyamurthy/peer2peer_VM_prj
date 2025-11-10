# In your VM's main.py - WITH REAL SOCKET.IO
import os
from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import datetime
import hashlib
import bencodepy
import time
import logging
import json

# Get the absolute path to the current directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'web', 'templates')

app = Flask(__name__, template_folder=TEMPLATE_DIR)
app.config['SECRET_KEY'] = 'tracker-secret-key'
CORS(app)

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
socketio = SocketIO(app,
                   cors_allowed_origins="*",
                   async_mode='threading',
                   logger=True,
                   engineio_logger=True,
                   ping_timeout=30,
                   ping_interval=20)

# Store connected clients with their info
connected_clients = {}
torrents_metadata = {}
torrent_swarms = {}

# Simple persistence for torrents and swarms
STATE_PATH = os.path.join(BASE_DIR, 'tracker_state.json')

def save_state():
    try:
        state = {
            'torrents_metadata': torrents_metadata,
            'torrent_swarms': torrent_swarms
        }
        with open(STATE_PATH, 'w') as f:
            json.dump(state, f)
    except Exception as e:
        print(f"❌ Failed to save state: {e}")

def load_state():
    global torrents_metadata, torrent_swarms
    try:
        if os.path.exists(STATE_PATH):
            with open(STATE_PATH, 'r') as f:
                state = json.load(f)
                torrents_metadata = state.get('torrents_metadata', {})
                torrent_swarms = state.get('torrent_swarms', {})
                print(f"✅ Loaded state: {len(torrents_metadata)} torrents, {len(torrent_swarms)} swarms")
        else:
            print("ℹ️ No existing state file; starting fresh")
    except Exception as e:
        print(f"❌ Failed to load state: {e}")

# Load persisted state on startup
load_state()

# Serve the REAL Socket.IO client that we just downloaded
@app.route('/socket.io.js')
def serve_socket_io():
    return send_from_directory(BASE_DIR, 'socket.io.min.js')

# Basic Socket.IO events
@socketio.on('connect')
def handle_connect():
    client_id = request.sid
    client_ip = request.remote_addr

    connected_clients[client_id] = {
        'ip': client_ip,
        'connected_at': datetime.datetime.now().isoformat(),
        'type': 'unknown',
        'peer_id': None,
        'active_torrents': []
    }

    print(f"🎯 REAL WebSocket connection established: {client_id} from {client_ip}")

    # Send immediate confirmation
    emit('server_message', {
        'type': 'success',
        'message': f'REAL WebSocket connected from {client_ip}'
    }, room=client_id)

    # Send current peer list
    emit('peers_updated', get_peer_list_data(), room=client_id)

@socketio.on('disconnect')
def handle_disconnect():
    client_id = request.sid
    if client_id in connected_clients:
        disconnected_client = connected_clients.pop(client_id)
        print(f"Client disconnected: {client_id} ({disconnected_client['ip']})")
        # Remove peer from any swarms
        peer_id = disconnected_client.get('peer_id')
        if peer_id:
            for info_hash, peers in list(torrent_swarms.items()):
                if peer_id in peers:
                    peers.remove(peer_id)
                    if not peers:
                        torrent_swarms.pop(info_hash, None)
            save_state()
        broadcast_peer_list()

@socketio.on('register_peer')
def handle_register_peer(data):
    client_id = request.sid
    if client_id in connected_clients:
        peer_id = data.get('peer_id', 'unknown')

        connected_clients[client_id].update({
            'type': 'peer',
            'peer_id': peer_id,
            'port': data.get('port', 6881),
            'client_type': data.get('client_type', 'unknown'),
            'ip_address': data.get('ip_address', request.remote_addr),
            'capabilities': data.get('capabilities', [])
        })

        print(f"✅ Peer registered: {peer_id}")

        broadcast_peer_list()

        emit('server_message', {
            'type': 'success',
            'message': f'Successfully registered as peer: {peer_id}'
        }, room=client_id)

        # Send registration confirmation
        emit('peer_registered', {
            'peer_id': peer_id,
            'status': 'success',
            'timestamp': datetime.datetime.now().isoformat()
        }, room=client_id)
    else:
        print(f"❌ Client {client_id} not found in connected_clients")

@socketio.on('get_peers')
def handle_get_peers():
    client_id = request.sid
    print(f"📊 Client {client_id} requested peer list")
    peer_data = get_peer_list_data()
    print(f"📊 Sending peer data: {peer_data}")
    emit('peers_updated', peer_data, room=client_id)

@socketio.on('get_torrents')
def handle_get_torrents():
    client_id = request.sid
    print(f"📁 Client {client_id} requested torrents list")
    emit('torrents_list', {
        'torrents': list(torrents_metadata.values()),
        'count': len(torrents_metadata)
    }, room=client_id)

@socketio.on('test_connection')
def handle_test_connection(data):
    client_id = request.sid
    print(f"🔧 Client {client_id} testing connection")
    emit('server_message', {
        'type': 'success',
        'message': f'WebSocket test successful - Client: {client_id}'
    }, room=client_id)

# REAL P2P: Torrent announcement
@socketio.on('announce_torrent')
def handle_announce_torrent(data):
    client_id = request.sid
    info_hash = data.get('info_hash')
    peer_id = data.get('peer_id')

    if not all([info_hash, peer_id]):
        return

    print(f"🎯 Peer {peer_id} announced torrent {info_hash[:8]}...")

    # Initialize swarm if needed
    if info_hash not in torrent_swarms:
        torrent_swarms[info_hash] = []

    # Add peer to swarm
    if peer_id not in torrent_swarms[info_hash]:
        torrent_swarms[info_hash].append(peer_id)
        save_state()

    # Send peer list for this torrent
    other_peers = [p for p in torrent_swarms[info_hash] if p != peer_id]

    emit('torrent_peers', {
        'info_hash': info_hash,
        'peers': other_peers,
        'swarm_size': len(torrent_swarms[info_hash])
    }, room=client_id)

@socketio.on('message')
def handle_message(data):
    print(f"📨 Received message: {data}")
    emit('server_message', {
        'type': 'info',
        'message': f'Message received: {data}'
    }, room=request.sid)

def get_peer_list_data():
    peers = []
    for client_id, client_info in connected_clients.items():
        if client_info.get('type') == 'peer':
            peer_info = {
                'client_id': client_id,
                'ip': client_info['ip'],
                'port': client_info.get('port', 6881),
                'peer_id': client_info.get('peer_id'),
                'connected_at': client_info.get('connected_at'),
                'active_torrents': client_info.get('active_torrents', [])
            }
            peers.append(peer_info)

    return {
        'peers': peers,
        'count': len(peers),
        'total_clients': len(connected_clients),
        'timestamp': datetime.datetime.now().isoformat()
    }

def broadcast_peer_list():
    peer_data = get_peer_list_data()
    print(f"📢 Broadcasting peer list to all clients: {peer_data}")
    socketio.emit('peers_updated', peer_data)

@app.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>P2P Tracker</title>
            <script src="/socket.io.js"></script>
        </head>
        <body>
            <h1>P2P Tracker Server</h1>
            <p>✅ Real Socket.IO client loaded</p>
            <p>Access: <a href="http://localhost:5001">http://localhost:5001</a></p>
            <p>Error: {str(e)}</p>
        </body>
        </html>
        """

@app.route('/upload-torrent', methods=['POST'])
def upload_torrent():
    try:
        if 'torrent' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'})

        torrent_file = request.files['torrent']
        filename = torrent_file.filename

        if not filename:
            return jsonify({'success': False, 'error': 'No file selected'})

        # Store file info
        file_id = hashlib.md5(filename.encode()).hexdigest()[:8]
        torrents_metadata[file_id] = {
            'filename': filename,
            'uploaded_at': datetime.datetime.now().isoformat(),
            'size': len(torrent_file.read()),
            'info_hash': file_id
        }
        save_state()
        
        # Reset file pointer
        torrent_file.seek(0)

        success_message = f"Torrent uploaded successfully: {filename} (ID: {file_id})"
        print(success_message)

        # Broadcast to all clients
        socketio.emit('server_message', {
            'type': 'success',
            'message': success_message
        })
        
        # Broadcast updated torrents list
        socketio.emit('torrents_list', {
            'torrents': list(torrents_metadata.values()),
            'count': len(torrents_metadata)
        })

        return jsonify({
            'success': True,
            'message': success_message,
            'filename': filename,
            'file_id': file_id
        })

    except Exception as e:
        error_msg = f"Upload error: {str(e)}"
        print(f"❌ {error_msg}")
        return jsonify({'success': False, 'error': error_msg})

@app.route('/api/status')
def api_status():
    return jsonify({
        "status": "tracker_running",
        "total_connected_clients": len(connected_clients),
        "total_peers": len([c for c in connected_clients.values() if c.get('type') == 'peer']),
        "total_torrents": len(torrents_metadata),
        "connected_peers": [c.get('peer_id') for c in connected_clients.values() if c.get('type') == 'peer'],
        "server_time": datetime.datetime.now().isoformat()
    })

@app.route('/api/peers')
def api_peers():
    return jsonify(get_peer_list_data())

@app.route('/api/torrents')
def api_torrents():
    return jsonify({
        'torrents': list(torrents_metadata.values()),
        'count': len(torrents_metadata)
    })

# Health check endpoint
@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.datetime.now().isoformat()
    })

if __name__ == '__main__':
    os.makedirs(TEMPLATE_DIR, exist_ok=True)

    # Verify Socket.IO client exists
    socket_io_path = os.path.join(BASE_DIR, 'socket.io.min.js')
    if os.path.exists(socket_io_path):
        print("✅ Real Socket.IO client found and ready!")
    else:
        print("❌ Socket.IO client missing - using Flask-SocketIO built-in")

    print(f"🚀 Starting P2P Tracker on http://0.0.0.0:5001")
    print("📍 Access via: http://localhost:5001")
    print("🔧 Real Socket.IO client enabled")
    print("📊 Debug logging enabled")
    print("=" * 50)

    socketio.run(app, 
                 host='0.0.0.0', 
                 port=5001, 
                 debug=True, 
                 allow_unsafe_werkzeug=True,
                 use_reloader=False)  # Disable reloader to prevent double connections
