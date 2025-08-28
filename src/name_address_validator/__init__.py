"""Name and Address Validator Package"""
__version__ = "1.1.0"

try:
    from .services.validation_service import ValidationService
except ImportError:
    try:
        from .services.validation_service_working import ValidationService
    except ImportError:
        ValidationService = None

try:
    from .utils.config import load_usps_credentials
except ImportError:
    def load_usps_credentials():
        import os
        return os.getenv('USPS_CLIENT_ID'), os.getenv('USPS_CLIENT_SECRET')

__all__ = []
if ValidationService:
    __all__.append('ValidationService')
__all__.extend(['load_usps_credentials'])
