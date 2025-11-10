// app.js
document.addEventListener('DOMContentLoaded', () => {
    const peerId = 'VM-' + Math.random().toString(36).substr(2, 8);
    let socket = null;

    // UI Elements
    const statusBox = document.getElementById('status');
    const socketStatus = document.getElementById('socket-status');
    const logs = document.getElementById('logs');
    const peerCount = document.getElementById('peerCount');
    const torrentCount = document.getElementById('torrentCount');
    const peersDiv = document.getElementById('peers');
    const torrentsDiv = document.getElementById('torrents');
    const torrentFile = document.getElementById('torrentFile');

    // Buttons
    const connectBtn = document.getElementById('connectBtn');
    const registerBtn = document.getElementById('registerBtn');
    const peersBtn = document.getElementById('peersBtn');
    const torrentsBtn = document.getElementById('torrentsBtn');
    const testBtn = document.getElementById('testBtn');
    const uploadBtn = document.getElementById('uploadBtn');
    const clearBtn = document.getElementById('clearBtn');
    const debugBtn = document.getElementById('debugBtn');

    // ------------------ Utility Functions ------------------

    function log(message, type = 'info') {
        const entry = document.createElement('div');
        entry.className = `log ${type}`;
        entry.innerHTML = `[${new Date().toLocaleTimeString()}] ${message}`;
        logs.appendChild(entry);
        logs.scrollTop = logs.scrollHeight;
        console.log(`[${type.toUpperCase()}] ${message}`);
    }

    function updateStatus(text, color = 'grey') {
        statusBox.textContent = text;
        statusBox.className = color === 'green'
            ? 'connected'
            : color === 'red'
            ? 'disconnected'
            : 'disconnected';
    }

    function updateSocketStatus(message, isGood) {
        socketStatus.innerHTML = message;
        socketStatus.className = `socket-status ${isGood ? 'socket-good' : 'socket-bad'}`;
    }

    function updateButtonStates(connected) {
        [registerBtn, peersBtn, torrentsBtn, testBtn, uploadBtn].forEach(
            btn => (btn.disabled = !connected)
        );
        connectBtn.innerHTML = connected ? 'Reconnect' : 'Connect to Tracker';
    }

    function clearLogs() {
        logs.innerHTML = '';
        log('Logs cleared', 'info');
    }

    function debugConnection() {
        log('=== DEBUG INFO ===', 'warning');
        log(`Socket exists: ${!!socket}`, 'info');
        log(`Socket connected: ${socket ? socket.connected : 'N/A'}`, 'info');
        log(`Socket ID: ${socket ? socket.id : 'N/A'}`, 'info');
        log(`Peer ID: ${peerId}`, 'info');
    }

    // ------------------ Socket Functions ------------------

    function connectToTracker() {
        if (typeof io === 'undefined') {
            log('❌ Socket.IO not loaded.', 'error');
            updateSocketStatus('❌ Socket.IO Missing', false);
            return;
        }

        if (socket && socket.connected) {
            log('🔄 Reconnecting...', 'info');
            socket.disconnect();
        }

        log('📡 Connecting to tracker...', 'info');
        updateStatus('Connecting...', 'orange');
        updateSocketStatus('🔄 Connecting...', false);

        socket = io('http://localhost:5001', {
            reconnection: true,
            reconnectionAttempts: 5,
            reconnectionDelay: 1000,
            transports: ['websocket']
        });

        // ---- Events ----
        socket.on('connect', () => {
            log(`✅ Connected! Socket ID: ${socket.id}`, 'success');
            updateStatus('Connected to Tracker', 'green');
            updateSocketStatus('✅ Connected', true);
            updateButtonStates(true);

            // auto-register
            registerAsPeer();
        });

        socket.on('disconnect', reason => {
            log(`❌ Disconnected: ${reason}`, 'error');
            updateStatus('Disconnected', 'red');
            updateSocketStatus('❌ Disconnected', false);
            updateButtonStates(false);
        });

        socket.on('connect_error', err => {
            log(`❌ Connection failed: ${err.message}`, 'error');
            updateStatus('Connection Failed', 'red');
            updateSocketStatus('❌ Connection Error', false);
        });

        socket.on('server_message', data => {
            log(`📨 ${data.message}`, data.type || 'info');
        });

        socket.on('peer_registered', data => {
            log(`👤 Registered as peer: ${data.peer_id}`, 'success');
        });

        socket.on('peers_updated', data => {
            log(`📊 Peer list updated (${data.count})`, 'info');
            peerCount.textContent = data.count;
            displayPeers(data.peers);
        });

        socket.on('torrents_list', data => {
            log(`📁 Torrents updated (${data.count})`, 'info');
            torrentCount.textContent = data.count;
            displayTorrents(data.torrents);
        });
    }

    function registerAsPeer() {
        if (!socket || !socket.connected) {
            log('❌ Not connected', 'error');
            return;
        }
        const data = {
            peer_id: peerId,
            port: 6881,
            ip_address: '127.0.0.1',
            client_type: 'vm-client',
            capabilities: ['p2p-sharing', 'webseed']
        };
        log(`👤 Registering peer: ${peerId}`, 'info');
        socket.emit('register_peer', data);
    }

    function getPeers() {
        if (!socket || !socket.connected) return log('❌ Not connected', 'error');
        log('🔍 Requesting peers...', 'info');
        socket.emit('get_peers');
    }

    function getTorrents() {
        if (!socket || !socket.connected) return log('❌ Not connected', 'error');
        log('📁 Requesting torrents...', 'info');
        socket.emit('get_torrents');
    }

    function testConnection() {
        if (!socket || !socket.connected) return log('❌ Not connected', 'error');
        log('🔧 Testing connection...', 'info');
        socket.emit('test_connection', { test: true, time: Date.now() });
    }

    async function uploadTorrent() {
        if (!socket || !socket.connected) return log('❌ Not connected', 'error');
        const file = torrentFile.files[0];
        if (!file) return log('❌ Select a .torrent file first', 'error');
        if (!file.name.endsWith('.torrent')) return log('❌ Invalid file type', 'error');

        log(`📤 Uploading ${file.name}...`, 'info');
        const formData = new FormData();
        formData.append('torrent', file);

        try {
            const response = await fetch('/upload-torrent', { method: 'POST', body: formData });
            const data = await response.json();
            if (data.success) {
                log(`✅ ${data.message}`, 'success');
                getTorrents();
            } else {
                log(`❌ Upload failed: ${data.error}`, 'error');
            }
        } catch (err) {
            log(`❌ Upload error: ${err.message}`, 'error');
        }
    }

    function displayPeers(peers) {
        if (!peers || peers.length === 0) {
            peersDiv.innerHTML = '<div style="color:#777;">No peers connected</div>';
            return;
        }
        peersDiv.innerHTML = peers.map(peer => `
            <li>
                <strong>${peer.peer_id}</strong><br>
                <small>IP: ${peer.ip}:${peer.port}</small><br>
                <small>Connected: ${new Date(peer.connected_at).toLocaleTimeString()}</small>
            </li>
        `).join('');
    }

    function displayTorrents(torrents) {
        if (!torrents || torrents.length === 0) {
            torrentsDiv.innerHTML = '<div style="color:#777;">No torrents available</div>';
            return;
        }
        torrentsDiv.innerHTML = torrents.map(t => `
            <li>
                <strong>${t.filename || 'Unknown File'}</strong><br>
                <small>Hash: ${t.info_hash || 'N/A'}</small><br>
                <small>Size: ${t.size ? (t.size / 1024).toFixed(2) + ' KB' : 'Unknown'}</small><br>
                <small>Uploaded: ${new Date(t.uploaded_at).toLocaleTimeString()}</small>
            </li>
        `).join('');
    }

    // ------------------ Event Bindings ------------------
    connectBtn.addEventListener('click', connectToTracker);
    registerBtn.addEventListener('click', registerAsPeer);
    peersBtn.addEventListener('click', getPeers);
    torrentsBtn.addEventListener('click', getTorrents);
    testBtn.addEventListener('click', testConnection);
    uploadBtn.addEventListener('click', uploadTorrent);
    clearBtn.addEventListener('click', clearLogs);
    debugBtn.addEventListener('click', debugConnection);

    // ------------------ Auto Initialization ------------------
    log('🚀 Client Started', 'info');
    log(`Peer ID: ${peerId}`, 'info');
    updateButtonStates(false);

    // Auto-connect
    setTimeout(connectToTracker, 800);
});
