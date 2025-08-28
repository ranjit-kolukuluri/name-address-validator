# src/name_address_validator/services/enhanced_validation_service.py
"""
Enhanced ValidationService with name-only validation workflows
Extends the existing validation service to support intelligent name parsing and validation
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
from ..utils.name_format_standardizer import NameFormatStandardizer


class EnhancedValidationService:
    """
    Enhanced validation service with name-only validation capabilities
    Supports both existing address validation and new name-only workflows
    """
    
    def __init__(self, debug_callback=None):
        self.debug_callback = debug_callback or debug_logger.info
        
        # Initialize existing components
        self.name_validator = EnhancedNameValidator()
        self.address_validator = None
        self.address_standardizer = AddressFormatStandardizer(debug_callback=self.debug_callback)
        
        # Initialize new name standardizer
        self.name_standardizer = NameFormatStandardizer(debug_callback=self.debug_callback)
        self.debug_callback("✅ Name standardizer initialized", "SERVICE")
        
        # Initialize USPS validator
        self._initialize_address_validator()
        
        self.debug_callback("🔧 Enhanced ValidationService fully initialized", "SERVICE")
    
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
    
    def is_name_validation_available(self) -> bool:
        """Check if name validation is available"""
        return self.name_validator is not None
    
    def validate_single_record(self, first_name: str, last_name: str, street_address: str, 
                             city: str, state: str, zip_code: str) -> Dict:
        """Validate a single record - existing functionality preserved"""
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
    
    # NEW NAME-ONLY VALIDATION METHODS
    
    def standardize_and_parse_names_from_csv(self, file_data_list: List[Tuple[pd.DataFrame, str]]) -> Dict:
        """
        NEW: Standardize CSV files and parse names intelligently
        This is for name-only workflows
        """
        self.debug_callback(f"📦 STARTING name standardization for {len(file_data_list)} files", "NAME_STANDARDIZATION")
        start_time = time.time()
        
        try:
            # Use name standardizer to process files
            standardized_df, standardization_info = self.name_standardizer.standardize_multiple_files(file_data_list)
            
            if standardized_df.empty:
                self.debug_callback("❌ Name standardization returned empty DataFrame", "NAME_STANDARDIZATION")
                return {
                    'success': False,
                    'error': 'No data could be standardized',
                    'processing_time_ms': int((time.time() - start_time) * 1000),
                    'total_rows': 0,
                    'valid_names': 0,
                    'invalid_names': 0
                }
            
            # Generate summary
            summary = self.name_standardizer.get_name_standardization_summary(standardization_info)
            
            duration = int((time.time() - start_time) * 1000)
            performance_tracker.track("name_standardization_parsing", duration, summary['successful_files'] > 0)
            
            result = {
                'success': True,
                'standardized_data': standardized_df,
                'standardization_info': standardization_info,
                'summary': summary,
                'processing_time_ms': duration,
                'total_rows': len(standardized_df),
                'valid_names': summary['valid_records'],
                'invalid_names': summary['invalid_records']
            }
            
            self.debug_callback(f"✅ NAME STANDARDIZATION COMPLETE ({duration}ms)", "NAME_STANDARDIZATION")
            self.debug_callback(f"   Final result: {summary['valid_records']}/{summary['total_records']} names valid", "NAME_STANDARDIZATION")
            
            return result
            
        except Exception as e:
            error_msg = f"Name standardization failed: {str(e)}"
            self.debug_callback(f"❌ {error_msg}", "NAME_STANDARDIZATION")
            
            duration = int((time.time() - start_time) * 1000)
            performance_tracker.track("name_standardization_parsing", duration, False)
            
            return {
                'success': False,
                'error': error_msg,
                'processing_time_ms': duration,
                'total_rows': 0,
                'valid_names': 0,
                'invalid_names': 0
            }
    
    def generate_name_validation_preview(self, standardization_result: Dict) -> Dict:
        """Generate preview of name standardization results"""
        
        self.debug_callback("📋 Generating name validation preview", "NAME_PREVIEW")
        
        if not standardization_result['success']:
            return {
                'success': False,
                'error': standardization_result.get('error', 'Unknown error')
            }
        
        standardized_df = standardization_result['standardized_data']
        summary = standardization_result['summary']
        
        # Generate sample data
        valid_df = standardized_df[standardized_df['name_valid'] == True] if 'name_valid' in standardized_df.columns else standardized_df
        invalid_df = standardized_df[standardized_df['name_valid'] == False] if 'name_valid' in standardized_df.columns else pd.DataFrame()
        
        valid_sample = valid_df.head(10) if not valid_df.empty else pd.DataFrame()
        invalid_sample = invalid_df.head(10) if not invalid_df.empty else pd.DataFrame()
        
        # Quality analysis
        quality_analysis = {}
        if not standardized_df.empty and 'name_quality_issues' in standardized_df.columns:
            all_issues = []
            for issues_str in standardized_df['name_quality_issues']:
                if issues_str and issues_str != 'No issues':
                    all_issues.extend(issues_str.split('; '))
            
            for issue in all_issues:
                quality_analysis[issue] = quality_analysis.get(issue, 0) + 1
        
        # File breakdown
        file_breakdown = {}
        standardization_info = standardization_result.get('standardization_info', [])
        for info in standardization_info:
            if 'error' not in info and 'parsing_summary' in info:
                parsing_summary = info['parsing_summary']
                file_breakdown[info['file_name']] = {
                    'total': parsing_summary['total_records'],
                    'valid': parsing_summary['valid_names'],
                    'rate': parsing_summary['validation_rate']
                }
        
        preview_data = {
            'success': True,
            'overview': {
                'total_files': summary.get('total_files', 0),
                'total_records': summary.get('total_records', 0),
                'valid_names': summary.get('valid_records', 0),
                'invalid_names': summary.get('invalid_records', 0),
                'validation_rate': summary.get('overall_validation_rate', 0),
                'parsing_success_rate': summary.get('average_parsing_success_rate', 0),
                'ready_for_validation': summary.get('ready_for_name_validation', False)
            },
            'valid_preview': {
                'count': len(valid_df),
                'sample_data': valid_sample.to_dict('records') if not valid_sample.empty else [],
                'columns': list(valid_df.columns) if not valid_df.empty else []
            },
            'invalid_preview': {
                'count': len(invalid_df),
                'sample_data': invalid_sample.to_dict('records') if not invalid_sample.empty else [],
                'quality_analysis': quality_analysis,
                'top_issues': sorted(quality_analysis.items(), key=lambda x: x[1], reverse=True)[:5]
            },
            'file_breakdown': file_breakdown,
            'standardization_info': standardization_result['standardization_info']
        }
        
        self.debug_callback(f"✅ Name preview generated successfully", "NAME_PREVIEW")
        return preview_data
    
    def validate_parsed_names_batch(self, parsed_names_df: pd.DataFrame, include_suggestions: bool = True, 
                                  max_records: Optional[int] = None) -> Dict:
        """Validate parsed names in batch"""
        
        self.debug_callback(f"👥 Batch name validation of {len(parsed_names_df)} records", "NAME_VALIDATION")
        
        if parsed_names_df.empty:
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
        
        # Convert to records and validate
        validation_columns = ['first_name', 'last_name', 'middle_name', 'title', 'suffix', 'source_file', 'source_row_number']
        available_columns = [col for col in validation_columns if col in parsed_names_df.columns]
        records = parsed_names_df[available_columns].to_dict('records')
        
        if max_records:
            records = records[:max_records]
        
        return self._validate_name_batch_records(
            records=records,
            include_suggestions=include_suggestions,
            source_info={'parsed_names_only': True}
        )
    
    def _validate_name_batch_records(self, records: List[Dict], include_suggestions: bool = True, 
                                   source_info: Optional[Dict] = None) -> Dict:
        """Internal batch name validation"""
        
        self.debug_callback(f"📦 Batch name validation: {len(records)} records", "NAME_SERVICE")
        batch_start = time.time()
        
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
                'common_first_names': 0,
                'common_last_names': 0,
                'uncommon_names': 0,
                'suggestions_provided': 0
            }
        }
        
        for i, record in enumerate(records):
            try:
                # Extract name fields
                first_name = str(record.get('first_name', '')).strip()
                last_name = str(record.get('last_name', '')).strip()
                middle_name = str(record.get('middle_name', '')).strip()
                title = str(record.get('title', '')).strip()
                suffix = str(record.get('suffix', '')).strip()
                
                # Validate the name
                validation_result = self.name_validator.validate(first_name, last_name)
                
                # Build result record
                record_result = {
                    'row': i + 1,
                    'source_file': record.get('source_file', 'unknown'),
                    'first_name': first_name,
                    'last_name': last_name,
                    'middle_name': middle_name,
                    'title': title,
                    'suffix': suffix,
                    'name_status': 'Valid' if validation_result['valid'] else 'Invalid',
                    'confidence': f"{validation_result['confidence']:.1%}",
                    'errors': '; '.join(validation_result.get('errors', [])),
                    'warnings': '; '.join(validation_result.get('warnings', []))
                }
                
                # Add suggestions if requested and available
                if include_suggestions and validation_result.get('suggestions'):
                    suggestions = validation_result['suggestions']
                    
                    if 'first_name' in suggestions and suggestions['first_name']:
                        top_first = suggestions['first_name'][0]
                        record_result['first_name_suggestion'] = f"{top_first['suggestion']} ({top_first['confidence']:.1%})"
                        results['summary']['suggestions_provided'] += 1
                    
                    if 'last_name' in suggestions and suggestions['last_name']:
                        top_last = suggestions['last_name'][0]
                        record_result['last_name_suggestion'] = f"{top_last['suggestion']} ({top_last['confidence']:.1%})"
                        results['summary']['suggestions_provided'] += 1
                
                # Update summary stats
                analysis = validation_result.get('analysis', {})
                if analysis.get('first_name', {}).get('is_common'):
                    results['summary']['common_first_names'] += 1
                if analysis.get('last_name', {}).get('is_common'):
                    results['summary']['common_last_names'] += 1
                if not analysis.get('first_name', {}).get('is_common') and not analysis.get('last_name', {}).get('is_common'):
                    results['summary']['uncommon_names'] += 1
                
                results['records'].append(record_result)
                results['processed_records'] += 1
                
                if validation_result['valid']:
                    results['successful_validations'] += 1
                else:
                    results['failed_validations'] += 1
                
            except Exception as e:
                self.debug_callback(f"❌ Error validating name record {i + 1}: {e}", "NAME_SERVICE")
                results['failed_validations'] += 1
                results['processed_records'] += 1
        
        results['processing_time_ms'] = int((time.time() - batch_start) * 1000)
        self.debug_callback(f"✅ Batch name validation complete: {results['successful_validations']}/{results['processed_records']} successful", "NAME_SERVICE")
        
        return results
    
    def process_complete_name_validation_pipeline(self, file_data_list: List[Tuple[pd.DataFrame, str]], 
                                                include_suggestions: bool = True, max_records: Optional[int] = None) -> Dict:
        """Complete name validation pipeline: parsing → preview → validation"""
        
        self.debug_callback(f"🚀 COMPLETE NAME PIPELINE for {len(file_data_list)} files", "NAME_PIPELINE")
        pipeline_start = time.time()
        
        try:
            # Step 1: Name standardization and parsing
            self.debug_callback("📋 STEP 1: Name standardization and parsing", "NAME_PIPELINE")
            standardization_result = self.standardize_and_parse_names_from_csv(file_data_list)
            
            if not standardization_result['success']:
                return {
                    'success': False,
                    'error': 'Name standardization failed: ' + standardization_result.get('error', 'Unknown'),
                    'stage': 'standardization'
                }
            
            # Step 2: Generate preview
            self.debug_callback("📋 STEP 2: Generate preview", "NAME_PIPELINE")
            preview_result = self.generate_name_validation_preview(standardization_result)
            
            if not preview_result['success']:
                return {
                    'success': False,
                    'error': 'Preview failed: ' + preview_result.get('error', 'Unknown'),
                    'stage': 'preview'
                }
            
            # Step 3: Name validation of valid names
            standardized_df = standardization_result['standardized_data']
            
            if standardized_df.empty:
                self.debug_callback("⚠️ No valid names for validation", "NAME_PIPELINE")
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
                self.debug_callback(f"🔍 STEP 3: Name validation of {len(standardized_df)} parsed names", "NAME_PIPELINE")
                validation_result = self.validate_parsed_names_batch(
                    parsed_names_df=standardized_df,
                    include_suggestions=include_suggestions,
                    max_records=max_records
                )
            
            # Step 4: Combine results
            total_duration = int((time.time() - pipeline_start) * 1000)
            performance_tracker.track("complete_name_pipeline", total_duration, True)
            
            combined_result = {
                'success': True,
                'pipeline_duration_ms': total_duration,
                'standardization': standardization_result,
                'preview': preview_result,
                'validation': validation_result,
                'summary': {
                    'files_processed': len(file_data_list),
                    'total_source_rows': sum(len(df) for df, _ in file_data_list),
                    'parsed_names': standardization_result['total_rows'],
                    'valid_parsed_names': standardization_result['valid_names'],
                    'invalid_parsed_names': standardization_result['invalid_names'],
                    'validated_names': validation_result['processed_records'],
                    'successful_validations': validation_result['successful_validations'],
                    'failed_validations': validation_result['failed_validations'],
                    'parsing_success_rate': standardization_result['summary']['average_parsing_success_rate'],
                    'validation_success_rate': validation_result['successful_validations'] / validation_result['processed_records'] if validation_result['processed_records'] > 0 else 0
                }
            }
            
            self.debug_callback(f"🎉 COMPLETE NAME PIPELINE FINISHED ({total_duration}ms)", "NAME_PIPELINE")
            return combined_result
            
        except Exception as e:
            error_msg = f"Name pipeline failed: {str(e)}"
            self.debug_callback(f"❌ {error_msg}", "NAME_PIPELINE")
            
            total_duration = int((time.time() - pipeline_start) * 1000)
            performance_tracker.track("complete_name_pipeline", total_duration, False)
            
            return {
                'success': False,
                'error': error_msg,
                'pipeline_duration_ms': total_duration,
                'stage': 'unknown'
            }
    
    # EXISTING ADDRESS VALIDATION METHODS (preserved)
    
    def standardize_and_qualify_csv_files(self, file_data_list: List[Tuple[pd.DataFrame, str]]) -> Dict:
        """Existing address standardization method - preserved"""
        self.debug_callback(f"📦 STARTING address standardization for {len(file_data_list)} files", "ADDRESS_STANDARDIZATION")
        start_time = time.time()
        
        try:
            standardized_df, standardization_info = self.address_standardizer.standardize_multiple_files(file_data_list)
            
            if standardized_df.empty:
                self.debug_callback("❌ Address standardization returned empty DataFrame", "ADDRESS_STANDARDIZATION")
                return {
                    'success': False,
                    'error': 'No data could be standardized',
                    'processing_time_ms': int((time.time() - start_time) * 1000),
                    'total_rows': 0,
                    'qualified_rows': 0,
                    'disqualified_rows': 0
                }
            
            if 'us_qualified' not in standardized_df.columns:
                self.debug_callback("❌ Qualification columns missing from standardized data", "ADDRESS_STANDARDIZATION")
                return {
                    'success': False,
                    'error': 'Qualification assessment failed during standardization',
                    'processing_time_ms': int((time.time() - start_time) * 1000),
                    'total_rows': len(standardized_df),
                    'qualified_rows': 0,
                    'disqualified_rows': 0
                }
            
            qualified_df = standardized_df[standardized_df['us_qualified'] == True].copy()
            disqualified_df = standardized_df[standardized_df['us_qualified'] == False].copy()
            
            summary = self.address_standardizer.get_standardization_summary(standardization_info)
            qualification_summary = self.address_standardizer.get_qualification_summary(standardized_df, standardization_info)
            
            duration = int((time.time() - start_time) * 1000)
            performance_tracker.track("address_standardization_qualification", duration, summary['successful_files'] > 0)
            
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
            
            self.debug_callback(f"✅ ADDRESS STANDARDIZATION COMPLETE ({duration}ms)", "ADDRESS_STANDARDIZATION")
            return result
            
        except Exception as e:
            error_msg = f"Address standardization failed: {str(e)}"
            self.debug_callback(f"❌ {error_msg}", "ADDRESS_STANDARDIZATION")
            
            duration = int((time.time() - start_time) * 1000)
            performance_tracker.track("address_standardization_qualification", duration, False)
            
            return {
                'success': False,
                'error': error_msg,
                'processing_time_ms': duration,
                'total_rows': 0,
                'qualified_rows': 0,
                'disqualified_rows': 0
            }
    
    def get_service_status(self) -> Dict:
        """Get enhanced service status"""
        return {
            'name_validation_available': self.is_name_validation_available(),
            'name_parsing_available': True,
            'address_validation_available': self.is_address_validation_available(),
            'address_standardization_available': True,
            'us_qualification_available': True,
            'multi_file_processing_available': True,
            'preview_generation_available': True,
            'name_only_workflows_available': True,
            'usps_configured': self.address_validator is not None,
            'performance_tracking': True,
            'debug_logging': True,
            'service_uptime': datetime.now().isoformat()
        }