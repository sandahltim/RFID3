import requests
import time
from datetime import datetime, timedelta
from config import API_USERNAME, API_PASSWORD, LOGIN_URL, ITEM_MASTER_URL, TRANSACTION_URL, SEED_URL
import logging
from urllib.parse import quote

# Configure logging for API client
logger = logging.getLogger(__name__)

class APIClient:
    def __init__(self):
        """Initialize API client with base URL and authentication."""
        self.base_url = "https://cs.iot.ptshome.com/api/v1/data/"
        self.auth_url = LOGIN_URL
        self.item_master_endpoint = "14223767938169344381"  # Endpoint for Item Master operations
        self.token = None
        self.token_expiry = None
        self.authenticate()

    def authenticate(self):
        """Authenticate with the API to obtain an access token."""
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

    def _make_request(self, endpoint_id, params=None, method='GET', data=None):
        """Make an API request with the specified method, endpoint, and data."""
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
                logger.debug(f"Making GET request to full URL: {full_url}")
                logger.debug(f"Request headers: {headers}")
                try:
                    response = requests.get(url, headers=headers, params=params, timeout=20)
                    data = response.json()
                    logger.debug(f"API response: {response.status_code} {response.reason}, response: {data}")
                    if response.status_code == 500:
                        logger.error(f"Server returned 500 Internal Server Error: {data}")
                        raise Exception(f"500 Internal Server Error: {data.get('result', {}).get('message', 'Unknown error')}")
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
                except requests.RequestException as e:
                    logger.error(f"Request failed: {str(e)}")
                    raise
            logger.debug(f"Total records fetched: {len(all_data)}")
            return all_data
        elif method in ['POST', 'PATCH']:
            logger.debug(f"Making {method} request to URL: {url}")
            logger.debug(f"Request headers: {headers}, data: {data}")
            try:
                if method == 'POST':
                    response = requests.post(url, headers=headers, json=data, timeout=20)
                else:
                    response = requests.patch(url, headers=headers, json=data, timeout=20)
                data = response.json()
                logger.debug(f"API response: {response.status_code} {response.reason}, response: {data}")
                if response.status_code == 500:
                    logger.error(f"Server returned 500 Internal Server Error: {data}")
                    raise Exception(f"500 Internal Server Error: {data.get('result', {}).get('message', 'Unknown error')}")
                if response.status_code not in [200, 201]:
                    logger.error(f"Request failed: {response.status_code} {response.reason}, response: {data}")
                    raise Exception(f"{response.status_code} {response.reason}")
                return data
            except requests.RequestException as e:
                logger.error(f"Request failed: {str(e)}")
                raise
        else:
            raise ValueError(f"Unsupported method: {method}")

    def get_item_master(self, since_date=None):
        """Fetch Item Master records, optionally filtered by since_date."""
        params = {}
        if since_date:
            since_date = datetime.fromisoformat(since_date).strftime('%Y-%m-%d %H:%M:%S') if isinstance(since_date, str) else since_date.strftime('%Y-%m-%d %H:%M:%S')
            logger.debug(f"Item master filter since_date: {since_date}")
            filter_str = f"date_last_scanned,gt,'{since_date}'"
            logger.debug(f"Constructed filter string: {filter_str}")
            params['filter[gt]'] = filter_str
        
        try:
            data = self._make_request("14223767938169344381", params)
        except Exception as e:
            logger.warning(f"Filter failed: {str(e)}. Fetching all data and filtering locally.")
            params.pop('filter[gt]', None)
            data = self._make_request("14223767938169344381")
            if since_date:
                since_dt = datetime.strptime(since_date, '%Y-%m-%d %H:%M:%S')
                data = [
                    item for item in data
                    if item.get('date_last_scanned') and datetime.strptime(item['date_last_scanned'], '%Y-%m-%d %H:%M:%S') > since_dt
                ]
        logger.debug(f"Item master data sample: {data[:5] if data else 'No data'}")
        return data

    def get_transactions(self, since_date=None):
        """Fetch transaction records, optionally filtered by since_date."""
        params = {}
        if since_date:
            since_date = datetime.fromisoformat(since_date).strftime('%Y-%m-%d %H:%M:%S') if isinstance(since_date, str) else since_date.strftime('%Y-%m-%d %H:%M:%S')
            logger.debug(f"Transactions filter since_date: {since_date}")
            filter_str = f"date_updated,gt,'{since_date}'"
            logger.debug(f"Constructed filter string: {filter_str}")
            params['filter[gt]'] = filter_str
            try:
                data = self._make_request("14223767938169346196", params)
            except Exception as e:
                logger.warning(f"Filter failed: {str(e)}. Fetching all data and filtering locally.")
                params.pop('filter[gt]', None)
                data = self._make_request("14223767938169346196")
                if since_date:
                    since_dt = datetime.strptime(since_date, '%Y-%m-%d %H:%M:%S')
                    data = [
                        item for item in data
                        if item.get('date_updated') and datetime.strptime(item['date_updated'], '%Y-%m-%d %H:%M:%S') > since_dt
                    ]
        else:
            data = self._make_request("14223767938169346196")
        logger.debug(f"Transactions data sample: {data[:5] if data else 'No data'}")
        return data

    def get_seed_data(self, since_date=None):
        """Fetch seed data (no date filtering supported)."""
        params = {}
        data = self._make_request("14223767938169215907", params)
        logger.debug(f"Seed data sample: {data[:5] if data else 'No data'}")
        return data

    def update_bin_location(self, tag_id, bin_location):
        """Update an item's bin location and date_last_scanned via API PATCH."""
        if not tag_id or not bin_location:
            raise ValueError("tag_id and bin_location are required")

        params = {'filter[eq]': f"tag_id,eq,'{tag_id}'"}
        items = self._make_request(self.item_master_endpoint, params)
        if not items:
            raise Exception(f"Item with tag_id {tag_id} not found in Item Master")

        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        update_data = {
            'tag_id': tag_id,
            'bin_location': bin_location,
            'date_last_scanned': current_time
        }

        response = self._make_request(self.item_master_endpoint, params=params, method='PATCH', data=[update_data])
        logger.info(f"Updated bin_location for tag_id {tag_id} to {bin_location} and date_last_scanned to {current_time} via API")
        return response

    def update_status(self, tag_id, status):
        """Update an item's status and date_last_scanned via API PATCH."""
        if not tag_id or not status:
            raise ValueError("tag_id and status are required")

        params = {'filter[eq]': f"tag_id,eq,'{tag_id}'"}
        items = self._make_request(self.item_master_endpoint, params)
        if not items:
            raise Exception(f"Item with tag_id {tag_id} not found in Item Master")

        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        update_data = {
            'tag_id': tag_id,
            'status': status,
            'date_last_scanned': current_time
        }

        response = self._make_request(self.item_master_endpoint, params=params, method='PATCH', data=[update_data])
        logger.info(f"Updated status for tag_id {tag_id} to {status} and date_last_scanned to {current_time} via API")
        return response

    def update_notes(self, tag_id, notes):
        """Update an item's notes and date_updated via API PATCH."""
        if not tag_id:
            raise ValueError("tag_id is required")

        params = {'filter[eq]': f"tag_id,eq,'{tag_id}'"}
        items = self._make_request(self.item_master_endpoint, params)
        if not items:
            raise Exception(f"Item with tag_id {tag_id} not found in Item Master")

        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        update_data = {
            'tag_id': tag_id,
            'notes': notes if notes else '',
            'date_updated': current_time
        }

        response = self._make_request(self.item_master_endpoint, params=params, method='PATCH', data=[update_data])
        logger.info(f"Updated notes for tag_id {tag_id} to '{notes}' and date_updated to {current_time} via API")
        return response

    def insert_item(self, item_data):
        """Insert a new item into Item Master via API POST."""
        if not item_data or 'tag_id' not in item_data:
            raise ValueError("item_data must contain a tag_id")

        response = self._make_request(self.item_master_endpoint, method='POST', data=[item_data])
        logger.info(f"Inserted new item with tag_id {item_data['tag_id']} into API via POST")
        return response