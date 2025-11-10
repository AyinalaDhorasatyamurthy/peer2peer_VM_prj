"""
Configuration settings for the Peer2Peer Torrent application.
"""
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.absolute()

# Network settings
HOST = '0.0.0.0'
PORT = 5001
TRACKER_URL = f'http://{HOST}:{PORT}'
UPLOAD_FOLDER = 'uploads'
TORRENT_FOLDER = 'torrents'
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
SECRET_KEY = 'vm1-secret-key-123'

# File storage
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
TORRENT_FOLDER = os.path.join(BASE_DIR, 'torrents')

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TORRENT_FOLDER, exist_ok=True)

# Tracker settings
TRACKER_INTERVAL = 30  # seconds
TRACKER_TIMEOUT = 120  # seconds

# Piece size (256KB)
PIECE_SIZE = 256 * 1024

# Logging
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
