"""Validation services module"""

try:
    from .validation_service import ValidationService
except ImportError:
    try:
        from .validation_service_working import ValidationService
    except ImportError:
        class ValidationService:
            def __init__(self, debug_callback=None):
                print("⚠️ Using minimal ValidationService fallback")
            
            def validate_single_record(self, first_name, last_name, street_address, city, state, zip_code):
                return {
                    'timestamp': 'test',
                    'name_result': {'valid': True, 'confidence': 0.5},
                    'address_result': {'deliverable': False, 'error': 'Service not available'},
                    'overall_valid': False,
                    'overall_confidence': 0.25,
                    'processing_time_ms': 0,
                    'errors': ['ValidationService not properly loaded'],
                    'warnings': ['Using fallback service']
                }

__all__ = ['ValidationService']
