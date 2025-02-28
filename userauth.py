from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
import secrets
import time
from typing import Dict, Optional, Tuple
from config import ROLES, SESSION_EXPIRY , USER_DB_PATH, SESSION_DB_PATH
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UserAuth:
    def __init__(self, user_db_path: Path = USER_DB_PATH, session_db_path: Path = SESSION_DB_PATH):
        self.user_db_path = user_db_path
        self.session_db_path = session_db_path
        self.users = self._load_users()
        self.sessions = self._load_sessions()
        self._cleanup_expired_sessions()
    
    def _load_users(self) -> Dict:
        if self.user_db_path.exists():
            with open(self.user_db_path, 'r') as f:
                return json.load(f)
        else:
            admin_salt = self._generate_salt()
            finance_salt = self._generate_salt()
            engineering_salt = self._generate_salt()
            
            default_users = {
                "admin": {
                    "password_hash": self._hash_password("admin123", admin_salt),
                    "role": "admin",
                    "salt": admin_salt,
                    "failed_attempts": 0,
                    "last_attempt": None
                },
                "finance_user": {
                    "password_hash": self._hash_password("finance123", finance_salt),
                    "role": "finance",
                    "salt": finance_salt,
                    "failed_attempts": 0,
                    "last_attempt": None
                },
                "engineering_user": {
                    "password_hash": self._hash_password("engineering123", engineering_salt),
                    "role": "engineering",
                    "salt": engineering_salt,
                    "failed_attempts": 0,
                    "last_attempt": None
                }
            }
            self._save_users(default_users)
            return default_users
    def _load_sessions(self) -> Dict:
        if self.session_db_path.exists():
            with open(self.session_db_path, 'r') as f:
                return json.load(f)
        else:
            return {}
    
    def _save_users(self, users: Dict = None) -> None:
        if users is None:
            users = self.users
        with open(self.user_db_path, 'w') as f:
            json.dump(users, f, indent=2)
    
    def _save_sessions(self, sessions: Dict = None) -> None:
        if sessions is None:
            sessions = self.sessions
        with open(self.session_db_path, 'w') as f:
            json.dump(sessions, f, indent=2)
    
    def _generate_salt(self) -> str:
        return secrets.token_hex(16)
    
    def _hash_password(self, password: str, salt: str) -> str:
        return hashlib.pbkdf2_hmac(
            'sha256', 
            password.encode(), 
            salt.encode(), 
            100000
        ).hex()
    
    def _cleanup_expired_sessions(self) -> None:
        current_time = time.time()
        active_sessions = {}
        
        for token, session in self.sessions.items():
            if session.get("expiry", 0) > current_time:
                active_sessions[token] = session
        
        if len(active_sessions) != len(self.sessions):
            logger.info(f"Cleaned up {len(self.sessions) - len(active_sessions)} expired sessions")
            self.sessions = active_sessions
            self._save_sessions()
    
    def _generate_session_token(self) -> str:
        return secrets.token_urlsafe(32)
    
    def _check_account_lockout(self, username: str) -> bool:
        if username not in self.users:
            return False
        
        user = self.users[username]
        if user.get("failed_attempts", 0) >= 5:
            last_attempt = user.get("last_attempt")
            if last_attempt:
                lockout_end = datetime.fromisoformat(last_attempt) + timedelta(minutes=10)
                if datetime.now() < lockout_end:
                    return True
                user["failed_attempts"] = 0
                self._save_users()
        return False
    
    def authenticate(self, username: str, password: str) -> Optional[Tuple[str, str]]:
        if self._check_account_lockout(username):
            logger.warning(f"Account locked: Too many failed attempts for {username}")
            return None
        
        if username not in self.users:
            logger.warning(f"Authentication failed: User {username} not found")
            return None
        
        user = self.users[username]
        salt = user["salt"]
        password_hash = self._hash_password(password, salt)
        
        if user["password_hash"] != password_hash:
            user["failed_attempts"] = user.get("failed_attempts", 0) + 1
            user["last_attempt"] = datetime.now().isoformat()
            self._save_users()
            
            logger.warning(f"Authentication failed: Incorrect password for {username}")
            return None
        
        user["failed_attempts"] = 0
        self._save_users()
        
        session_token = self._generate_session_token()
        self.sessions[session_token] = {
            "username": username,
            "role": user["role"],
            "expiry": time.time() + SESSION_EXPIRY
        }
        self._save_sessions()
        
        logger.info(f"User {username} authenticated successfully")
        return session_token, user["role"]
    
    def validate_session(self, token: str) -> Optional[Tuple[str, str]]:
        if token not in self.sessions:
            return None
        
        session = self.sessions[token]
        if session.get("expiry", 0) < time.time():
            del self.sessions[token]
            self._save_sessions()
            return None
        
        session["expiry"] = time.time() + SESSION_EXPIRY
        self._save_sessions()
        
        return session["username"], session["role"]
    
    def logout(self, token: str) -> bool:
        if token in self.sessions:
            del self.sessions[token]
            self._save_sessions()
            return True
        return False
    
    def add_user(self, username: str, password: str, role: str) -> bool:
        if username in self.users:
            logger.warning(f"User {username} already exists")
            return False
        
        if role not in ROLES:
            logger.warning(f"Invalid role: {role}. Must be one of {ROLES}")
            return False
        
        salt = self._generate_salt()
        self.users[username] = {
            "password_hash": self._hash_password(password, salt),
            "role": role,
            "salt": salt,
            "failed_attempts": 0,
            "last_attempt": None
        }
        self._save_users()
        logger.info(f"Added user {username} with role {role}")
        return True
    
    def list_users(self) -> Dict:
        """Return a dict of username -> role mappings (without sensitive data)"""
        return {username: user_data["role"] for username, user_data in self.users.items()}