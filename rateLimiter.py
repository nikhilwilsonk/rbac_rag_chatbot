import time
from collections import defaultdict
from config import RATE_LIMIT_MAX_REQUESTS, RATE_LIMIT_WINDOW
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self, window: int = RATE_LIMIT_WINDOW, max_requests: int = RATE_LIMIT_MAX_REQUESTS):
        self.window = window
        self.max_requests = max_requests
        self.user_requests = defaultdict(list)
    
    def check_rate_limit(self, username: str) -> bool:
        current_time = time.time()
        
        self.user_requests[username] = [
            timestamp for timestamp in self.user_requests[username]
            if current_time - timestamp < self.window
        ]
        
        if len(self.user_requests[username]) >= self.max_requests:
            logger.warning(f"Rate limit exceeded for user {username}")
            return False
        
        self.user_requests[username].append(current_time)
        return True