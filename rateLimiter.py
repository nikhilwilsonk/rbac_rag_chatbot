
from datetime import time
from config import RATE_LIMIT_MAX_REQUESTS, RATE_LIMIT_WINDOW
from app import logger

class RateLimiter:
    def __init__(self, window: int = RATE_LIMIT_WINDOW, max_requests: int = RATE_LIMIT_MAX_REQUESTS):
        self.window = window  
        self.max_requests = max_requests  
        self.user_requests = {}  
    
    def check_rate_limit(self, username: str) -> bool:
        """Check if a user has exceeded their rate limit
        
        Returns:
            bool: True if the request is allowed, False if rate limit exceeded
        """
        current_time = time.time()
        
        if username not in self.user_requests:
            self.user_requests[username] = []
        
        self.user_requests[username] = [
            req for req in self.user_requests[username]
            if current_time - req[0] < self.window
        ]
        
        request_count = sum(req[1] for req in self.user_requests[username])
        if request_count >= self.max_requests:
            logger.warning(f"Rate limit exceeded for user {username}")
            return False
        
        self.user_requests[username].append((current_time, 1))
        return True
