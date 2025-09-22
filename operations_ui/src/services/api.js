// API Service for Operations
// Version: 1.0.0
// Date: 2025-09-20

import axios from 'axios';

// Determine API base URL based on environment and hostname
const getApiBaseUrl = () => {
  // In production or when accessing from remote host
  if (import.meta.env.PROD || window.location.hostname !== 'localhost') {
    // Use HTTPS on port 8443 for production/remote access
    return `https://${window.location.hostname}:8443/api/v1`;
  }
  // In development on localhost
  return '/api/v1';
};

const API_BASE_URL = getApiBaseUrl();

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  }
});

// Add auth token if available
api.interceptors.request.use(config => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Contract Operations
export const contractsAPI = {
  getOpen: (params = {}) => api.get('/contracts/open', { params }),
  getOne: (contractNo) => api.get(`/contracts/${contractNo}/items`),
  createManual: (data) => api.post('/contracts/manual', data),
  assignTag: (data) => api.post('/contracts/assign-tag', data),
  mergeWithPOS: (tempId, posContractNo) =>
    api.post('/contracts/merge-pos', { temp_id: tempId, pos_contract_no: posContractNo })
};

// Item Operations
export const itemsAPI = {
  getAll: (params = {}) => api.get('/items', { params }),
  getOne: (tagId) => api.get(`/items/${tagId}`),
  create: (data) => api.post('/items', data),
  update: (tagId, data) => api.put(`/items/${tagId}`, data),
  delete: (tagId) => api.delete(`/items/${tagId}`),
  search: (params = {}) => api.get('/items/search', { params }),
  // Inventory hierarchy endpoints
  getCategories: (filters = {}) => api.get('/items/categories', { params: filters }),
  getSubcategories: (categoryId, filters = {}) =>
    api.get(`/items/categories/${categoryId}/subcategories`, { params: filters }),
  getCommonNames: (categoryId, subcategoryId, filters = {}) =>
    api.get(`/items/subcategories/${subcategoryId}/common-names`, {
      params: { category_id: categoryId, ...filters }
    }),
  getItems: (params = {}) => api.get('/items/by-rental-class', { params }),
  updateStatus: (tagId, data) => api.patch(`/items/${tagId}/status`, data),
  updateLocation: (tagId, data) => api.patch(`/items/${tagId}/location`, data),
  bulkUpdateStatus: (tagIds, status) =>
    api.post('/items/bulk-update-status', { tag_ids: tagIds, status }),
  // Resale operations
  getResaleItems: (params = {}) => api.get('/items/resale', { params }),
  exportSoldItems: () => api.get('/items/export-sold', { responseType: 'blob' })
};

// Scanning Operations
export const scanAPI = {
  scan: (data) => api.post('/scan', data),
  lookup: (identifier) => api.get(`/scan/lookup/${identifier}`),
  batchScan: (scans) => api.post('/scan/batch', scans)
};

// Sync Operations
export const syncAPI = {
  syncFromManager: (force = false) =>
    api.post('/sync/manager', { source: 'manager_db', force }),
  getSyncStatus: () => api.get('/sync/status')
};

// Service Operations
export const serviceAPI = {
  getServiceItems: (params = {}) => api.get('/service/items', { params }),
  completeService: (tagId, data) => api.post(`/service/${tagId}/complete`, data),
  generateTagCSV: (data) => api.post('/service/generate-tags', data),
  updateSyncedStatus: (tagIds) => api.post('/service/update-synced', { tag_ids: tagIds }),
  getLaundryContracts: () => api.get('/service/laundry-contracts'),
  createLaundryContract: (data) => api.post('/service/laundry-contract', data),
  finalizeLaundryContract: (contractId) => api.post(`/service/laundry-contract/${contractId}/finalize`),
  markLaundryReturned: (contractId) => api.post(`/service/laundry-contract/${contractId}/returned`),
  reactivateLaundryContract: (contractId) => api.post(`/service/laundry-contract/${contractId}/reactivate`),
  addHandCountedItem: (data) => api.post('/service/hand-counted-item', data)
};

// Health Check
export const healthAPI = {
  check: () => api.get('/health')
};

export default api;