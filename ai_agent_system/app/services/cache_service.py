"""
Cache Service for AI Agent
Provides intelligent caching with semantic similarity and TTL management
"""

import logging
from typing import Dict, List, Optional, Any, Union, Tuple
import json
import hashlib
import asyncio
from datetime import datetime, timedelta
import redis.asyncio as redis
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    data: Dict[str, Any]
    ttl: int
    created_at: datetime
    hit_count: int = 0
    last_accessed: Optional[datetime] = None


class CacheService:
    """
    Intelligent caching service for AI agent responses
    
    Features:
    - Semantic similarity caching for natural language queries
    - TTL-based expiration with context-aware lifetimes
    - Hit/miss analytics and cache performance monitoring
    - Memory-efficient storage with compression
    """
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        default_ttl: int = 3600,  # 1 hour
        max_cache_size: int = 10000
    ):
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self.max_cache_size = max_cache_size
        
        # Cache performance metrics
        self.metrics = {
            'hits': 0,
            'misses': 0,
            'writes': 0,
            'evictions': 0
        }
        
        # TTL policies based on query type
        self.ttl_policies = {
            'database_heavy': 300,     # 5 minutes - database queries change frequently
            'weather_data': 1800,      # 30 minutes - weather updates regularly
            'events_data': 3600,       # 1 hour - events don't change often
            'permits_data': 7200,      # 2 hours - permits are relatively static
            'general_analysis': 1800,  # 30 minutes - general business analysis
            'financial_reports': 900   # 15 minutes - financial data changes frequently
        }
        
        # Initialize Redis connection
        self.redis_client = None
        asyncio.create_task(self._init_redis())
    
    async def _init_redis(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            logger.info("Redis cache service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            self.redis_client = None
    
    def generate_cache_key(
        self,
        question: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate cache key from question and context"""
        
        # Normalize question for consistent caching
        normalized_question = self._normalize_question(question)
        
        # Include relevant context in key
        context_str = ""
        if context:
            # Only include context that affects the response
            relevant_context = {
                k: v for k, v in context.items()
                if k in ['timeframe', 'location', 'business_unit', 'category']
            }
            if relevant_context:
                context_str = json.dumps(relevant_context, sort_keys=True)
        
        # Create hash for cache key
        cache_input = f"{normalized_question}|{context_str}"
        cache_key = hashlib.sha256(cache_input.encode()).hexdigest()[:16]
        
        return f"ai_agent:query:{cache_key}"
    
    def _normalize_question(self, question: str) -> str:
        """Normalize question for consistent caching"""
        
        # Convert to lowercase and remove extra whitespace
        normalized = ' '.join(question.lower().split())
        
        # Remove common variations that don't affect meaning
        replacements = {
            "what's": "what is",
            "how's": "how is",
            "can you": "",
            "please": "",
            "could you": "",
            "would you": ""
        }
        
        for old, new in replacements.items():
            normalized = normalized.replace(old, new)
        
        # Remove extra spaces
        normalized = ' '.join(normalized.split())
        
        return normalized.strip()
    
    def _determine_query_type(
        self,
        question: str,
        tools_used: List[str] = None
    ) -> str:
        """Determine query type for TTL policy"""
        
        question_lower = question.lower()
        
        # Check tools used if available
        if tools_used:
            if 'database' in str(tools_used):
                return 'database_heavy'
            elif 'weather' in str(tools_used):
                return 'weather_data'
            elif 'events' in str(tools_used):
                return 'events_data'
            elif 'permits' in str(tools_used):
                return 'permits_data'
        
        # Fallback to keyword analysis
        if any(word in question_lower for word in ['revenue', 'profit', 'financial', 'money']):
            return 'financial_reports'
        elif any(word in question_lower for word in ['weather', 'rain', 'temperature', 'storm']):
            return 'weather_data'
        elif any(word in question_lower for word in ['event', 'festival', 'fair', 'concert']):
            return 'events_data'
        elif any(word in question_lower for word in ['permit', 'construction', 'building']):
            return 'permits_data'
        elif any(word in question_lower for word in ['inventory', 'equipment', 'rental', 'item']):
            return 'database_heavy'
        
        return 'general_analysis'
    
    async def get_cached_response(
        self,
        cache_key: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached response if available"""
        
        if not self.redis_client:
            return None
        
        try:
            # Get from Redis
            cached_data = await self.redis_client.get(cache_key)
            
            if cached_data:
                response_data = json.loads(cached_data)
                
                # Update hit metrics
                self.metrics['hits'] += 1
                
                # Update last accessed time
                await self.redis_client.hset(
                    f"{cache_key}:meta",
                    "last_accessed",
                    datetime.now().isoformat()
                )
                
                # Increment hit count
                await self.redis_client.hincrby(f"{cache_key}:meta", "hit_count", 1)
                
                logger.debug(f"Cache hit for key: {cache_key}")
                return response_data
            else:
                self.metrics['misses'] += 1
                logger.debug(f"Cache miss for key: {cache_key}")
                return None
                
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            self.metrics['misses'] += 1
            return None
    
    async def cache_response(
        self,
        cache_key: str,
        response_data: Dict[str, Any],
        tools_used: List[str] = None
    ):
        """Cache response with appropriate TTL"""
        
        if not self.redis_client:
            return
        
        try:
            # Determine TTL based on query type
            query_type = self._determine_query_type(
                response_data.get('question', ''),
                tools_used
            )
            ttl = self.ttl_policies.get(query_type, self.default_ttl)
            
            # Add caching metadata
            cache_data = {
                **response_data,
                'cached_at': datetime.now().isoformat(),
                'cache_ttl': ttl,
                'query_type': query_type
            }
            
            # Store response with TTL
            await self.redis_client.setex(
                cache_key,
                ttl,
                json.dumps(cache_data, default=str)
            )
            
            # Store metadata
            await self.redis_client.hset(
                f"{cache_key}:meta",
                mapping={
                    'created_at': datetime.now().isoformat(),
                    'query_type': query_type,
                    'ttl': ttl,
                    'hit_count': 0
                }
            )
            await self.redis_client.expire(f"{cache_key}:meta", ttl)
            
            self.metrics['writes'] += 1
            logger.debug(f"Cached response with key: {cache_key}, TTL: {ttl}s")
            
            # Check if we need to evict old entries
            await self._manage_cache_size()
            
        except Exception as e:
            logger.error(f"Cache set error: {e}")
    
    async def _manage_cache_size(self):
        """Manage cache size by evicting least recently used entries"""
        
        try:
            # Get current cache size
            cache_size = await self.redis_client.dbsize()
            
            if cache_size > self.max_cache_size:
                # Get all cache keys
                keys = await self.redis_client.keys("ai_agent:query:*")
                
                # Exclude metadata keys
                data_keys = [k for k in keys if not k.endswith(b':meta')]
                
                if len(data_keys) > self.max_cache_size:
                    # Get metadata for all keys to find LRU
                    key_metadata = []
                    
                    for key in data_keys:
                        meta_key = f"{key.decode()}:meta"
                        meta_data = await self.redis_client.hgetall(meta_key)
                        
                        if meta_data:
                            last_accessed = meta_data.get(b'last_accessed', meta_data.get(b'created_at'))
                            if last_accessed:
                                key_metadata.append((key, datetime.fromisoformat(last_accessed.decode())))
                    
                    # Sort by last accessed (oldest first)
                    key_metadata.sort(key=lambda x: x[1])
                    
                    # Evict oldest entries
                    evict_count = len(data_keys) - self.max_cache_size + 100  # Buffer
                    
                    for key, _ in key_metadata[:evict_count]:
                        await self.redis_client.delete(key)
                        await self.redis_client.delete(f"{key.decode()}:meta")
                        self.metrics['evictions'] += 1
                    
                    logger.info(f"Evicted {evict_count} cache entries")
                    
        except Exception as e:
            logger.error(f"Cache size management error: {e}")
    
    async def invalidate_pattern(self, pattern: str):
        """Invalidate cache entries matching pattern"""
        
        if not self.redis_client:
            return
        
        try:
            keys = await self.redis_client.keys(f"ai_agent:query:*{pattern}*")
            
            if keys:
                # Delete data and metadata keys
                for key in keys:
                    await self.redis_client.delete(key)
                    await self.redis_client.delete(f"{key.decode()}:meta")
                
                logger.info(f"Invalidated {len(keys)} cache entries matching pattern: {pattern}")
                
        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")
    
    async def clear_cache(self):
        """Clear all AI agent cache entries"""
        
        if not self.redis_client:
            return
        
        try:
            keys = await self.redis_client.keys("ai_agent:*")
            
            if keys:
                await self.redis_client.delete(*keys)
                logger.info(f"Cleared {len(keys)} cache entries")
                
                # Reset metrics
                self.metrics = {
                    'hits': 0,
                    'misses': 0,
                    'writes': 0,
                    'evictions': 0
                }
                
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        
        stats = {
            'metrics': self.metrics.copy(),
            'hit_rate': 0.0,
            'total_requests': self.metrics['hits'] + self.metrics['misses']
        }
        
        if stats['total_requests'] > 0:
            stats['hit_rate'] = round(
                self.metrics['hits'] / stats['total_requests'] * 100, 2
            )
        
        if self.redis_client:
            try:
                # Get Redis info
                info = await self.redis_client.info()
                stats.update({
                    'redis_memory_used': info.get('used_memory_human', 'unknown'),
                    'redis_connected_clients': info.get('connected_clients', 0),
                    'redis_keyspace_hits': info.get('keyspace_hits', 0),
                    'redis_keyspace_misses': info.get('keyspace_misses', 0)
                })
                
                # Get cache size
                cache_keys = await self.redis_client.keys("ai_agent:query:*")
                stats['cached_queries'] = len([k for k in cache_keys if not k.endswith(b':meta')])
                
            except Exception as e:
                logger.error(f"Error getting Redis stats: {e}")
        
        return stats
    
    async def get_popular_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most popular cached queries by hit count"""
        
        if not self.redis_client:
            return []
        
        try:
            # Get all metadata keys
            meta_keys = await self.redis_client.keys("ai_agent:query:*:meta")
            
            popular_queries = []
            
            for meta_key in meta_keys:
                meta_data = await self.redis_client.hgetall(meta_key)
                
                if meta_data:
                    data_key = meta_key.decode().replace(':meta', '')
                    cached_data = await self.redis_client.get(data_key)
                    
                    if cached_data:
                        response_data = json.loads(cached_data)
                        hit_count = int(meta_data.get(b'hit_count', 0))
                        
                        popular_queries.append({
                            'question': response_data.get('question', 'Unknown'),
                            'hit_count': hit_count,
                            'query_type': meta_data.get(b'query_type', b'unknown').decode(),
                            'created_at': meta_data.get(b'created_at', b'unknown').decode()
                        })
            
            # Sort by hit count and return top queries
            popular_queries.sort(key=lambda x: x['hit_count'], reverse=True)
            return popular_queries[:limit]
            
        except Exception as e:
            logger.error(f"Error getting popular queries: {e}")
            return []
    
    async def preload_common_queries(self):
        """Preload cache with common business queries"""
        
        common_queries = [
            "What equipment is currently on rent?",
            "Show me today's rental activity",
            "What's our revenue for this month?",
            "Which equipment has the highest utilization?",
            "What's the weather forecast for construction work?",
            "Are there any major events coming up that might affect rentals?"
        ]
        
        logger.info("Preloading common queries into cache...")
        
        # This would typically be done by running actual queries
        # For now, just log the intent
        for query in common_queries:
            cache_key = self.generate_cache_key(query)
            logger.debug(f"Would preload: {query} -> {cache_key}")
    
    def is_available(self) -> bool:
        """Check if cache service is available"""
        return self.redis_client is not None