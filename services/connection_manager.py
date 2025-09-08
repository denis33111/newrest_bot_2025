import time
import logging
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import threading

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages Google Sheets connections with pooling and caching"""
    
    def __init__(self):
        self._connection = None
        self._last_connection_time = None
        self._connection_lock = threading.Lock()
        self._cache = {}
        self._cache_lock = threading.Lock()
        self._cache_ttl = 30  # Cache for 30 seconds
        
    def get_connection(self, force_refresh=False):
        """Get or create Google Sheets connection with pooling"""
        with self._connection_lock:
            now = time.time()
            
            # Return existing connection if it's fresh and not forced refresh
            if (self._connection and 
                self._last_connection_time and 
                (now - self._last_connection_time) < 300 and  # 5 minutes
                not force_refresh):
                logger.info("🔍 DEBUG: Reusing existing Google Sheets connection")
                return self._connection
            
            # Create new connection
            logger.info("🔍 DEBUG: Creating new Google Sheets connection")
            start_time = time.time()
            
            try:
                from .google_sheets import _init_google_sheets_with_retry
                self._connection = _init_google_sheets_with_retry()
                self._last_connection_time = now
                
                connection_time = time.time() - start_time
                logger.info(f"🔍 DEBUG: New connection created in {connection_time:.2f}s")
                
                return self._connection
            except Exception as e:
                logger.error(f"Failed to create connection: {e}")
                return None
    
    def get_cached_data(self, key: str) -> Optional[Any]:
        """Get cached data if still valid"""
        with self._cache_lock:
            if key in self._cache:
                data, timestamp = self._cache[key]
                if time.time() - timestamp < self._cache_ttl:
                    logger.info(f"🔍 DEBUG: Cache hit for key: {key}")
                    return data
                else:
                    # Remove expired cache
                    del self._cache[key]
                    logger.info(f"🔍 DEBUG: Cache expired for key: {key}")
            return None
    
    def set_cached_data(self, key: str, data: Any):
        """Cache data with TTL"""
        with self._cache_lock:
            self._cache[key] = (data, time.time())
            logger.info(f"🔍 DEBUG: Cached data for key: {key}")
    
    def clear_cache(self):
        """Clear all cached data"""
        with self._cache_lock:
            self._cache.clear()
            logger.info("🔍 DEBUG: Cache cleared")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        with self._cache_lock:
            return {
                'total_keys': len(self._cache),
                'expired_keys': sum(1 for _, (_, timestamp) in self._cache.items() 
                                  if time.time() - timestamp >= self._cache_ttl)
            }

# Global connection manager instance
connection_manager = ConnectionManager()
