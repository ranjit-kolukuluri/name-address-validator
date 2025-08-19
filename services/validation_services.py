# src/name_address_validator/services/validation_service.py
"""
Unified validation service that coordinates name and address validation
"""

import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from ..validators.name_validator import EnhancedNameValidator
from ..validators.address_validator import USPSAddressValidator
from ..utils.config import load_usps_credentials
from ..utils.logger import debug_logger, performance_tracker


class ValidationService:
    """
    Unified validation service that coordinates all validation operations
    """
    
    def __init__(self, debug_callback=None):
        self.debug_callback = debug_callback or debug_logger.info
        self.name_validator = EnhancedNameValidator()
        self.address_validator = None
        self._initialize_address_validator()
    
    def _initialize_address_validator(self):
        """Initialize USPS address validator with credentials"""
        try:
            client_id, client_secret = load_usps_credentials()
            if client_id and client_secret:
                self.address_validator = USPSAddressValidator(
                    client_id, 
                    client_secret,
                    debug_callback=self.debug_callback
                )
                self.debug_callback("✅ Address validator initialized with USPS credentials", "SERVICE")
            else:
                self.debug_callback("⚠️ USPS credentials not available - address validation disabled", "SERVICE")
        except Exception as e:
            self.debug_callback(f"❌ Failed to initialize address validator: {str(e)}", "SERVICE")
    
    def is_address_validation_available(self) -> bool:
        """Check if address validation is available"""
        return self.address_validator is not None and self.address_validator.is_configured()
    
    def validate_single_record(self, first_name: str, last_name: str, street_address: str, 
                             city: str, state: str, zip_code: str) -> Dict:
        """
        Validate a single complete record (name + address)
        
        Args:
            first_name: Person's first name
            last_name: Person's last name  
            street_address: Street address
            city: City name
            state: 2-letter state code
            zip_code: ZIP code (5 or 9 digits)
            
        Returns:
            Dict with comprehensive validation results
        """
        
        self.debug_callback("🔍 Starting single record validation", "SERVICE")
        start_time = time.time()
        
        results = {
            'timestamp': datetime.now(),
            'name_result': None,
            'address_result': None,
            'overall_valid': False,
            'overall_confidence': 0.0,
            'processing_time_ms': 0,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Validate name
            name_start = time.time()
            name_result = self.name_validator.validate(first_name, last_name)
            name_duration = int((time.time() - name_start) * 1000)
            performance_tracker.track("name_validation", name_duration, name_result['valid'])
            
            results['name_result'] = name_result
            self.debug_callback(f"✅ Name validation completed ({name_duration}ms)", "SERVICE")
            
            # Validate address if validator is available
            if self.is_address_validation_available():
                address_start = time.time()
                address_data = {
                    'street_address': street_address,
                    'city': city,
                    'state': state,
                    'zip_code': zip_code
                }
                
                address_result = self.address_validator.validate_address(address_data)
                address_duration = int((time.time() - address_start) * 1000)
                performance_tracker.track("address_validation", address_duration, address_result.get('success', False))
                
                results['address_result'] = address_result
                self.debug_callback(f"✅ Address validation completed ({address_duration}ms)", "SERVICE")
            else:
                results['errors'].append("Address validation not available - USPS API not configured")
                results['address_result'] = {
                    'success': False,
                    'error': 'USPS API not configured',
                    'deliverable': False
                }
                self.debug_callback("⚠️ Address validation skipped - API not available", "SERVICE")
            
            # Calculate overall results
            name_valid = name_result.get('valid', False)
            address_deliverable = results['address_result'].get('deliverable', False) if self.is_address_validation_available() else True
            
            results['overall_valid'] = name_valid and address_deliverable
            
            # Calculate overall confidence
            name_confidence = name_result.get('confidence', 0)
            address_confidence = results['address_result'].get('confidence', 0) if self.is_address_validation_available() else 1.0
            results['overall_confidence'] = (name_confidence + address_confidence) / 2
            
            # Collect errors and warnings
            if name_result.get('errors'):
                results['errors'].extend(name_result['errors'])
            if name_result.get('warnings'):
                results['warnings'].extend(name_result['warnings'])
            
            if results['address_result'].get('error') and self.is_address_validation_available():
                results['errors'].append(f"Address: {results['address_result']['error']}")
            
        except Exception as e:
            error_msg = f"Validation service error: {str(e)}"
            results['errors'].append(error_msg)
            self.debug_callback(f"❌ {error_msg}", "SERVICE")
            performance_tracker.track("single_validation", 0, False)
        
        # Calculate total processing time
        total_duration = int((time.time() - start_time) * 1000)
        results['processing_time_ms'] = total_duration
        performance_tracker.track("single_record_validation", total_duration, results['overall_valid'])
        
        self.debug_callback(f"🏁 Single record validation completed ({total_duration}ms)", "SERVICE")
        return results
    
    def validate_batch_records(self, records: List[Dict], include_suggestions: bool = True, 
                             max_records: Optional[int] = None) -> Dict:
        """
        Validate multiple records in batch
        
        Args:
            records: List of dicts with keys: first_name, last_name, street_address, city, state, zip_code
            include_suggestions: Whether to include name/address suggestions
            max_records: Maximum number of records to process
            
        Returns:
            Dict with batch validation results
        """
        
        self.debug_callback(f"📦 Starting batch validation of {len(records)} records", "SERVICE")
        batch_start = time.time()
        
        if max_records:
            records = records[:max_records]
            self.debug_callback(f"📦 Limited to {max_records} records", "SERVICE")
        
        results = {
            'timestamp': datetime.now(),
            'total_records': len(records),
            'processed_records': 0,
            'successful_validations': 0,
            'failed_validations': 0,
            'processing_time_ms': 0,
            'records': [],
            'summary': {
                'business_addresses': 0,
                'residential_addresses': 0,
                'unknown_addresses': 0,
                'corrections_made': 0
            }
        }
        
        for i, record in enumerate(records):
            record_start = time.time()
            
            try:
                # Extract fields with defaults
                first_name = str(record.get('first_name', '')).strip()
                last_name = str(record.get('last_name', '')).strip()
                street_address = str(record.get('street_address', '')).strip()
                city = str(record.get('city', '')).strip()
                state = str(record.get('state', '')).strip().upper()
                zip_code = str(record.get('zip_code', '')).strip()
                
                # Store original address for comparison
                original_address = f"{street_address}, {city}, {state} {zip_code}"
                
                # Validate the record
                validation_result = self.validate_single_record(
                    first_name, last_name, street_address, city, state, zip_code
                )
                
                # Determine address type
                address_type = "Unknown"
                if validation_result['address_result'].get('success') and validation_result['address_result'].get('metadata'):
                    metadata = validation_result['address_result']['metadata']
                    if metadata.get('business'):
                        address_type = "Business"
                        results['summary']['business_addresses'] += 1
                    else:
                        address_type = "Residential"
                        results['summary']['residential_addresses'] += 1
                else:
                    results['summary']['unknown_addresses'] += 1
                
                # Build record result
                record_result = {
                    'row': i + 1,
                    'first_name': first_name,
                    'last_name': last_name,
                    'original_address': original_address,
                    'name_status': 'Valid' if validation_result['name_result']['valid'] else 'Invalid',
                    'address_status': 'Deliverable' if validation_result['address_result'].get('deliverable', False) else 'Not Deliverable',
                    'address_type': address_type,
                    'overall_status': 'Valid' if validation_result['overall_valid'] else 'Invalid',
                    'confidence': f"{validation_result['overall_confidence']:.1%}",
                    'processing_time_ms': validation_result['processing_time_ms']
                }
                
                # Add suggestions if requested
                if include_suggestions:
                    # Name suggestions
                    name_suggestions = validation_result['name_result'].get('suggestions', {})
                    
                    first_name_suggestions = []
                    last_name_suggestions = []
                    
                    if 'first_name' in name_suggestions and name_suggestions['first_name']:
                        first_name_suggestions = [s['suggestion'] for s in name_suggestions['first_name'][:3]]
                    if 'last_name' in name_suggestions and name_suggestions['last_name']:
                        last_name_suggestions = [s['suggestion'] for s in name_suggestions['last_name'][:3]]
                    
                    record_result['first_name_suggestions'] = ', '.join(first_name_suggestions) if first_name_suggestions else 'None'
                    record_result['last_name_suggestions'] = ', '.join(last_name_suggestions) if last_name_suggestions else 'None'
                    
                    # Address standardization and corrections
                    if validation_result['address_result'].get('success') and validation_result['address_result'].get('standardized'):
                        std = validation_result['address_result']['standardized']
                        standardized_address = f"{std['street_address']}, {std['city']}, {std['state']} {std['zip_code']}"
                        record_result['usps_standardized_address'] = standardized_address
                        
                        # Track corrections
                        corrections = self._identify_corrections(
                            street_address, city, state, zip_code, std
                        )
                        
                        record_result['address_corrections'] = '; '.join(corrections) if corrections else 'No corrections needed'
                        
                        if corrections:
                            results['summary']['corrections_made'] += 1
                        
                        # Add metadata details
                        metadata_details = self._format_metadata_details(validation_result['address_result'].get('metadata', {}))
                        record_result['address_details'] = metadata_details
                        
                        # Delivery point
                        delivery_point = validation_result['address_result'].get('metadata', {}).get('delivery_point', 'Not Available')
                        record_result['delivery_point'] = delivery_point
                    else:
                        record_result['usps_standardized_address'] = 'Not Available'
                        record_result['address_corrections'] = 'Unable to standardize'
                        record_result['address_details'] = 'Standard delivery'
                        record_result['delivery_point'] = 'Not Available'
                
                # Track success/failure
                if validation_result['overall_valid']:
                    results['successful_validations'] += 1
                else:
                    results['failed_validations'] += 1
                
                results['records'].append(record_result)
                results['processed_records'] += 1
                
                record_duration = int((time.time() - record_start) * 1000)
                performance_tracker.track("batch_record_validation", record_duration, validation_result['overall_valid'])
                
            except Exception as e:
                self.debug_callback(f"❌ Error processing record {i + 1}: {str(e)}", "SERVICE")
                
                # Add error record
                error_record = {
                    'row': i + 1,
                    'first_name': str(record.get('first_name', '')),
                    'last_name': str(record.get('last_name', '')),
                    'original_address': f"{record.get('street_address', '')}, {record.get('city', '')}, {record.get('state', '')} {record.get('zip_code', '')}",
                    'name_status': 'Error',
                    'address_status': 'Error',
                    'address_type': 'Error',
                    'overall_status': f'Error: {str(e)[:50]}',
                    'confidence': '0%',
                    'processing_time_ms': 0
                }
                
                if include_suggestions:
                    error_record.update({
                        'first_name_suggestions': 'Error',
                        'last_name_suggestions': 'Error',
                        'usps_standardized_address': 'Error',
                        'address_corrections': 'Error',
                        'address_details': 'Error',
                        'delivery_point': 'Error'
                    })
                
                results['records'].append(error_record)
                results['failed_validations'] += 1
                results['processed_records'] += 1
                
                performance_tracker.track("batch_record_validation", 0, False)
        
        # Calculate total processing time
        total_duration = int((time.time() - batch_start) * 1000)
        results['processing_time_ms'] = total_duration
        performance_tracker.track("batch_validation", total_duration, results['successful_validations'] > 0)
        
        self.debug_callback(f"🏁 Batch validation completed ({total_duration}ms)", "SERVICE")
        return results
    
    def _identify_corrections(self, original_street: str, original_city: str, 
                            original_state: str, original_zip: str, standardized: Dict) -> List[str]:
        """Identify what corrections USPS made"""
        corrections = []
        
        # Check street address changes
        if original_street.upper() != standardized['street_address'].upper():
            corrections.append(f"Street: '{original_street}' → '{standardized['street_address']}'")
        
        # Check city changes
        if original_city.upper() != standardized['city'].upper():
            corrections.append(f"City: '{original_city}' → '{standardized['city']}'")
        
        # Check state changes
        if original_state.upper() != standardized['state'].upper():
            corrections.append(f"State: '{original_state}' → '{standardized['state']}'")
        
        # Check ZIP changes
        original_zip_base = original_zip.split('-')[0]
        standardized_zip_base = standardized['zip_code'].split('-')[0]
        
        if original_zip_base != standardized_zip_base:
            corrections.append(f"ZIP: '{original_zip}' → '{standardized['zip_code']}'")
        elif len(standardized['zip_code']) > len(original_zip):
            corrections.append(f"ZIP+4: '{original_zip}' → '{standardized['zip_code']}'")
        
        return corrections
    
    def _format_metadata_details(self, metadata: Dict) -> str:
        """Format address metadata into readable details"""
        details = []
        
        if metadata.get('vacant'):
            details.append('Vacant Property')
        if metadata.get('centralized'):
            details.append('Centralized Delivery')
        if metadata.get('carrier_route'):
            details.append(f"Route: {metadata['carrier_route']}")
        if metadata.get('dpv_confirmation'):
            dpv_meanings = {
                'Y': 'Deliverable',
                'N': 'Not Deliverable',
                'D': 'Deliverable (Missing Unit)'
            }
            dpv_meaning = dpv_meanings.get(metadata['dpv_confirmation'], metadata['dpv_confirmation'])
            details.append(f"DPV: {dpv_meaning}")
        
        return '; '.join(details) if details else 'Standard delivery'
    
    def get_service_status(self) -> Dict:
        """Get current service status and capabilities"""
        return {
            'name_validation_available': True,
            'address_validation_available': self.is_address_validation_available(),
            'usps_configured': self.address_validator is not None,
            'performance_tracking': True,
            'debug_logging': True,
            'service_uptime': datetime.now().isoformat()
        }