# src/name_address_validator/services/validation_service.py
"""
Enhanced validation service with address format standardization and US qualification filtering
"""

import time
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from ..validators.name_validator import EnhancedNameValidator
from ..validators.address_validator import USPSAddressValidator
from ..utils.config import load_usps_credentials
from ..utils.logger import debug_logger, performance_tracker
from ..utils.address_standardizer import AddressFormatStandardizer


class ValidationService:
    """
    Enhanced validation service with address format standardization and qualification filtering
    """
    
    def __init__(self, debug_callback=None):
        self.debug_callback = debug_callback or debug_logger.info
        self.name_validator = EnhancedNameValidator()
        self.address_validator = None
        self.address_standardizer = AddressFormatStandardizer(debug_callback=self.debug_callback)
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
    
    def standardize_and_qualify_csv_files(self, file_data_list: List[Tuple[pd.DataFrame, str]]) -> Dict:
        """
        Standardize multiple CSV files and assess US qualification (NEW METHOD)
        
        Args:
            file_data_list: List of (DataFrame, filename) tuples
            
        Returns:
            Dict with standardization and qualification results
        """
        self.debug_callback(f"📦 Starting CSV standardization and qualification for {len(file_data_list)} files", "STANDARDIZATION")
        start_time = time.time()
        
        try:
            # Use address standardizer to process files with qualification
            standardized_df, standardization_info = self.address_standardizer.standardize_multiple_files(file_data_list)
            
            # Get comprehensive summary including qualification
            summary = self.address_standardizer.get_standardization_summary(standardization_info)
            qualification_summary = self.address_standardizer.get_qualification_summary(standardized_df, standardization_info)
            
            # Split qualified and disqualified addresses
            qualified_df, disqualified_df = self.address_standardizer.filter_qualified_addresses(standardized_df)
            
            duration = int((time.time() - start_time) * 1000)
            performance_tracker.track("csv_standardization_qualification", duration, summary['successful_files'] > 0)
            
            result = {
                'success': True,
                'standardized_data': standardized_df,
                'qualified_data': qualified_df,
                'disqualified_data': disqualified_df,
                'standardization_info': standardization_info,
                'summary': summary,
                'qualification_summary': qualification_summary,
                'processing_time_ms': duration,
                'total_rows': len(standardized_df),
                'qualified_rows': len(qualified_df),
                'disqualified_rows': len(disqualified_df)
            }
            
            self.debug_callback(f"✅ Standardization and qualification completed ({duration}ms): {len(qualified_df)}/{len(standardized_df)} rows qualified", "STANDARDIZATION")
            return result
            
        except Exception as e:
            error_msg = f"CSV standardization and qualification failed: {str(e)}"
            self.debug_callback(f"❌ {error_msg}", "STANDARDIZATION")
            
            duration = int((time.time() - start_time) * 1000)
            performance_tracker.track("csv_standardization_qualification", duration, False)
            
            return {
                'success': False,
                'error': error_msg,
                'processing_time_ms': duration,
                'total_rows': 0,
                'qualified_rows': 0,
                'disqualified_rows': 0
            }
    
    def validate_qualified_addresses_only(self, qualified_df: pd.DataFrame, include_suggestions: bool = True, 
                                        max_records: Optional[int] = None) -> Dict:
        """
        Validate only qualified US addresses (NEW METHOD)
        
        Args:
            qualified_df: DataFrame with only qualified US addresses
            include_suggestions: Whether to include name/address suggestions
            max_records: Maximum number of records to process
            
        Returns:
            Dict with validation results for qualified addresses only
        """
        
        self.debug_callback(f"🎯 Starting validation of qualified addresses only ({len(qualified_df)} records)", "VALIDATION")
        
        if qualified_df.empty:
            self.debug_callback("⚠️ No qualified addresses to validate", "VALIDATION")
            return {
                'timestamp': datetime.now(),
                'total_records': 0,
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
        
        # Convert qualified DataFrame to records list (removing qualification columns for validation)
        validation_columns = ['first_name', 'last_name', 'street_address', 'city', 'state', 'zip_code', 'source_file', 'source_row_number']
        records = qualified_df[validation_columns].to_dict('records')
        
        # Run batch validation on qualified addresses only
        return self.validate_batch_records(
            records=records,
            include_suggestions=include_suggestions,
            max_records=max_records,
            source_info={'qualified_addresses_only': True, 'original_qualified_count': len(qualified_df)}
        )
    
    def generate_comprehensive_preview(self, standardization_result: Dict) -> Dict:
        """
        Generate comprehensive preview of standardization and qualification results (NEW METHOD)
        
        Args:
            standardization_result: Result from standardize_and_qualify_csv_files
            
        Returns:
            Dict with preview data formatted for UI display
        """
        
        self.debug_callback("📋 Generating comprehensive preview", "PREVIEW")
        
        if not standardization_result['success']:
            return {
                'success': False,
                'error': standardization_result.get('error', 'Unknown error')
            }
        
        standardized_df = standardization_result['standardized_data']
        qualified_df = standardization_result['qualified_data']
        disqualified_df = standardization_result['disqualified_data']
        qualification_summary = standardization_result['qualification_summary']
        
        # Generate preview samples
        qualified_sample = qualified_df.head(10) if not qualified_df.empty else pd.DataFrame()
        disqualified_sample = disqualified_df.head(10) if not disqualified_df.empty else pd.DataFrame()
        
        # Error analysis
        error_analysis = {}
        if not disqualified_df.empty and 'qualification_errors' in disqualified_df.columns:
            all_errors = []
            for errors_str in disqualified_df['qualification_errors']:
                if errors_str:
                    all_errors.extend(errors_str.split('; '))
            
            for error in all_errors:
                error_analysis[error] = error_analysis.get(error, 0) + 1
        
        # File-by-file breakdown
        file_breakdown = {}
        for file_info in qualification_summary.get('files_summary', []):
            file_breakdown[file_info['file_name']] = {
                'total': file_info['total_rows'],
                'qualified': file_info['qualified_rows'],
                'rate': file_info['qualification_rate']
            }
        
        preview_data = {
            'success': True,
            'overview': {
                'total_files': qualification_summary['total_files'],
                'total_rows': qualification_summary['total_rows'],
                'qualified_rows': qualification_summary['qualified_rows'],
                'disqualified_rows': qualification_summary['disqualified_rows'],
                'qualification_rate': qualification_summary['qualification_rate'],
                'ready_for_usps': qualification_summary['ready_for_usps']
            },
            'qualified_preview': {
                'count': len(qualified_df),
                'sample_data': qualified_sample.to_dict('records') if not qualified_sample.empty else [],
                'columns': list(qualified_df.columns) if not qualified_df.empty else []
            },
            'disqualified_preview': {
                'count': len(disqualified_df),
                'sample_data': disqualified_sample.to_dict('records') if not disqualified_sample.empty else [],
                'error_analysis': error_analysis,
                'top_errors': sorted(error_analysis.items(), key=lambda x: x[1], reverse=True)[:5]
            },
            'file_breakdown': file_breakdown,
            'standardization_info': standardization_result['standardization_info']
        }
        
        self.debug_callback(f"✅ Preview generated: {len(qualified_df)} qualified, {len(disqualified_df)} disqualified", "PREVIEW")
        return preview_data
    
    def process_complete_pipeline_with_preview(self, file_data_list: List[Tuple[pd.DataFrame, str]], 
                                            include_suggestions: bool = True, max_records: Optional[int] = None) -> Dict:
        """
        Complete pipeline with standardization preview and qualified-only validation (NEW METHOD)
        
        Args:
            file_data_list: List of (DataFrame, filename) tuples
            include_suggestions: Whether to include suggestions in validation
            max_records: Maximum records to validate (applied to qualified addresses only)
            
        Returns:
            Dict with complete results including preview and validation
        """
        
        self.debug_callback(f"🚀 Starting complete pipeline with preview for {len(file_data_list)} files", "PIPELINE")
        pipeline_start = time.time()
        
        try:
            # Step 1: Standardize and qualify addresses
            self.debug_callback("📋 Step 1: Standardizing and qualifying addresses", "PIPELINE")
            standardization_result = self.standardize_and_qualify_csv_files(file_data_list)
            
            if not standardization_result['success']:
                return {
                    'success': False,
                    'error': 'Standardization failed: ' + standardization_result.get('error', 'Unknown error'),
                    'stage': 'standardization'
                }
            
            # Step 2: Generate comprehensive preview
            self.debug_callback("📋 Step 2: Generating comprehensive preview", "PIPELINE")
            preview_result = self.generate_comprehensive_preview(standardization_result)
            
            if not preview_result['success']:
                return {
                    'success': False,
                    'error': 'Preview generation failed: ' + preview_result.get('error', 'Unknown error'),
                    'stage': 'preview'
                }
            
            # Step 3: Validate qualified addresses only
            qualified_df = standardization_result['qualified_data']
            
            if qualified_df.empty:
                self.debug_callback("⚠️ No qualified addresses to validate", "PIPELINE")
                validation_result = {
                    'timestamp': datetime.now(),
                    'total_records': 0,
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
            else:
                self.debug_callback(f"🔍 Step 3: Validating {len(qualified_df)} qualified addresses", "PIPELINE")
                validation_result = self.validate_qualified_addresses_only(
                    qualified_df=qualified_df,
                    include_suggestions=include_suggestions,
                    max_records=max_records
                )
            
            # Step 4: Combine all results
            total_duration = int((time.time() - pipeline_start) * 1000)
            performance_tracker.track("complete_pipeline_with_preview", total_duration, True)
            
            combined_result = {
                'success': True,
                'pipeline_duration_ms': total_duration,
                'standardization': standardization_result,
                'preview': preview_result,
                'validation': validation_result,
                'summary': {
                    'files_processed': len(file_data_list),
                    'total_source_rows': sum(len(df) for df, _ in file_data_list),
                    'standardized_rows': standardization_result['total_rows'],
                    'qualified_rows': standardization_result['qualified_rows'],
                    'disqualified_rows': standardization_result['disqualified_rows'],
                    'validated_rows': validation_result['processed_records'],
                    'successful_validations': validation_result['successful_validations'],
                    'failed_validations': validation_result['failed_validations'],
                    'qualification_rate': standardization_result['qualification_summary']['qualification_rate']
                }
            }
            
            self.debug_callback(f"🎉 Complete pipeline with preview finished ({total_duration}ms)", "PIPELINE")
            return combined_result
            
        except Exception as e:
            error_msg = f"Pipeline with preview failed: {str(e)}"
            self.debug_callback(f"❌ {error_msg}", "PIPELINE")
            
            total_duration = int((time.time() - pipeline_start) * 1000)
            performance_tracker.track("complete_pipeline_with_preview", total_duration, False)
            
            return {
                'success': False,
                'error': error_msg,
                'pipeline_duration_ms': total_duration,
                'stage': 'unknown'
            }
    
    # LEGACY METHODS (keeping for backward compatibility)
    
    def standardize_csv_files(self, file_data_list: List[Tuple[pd.DataFrame, str]]) -> Dict:
        """
        Legacy method: Standardize multiple CSV files (no qualification)
        """
        self.debug_callback(f"📦 Starting legacy CSV standardization for {len(file_data_list)} files", "STANDARDIZATION")
        start_time = time.time()
        
        try:
            # Use address standardizer to process files
            standardized_df, standardization_info = self.address_standardizer.standardize_multiple_files(file_data_list)
            
            # Get summary (legacy format without qualification details)
            summary = {
                'successful_files': len([info for info in standardization_info if 'error' not in info]),
                'total_rows_processed': len(standardized_df),
                'files_with_combined_addresses': len([info for info in standardization_info if info.get('combined_address_parsed', False)]),
                'common_errors': {}
            }
            
            duration = int((time.time() - start_time) * 1000)
            performance_tracker.track("csv_standardization", duration, summary['successful_files'] > 0)
            
            result = {
                'success': True,
                'standardized_data': standardized_df,
                'standardization_info': standardization_info,
                'summary': summary,
                'processing_time_ms': duration,
                'total_rows': len(standardized_df)
            }
            
            self.debug_callback(f"✅ Legacy CSV standardization completed ({duration}ms): {len(standardized_df)} rows", "STANDARDIZATION")
            return result
            
        except Exception as e:
            error_msg = f"Legacy CSV standardization failed: {str(e)}"
            self.debug_callback(f"❌ {error_msg}", "STANDARDIZATION")
            
            duration = int((time.time() - start_time) * 1000)
            performance_tracker.track("csv_standardization", duration, False)
            
            return {
                'success': False,
                'error': error_msg,
                'processing_time_ms': duration,
                'total_rows': 0
            }
    
    def validate_batch_records(self, records: List[Dict], include_suggestions: bool = True, 
                             max_records: Optional[int] = None, source_info: Optional[Dict] = None) -> Dict:
        """
        Enhanced batch validation with standardization support
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
            'source_info': source_info or {},
            'summary': {
                'business_addresses': 0,
                'residential_addresses': 0,
                'unknown_addresses': 0,
                'corrections_made': 0,
                'files_processed': source_info.get('files_processed', 0) if source_info else 0
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
                
                # Get source file info if available
                source_file = record.get('source_file', 'unknown')
                source_row = record.get('source_row_number', i + 1)
                
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
                    'source_file': source_file,
                    'source_row': source_row,
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
                    'source_file': record.get('source_file', 'unknown'),
                    'source_row': record.get('source_row_number', i + 1),
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
    
    def validate_standardized_csv_data(self, standardized_df: pd.DataFrame, include_suggestions: bool = True, 
                                     max_records: Optional[int] = None, standardization_info: Optional[List[Dict]] = None) -> Dict:
        """
        Validate already standardized CSV data
        """
        
        self.debug_callback(f"🎯 Starting validation of standardized data ({len(standardized_df)} rows)", "SERVICE")
        
        # Convert DataFrame to records list
        records = standardized_df.to_dict('records')
        
        # Prepare source info
        source_info = {
            'standardization_performed': True,
            'files_processed': len(standardization_info) if standardization_info else 1,
            'total_source_rows': len(standardized_df),
            'standardization_info': standardization_info
        }
        
        # Run batch validation
        return self.validate_batch_records(
            records=records,
            include_suggestions=include_suggestions,
            max_records=max_records,
            source_info=source_info
        )
    
    def process_multiple_csv_files(self, file_data_list: List[Tuple[pd.DataFrame, str]], 
                                 include_suggestions: bool = True, max_records: Optional[int] = None) -> Dict:
        """
        Legacy method: Complete pipeline without qualification preview
        """
        
        self.debug_callback(f"🚀 Starting legacy pipeline for {len(file_data_list)} files", "PIPELINE")
        pipeline_start = time.time()
        
        try:
            # Step 1: Standardize CSV files (legacy method)
            self.debug_callback("📋 Step 1: Standardizing CSV files", "PIPELINE")
            standardization_result = self.standardize_csv_files(file_data_list)
            
            if not standardization_result['success']:
                return {
                    'success': False,
                    'error': 'Standardization failed: ' + standardization_result.get('error', 'Unknown error'),
                    'stage': 'standardization'
                }
            
            standardized_df = standardization_result['standardized_data']
            standardization_info = standardization_result['standardization_info']
            
            self.debug_callback(f"✅ Standardization complete: {len(standardized_df)} rows ready for validation", "PIPELINE")
            
            # Step 2: Validate standardized data
            self.debug_callback("🔍 Step 2: Validating standardized data", "PIPELINE")
            validation_result = self.validate_standardized_csv_data(
                standardized_df=standardized_df,
                include_suggestions=include_suggestions,
                max_records=max_records,
                standardization_info=standardization_info
            )
            
            # Step 3: Combine results
            total_duration = int((time.time() - pipeline_start) * 1000)
            performance_tracker.track("complete_pipeline", total_duration, True)
            
            combined_result = {
                'success': True,
                'pipeline_duration_ms': total_duration,
                'standardization': standardization_result,
                'validation': validation_result,
                'summary': {
                    'files_processed': len(file_data_list),
                    'total_source_rows': sum(len(df) for df, _ in file_data_list),
                    'standardized_rows': len(standardized_df),
                    'validated_rows': validation_result['processed_records'],
                    'successful_validations': validation_result['successful_validations'],
                    'failed_validations': validation_result['failed_validations']
                }
            }
            
            self.debug_callback(f"🎉 Legacy pipeline finished ({total_duration}ms)", "PIPELINE")
            return combined_result
            
        except Exception as e:
            error_msg = f"Legacy pipeline failed: {str(e)}"
            self.debug_callback(f"❌ {error_msg}", "PIPELINE")
            
            total_duration = int((time.time() - pipeline_start) * 1000)
            performance_tracker.track("complete_pipeline", total_duration, False)
            
            return {
                'success': False,
                'error': error_msg,
                'pipeline_duration_ms': total_duration,
                'stage': 'unknown'
            }
    
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
            'address_standardization_available': True,
            'us_qualification_available': True,
            'multi_file_processing_available': True,
            'preview_generation_available': True,
            'usps_configured': self.address_validator is not None,
            'performance_tracking': True,
            'debug_logging': True,
            'service_uptime': datetime.now().isoformat()
        }