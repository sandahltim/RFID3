# app/services/api_client.py
# api_client.py version: 2025-06-26-v4
import requests
import time
from datetime import datetime, timedelta
from config import API_USERNAME, API_PASSWORD, LOGIN_URL, INCREMENTAL_FALLBACK_SECONDS
import logging
from urllib.parse import quote
from .. import cache

# Configure logging
logger = logging.getLogger('api_client')
logger.setLevel(logging.INFO)
logger.handlers = []
file_handler = logging.FileHandler('/home/tim/test_rfidpi/logs/rfid_dashboard.log')
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

class APIClient:
    def __init__(self):
        self.base_url = "https://cs.iot.ptshome.com/api/v1/data/"
        self.auth_url = LOGIN_URL
        self.item_master_endpoint = "14223767938169344381"
        self.token = None
        self.token_expiry = None
        self.authenticate()

    def authenticate(self):
        payload = {"username": API_USERNAME, "password": API_PASSWORD}
        for attempt in range(5):
            try:
                logger.debug(f"Requesting token from {self.auth_url}")
                response = requests.post(self.auth_url, json=payload, timeout=20)
                data = response.json()
                logger.debug(f"Token attempt {attempt + 1}: Status {response.status_code}")
                if response.status_code == 200 and data.get('result'):
                    self.token = data.get('access_token')
                    self.token_expiry = datetime.now() + timedelta(minutes=30)
                    logger.debug(f"Access token received: expires {self.token_expiry}")
                    return
                else:
                    logger.error(f"Token attempt {attempt + 1} failed: {response.status_code}")
                    if attempt < 4:
                        time.sleep(3)
            except requests.RequestException as e:
                logger.error(f"Token attempt {attempt + 1} failed: {str(e)}")
                if attempt < 4:
                    time.sleep(3)
        logger.error("Failed to fetch access token after 5 attempts")
        raise Exception("Failed to fetch access token after 5 attempts")

    def _make_request(self, endpoint_id, params=None, method='GET', data=None, timeout=20):
        if not params:
            params = {}
        if method == 'GET':
            params['offset'] = params.get('offset', 0)
            params['limit'] = params.get('limit', 200)
            params['returncount'] = params.get('returncount', True)

        if self.token_expiry and datetime.now() >= self.token_expiry:
            self.authenticate()

        headers = {"Authorization": f"Bearer {self.token}"}
        url = f"{self.base_url}{endpoint_id}"

        if method == 'GET':
            all_data = []
            while True:
                query_string = '&'.join([f"{k}={quote(str(v))}" for k, v in params.items()])
                full_url = f"{url}?{query_string}"
                logger.debug(f"Making GET request: {full_url}")
                try:
                    response = requests.get(url, headers=headers, params=params, timeout=timeout)
                    data = response.json()
                    if response.status_code == 500:
                        logger.error(f"Server error: {data}")
                        raise Exception(f"500 Internal Server Error: {data.get('result', {}).get('message', 'Unknown error')}")
                    if response.status_code != 200:
                        logger.error(f"Request failed: {response.status_code} {response.reason}")
                        raise Exception(f"{response.status_code} {response.reason}")
                    records = data.get('data', [])
                    total_count = data.get('totalcount', 0)
                    offset = params['offset']
                    logger.debug(f"Fetched {len(records)} records, Total: {total_count}, Offset: {offset}")
                    all_data.extend(records)
                    if len(records) < params['limit'] or offset + len(records) >= total_count:
                        break
                    params['offset'] += len(records)
                except requests.RequestException as e:
                    logger.error(f"Request failed: {str(e)}")
                    raise
            logger.debug(f"Total records fetched: {len(all_data)}")
            return all_data
        elif method in ['POST', 'PATCH']:
            with cache.lock("user_operation_lock", timeout=30):
                logger.debug(f"Making {method} request to URL: {url}")
                try:
                    if method == 'POST':
                        response = requests.post(url, headers=headers, json=data, timeout=timeout)
                    else:
                        response = requests.patch(url, headers=headers, json=data, timeout=timeout)
                    data = response.json()
                    if response.status_code == 500:
                        logger.error(f"Server error: {data}")
                        raise Exception(f"500 Internal Server Error: {data.get('result', {}).get('message', 'Unknown error')}")
                    if response.status_code not in [200, 201]:
                        logger.error(f"Request failed: {response.status_code} {response.reason}")
                        raise Exception(f"{response.status_code} {response.reason}")
                    return data
                except requests.RequestException as e:
                    logger.error(f"Request failed: {str(e)}")
                    raise
        else:
            raise ValueError(f"Unsupported method: {method}")

    def validate_date(self, date_str, field_name):
        if date_str is None or date_str == '0000-00-00 00:00:00':
            logger.debug(f"Null or invalid {field_name}: {date_str}, returning None")
            return None
        try:
            return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            try:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except ValueError as e:
                logger.warning(f"Invalid {field_name}: {date_str}. Error: {str(e)}. Returning None.")
                return None

    def get_item_master(self, since_date=None):
        params = {}
        all_data = []
        if since_date:
            since_date_str = since_date.strftime('%Y-%m-%d %H:%M:%S') if isinstance(since_date, datetime) else since_date
            logger.debug(f"Item master filter since_date: {since_date_str}")
            filter_str = f"date_last_scanned,gt,'{since_date_str}'"
            params['filter[gt]'] = filter_str
        
        try:
            data = self._make_request("14223767938169344381", params, timeout=20)
            all_data = data
            logger.info(f"Fetched {len(all_data)} items with since_date filter")
            if len(all_data) < 10000 and since_date:
                logger.warning(f"Only {len(all_data)} items fetched with since_date filter, trying without filter")
                params.pop('filter[gt]', None)
                all_data = self._make_request("14223767938169344381", params, timeout=20)
                logger.info(f"Fetched {len(all_data)} items without since_date filter")
        except Exception as e:
            logger.warning(f"Filter failed: {str(e)}. Fetching all data and filtering locally for last {INCREMENTAL_FALLBACK_SECONDS} seconds.")
            params.pop('filter[gt]', None)
            all_data = self._make_request("14223767938169344381", timeout=20)
            if since_date:
                since_dt = self.validate_date(since_date_str, 'since_date')
                if since_dt:
                    fallback_dt = datetime.utcnow() - timedelta(seconds=INCREMENTAL_FALLBACK_SECONDS)
                    all_data = [
                        item for item in all_data
                        if item.get('date_last_scanned') is None or 
                        (
                            self.validate_date(item.get('date_last_scanned'), 'date_last_scanned') and
                            self.validate_date(item.get('date_last_scanned'), 'date_last_scanned') > max(since_dt, fallback_dt)
                        )
                    ]
                    logger.info(f"Filtered to {len(all_data)} items locally after fetching all")
        return all_data

    def get_transactions(self, since_date=None):
        params = {}
        all_data = []
        if since_date:
            since_date_str = since_date.strftime('%Y-%m-%d %H:%M:%S') if isinstance(since_date, datetime) else since_date
            logger.debug(f"Transactions filter since_date: {since_date_str}")
            filter_str = f"scan_date,gt,'{since_date_str}'"
            params['filter[gt]'] = filter_str
            try:
                data = self._make_request("14223767938169346196", params, timeout=20)
                all_data = data
                logger.info(f"Fetched {len(all_data)} transactions with since_date filter")
                if len(all_data) < 10000 and since_date:
                    logger.warning(f"Only {len(all_data)} transactions fetched with since_date filter, trying without filter")
                    params.pop('filter[gt]', None)
                    all_data = self._make_request("14223767938169346196", params, timeout=20)
                    logger.info(f"Fetched {len(all_data)} transactions without since_date filter")
            except Exception as e:
                logger.warning(f"Filter failed: {str(e)}. Fetching all data and filtering locally for last {INCREMENTAL_FALLBACK_SECONDS} seconds.")
                params.pop('filter[gt]', None)
                all_data = self._make_request("14223767938169346196", timeout=20)
                if since_date:
                    since_dt = self.validate_date(since_date_str, 'since_date')
                    if since_dt:
                        fallback_dt = datetime.utcnow() - timedelta(seconds=INCREMENTAL_FALLBACK_SECONDS)
                        all_data = [
                            item for item in all_data
                            if item.get('scan_date') is None or 
                            (
                                self.validate_date(item.get('scan_date'), 'scan_date') and
                                self.validate_date(item.get('scan_date'), 'scan_date') > max(since_dt, fallback_dt)
                            )
                        ]
                        logger.info(f"Filtered to {len(all_data)} transactions locally after fetching all")
        else:
            all_data = self._make_request("14223767938169346196", timeout=20)
            logger.info(f"Fetched {len(all_data)} transactions without filter")
        return all_data

    def get_seed_data(self, since_date=None):
        params = {}
        data = self._make_request("14223767938169215907", params, timeout=20)
        logger.info(f"Fetched {len(data)} seed rental classes")
        return data

    def update_bin_location(self, tag_id, bin_location, timeout=20):
        if not tag_id or not bin_location:
            raise ValueError("tag_id and bin_location are required")

        params = {'filter[eq]': f"tag_id,eq,'{tag_id}'"}
        items = self._make_request(self.item_master_endpoint, params, timeout=timeout)
        if not items:
            raise Exception(f"Item with tag_id {tag_id} not found in Item Master")

        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        update_data = [{
            'tag_id': tag_id,
            'bin_location': bin_location,
            'date_last_scanned': current_time
        }]

        response = self._make_request(self.item_master_endpoint, params=params, method='PATCH', data=update_data, timeout=timeout)
        logger.info(f"Updated bin_location for tag_id {tag_id} to {bin_location} via API")
        return response

    def update_status(self, tag_id, status, timeout=20):
        if not tag_id or not status:
            raise ValueError("tag_id and status are required")

        params = {'filter[eq]': f"tag_id,eq,'{tag_id}'"}
        items = self._make_request(self.item_master_endpoint, params, timeout=timeout)
        if not items:
            raise Exception(f"Item with tag_id {tag_id} not found in Item Master")

        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        update_data = [{
            'tag_id': tag_id,
            'status': status,
            'date_last_scanned': current_time
        }]

        response = self._make_request(self.item_master_endpoint, params=params, method='PATCH', data=update_data, timeout=timeout)
        logger.info(f"Updated status for tag_id {tag_id} to {status} via API")
        return response

    def update_notes(self, tag_id, notes):
        if not tag_id:
            raise ValueError("tag_id is required")

        params = {'filter[eq]': f"tag_id,eq,'{tag_id}'"}
        items = self._make_request(self.item_master_endpoint, params)
        if not items:
            raise Exception(f"Item with tag_id {tag_id} not found in Item Master")

        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        update_data = [{
            'tag_id': tag_id,
            'notes': notes if notes else '',
            'date_updated': current_time
        }]

        response = self._make_request(self.item_master_endpoint, params=params, method='PATCH', data=update_data)
        logger.info(f"Updated notes for tag_id {tag_id} to '{notes}' via API")
        return response

    def insert_item(self, item_data, timeout=20):
        if not item_data or 'tag_id' not in item_data:
            raise ValueError("item_data must contain a tag_id")

        response = self._make_request(self.item_master_endpoint, method='POST', data=[item_data], timeout=timeout)
        logger.info(f"Inserted new item with tag_id {item_data['tag_id']} via API")
        return response