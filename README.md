# Peer2Peer Torrent Client

A decentralized file-sharing application built with Python and WebSockets, enabling direct peer-to-peer file transfers with real-time progress tracking.

## 🚀 Features

- [x] Direct peer-to-peer file transfers
- [x] Web-based interface for easy access
- [x] Real-time progress tracking
- [x] Automatic peer discovery
- [x] Download/upload speed monitoring
- [x] Multi-peer file distribution
- [x] Support for .torrent files

## 🛠️ Tech Stack

- **Backend**: Python, Flask, Socket.IO
- **Frontend**: HTML5, JavaScript, Bootstrap 5
- **Networking**: WebSockets, HTTP Tracker Protocol
- **Storage**: Local file system

## 📦 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/AyinalaDhorasatyamurthy/peer2peer_prj.git
   cd peer2peer_prj/backend
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   # OR
   source venv/bin/activate  # Linux/Mac
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## ⚙️ Configuration

Edit `config.py` to set up your network settings:

```python
HOST = '0.0.0.0'          # Bind address
PORT = 5001               # Port used by the tracker/web UI
TRACKER_URL = f'http://{HOST}:{PORT}'
UPLOAD_FOLDER = 'uploads'
TORRENT_FOLDER = 'torrents'
```

## 🚀 Usage

1. Start the application:
   ```bash
   python main.py
   ```

2. Open your browser and navigate to:
   ```
   http://localhost:5001
   ```

3. From the web UI:
   - **Connect** to the tracker (auto on load if available)
   - **Upload** a .torrent file to register it
   - View **Peers** and **Torrents** in real time

The Socket.IO client script is served from `GET /socket.io.js` by the backend.

## 🌟 Multi-VM Setup

For testing with multiple peers:

1. Set up 3 VMs with IPs: 192.168.56.103, 192.168.56.104, 192.168.56.105
2. On each VM:
   - Clone the repository
   - Update `config.py` with the VM's IP and ensure `PORT = 5001`
   - Set `TRACKER_URL` to the tracker host: `http://<TRACKER_IP>:5001`
   - Run `python main.py`
3. Access the tracker UI at `http://<TRACKER_IP>:5001`.

## 📂 Project Structure

```
peer2peer_prj/
├── backend/
│   ├── app/                 # Application modules
│   │   ├── bencode.py       # Bencode utilities
│   │   ├── peer.py          # Peer management
│   │   ├── torrent.py       # Torrent handling
│   │   └── tracker.py       # Tracker logic
│   ├── web/                 # Web interface
│   │   ├── static/          # Static files
│   │   └── templates/
│   │       └── index.html   # Main UI
│   ├── uploads/             # Uploaded files
│   ├── torrents/            # Torrent files
│   ├── socket.io.min.js     # Socket.IO client served at /socket.io.js
│   ├── tracker_state.json   # Persisted state for torrents and swarms
│   ├── config.py            # Configuration
│   ├── main.py              # Entry point (runs on port 5001)
│   └── requirements.txt     # Dependencies
└── README.md
```

## 🔌 API Endpoints

- **GET /**: Web UI
- **GET /health**: Health check
- **GET /api/status**: Tracker status and counts
- **GET /api/peers**: Current peers connected
- **GET /api/torrents**: Torrents known to the tracker
- **POST /upload-torrent**: Upload a `.torrent` file

Socket.IO events include: `connect`, `register_peer`, `get_peers`, `get_torrents`, `test_connection`, plus broadcast events like `peers_updated`, `torrents_list`, and `server_message`.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with ❤️ using Python, Flask, and Socket.IO
- Inspired by BitTorrent protocol
- Icons by [Bootstrap Icons](https://icons.getbootstrap.com/)

## 🧰 Troubleshooting

- If you see an import error for `bencodepy`, install it:
  ```bash
  pip install bencodepy
  ```
- If the web UI reports Socket.IO not available, ensure `backend/socket.io.min.js` exists; the app serves it at `/socket.io.js`.
