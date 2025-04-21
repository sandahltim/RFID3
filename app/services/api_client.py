import requests
import time
from datetime import datetime, timedelta
from config import API_USERNAME, API_PASSWORD, LOGIN_URL, ITEM_MASTER_URL, TRANSACTION_URL, SEED_URL
import logging
from urllib.parse import quote
import os
import getpass

logger = logging.getLogger(__name__)

class APIClient:
    def __init__(self):
        self.base_url = "https://cs.iot.ptshome.com/api/v1/data/"
        self.auth_url = LOGIN_URL
        self.token = None
        self.token_expiry = None
        self.authenticate()

    def authenticate(self):
        payload = {"username": API_USERNAME, "password": API_PASSWORD}
        for attempt in range(5):
            try:
                logger.debug(f"Requesting token from {self.auth_url} with username={API_USERNAME}")
                response = requests.post(self.auth_url, json=payload, timeout=20)
                data = response.json()
                logger.debug(f"Token attempt {attempt + 1}: Status {response.status_code}, Response: {data}")
                if response.status_code == 200 and data.get('result'):
                    self.token = data.get('access_token')
                    self.token_expiry = datetime.now() + timedelta(minutes=30)
                    logger.debug(f"Access token received: {self.token} (expires {self.token_expiry})")
                    return
                else:
                    logger.error(f"Token attempt {attempt + 1} failed: {response.status_code} {response.reason}, response: {data}")
                    if attempt < 4:
                        time.sleep(3)
            except requests.RequestException as e:
                logger.error(f"Token attempt {attempt + 1} failed with exception: {str(e)}")
                if attempt < 4:
                    time.sleep(3)
        logger.error("Failed to fetch access token after 5 attempts")
        raise Exception("Failed to fetch access token after 5 attempts")

    def _make_request(self, endpoint_id, params=None):
        if not params:
            params = {}
        params['offset'] = params.get('offset', 0)
        params['limit'] = params.get('limit', 200)
        params['returncount'] = params.get('returncount', True)

        if self.token_expiry and datetime.now() >= self.token_expiry:
            self.authenticate()

        headers = {"Authorization": f"Bearer {self.token}"}
        url = f"{self.base_url}{endpoint_id}"
        all_data = []
        while True:
            query_string = '&'.join([f"{k}={quote(str(v))}" for k, v in params.items()])
            full_url = f"{url}?{query_string}"
            logger.debug(f"Making request to full URL: {full_url}")
            logger.debug(f"Request headers: {headers}")
            response = requests.get(url, headers=headers, params=params, timeout=20)
            data = response.json()
            logger.debug(f"API response: {response.status_code} {response.reason}, response: {data}")
            if response.status_code != 200:
                logger.error(f"Request failed: {response.status_code} {response.reason}, response: {data}")
                raise Exception(f"{response.status_code} {response.reason}")
            records = data.get('data', [])
            total_count = data.get('totalcount', 0)
            offset = params['offset']
            logger.debug(f"Fetched {len(records)} records, Total Count: {total_count}, Offset: {offset}")
            all_data.extend(records)
            if len(records) < params['limit'] or offset + len(records) >= total_count:
                break
            params['offset'] += len(records)
        logger.debug(f"Total records fetched: {len(all_data)}")
        return all_data

    def get_item_master(self, since_date=None):
        params = {}
        if since_date:
            since_date = datetime.fromisoformat(since_date).strftime('%Y-%m-%d %H:%M:%S') if isinstance(since_date, str) else since_date.strftime('%Y-%m-%d %H:%M:%S')
        else:
            since_date = (datetime.now() - timedelta(seconds=30)).strftime('%Y-%m-%d %H:%M:%S')
        logger.debug(f"Item master filter since_date: {since_date}")
        filter_str = f"date_last_scanned,gt,'{since_date}'"
        logger.debug(f"Constructed filter string: {filter_str}")
        params['filter[gt]'] = filter_str  // Use filter[gt] instead of filter[]
        
        try:
            data = self._make_request("14223767938169344381", params)
        except Exception as e:
            logger.warning(f"Filter failed: {str(e)}. Fetching all data and filtering locally.")
            data = self._make_request("14223767938169344381")
            if since_date:
                since_dt = datetime.strptime(since_date, '%Y-%m-%d %H:%M:%S')
                data = [
                    item for item in data
                    if item.get('date_last_scanned') and datetime.strptime(item['date_last_scanned'], '%Y-%m-%d %H:%M:%S') > since_dt
                ]
        return data

    def get_transactions(self, since_date=None):
        params = {}
        if since_date:
            since_date = datetime.fromisoformat(since_date).strftime('%Y-%m-%d %H:%M:%S') if isinstance(since_date, str) else since_date.strftime('%Y-%m-%d %H:%M:%S')
            logger.debug(f"Transactions filter since_date: {since_date}")
            filter_str = f"date_last_scanned,gt,'{since_date}'"  // Use date_last_scanned as per item master
            logger.debug(f"Constructed filter string: {filter_str}")
            params['filter[gt]'] = filter_str  // Use filter[gt] instead of filter[]
            try:
                data = self._make_request("14223767938169346196", params)
            except Exception as e:
                logger.warning(f"Filter failed: {str(e)}. Fetching all data and filtering locally.")
                data = self._make_request("14223767938169346196")
                if since_date:
                    since_dt = datetime.strptime(since_date, '%Y-%m-%d %H:%M:%S')
                    data = [
                        item for item in data
                        if item.get('date_updated') and datetime.strptime(item['date_updated'], '%Y-%m-%d %H:%M:%S') > since_dt
                    ]
                return data
        else:
            data = self._make_request("14223767938169346196")
        return data

    def get_seed_data(self, since_date=None):
        params = {}
        // Remove filter for seed data to avoid errors
        data = self._make_request("14223767938169215907", params)
        if since_date:
            since_date = datetime.fromisoformat(since_date).strftime('%Y-%m-%d %H:%M:%S') if isinstance(since_date, str) else since_date.strftime('%Y-%m-%d %H:%M:%S')
            logger.debug(f"Seed data filter since_date: {since_date}")
            since_dt = datetime.strptime(since_date, '%Y-%m-%d %H:%M:%S')
            data = [
                item for item in data
                if item.get('date_updated') and datetime.strptime(item['date_updated'], '%Y-%m-%d %H:%M:%S') > since_dt
            ]
        return data