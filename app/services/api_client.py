import requests
import os
from datetime import datetime

class APIClient:
    def __init__(self):
        self.base_url = "https://cs.iot.ptshome.com/api/v1/data/"
        self.auth_url = "https://login.cloud.ptshome.com/api/v1/login"
        self.token = None
        self.authenticate()

    def authenticate(self):
        username = os.environ.get('API_USERNAME', 'your_username')
        password = os.environ.get('API_PASSWORD', 'your_password')
        response = requests.post(self.auth_url, json={'username': username, 'password': password})
        response.raise_for_status()
        self.token = response.json().get('access_token')

    def _make_request(self, endpoint_id, params=None):
        if not self.token:
            self.authenticate()
        headers = {'Authorization': f'Bearer {self.token}'}
        url = f"{self.base_url}{endpoint_id}"
        response = requests.get(url, headers=headers, params=params)
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
            total_count = int(data.get('totalcount', 0))  # Ensure totalcount is an integer
            offset += limit
            if offset >= total_count:
                break
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
            offset += limit
            if offset >= total_count:
                break
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
            offset += limit
            if offset >= total_count:
                break
        return seeds