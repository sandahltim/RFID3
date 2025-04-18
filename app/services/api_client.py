import requests
from tenacity import retry, stop_after_attempt, wait_exponential
from flask import current_app
import json
from datetime import datetime, timedelta
from redis import StrictRedis
from config import LOGIN_URL, ITEM_MASTER_URL, TRANSACTION_URL, SEED_URL, API_USERNAME, API_PASSWORD, REDIS_URL

class APIClient:
    def __init__(self):
        self.redis = StrictRedis.from_url(REDIS_URL, decode_responses=True)
        self.token = None
        self.token_expiry = None

    def authenticate(self):
        """Authenticate with the API and store token in Redis."""
        try:
            cached_token = self.redis.get('api_token')
            cached_expiry = self.redis.get('token_expiry')
            if cached_token and cached_expiry and datetime.fromisoformat(cached_expiry) > datetime.now():
                self.token = cached_token
                self.token_expiry = datetime.fromisoformat(cached_expiry)
                return

            response = requests.post(
                LOGIN_URL,
                json={'username': API_USERNAME, 'password': API_PASSWORD},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            self.token = data.get('token')
            self.token_expiry = datetime.now() + timedelta(seconds=data.get('expires_in', 3600))

            self.redis.setex('api_token', 3600, self.token)
            self.redis.setex('token_expiry', 3600, self.token_expiry.isoformat())
            current_app.logger.info("API authentication successful")
        except Exception as e:
            current_app.logger.error(f"API authentication failed: {str(e)}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def fetch_paginated_data(self, url, since_date=None):
        """Fetch paginated data from the API."""
        if not self.token:
            self.authenticate()

        params = {'limit': 200}
        if since_date:
            params['since'] = since_date

        data = []
        while True:
            try:
                response = requests.get(
                    url,
                    headers={'Authorization': f'Bearer {self.token}'},
                    params=params,
                    timeout=10
                )
                response.raise_for_status()
                page_data = response.json().get('data', [])
                data.extend(page_data)
                
                next_page = response.json().get('next_page')
                if not next_page:
                    break
                params['page'] = next_page
            except requests.RequestException as e:
                current_app.logger.error(f"Failed to fetch data from {url}: {str(e)}")
                self.authenticate()  # Retry with fresh token
                raise

        return data

    def get_item_master(self, since_date=None):
        """Fetch item master data."""
        return self.fetch_paginated_data(ITEM_MASTER_URL, since_date)

    def get_transactions(self, since_date=None):
        """Fetch transaction data."""
        return self.fetch_paginated_data(TRANSACTION_URL, since_date)

    def get_seed_data(self, since_date=None):
        """Fetch seed data."""
        return self.fetch_paginated_data(SEED_URL, since_date)