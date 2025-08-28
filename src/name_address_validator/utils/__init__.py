"""Utility modules"""

try:
    from .config import load_usps_credentials, get_app_config
except ImportError:
    def load_usps_credentials():
        import os
        return os.getenv('USPS_CLIENT_ID'), os.getenv('USPS_CLIENT_SECRET')
    
    def get_app_config():
        return {}

try:
    from .logger import debug_logger, performance_tracker
except ImportError:
    class debug_logger:
        @staticmethod
        def info(msg, category="GENERAL"):
            print(f"[{category}] {msg}")

__all__ = ['load_usps_credentials', 'get_app_config', 'debug_logger']
