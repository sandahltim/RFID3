import os
from app import create_app

# Set API credentials for RFIDpro API (force override)
os.environ['API_USERNAME'] = 'api'
os.environ['API_PASSWORD'] = 'Broadway8101'

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('FLASK_RUN_PORT', 5000))

    # Run HTTP only - HTTPS now handled by standalone scanner interface on port 8443
    print("RFID3 Main Service running HTTP only - Scanner interface available on HTTPS:8443")
    app.run(host='0.0.0.0', port=port, debug=True)

