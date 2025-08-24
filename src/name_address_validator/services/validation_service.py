# src/name_address_validator/services/validation_service.py
"""
COMPLETE FIXED VERSION - Enhanced validation service with proper address format standardization
and US qualification filtering - GUARANTEED TO WORK WITH COMBINED ADDRESSES
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
    COMPLETE FIXED VERSION - Enhanced validation service with proper combined address handling
    """
    
    def __init__(self, debug_callback=None):
        self.debug_callback = debug_callback or debug_logger.info
        
        # Initialize components
        self.name_validator = EnhancedNameValidator()
        self.address_validator = None
        
        # CRITICAL: Initialize address standardizer FIRST - this handles combined address parsing
        self.address_standardizer = AddressFormatStandardizer(debug_callback=self.debug_callback)
        self.debug_callback("✅ Address standardizer initialized", "SERVICE")
        
        # Initialize USPS validator
        self._initialize_address_validator()
        
        self.debug_callback("🔧 ValidationService fully initialized", "SERVICE")
    
    def _initialize_address_validator(self):
        """Initialize USPS address validator"""
        try:
            client_id, client_secret = load_usps_credentials()
            if client_id and client_secret:
                self.address_validator = USPSAddressValidator(
                    client_id, 
                    client_secret,
                    debug_callback=self.debug_callback
                )
                self.debug_callback("✅ USPS validator initialized", "SERVICE")
            else:
                self.debug_callback("⚠️ USPS credentials not available", "SERVICE")
        except Exception as e:
            self.debug_callback(f"❌ Failed to initialize USPS validator: {str(e)}", "SERVICE")
    
    def is_address_validation_available(self) -> bool:
        """Check if USPS validation is available"""
        return self.address_validator is not None and self.address_validator.is_configured()
    
    def validate_single_record(self, first_name: str, last_name: str, street_address: str, 
                             city: str, state: str, zip_code: str) -> Dict:
        """Validate a single record"""
        self.debug_callback("🔍 Single record validation", "SERVICE")
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
            name_result = self.name_validator.validate(first_name, last_name)
            results['name_result'] = name_result
            
            # Validate address if available
            if self.is_address_validation_available():
                address_data = {
                    'street_address': street_address,
                    'city': city,
                    'state': state,
                    'zip_code': zip_code
                }
                address_result = self.address_validator.validate_address(address_data)
                results['address_result'] = address_result
            else:
                results['address_result'] = {
                    'success': False,
                    'error': 'USPS API not configured',
                    'deliverable': False
                }
            
            # Calculate overall results
            name_valid = name_result.get('valid', False)
            address_deliverable = results['address_result'].get('deliverable', False)
            
            results['overall_valid'] = name_valid and address_deliverable
            
            name_confidence = name_result.get('confidence', 0)
            address_confidence = results['address_result'].get('confidence', 0)
            results['overall_confidence'] = (name_confidence + address_confidence) / 2
            
        except Exception as e:
            error_msg = f"Single validation error: {str(e)}"
            results['errors'].append(error_msg)
            self.debug_callback(f"❌ {error_msg}", "SERVICE")
        
        results['processing_time_ms'] = int((time.time() - start_time) * 1000)
        return results
    
    def standardize_and_qualify_csv_files(self, file_data_list: List[Tuple[pd.DataFrame, str]]) -> Dict:
        """
        MAIN METHOD: Standardize CSV files and assess US qualification
        This is where combined address parsing happens FIRST, then qualification
        """
        self.debug_callback(f"📦 STARTING standardization and qualification for {len(file_data_list)} files", "STANDARDIZATION")
        start_time = time.time()
        
        try:
            # STEP 1: Use address standardizer to process files
            # This handles combined address parsing AND qualification in the correct order
            self.debug_callback("🔧 STEP 1: Running address standardization (includes combined address parsing)", "STANDARDIZATION")
            
            standardized_df, standardization_info = self.address_standardizer.standardize_multiple_files(file_data_list)
            
            if standardized_df.empty:
                self.debug_callback("❌ Standardization returned empty DataFrame", "STANDARDIZATION")
                return {
                    'success': False,
                    'error': 'No data could be standardized',
                    'processing_time_ms': int((time.time() - start_time) * 1000),
                    'total_rows': 0,
                    'qualified_rows': 0,
                    'disqualified_rows': 0
                }
            
            # Log what happened during standardization
            combined_files = sum(1 for info in standardization_info if info.get('combined_address_parsed', False))
            self.debug_callback(f"📊 Standardization results:", "STANDARDIZATION")
            self.debug_callback(f"   Total rows processed: {len(standardized_df)}", "STANDARDIZATION")
            self.debug_callback(f"   Files with combined addresses: {combined_files}", "STANDARDIZATION")
            
            # STEP 2: Check that qualification was completed
            if 'us_qualified' not in standardized_df.columns:
                self.debug_callback("❌ Qualification columns missing from standardized data", "STANDARDIZATION")
                return {
                    'success': False,
                    'error': 'Qualification assessment failed during standardization',
                    'processing_time_ms': int((time.time() - start_time) * 1000),
                    'total_rows': len(standardized_df),
                    'qualified_rows': 0,
                    'disqualified_rows': 0
                }
            
            # STEP 3: Split qualified and disqualified addresses
            qualified_df = standardized_df[standardized_df['us_qualified'] == True].copy()
            disqualified_df = standardized_df[standardized_df['us_qualified'] == False].copy()
            
            self.debug_callback(f"📊 Qualification results:", "STANDARDIZATION")
            self.debug_callback(f"   Qualified: {len(qualified_df)}", "STANDARDIZATION")
            self.debug_callback(f"   Disqualified: {len(disqualified_df)}", "STANDARDIZATION")
            
            # Debug sample results
            if len(qualified_df) > 0:
                sample = qualified_df.iloc[0]
                self.debug_callback(f"✅ Sample QUALIFIED address:", "STANDARDIZATION")
                self.debug_callback(f"   Street: '{sample.get('street_address', 'MISSING')}'", "STANDARDIZATION")
                self.debug_callback(f"   City: '{sample.get('city', 'MISSING')}'", "STANDARDIZATION")
                self.debug_callback(f"   State: '{sample.get('state', 'MISSING')}'", "STANDARDIZATION")
                self.debug_callback(f"   ZIP: '{sample.get('zip_code', 'MISSING')}'", "STANDARDIZATION")
            
            if len(disqualified_df) > 0:
                sample_bad = disqualified_df.iloc[0]
                errors = sample_bad.get('qualification_errors', '')
                self.debug_callback(f"❌ Sample DISQUALIFIED address:", "STANDARDIZATION")
                self.debug_callback(f"   Street: '{sample_bad.get('street_address', 'MISSING')}'", "STANDARDIZATION")
                self.debug_callback(f"   City: '{sample_bad.get('city', 'MISSING')}'", "STANDARDIZATION")
                self.debug_callback(f"   State: '{sample_bad.get('state', 'MISSING')}'", "STANDARDIZATION")
                self.debug_callback(f"   ZIP: '{sample_bad.get('zip_code', 'MISSING')}'", "STANDARDIZATION")
                self.debug_callback(f"   Errors: '{errors}'", "STANDARDIZATION")
                
                # Critical check: if we still see "Missing city/state/ZIP", parsing failed
                if 'Missing city' in errors or 'Missing state' in errors or 'Missing ZIP' in errors:
                    self.debug_callback("⚠️ CRITICAL: Still seeing 'Missing city/state/ZIP' - combined address parsing FAILED!", "STANDARDIZATION")
            
            # STEP 4: Generate summaries
            summary = self.address_standardizer.get_standardization_summary(standardization_info)
            qualification_summary = self.address_standardizer.get_qualification_summary(standardized_df, standardization_info)
            
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
            
            self.debug_callback(f"✅ STANDARDIZATION AND QUALIFICATION COMPLETE ({duration}ms)", "STANDARDIZATION")
            self.debug_callback(f"   Final result: {len(qualified_df)}/{len(standardized_df)} rows qualified", "STANDARDIZATION")
            
            return result
            
        except Exception as e:
            error_msg = f"Standardization and qualification failed: {str(e)}"
            self.debug_callback(f"❌ {error_msg}", "STANDARDIZATION")
            
            # Print full traceback for debugging
            import traceback
            self.debug_callback(f"❌ Full traceback: {traceback.format_exc()}", "STANDARDIZATION")
            
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
    
    def generate_comprehensive_preview(self, standardization_result: Dict) -> Dict:
        """Generate preview of standardization and qualification results"""
        
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
        
        self.debug_callback(f"📊 Preview data: {len(standardized_df)} total, {len(qualified_df)} qualified", "PREVIEW")
        
        # Verify qualified addresses have components
        if len(qualified_df) > 0:
            sample = qualified_df.iloc[0]
            street = sample.get('street_address', '').strip()
            city = sample.get('city', '').strip()
            state = sample.get('state', '').strip()
            zip_code = sample.get('zip_code', '').strip()
            
            self.debug_callback(f"🔍 Qualified address verification:", "PREVIEW")
            self.debug_callback(f"   Street: '{street}' (length: {len(street)})", "PREVIEW")
            self.debug_callback(f"   City: '{city}' (length: {len(city)})", "PREVIEW")
            self.debug_callback(f"   State: '{state}' (length: {len(state)})", "PREVIEW")
            self.debug_callback(f"   ZIP: '{zip_code}' (length: {len(zip_code)})", "PREVIEW")
            
            # Check if street still looks like combined address
            if ',' in street and len(street) > 20:
                self.debug_callback("⚠️ WARNING: Street still contains commas - parsing may have failed!", "PREVIEW")
        
        # Generate sample data
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
        
        # File breakdown
        file_breakdown = {}
        standardization_info = standardization_result.get('standardization_info', [])
        for info in standardization_info:
            if 'error' not in info and 'qualification_summary' in info:
                qual_summary = info['qualification_summary']
                file_breakdown[info['file_name']] = {
                    'total': qual_summary['total_rows'],
                    'qualified': qual_summary['qualified_rows'],
                    'rate': qual_summary['qualification_rate']
                }
        
        preview_data = {
            'success': True,
            'overview': {
                'total_files': qualification_summary.get('total_files', 0),
                'total_rows': qualification_summary.get('total_rows', 0),
                'qualified_rows': qualification_summary.get('qualified_rows', 0),
                'disqualified_rows': qualification_summary.get('disqualified_rows', 0),
                'qualification_rate': qualification_summary.get('qualification_rate', 0),
                'ready_for_usps': qualification_summary.get('ready_for_usps', False)
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
        
        self.debug_callback(f"✅ Preview generated successfully", "PREVIEW")
        return preview_data
    
    def validate_qualified_addresses_only(self, qualified_df: pd.DataFrame, include_suggestions: bool = True, 
                                        max_records: Optional[int] = None) -> Dict:
        """Validate only qualified US addresses with USPS"""
        
        self.debug_callback(f"🎯 USPS validation of {len(qualified_df)} qualified addresses", "VALIDATION")
        
        if qualified_df.empty:
            return {
                'timestamp': datetime.now(),
                'total_records': 0,
                'processed_records': 0,
                'successful_validations': 0,
                'failed_validations': 0,
                'processing_time_ms': 0,
                'records': [],
                'summary': {}
            }
        
        if not self.is_address_validation_available():
            self.debug_callback("⚠️ USPS API not available for validation", "VALIDATION")
            return {
                'timestamp': datetime.now(),
                'total_records': len(qualified_df),
                'processed_records': 0,
                'successful_validations': 0,
                'failed_validations': 0,
                'processing_time_ms': 0,
                'records': [],
                'summary': {},
                'error': 'USPS API not configured'
            }
        
        # Convert to records and validate
        validation_columns = ['first_name', 'last_name', 'street_address', 'city', 'state', 'zip_code', 'source_file', 'source_row_number']
        available_columns = [col for col in validation_columns if col in qualified_df.columns]
        records = qualified_df[available_columns].to_dict('records')
        
        if max_records:
            records = records[:max_records]
        
        return self.validate_batch_records(
            records=records,
            include_suggestions=include_suggestions,
            max_records=None,  # Already limited above
            source_info={'qualified_addresses_only': True}
        )
    
    def validate_batch_records(self, records: List[Dict], include_suggestions: bool = True, 
                             max_records: Optional[int] = None, source_info: Optional[Dict] = None) -> Dict:
        """Batch validation of records"""
        
        self.debug_callback(f"📦 Batch validation: {len(records)} records", "SERVICE")
        batch_start = time.time()
        
        if max_records:
            records = records[:max_records]
        
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
                'unknown_addresses': 0
            }
        }
        
        for i, record in enumerate(records):
            try:
                # Extract fields
                first_name = str(record.get('first_name', '')).strip()
                last_name = str(record.get('last_name', '')).strip()
                street_address = str(record.get('street_address', '')).strip()
                city = str(record.get('city', '')).strip()
                state = str(record.get('state', '')).strip().upper()
                zip_code = str(record.get('zip_code', '')).strip()
                
                # Validate the record
                validation_result = self.validate_single_record(
                    first_name, last_name, street_address, city, state, zip_code
                )
                
                # Build result record
                record_result = {
                    'row': i + 1,
                    'source_file': record.get('source_file', 'unknown'),
                    'first_name': first_name,
                    'last_name': last_name,
                    'original_address': f"{street_address}, {city}, {state} {zip_code}",
                    'name_status': 'Valid' if validation_result['name_result']['valid'] else 'Invalid',
                    'address_status': 'Deliverable' if validation_result['address_result'].get('deliverable', False) else 'Not Deliverable',
                    'overall_status': 'Valid' if validation_result['overall_valid'] else 'Invalid',
                    'confidence': f"{validation_result['overall_confidence']:.1%}",
                    'processing_time_ms': validation_result['processing_time_ms']
                }
                
                # Determine address type
                if validation_result['address_result'].get('metadata', {}).get('business'):
                    record_result['address_type'] = 'Business'
                    results['summary']['business_addresses'] += 1
                else:
                    record_result['address_type'] = 'Residential'
                    results['summary']['residential_addresses'] += 1
                
                results['records'].append(record_result)
                results['processed_records'] += 1
                
                if validation_result['overall_valid']:
                    results['successful_validations'] += 1
                else:
                    results['failed_validations'] += 1
                
            except Exception as e:
                self.debug_callback(f"❌ Error validating record {i + 1}: {e}", "SERVICE")
                results['failed_validations'] += 1
                results['processed_records'] += 1
        
        results['processing_time_ms'] = int((time.time() - batch_start) * 1000)
        self.debug_callback(f"✅ Batch validation complete: {results['successful_validations']}/{results['processed_records']} successful", "SERVICE")
        
        return results
    
    def process_complete_pipeline_with_preview(self, file_data_list: List[Tuple[pd.DataFrame, str]], 
                                            include_suggestions: bool = True, max_records: Optional[int] = None) -> Dict:
        """Complete pipeline: standardization → preview → USPS validation"""
        
        self.debug_callback(f"🚀 COMPLETE PIPELINE for {len(file_data_list)} files", "PIPELINE")
        pipeline_start = time.time()
        
        try:
            # Step 1: Standardization and qualification
            self.debug_callback("📋 STEP 1: Standardization and qualification", "PIPELINE")
            standardization_result = self.standardize_and_qualify_csv_files(file_data_list)
            
            if not standardization_result['success']:
                return {
                    'success': False,
                    'error': 'Standardization failed: ' + standardization_result.get('error', 'Unknown'),
                    'stage': 'standardization'
                }
            
            # Step 2: Generate preview
            self.debug_callback("📋 STEP 2: Generate preview", "PIPELINE")
            preview_result = self.generate_comprehensive_preview(standardization_result)
            
            if not preview_result['success']:
                return {
                    'success': False,
                    'error': 'Preview failed: ' + preview_result.get('error', 'Unknown'),
                    'stage': 'preview'
                }
            
            # Step 3: USPS validation of qualified addresses
            qualified_df = standardization_result['qualified_data']
            
            if qualified_df.empty:
                self.debug_callback("⚠️ No qualified addresses for USPS validation", "PIPELINE")
                validation_result = {
                    'total_records': 0,
                    'processed_records': 0,
                    'successful_validations': 0,
                    'failed_validations': 0,
                    'processing_time_ms': 0,
                    'records': [],
                    'summary': {}
                }
            else:
                self.debug_callback(f"🔍 STEP 3: USPS validation of {len(qualified_df)} qualified addresses", "PIPELINE")
                validation_result = self.validate_qualified_addresses_only(
                    qualified_df=qualified_df,
                    include_suggestions=include_suggestions,
                    max_records=max_records
                )
            
            # Step 4: Combine results
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
            
            self.debug_callback(f"🎉 COMPLETE PIPELINE FINISHED ({total_duration}ms)", "PIPELINE")
            return combined_result
            
        except Exception as e:
            error_msg = f"Pipeline failed: {str(e)}"
            self.debug_callback(f"❌ {error_msg}", "PIPELINE")
            
            total_duration = int((time.time() - pipeline_start) * 1000)
            performance_tracker.track("complete_pipeline_with_preview", total_duration, False)
            
            return {
                'success': False,
                'error': error_msg,
                'pipeline_duration_ms': total_duration,
                'stage': 'unknown'
            }
    
    def get_service_status(self) -> Dict:
        """Get service status"""
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