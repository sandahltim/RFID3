import requests
from datetime import datetime, timedelta
from config import API_USERNAME, API_PASSWORD, LOGIN_URL, ITEM_MASTER_URL, TRANSACTION_URL, SEED_URL
import logging

logging.basicConfig(level=logging.DEBUG, filename='/home/tim/test_rfidpi/sync.log', filemode='a')
logger = logging.getLogger(__name__)

class APIClient:
    def __init__(self):
        self.base_url = "https://cs.iot.ptshome.com/api/v1/data/"
        self.auth_url = LOGIN_URL
        self.token = None
        self.token_expiry = None
        self.authenticate()

    def authenticate(self):
        now = datetime.utcnow()
        if self.token and self.token_expiry and now < self.token_expiry:
            logger.debug("Using cached access token")
            return self.token
        payload = {"username": API_USERNAME, "password": API_PASSWORD}
        logger.debug(f"Requesting token from {self.auth_url} with username={API_USERNAME}")
        for attempt in range(5):
            try:
                response = requests.post(self.auth_url, json=payload, timeout=20)
                logger.debug(f"Token attempt {attempt+1}: Status {response.status_code}, Response: {response.text[:100]}...")
                response.raise_for_status()
                data = response.json()
                self.token = data.get("access_token")
                self.token_expiry = now + timedelta(minutes=55)
                logger.debug(f"Access token received: {self.token[:10]}... (expires {self.token_expiry})")
                return self.token
            except requests.RequestException as e:
                logger.error(f"Token attempt {attempt+1} failed: {e}, response: {getattr(e.response, 'text', 'N/A')}")
                if attempt < 4:
                    time.sleep(3)
            except ValueError as e:
                logger.error(f"Invalid JSON response from login: {e}")
                return None
        logger.error("Failed to fetch access token after 5 attempts")
        raise Exception("Failed to fetch access token after 5 attempts")

    def _make_request(self, endpoint_id, params=None):
        if not self.token:
            self.authenticate()
        headers = {'Authorization': f'Bearer {self.token}'}
        url = f"{self.base_url}{endpoint_id}"
        logger.debug(f"Making request to {url} with params: {params}")
        response = requests.get(url, headers=headers, params=params, timeout=20)
        response.raise_for_status()
        return response.json()

    def get_item_master(self, since_date=None):
        items = []
        offset = 0
        limit = 200
        while True:
            params = {'offset': offset, 'limit': limit, 'returncount': True}
            if since_date:
                params['filter[]'] = f"date_last_scanned>{since_date}"
            data = self._make_request("14223767938169344381", params=params)
            items.extend(data.get('data', []))
            total_count = int(data.get('totalcount', 0))
            logger.debug(f"Item Master: Fetched {len(data.get('data', []))} records, Total Count: {total_count}, Offset: {offset}")
            offset += limit
            if len(data.get('data', [])) == 0 or offset >= total_count:
                break
        logger.debug(f"Total Item Master records fetched: {len(items)}")
        return items

    def get_transactions(self, since_date=None):
        transactions = []
        offset = 0
        limit = 200
        while True:
            params = {'offset': offset, 'limit': limit, 'returncount': True}
            if since_date:
                params['filter[]'] = f"scan_date>{since_date}"
            data = self._make_request("14223767938169346196", params=params)
            transactions.extend(data.get('data', []))
            total_count = int(data.get('totalcount', 0))
            logger.debug(f"Transactions: Fetched {len(data.get('data', []))} records, Total Count: {total_count}, Offset: {offset}")
            offset += limit
            if len(data.get('data', [])) == 0 or offset >= total_count:
                break
        logger.debug(f"Total Transactions records fetched: {len(transactions)}")
        return transactions

    def get_seed_data(self, since_date=None):
        seeds = []
        offset = 0
        limit = 200
        while True:
            params = {'offset': offset, 'limit': limit, 'returncount': True}
            if since_date:
                params['filter[]'] = f"date_updated>{since_date}"
            data = self._make_request("14223767938169215907", params=params)
            seeds.extend(data.get('data', []))
            total_count = int(data.get('totalcount', 0))
            logger.debug(f"Seed Data: Fetched {len(data.get('data', []))} records, Total Count: {total_count}, Offset: {offset}")
            offset += limit
            if len(data.get('data', [])) == 0 or offset >= total_count:
                break
        logger.debug(f"Total Seed Data records fetched: {len(seeds)}")
        return seeds