import time
import logging
from typing import Dict
import threading

logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiter to prevent Google Sheets API quota exceeded errors"""
    
    def __init__(self, max_requests_per_minute=50):  # Conservative limit
        self.max_requests = max_requests_per_minute
        self.requests = []
        self.lock = threading.Lock()
    
    def can_make_request(self) -> bool:
        """Check if we can make a request without exceeding rate limit"""
        with self.lock:
            now = time.time()
            # Remove requests older than 1 minute
            self.requests = [req_time for req_time in self.requests if now - req_time < 60]
            
            if len(self.requests) >= self.max_requests:
                logger.warning(f"🔍 DEBUG: Rate limit reached ({len(self.requests)}/{self.max_requests})")
                return False
            
            return True
    
    def record_request(self):
        """Record that a request was made"""
        with self.lock:
            self.requests.append(time.time())
            logger.info(f"🔍 DEBUG: Request recorded ({len(self.requests)}/{self.max_requests})")
    
    def wait_if_needed(self):
        """Wait if we're approaching rate limit"""
        with self.lock:
            if len(self.requests) >= self.max_requests * 0.8:  # 80% of limit
                wait_time = 60 - (time.time() - self.requests[0]) if self.requests else 0
                if wait_time > 0:
                    logger.info(f"🔍 DEBUG: Approaching rate limit, waiting {wait_time:.1f}s")
                    time.sleep(wait_time)

# Global rate limiter instance
rate_limiter = RateLimiter()
