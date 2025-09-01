# Performance Optimization Strategy for Predictive Analytics
**Version**: 1.0  
**Date**: August 31, 2025  
**Target Environment**: Raspberry Pi 5 (8GB RAM, 4-core ARM64)

## 🎯 Performance Objectives

### Primary Targets
- **API Response Time**: <2 seconds for all prediction endpoints
- **System Uptime**: >99.5% availability
- **Memory Usage**: <6GB total system memory (75% of available)
- **CPU Usage**: <80% average during peak operations
- **Prediction Accuracy**: Maintain >75% accuracy while optimizing speed
- **Concurrent Users**: Support 50+ concurrent API requests

### Performance Constraints
- **Hardware Limitations**: 8GB RAM, 4-core ARM Cortex-A76
- **Storage**: Limited I/O bandwidth on SD card/SSD
- **Network**: Variable latency for external API calls
- **Power**: Thermal throttling considerations
- **Real-time Requirements**: Sub-second inference for cached predictions

---

## 🧠 Memory Optimization Strategy

### 1. Memory Allocation Plan

```python
# Memory budget allocation (8GB total)
MEMORY_ALLOCATION = {
    "system_os": "1.5GB",           # Ubuntu + system processes
    "mysql_database": "2.0GB",      # MySQL buffer pool + connections
    "redis_cache": "1.5GB",         # Prediction cache + session storage
    "flask_application": "1.0GB",   # Main application + workers
    "ml_models": "1.0GB",           # Loaded ML models in memory
    "feature_processing": "0.5GB",  # Feature engineering pipeline
    "system_buffer": "0.5GB"       # Emergency buffer + monitoring
}
```

### 2. Dynamic Memory Management

```python
# /app/services/performance/memory_manager.py
import psutil
import gc
import threading
from typing import Dict, Any
from app.services.logger import get_logger

class MemoryManager:
    """Dynamic memory management for predictive analytics"""
    
    def __init__(self):
        self.logger = get_logger("memory_manager")
        self.memory_thresholds = {
            "warning": 0.75,    # 75% memory usage
            "critical": 0.85,   # 85% memory usage
            "emergency": 0.95   # 95% memory usage
        }
        self.model_cache = {}
        self.feature_cache = {}
        self.monitoring_active = True
        
    async def monitor_memory_usage(self):
        """Continuous memory monitoring and optimization"""
        while self.monitoring_active:
            memory = psutil.virtual_memory()
            usage_percent = memory.percent / 100.0
            
            if usage_percent > self.memory_thresholds["critical"]:
                await self._emergency_memory_cleanup()
            elif usage_percent > self.memory_thresholds["warning"]:
                await self._proactive_memory_cleanup()
            
            await asyncio.sleep(30)  # Check every 30 seconds
    
    async def _emergency_memory_cleanup(self):
        """Emergency memory cleanup procedures"""
        self.logger.warning("Emergency memory cleanup initiated")
        
        # 1. Clear oldest model cache entries
        await self._cleanup_model_cache(keep_ratio=0.3)
        
        # 2. Clear feature cache
        await self._cleanup_feature_cache(keep_ratio=0.1)
        
        # 3. Force garbage collection
        gc.collect()
        
        # 4. Clear prediction cache (except critical)
        await self._cleanup_prediction_cache(priority_only=True)
        
    async def _proactive_memory_cleanup(self):
        """Proactive memory management"""
        self.logger.info("Proactive memory cleanup initiated")
        
        # 1. Clean old feature cache entries
        await self._cleanup_feature_cache(keep_ratio=0.5)
        
        # 2. Unload least-used models
        await self._optimize_model_cache()
        
        # 3. Garbage collection
        gc.collect()
    
    async def _cleanup_model_cache(self, keep_ratio: float = 0.5):
        """Clean up model cache, keeping most frequently used"""
        if not self.model_cache:
            return
            
        # Sort by usage frequency
        sorted_models = sorted(
            self.model_cache.items(),
            key=lambda x: x[1].get('usage_count', 0),
            reverse=True
        )
        
        keep_count = max(1, int(len(sorted_models) * keep_ratio))
        
        # Remove least used models
        for model_key, _ in sorted_models[keep_count:]:
            del self.model_cache[model_key]
            self.logger.info(f"Unloaded model from cache: {model_key}")
    
    def get_memory_usage_report(self) -> Dict[str, Any]:
        """Get detailed memory usage report"""
        memory = psutil.virtual_memory()
        return {
            "total_memory_gb": round(memory.total / (1024**3), 2),
            "available_memory_gb": round(memory.available / (1024**3), 2),
            "used_memory_gb": round(memory.used / (1024**3), 2),
            "usage_percentage": round(memory.percent, 1),
            "model_cache_size": len(self.model_cache),
            "feature_cache_size": len(self.feature_cache),
            "status": self._get_memory_status(memory.percent)
        }
    
    def _get_memory_status(self, usage_percent: float) -> str:
        """Get memory status based on usage"""
        if usage_percent > 85:
            return "critical"
        elif usage_percent > 75:
            return "warning"
        else:
            return "healthy"
```

### 3. Model Loading Strategy

```python
# /app/services/performance/lazy_model_loader.py
from typing import Dict, Any, Optional
import joblib
import threading
from datetime import datetime, timedelta

class LazyModelLoader:
    """Lazy loading and unloading of ML models"""
    
    def __init__(self):
        self.loaded_models = {}
        self.model_metadata = {}
        self.usage_tracking = {}
        self.max_loaded_models = 5
        
    async def get_model(self, service_name: str, model_type: str, version: str = None):
        """Get model with lazy loading"""
        model_key = f"{service_name}_{model_type}_{version or 'latest'}"
        
        # Check if already loaded
        if model_key in self.loaded_models:
            self._update_usage(model_key)
            return self.loaded_models[model_key]
        
        # Load model if cache has space
        if len(self.loaded_models) < self.max_loaded_models:
            model = await self._load_model(model_key)
            self.loaded_models[model_key] = model
            self._update_usage(model_key)
            return model
        
        # Unload least recently used model
        await self._unload_lru_model()
        
        # Load requested model
        model = await self._load_model(model_key)
        self.loaded_models[model_key] = model
        self._update_usage(model_key)
        return model
    
    async def _unload_lru_model(self):
        """Unload least recently used model"""
        if not self.loaded_models:
            return
            
        # Find LRU model
        lru_key = min(
            self.usage_tracking.keys(),
            key=lambda k: self.usage_tracking[k]['last_used']
        )
        
        # Unload model
        del self.loaded_models[lru_key]
        self.logger.info(f"Unloaded LRU model: {lru_key}")
    
    def _update_usage(self, model_key: str):
        """Update model usage statistics"""
        now = datetime.now()
        if model_key not in self.usage_tracking:
            self.usage_tracking[model_key] = {
                'usage_count': 0,
                'first_used': now,
                'last_used': now
            }
        
        self.usage_tracking[model_key]['usage_count'] += 1
        self.usage_tracking[model_key]['last_used'] = now
```

---

## ⚡ CPU Optimization Strategy

### 1. Asynchronous Processing

```python
# /app/services/performance/async_processor.py
import asyncio
import concurrent.futures
from typing import List, Callable, Any
import multiprocessing as mp

class AsyncProcessor:
    """Asynchronous processing for CPU-intensive tasks"""
    
    def __init__(self):
        self.cpu_cores = mp.cpu_count()
        self.thread_pool = concurrent.futures.ThreadPoolExecutor(
            max_workers=min(4, self.cpu_cores)
        )
        self.process_pool = concurrent.futures.ProcessPoolExecutor(
            max_workers=max(1, self.cpu_cores - 1)  # Leave 1 core for system
        )
        
    async def run_cpu_intensive_task(self, func: Callable, *args, **kwargs):
        """Run CPU intensive task in process pool"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.process_pool, func, *args, **kwargs)
    
    async def run_io_intensive_task(self, func: Callable, *args, **kwargs):
        """Run I/O intensive task in thread pool"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.thread_pool, func, *args, **kwargs)
    
    async def batch_process_predictions(self, prediction_requests: List[Dict], 
                                      batch_size: int = 10):
        """Process predictions in batches to optimize CPU usage"""
        results = []
        
        for i in range(0, len(prediction_requests), batch_size):
            batch = prediction_requests[i:i + batch_size]
            
            # Process batch asynchronously
            batch_tasks = [
                self._process_single_prediction(request)
                for request in batch
            ]
            
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            results.extend(batch_results)
            
            # Small delay between batches to prevent CPU overload
            await asyncio.sleep(0.01)
        
        return results
```

### 2. Model Inference Optimization

```python
# /app/services/performance/optimized_inference.py
import numpy as np
from sklearn.base import BaseEstimator
from typing import Union, List
import pickle

class OptimizedInferenceEngine:
    """Optimized inference engine for ML models"""
    
    def __init__(self):
        self.model_cache = {}
        self.feature_scalers = {}
        self.prediction_cache = {}
        
    async def predict_batch(self, model_key: str, features_batch: np.ndarray) -> np.ndarray:
        """Optimized batch prediction"""
        # Use vectorized operations for batch processing
        model = await self._get_cached_model(model_key)
        
        # Pre-process features in batch
        scaled_features = await self._batch_scale_features(model_key, features_batch)
        
        # Batch prediction (most efficient)
        predictions = model.predict(scaled_features)
        
        return predictions
    
    async def predict_single_optimized(self, model_key: str, features: np.ndarray) -> float:
        """Optimized single prediction with caching"""
        # Check prediction cache first
        feature_hash = hash(features.tobytes())
        cache_key = f"{model_key}_{feature_hash}"
        
        if cache_key in self.prediction_cache:
            return self.prediction_cache[cache_key]
        
        # Perform prediction
        model = await self._get_cached_model(model_key)
        scaled_features = await self._scale_features(model_key, features.reshape(1, -1))
        prediction = model.predict(scaled_features)[0]
        
        # Cache result with TTL
        self.prediction_cache[cache_key] = prediction
        
        # Limit cache size
        if len(self.prediction_cache) > 1000:
            # Remove oldest 200 entries
            oldest_keys = list(self.prediction_cache.keys())[:200]
            for key in oldest_keys:
                del self.prediction_cache[key]
        
        return prediction
    
    async def _batch_scale_features(self, model_key: str, features_batch: np.ndarray) -> np.ndarray:
        """Efficient batch feature scaling"""
        if model_key in self.feature_scalers:
            scaler = self.feature_scalers[model_key]
            return scaler.transform(features_batch)
        return features_batch
```

---

## 📊 Database Optimization Strategy

### 1. Query Optimization

```sql
-- Optimized indexes for predictive analytics queries
CREATE INDEX idx_predictions_composite 
ON analytics_predictions(prediction_type, target_item_id, prediction_date)
PARTITION BY RANGE (YEAR(prediction_date));

CREATE INDEX idx_feature_store_optimized
ON ml_feature_store(feature_name, target_entity, feature_timestamp)
PARTITION BY RANGE (TO_DAYS(feature_timestamp));

CREATE INDEX idx_transactions_analytics
ON id_transactions(tag_id, scan_date, scan_type)
WHERE scan_date >= DATE_SUB(CURRENT_DATE, INTERVAL 2 YEAR);

-- Materialized view for frequent aggregate queries
CREATE VIEW demand_analytics_mv AS
SELECT 
    im.rental_class_num,
    DATE(t.scan_date) as scan_date,
    COUNT(CASE WHEN t.scan_type = 'out' THEN 1 END) as daily_demand,
    COUNT(CASE WHEN t.scan_type = 'return' THEN 1 END) as daily_returns,
    AVG(CASE WHEN t.scan_type = 'out' THEN 1 ELSE 0 END) as demand_rate
FROM id_item_master im
JOIN id_transactions t ON im.tag_id = t.tag_id
WHERE t.scan_date >= DATE_SUB(CURRENT_DATE, INTERVAL 365 DAY)
GROUP BY im.rental_class_num, DATE(t.scan_date);
```

### 2. Connection Pool Optimization

```python
# /app/services/performance/db_optimizer.py
from sqlalchemy.pool import QueuePool
from sqlalchemy import create_engine
import asyncio

class DatabaseOptimizer:
    """Database connection and query optimization"""
    
    def __init__(self):
        self.connection_pools = {}
        self.query_cache = {}
        
    def create_optimized_engine(self, db_url: str):
        """Create optimized database engine"""
        return create_engine(
            db_url,
            poolclass=QueuePool,
            pool_size=5,                    # Reduced for Pi 5
            max_overflow=10,                # Allow burst capacity
            pool_timeout=30,                # Connection timeout
            pool_recycle=3600,              # Recycle connections hourly
            pool_pre_ping=True,             # Validate connections
            echo=False,                     # Disable query logging in production
            connect_args={
                "charset": "utf8mb4",
                "autocommit": False,
                "connect_timeout": 10
            }
        )
    
    async def execute_optimized_query(self, query: str, params: dict = None):
        """Execute query with optimization strategies"""
        # Check query cache
        cache_key = hash(f"{query}_{str(params)}")
        if cache_key in self.query_cache:
            cache_entry = self.query_cache[cache_key]
            if not cache_entry.is_expired():
                return cache_entry.result
        
        # Execute query
        result = await self._execute_query(query, params)
        
        # Cache result if appropriate
        if self._should_cache_query(query):
            self.query_cache[cache_key] = QueryCacheEntry(result, ttl=300)
        
        return result
    
    def optimize_mysql_config(self) -> dict:
        """MySQL configuration optimized for Pi 5"""
        return {
            "innodb_buffer_pool_size": "1.5G",     # 20% of total RAM
            "innodb_log_file_size": "256M",
            "innodb_flush_log_at_trx_commit": 2,   # Better performance
            "query_cache_size": "128M",
            "query_cache_type": 1,
            "max_connections": 50,                  # Limited for Pi 5
            "thread_cache_size": 8,
            "table_open_cache": 1000,
            "sort_buffer_size": "2M",
            "read_buffer_size": "1M",
            "innodb_io_capacity": 200,              # SSD optimized
            "innodb_read_io_threads": 2,
            "innodb_write_io_threads": 2
        }
```

---

## 🚀 Caching Strategy

### 1. Multi-level Caching Architecture

```python
# /app/services/performance/cache_manager.py
from typing import Any, Optional, Dict
import json
import hashlib
from datetime import datetime, timedelta
import pickle

class MultiLevelCacheManager:
    """Multi-level caching for optimal performance"""
    
    def __init__(self):
        # Level 1: In-memory dictionary (fastest)
        self.memory_cache = {}
        self.memory_cache_max_size = 500
        
        # Level 2: Redis cache (fast)
        self.redis_cache = cache
        
        # Level 3: Database cache tables (persistent)
        self.db = db
        
        # Cache statistics
        self.stats = {
            "l1_hits": 0,
            "l2_hits": 0,
            "l3_hits": 0,
            "misses": 0
        }
    
    async def get(self, key: str, cache_levels: List[str] = ["l1", "l2", "l3"]) -> Optional[Any]:
        """Get value from multi-level cache"""
        
        # Level 1: Memory cache
        if "l1" in cache_levels and key in self.memory_cache:
            entry = self.memory_cache[key]
            if not entry.is_expired():
                self.stats["l1_hits"] += 1
                return entry.value
            else:
                del self.memory_cache[key]
        
        # Level 2: Redis cache
        if "l2" in cache_levels:
            redis_value = await self.redis_cache.get(f"cache:{key}")
            if redis_value:
                value = pickle.loads(redis_value)
                # Promote to L1 cache
                await self.set_l1(key, value, ttl=300)
                self.stats["l2_hits"] += 1
                return value
        
        # Level 3: Database cache
        if "l3" in cache_levels:
            db_value = await self._get_from_db_cache(key)
            if db_value:
                # Promote to L2 and L1
                await self.set_l2(key, db_value, ttl=1800)
                await self.set_l1(key, db_value, ttl=300)
                self.stats["l3_hits"] += 1
                return db_value
        
        self.stats["misses"] += 1
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 300):
        """Set value in all cache levels"""
        await self.set_l1(key, value, ttl)
        await self.set_l2(key, value, ttl * 2)  # Longer TTL for L2
        await self.set_l3(key, value, ttl * 6)  # Even longer for L3
    
    async def set_l1(self, key: str, value: Any, ttl: int):
        """Set value in memory cache"""
        # Implement LRU eviction if needed
        if len(self.memory_cache) >= self.memory_cache_max_size:
            await self._evict_lru_memory()
        
        self.memory_cache[key] = CacheEntry(value, ttl)
    
    async def set_l2(self, key: str, value: Any, ttl: int):
        """Set value in Redis cache"""
        serialized_value = pickle.dumps(value)
        await self.redis_cache.setex(f"cache:{key}", ttl, serialized_value)
    
    async def set_l3(self, key: str, value: Any, ttl: int):
        """Set value in database cache"""
        expiry_time = datetime.now() + timedelta(seconds=ttl)
        
        query = text("""
            INSERT INTO prediction_cache (cache_key, cache_value, expiry_time, created_at)
            VALUES (:key, :value, :expiry, NOW())
            ON DUPLICATE KEY UPDATE
            cache_value = VALUES(cache_value),
            expiry_time = VALUES(expiry_time),
            updated_at = NOW()
        """)
        
        await self.db.session.execute(query, {
            "key": key,
            "value": json.dumps(value, default=str),
            "expiry": expiry_time
        })
        await self.db.session.commit()
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        total_requests = sum(self.stats.values())
        if total_requests == 0:
            return {"cache_hit_rate": 0.0}
        
        hit_rate = (total_requests - self.stats["misses"]) / total_requests
        
        return {
            "cache_hit_rate": round(hit_rate, 3),
            "l1_hit_rate": round(self.stats["l1_hits"] / total_requests, 3),
            "l2_hit_rate": round(self.stats["l2_hits"] / total_requests, 3),
            "l3_hit_rate": round(self.stats["l3_hits"] / total_requests, 3),
            "total_requests": total_requests,
            "memory_cache_size": len(self.memory_cache)
        }
```

### 2. Prediction-Specific Caching

```python
# /app/services/performance/prediction_cache.py
class PredictionCacheManager:
    """Specialized caching for predictions"""
    
    def __init__(self):
        self.cache_manager = MultiLevelCacheManager()
        
    async def cache_prediction(self, request: PredictionRequest, 
                             result: PredictionResult, ttl: int = None):
        """Cache prediction with intelligent TTL"""
        cache_key = self._generate_prediction_cache_key(request)
        
        # Dynamic TTL based on prediction type and confidence
        if ttl is None:
            ttl = self._calculate_dynamic_ttl(request, result)
        
        await self.cache_manager.set(cache_key, result, ttl)
    
    def _calculate_dynamic_ttl(self, request: PredictionRequest, 
                             result: PredictionResult) -> int:
        """Calculate dynamic TTL based on prediction characteristics"""
        base_ttl = 300  # 5 minutes base
        
        # Adjust based on confidence
        confidence_multiplier = result.confidence_score
        
        # Adjust based on prediction type
        type_multipliers = {
            "demand": 1.0,          # Medium volatility
            "maintenance": 2.0,     # Lower volatility
            "quality": 1.5,         # Medium-low volatility
            "pricing": 0.5          # High volatility
        }
        
        type_multiplier = type_multipliers.get(request.prediction_type, 1.0)
        
        # Calculate final TTL
        final_ttl = int(base_ttl * confidence_multiplier * type_multiplier)
        
        return max(60, min(1800, final_ttl))  # Clamp between 1 min and 30 min
    
    def _generate_prediction_cache_key(self, request: PredictionRequest) -> str:
        """Generate consistent cache key for predictions"""
        key_components = {
            "type": request.prediction_type,
            "entity": request.target_entity,
            "horizon": request.horizon_days,
            "features_hash": hashlib.md5(
                json.dumps(request.features, sort_keys=True).encode()
            ).hexdigest()[:8]
        }
        
        return f"pred:{key_components['type']}:{key_components['entity']}:{key_components['horizon']}:{key_components['features_hash']}"
```

---

## 📡 Network & I/O Optimization

### 1. Async HTTP Client

```python
# /app/services/performance/async_http_client.py
import aiohttp
import asyncio
from typing import Dict, Any, Optional

class OptimizedHttpClient:
    """Optimized async HTTP client for external APIs"""
    
    def __init__(self):
        self.session = None
        self.connection_pool_size = 10
        self.timeout = aiohttp.ClientTimeout(total=30, connect=5)
        
    async def __aenter__(self):
        connector = aiohttp.TCPConnector(
            limit=self.connection_pool_size,
            limit_per_host=5,
            keepalive_timeout=60,
            enable_cleanup_closed=True
        )
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=self.timeout
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def fetch_external_data_batch(self, urls: List[str]) -> List[Dict[str, Any]]:
        """Fetch multiple external APIs concurrently"""
        if not self.session:
            raise RuntimeError("HTTP client not initialized")
        
        tasks = [self._fetch_single_url(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return [r for r in results if not isinstance(r, Exception)]
    
    async def _fetch_single_url(self, url: str) -> Dict[str, Any]:
        """Fetch single URL with error handling"""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"error": f"HTTP {response.status}"}
        except asyncio.TimeoutError:
            return {"error": "timeout"}
        except Exception as e:
            return {"error": str(e)}
```

### 2. File I/O Optimization

```python
# /app/services/performance/io_optimizer.py
import aiofiles
import asyncio
import pandas as pd
from pathlib import Path

class IOOptimizer:
    """Optimized file I/O operations"""
    
    def __init__(self):
        self.chunk_size = 8192  # Optimal for Pi 5 SD card
        
    async def read_large_csv_chunked(self, file_path: Path, chunk_size: int = 1000):
        """Read large CSV files in chunks to minimize memory usage"""
        chunks = []
        
        for chunk in pd.read_csv(file_path, chunksize=chunk_size):
            # Process chunk asynchronously
            processed_chunk = await self._process_chunk_async(chunk)
            chunks.append(processed_chunk)
            
            # Allow other tasks to run
            await asyncio.sleep(0)
        
        return pd.concat(chunks, ignore_index=True)
    
    async def write_data_async(self, data: pd.DataFrame, file_path: Path):
        """Write data asynchronously"""
        # Convert to CSV in memory
        csv_data = data.to_csv(index=False)
        
        # Write asynchronously
        async with aiofiles.open(file_path, 'w') as f:
            await f.write(csv_data)
    
    async def _process_chunk_async(self, chunk: pd.DataFrame) -> pd.DataFrame:
        """Process data chunk asynchronously"""
        # Simulate async processing
        await asyncio.sleep(0.001)
        return chunk
```

---

## 📈 Monitoring & Performance Metrics

### 1. Performance Monitor

```python
# /app/services/performance/performance_monitor.py
import psutil
import time
from dataclasses import dataclass
from typing import Dict, Any, List
import threading

@dataclass
class PerformanceMetrics:
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_bytes_sent: int
    network_bytes_recv: int
    active_threads: int
    api_response_time_ms: float

class PerformanceMonitor:
    """Real-time performance monitoring"""
    
    def __init__(self):
        self.metrics_history: List[PerformanceMetrics] = []
        self.max_history_size = 1000
        self.monitoring_active = False
        self.api_response_times = []
        
    async def start_monitoring(self):
        """Start performance monitoring"""
        self.monitoring_active = True
        
        while self.monitoring_active:
            metrics = await self._collect_metrics()
            self.metrics_history.append(metrics)
            
            # Limit history size
            if len(self.metrics_history) > self.max_history_size:
                self.metrics_history = self.metrics_history[-self.max_history_size:]
            
            await asyncio.sleep(1)  # Collect metrics every second
    
    async def _collect_metrics(self) -> PerformanceMetrics:
        """Collect system performance metrics"""
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # Memory metrics
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_mb = memory.used / (1024 * 1024)
        
        # Disk I/O metrics
        disk_io = psutil.disk_io_counters()
        disk_read_mb = disk_io.read_bytes / (1024 * 1024) if disk_io else 0
        disk_write_mb = disk_io.write_bytes / (1024 * 1024) if disk_io else 0
        
        # Network metrics
        network = psutil.net_io_counters()
        network_sent = network.bytes_sent if network else 0
        network_recv = network.bytes_recv if network else 0
        
        # Thread count
        active_threads = threading.active_count()
        
        # API response time (average of last 10 responses)
        avg_response_time = (
            sum(self.api_response_times[-10:]) / len(self.api_response_times[-10:])
            if self.api_response_times else 0
        )
        
        return PerformanceMetrics(
            timestamp=time.time(),
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_mb=memory_mb,
            disk_io_read_mb=disk_read_mb,
            disk_io_write_mb=disk_write_mb,
            network_bytes_sent=network_sent,
            network_bytes_recv=network_recv,
            active_threads=active_threads,
            api_response_time_ms=avg_response_time
        )
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        if not self.metrics_history:
            return {"status": "no_data"}
        
        recent_metrics = self.metrics_history[-60:]  # Last minute
        
        return {
            "current_cpu_percent": recent_metrics[-1].cpu_percent,
            "avg_cpu_percent": sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics),
            "current_memory_percent": recent_metrics[-1].memory_percent,
            "avg_memory_mb": sum(m.memory_mb for m in recent_metrics) / len(recent_metrics),
            "avg_response_time_ms": sum(m.api_response_time_ms for m in recent_metrics) / len(recent_metrics),
            "active_threads": recent_metrics[-1].active_threads,
            "status": self._get_performance_status(recent_metrics)
        }
    
    def _get_performance_status(self, metrics: List[PerformanceMetrics]) -> str:
        """Determine overall performance status"""
        avg_cpu = sum(m.cpu_percent for m in metrics) / len(metrics)
        avg_memory = sum(m.memory_percent for m in metrics) / len(metrics)
        avg_response = sum(m.api_response_time_ms for m in metrics) / len(metrics)
        
        if avg_cpu > 80 or avg_memory > 85 or avg_response > 2000:
            return "critical"
        elif avg_cpu > 60 or avg_memory > 75 or avg_response > 1500:
            return "warning"
        else:
            return "healthy"
```

---

## 🚨 Performance Alerts & Auto-scaling

```python
# /app/services/performance/performance_alerts.py
class PerformanceAlertManager:
    """Automated performance alerts and optimization"""
    
    def __init__(self):
        self.alert_thresholds = {
            "cpu_critical": 80,
            "cpu_warning": 60,
            "memory_critical": 85,
            "memory_warning": 75,
            "response_time_critical": 2000,  # ms
            "response_time_warning": 1500     # ms
        }
        self.active_optimizations = set()
        
    async def check_performance_and_optimize(self, metrics: PerformanceMetrics):
        """Check performance and trigger optimizations"""
        alerts = []
        
        # CPU optimization
        if metrics.cpu_percent > self.alert_thresholds["cpu_critical"]:
            alerts.append("CPU usage critical")
            await self._optimize_cpu_usage()
        
        # Memory optimization
        if metrics.memory_percent > self.alert_thresholds["memory_critical"]:
            alerts.append("Memory usage critical")
            await self._optimize_memory_usage()
        
        # Response time optimization
        if metrics.api_response_time_ms > self.alert_thresholds["response_time_critical"]:
            alerts.append("API response time critical")
            await self._optimize_response_time()
        
        return alerts
    
    async def _optimize_cpu_usage(self):
        """Automated CPU usage optimization"""
        if "cpu_optimization" in self.active_optimizations:
            return
            
        self.active_optimizations.add("cpu_optimization")
        
        # Reduce concurrent ML model training
        # Increase batch processing delays
        # Temporarily disable non-critical features
        
        # Remove optimization lock after delay
        await asyncio.sleep(300)  # 5 minutes
        self.active_optimizations.remove("cpu_optimization")
```

This comprehensive performance optimization strategy ensures the predictive analytics system can deliver on its <2 second response time targets while maintaining reliability and accuracy on the Pi 5 hardware constraints.