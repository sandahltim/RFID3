from flask import Flask, request
from app import create_app

app = create_app()

# Prevent caching of static files by Cloudflare and browsers
@app.after_request
def add_header(response):
    if 'static' in request.path:
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
        # Prevent Cloudflare caching
        response.headers['CF-Cache-Control'] = 'no-cache'
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3609, debug=True)