import requests
from datetime import datetime
from config import API_USERNAME, API_PASSWORD, LOGIN_URL, ITEM_MASTER_URL, TRANSACTION_URL, SEED_URL

class APIClient:
    def __init__(self):
        self.base_url = "https://cs.iot.ptshome.com/api/v1/data/"
        self.auth_url = LOGIN_URL
        self.token = None
        self.authenticate()

    def authenticate(self):
        response = requests.post(self.auth_url, json={'username': API_USERNAME, 'password': API_PASSWORD})
        response.raise_for_status()
        self.token = response.json().get('access_token')
        print(f"Authenticated successfully with token: {self.token[:10]}...")

    def _make_request(self, endpoint_id, params=None):
        if not self.token:
            self.authenticate()
        headers = {'Authorization': f'Bearer {self.token}'}
        url = f"{self.base_url}{endpoint_id}"
        print(f"Making request to {url} with params: {params}")
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
            total_count = int(data.get('totalcount', 0))
            print(f"Item Master: Fetched {len(data.get('data', []))} records, Total Count: {total_count}, Offset: {offset}")
            offset += limit
            if len(data.get('data', [])) == 0 or offset >= total_count:
                break
        print(f"Total Item Master records fetched: {len(items)}")
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
            print(f"Transactions: Fetched {len(data.get('data', []))} records, Total Count: {total_count}, Offset: {offset}")
            offset += limit
            if len(data.get('data', [])) == 0 or offset >= total_count:
                break
        print(f"Total Transactions records fetched: {len(transactions)}")
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
            print(f"Seed Data: Fetched {len(data.get('data', []))} records, Total Count: {total_count}, Offset: {offset}")
            offset += limit
            if len(data.get('data', [])) == 0 or offset >= total_count:
                break
        print(f"Total Seed Data records fetched: {len(seeds)}")
        return seeds