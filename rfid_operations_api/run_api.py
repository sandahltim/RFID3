#!/usr/bin/env python3
# RFID Operations API - Production Runner
import os
import sys
import uvicorn
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def main():
    """Run the RFID Operations API"""

    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv('config/.env')

    # Configuration
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8443))
    reload = os.getenv("API_RELOAD", "false").lower() == "true"
    ssl_keyfile = os.getenv("SSL_KEYFILE", "/etc/ssl/private/pi5-rfid3.key")
    ssl_certfile = os.getenv("SSL_CERTFILE", "/etc/ssl/certs/pi5-rfid3.crt")

    print(f"🚀 Starting RFID Operations API on https://{host}:{port}")
    print(f"📚 API Documentation: https://{host}:{port}/docs")
    print(f"🏥 Health Check: https://{host}:{port}/health")

    # Run with SSL for HTTPS support (required for camera/mobile)
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        ssl_keyfile=ssl_keyfile,
        ssl_certfile=ssl_certfile,
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    main()