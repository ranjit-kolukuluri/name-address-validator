# src/name_address_validator/utils/address_standardizer.py
"""
Enhanced Address Format Standardizer with US Address Qualification and Filtering
"""

import pandas as pd
import re
from typing import Dict, List, Tuple, Optional, Any
from fuzzywuzzy import fuzz
import numpy as np


class AddressFormatStandardizer:
    """
    Enhanced standardizer with US address qualification and filtering
    """
    
    def __init__(self, debug_callback=None):
        self.debug_callback = debug_callback or (lambda msg, cat="STANDARDIZER": None)
        
        # Standard column mapping - target format
        self.standard_columns = {
            'first_name': 'first_name',
            'last_name': 'last_name', 
            'street_address': 'street_address',
            'city': 'city',
            'state': 'state',
            'zip_code': 'zip_code'
        }
        
        # Common column name variations and their mappings
        self.column_mappings = {
            # First Name variations
            'first_name': ['first_name', 'first', 'fname', 'given_name', 'forename', 'firstname', 'first_nm'],
            
            # Last Name variations  
            'last_name': ['last_name', 'last', 'lname', 'surname', 'family_name', 'lastname', 'last_nm'],
            
            # Street Address variations
            'street_address': [
                'street_address', 'street', 'address', 'addr', 'address1', 'street1', 
                'street_addr', 'street_line_1', 'address_line_1', 'addr1', 'street_line1',
                'house_number', 'street_name', 'full_address', 'mailing_address'
            ],
            
            # Additional address lines
            'address_line_2': [
                'address2', 'addr2', 'street2', 'address_line_2', 'street_line_2', 
                'apt', 'apartment', 'unit', 'suite', 'ste', 'floor', 'fl'
            ],
            
            # City variations
            'city': ['city', 'town', 'municipality', 'locality', 'city_name'],
            
            # State variations
            'state': ['state', 'st', 'state_code', 'province', 'region', 'state_abbr'],
            
            # ZIP Code variations
            'zip_code': [
                'zip_code', 'zip', 'zipcode', 'postal_code', 'postcode', 'zip5', 
                'zip_5', 'postal', 'mail_code', 'zip4', 'zip_4'
            ]
        }
        
        # Patterns for detecting combined address fields
        self.combined_address_patterns = [
            r'^(.+?),\s*([^,]+),\s*([A-Z]{2})\s+(\d{5}(?:-\d{4})?)$',  # "123 Main St, City, ST 12345"
            r'^(.+?)\s+([^,]+),?\s+([A-Z]{2})\s+(\d{5}(?:-\d{4})?)$',   # "123 Main St City ST 12345"
            r'^(.+?),\s*([^,]+)\s+([A-Z]{2})\s+(\d{5}(?:-\d{4})?)$'     # "123 Main St, City ST 12345"
        ]
        
        # US States for validation
        self.us_states = {
            'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
            'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
            'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
            'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
            'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY', 'DC'
        }
        
        # US State name to abbreviation mapping for conversion
        self.state_name_to_abbr = {
            'alabama': 'AL', 'alaska': 'AK', 'arizona': 'AZ', 'arkansas': 'AR',
            'california': 'CA', 'colorado': 'CO', 'connecticut': 'CT', 'delaware': 'DE',
            'florida': 'FL', 'georgia': 'GA', 'hawaii': 'HI', 'idaho': 'ID',
            'illinois': 'IL', 'indiana': 'IN', 'iowa': 'IA', 'kansas': 'KS',
            'kentucky': 'KY', 'louisiana': 'LA', 'maine': 'ME', 'maryland': 'MD',
            'massachusetts': 'MA', 'michigan': 'MI', 'minnesota': 'MN', 'mississippi': 'MS',
            'missouri': 'MO', 'montana': 'MT', 'nebraska': 'NE', 'nevada': 'NV',
            'new hampshire': 'NH', 'new jersey': 'NJ', 'new mexico': 'NM', 'new york': 'NY',
            'north carolina': 'NC', 'north dakota': 'ND', 'ohio': 'OH', 'oklahoma': 'OK',
            'oregon': 'OR', 'pennsylvania': 'PA', 'rhode island': 'RI', 'south carolina': 'SC',
            'south dakota': 'SD', 'tennessee': 'TN', 'texas': 'TX', 'utah': 'UT',
            'vermont': 'VT', 'virginia': 'VA', 'washington': 'WA', 'west virginia': 'WV',
            'wisconsin': 'WI', 'wyoming': 'WY', 'district of columbia': 'DC'
        }
    
    def log(self, message: str, category: str = "STANDARDIZER"):
        """Log debug message"""
        self.debug_callback(message, category)
    
    def detect_column_mapping(self, df: pd.DataFrame) -> Dict[str, str]:
        """
        Detect which columns in the DataFrame map to our standard columns
        """
        self.log(f"🔍 Detecting column mapping for {len(df.columns)} columns: {list(df.columns)}")
        
        detected_mapping = {}
        available_columns = [col.lower().strip() for col in df.columns]
        
        # Direct matching first
        for standard_col, variations in self.column_mappings.items():
            best_match = None
            best_score = 0
            
            for variation in variations:
                for actual_col in df.columns:
                    actual_col_clean = actual_col.lower().strip()
                    
                    # Exact match (highest priority)
                    if actual_col_clean == variation:
                        detected_mapping[standard_col] = actual_col
                        self.log(f"✅ Exact match: {standard_col} -> {actual_col}")
                        best_match = actual_col
                        break
                    
                    # Fuzzy match
                    score = fuzz.ratio(actual_col_clean, variation)
                    if score > 80 and score > best_score:
                        best_score = score
                        best_match = actual_col
                
                if best_match and standard_col not in detected_mapping:
                    detected_mapping[standard_col] = best_match
                    self.log(f"🎯 Fuzzy match: {standard_col} -> {best_match} (score: {best_score})")
                    break
        
        # Check for combined address fields
        self._detect_combined_address_fields(df, detected_mapping)
        
        self.log(f"📋 Final column mapping: {detected_mapping}")
        return detected_mapping
    
    def _detect_combined_address_fields(self, df: pd.DataFrame, mapping: Dict[str, str]):
        """Detect if address components are combined in a single field"""
        
        if 'street_address' in mapping:
            return  # Already have separate street address
        
        # Look for full address fields that might contain everything
        potential_address_columns = []
        
        for col in df.columns:
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in ['address', 'addr', 'full', 'complete', 'mailing']):
                potential_address_columns.append(col)
        
        # Sample some rows to check if they contain full addresses
        sample_size = min(10, len(df))
        for col in potential_address_columns:
            sample_data = df[col].dropna().head(sample_size)
            
            combined_count = 0
            for value in sample_data:
                if isinstance(value, str) and self._is_combined_address(value):
                    combined_count += 1
            
            # If more than 50% look like combined addresses
            if combined_count > sample_size * 0.5:
                mapping['combined_address'] = col
                self.log(f"🏠 Detected combined address field: {col}")
                break
    
    def _is_combined_address(self, address_text: str) -> bool:
        """Check if text looks like a complete address"""
        if not isinstance(address_text, str) or len(address_text.strip()) < 10:
            return False
        
        text = address_text.strip()
        
        # Check against our patterns
        for pattern in self.combined_address_patterns:
            if re.match(pattern, text, re.IGNORECASE):
                return True
        
        # Additional heuristics
        has_numbers = bool(re.search(r'\d', text))
        has_state = any(state in text.upper() for state in self.us_states)
        has_zip = bool(re.search(r'\d{5}', text))
        has_commas = text.count(',') >= 1
        
        return has_numbers and has_state and (has_zip or has_commas)
    
    def parse_combined_address(self, address_text: str) -> Dict[str, str]:
        """Parse a combined address into components"""
        if not isinstance(address_text, str):
            return {}
        
        text = address_text.strip()
        self.log(f"🔍 Parsing combined address: {text}")
        
        # Try each pattern
        for pattern in self.combined_address_patterns:
            match = re.match(pattern, text, re.IGNORECASE)
            if match:
                groups = match.groups()
                parsed = {
                    'street_address': groups[0].strip(),
                    'city': groups[1].strip(),
                    'state': groups[2].strip().upper(),
                    'zip_code': groups[3].strip()
                }
                self.log(f"✅ Successfully parsed: {parsed}")
                return parsed
        
        # Fallback: try to extract components manually
        return self._manual_address_parse(text)
    
    def _manual_address_parse(self, text: str) -> Dict[str, str]:
        """Manual parsing fallback for complex address formats"""
        
        # Extract ZIP code first
        zip_match = re.search(r'\b(\d{5}(?:-\d{4})?)\b', text)
        zip_code = zip_match.group(1) if zip_match else ''
        if zip_code:
            text = text.replace(zip_code, '').strip()
        
        # Extract state (2-letter code)
        state_match = re.search(r'\b([A-Z]{2})\b', text.upper())
        state = state_match.group(1) if state_match else ''
        if state and state in self.us_states:
            # Remove state from text
            text = re.sub(r'\b' + re.escape(state) + r'\b', '', text, flags=re.IGNORECASE).strip()
        
        # Split remaining text by commas
        parts = [part.strip() for part in text.split(',')]
        parts = [part for part in parts if part]  # Remove empty parts
        
        street_address = ''
        city = ''
        
        if len(parts) >= 2:
            street_address = parts[0]
            city = parts[1]
        elif len(parts) == 1:
            # Try to split by common patterns
            words = parts[0].split()
            if len(words) > 3:
                # Assume first 2-3 words are street, rest is city
                street_address = ' '.join(words[:3])
                city = ' '.join(words[3:])
            else:
                street_address = parts[0]
        
        result = {
            'street_address': street_address,
            'city': city,
            'state': state,
            'zip_code': zip_code
        }
        
        self.log(f"🔧 Manual parse result: {result}")
        return result
    
    def qualify_us_address(self, row: Dict) -> Dict:
        """
        Determine if an address qualifies as a valid US address for USPS validation
        
        Returns:
            Dict with 'qualified', 'qualification_errors', 'qualification_warnings'
        """
        
        street_address = str(row.get('street_address', '')).strip()
        city = str(row.get('city', '')).strip()
        state = str(row.get('state', '')).strip().upper()
        zip_code = str(row.get('zip_code', '')).strip()
        
        errors = []
        warnings = []
        qualified = True
        
        # Check required fields
        if not street_address:
            errors.append("Missing street address")
            qualified = False
        elif len(street_address) < 3:
            errors.append("Street address too short")
            qualified = False
        elif not re.search(r'\d', street_address):
            warnings.append("No house number detected in street address")
        
        if not city:
            errors.append("Missing city")
            qualified = False
        elif len(city) < 2:
            errors.append("City name too short")
            qualified = False
        elif not re.match(r"^[a-zA-Z\s\-'\.]+$", city):
            errors.append("City contains invalid characters")
            qualified = False
        
        if not state:
            errors.append("Missing state")
            qualified = False
        else:
            # Try to convert full state name to abbreviation
            state_lower = state.lower()
            if state_lower in self.state_name_to_abbr:
                state = self.state_name_to_abbr[state_lower]
                # Update the row with corrected state
                row['state'] = state
            
            if len(state) != 2:
                errors.append("State must be 2-letter code")
                qualified = False
            elif state not in self.us_states:
                errors.append(f"Invalid US state code: {state}")
                qualified = False
        
        if not zip_code:
            errors.append("Missing ZIP code")
            qualified = False
        else:
            # Clean and validate ZIP code
            zip_clean = re.sub(r'[^\d\-]', '', zip_code)
            if not re.match(r'^\d{5}(-\d{4})?$', zip_clean):
                errors.append("Invalid ZIP code format (must be 12345 or 12345-6789)")
                qualified = False
            elif zip_clean.startswith('00000'):
                errors.append("Invalid ZIP code (cannot be all zeros)")
                qualified = False
            else:
                # Update row with cleaned ZIP
                row['zip_code'] = zip_clean
        
        # Check for PO Box addresses (warning, not disqualifying)
        if re.search(r'\b(po|p\.o\.)\s*box\b', street_address, re.IGNORECASE):
            warnings.append("PO Box address detected")
        
        # Check for business indicators
        business_indicators = ['llc', 'inc', 'corp', 'ltd', 'company', 'co.', 'corporation']
        if any(indicator in street_address.lower() for indicator in business_indicators):
            warnings.append("Possible business address")
        
        return {
            'qualified': qualified,
            'qualification_errors': errors,
            'qualification_warnings': warnings,
            'qualification_score': 1.0 if qualified else 0.0
        }
    
    def standardize_dataframe(self, df: pd.DataFrame, file_name: str = "unknown") -> Tuple[pd.DataFrame, Dict]:
        """
        Standardize a DataFrame to our standard format with US qualification
        """
        self.log(f"🚀 Starting standardization for {file_name} ({len(df)} rows, {len(df.columns)} columns)")
        
        # Detect column mapping
        column_mapping = self.detect_column_mapping(df)
        
        standardization_info = {
            'file_name': file_name,
            'original_columns': list(df.columns),
            'detected_mapping': column_mapping,
            'row_count': len(df),
            'standardization_errors': [],
            'combined_address_parsed': False,
            'qualification_summary': {
                'total_rows': 0,
                'qualified_rows': 0,
                'disqualified_rows': 0,
                'common_errors': {}
            }
        }
        
        # Create standardized DataFrame
        standardized_df = pd.DataFrame()
        
        # Handle combined address parsing
        if 'combined_address' in column_mapping:
            self.log("🏠 Processing combined address field")
            standardization_info['combined_address_parsed'] = True
            
            combined_col = column_mapping['combined_address']
            parsed_addresses = []
            
            for idx, row in df.iterrows():
                address_text = row[combined_col]
                parsed = self.parse_combined_address(address_text)
                parsed_addresses.append(parsed)
            
            # Add parsed address components
            for component in ['street_address', 'city', 'state', 'zip_code']:
                standardized_df[component] = [addr.get(component, '') for addr in parsed_addresses]
        
        # Map standard columns
        for standard_col in self.standard_columns.keys():
            if standard_col in column_mapping:
                source_col = column_mapping[standard_col]
                standardized_df[standard_col] = df[source_col].fillna('')
                self.log(f"✅ Mapped {source_col} -> {standard_col}")
            elif standard_col not in standardized_df.columns:
                # Create empty column if not found
                standardized_df[standard_col] = ''
                standardization_info['standardization_errors'].append(f"Missing {standard_col} column")
                self.log(f"⚠️ Missing column: {standard_col}")
        
        # Handle address line 2 concatenation
        if 'address_line_2' in column_mapping and 'street_address' in standardized_df.columns:
            addr2_col = column_mapping['address_line_2']
            addr2_data = df[addr2_col].fillna('')
            
            # Combine address lines
            for idx in standardized_df.index:
                base_addr = str(standardized_df.loc[idx, 'street_address']).strip()
                addr2 = str(addr2_data.iloc[idx]).strip()
                
                if addr2:
                    standardized_df.loc[idx, 'street_address'] = f"{base_addr} {addr2}".strip()
            
            self.log(f"🏠 Combined address lines 1 and 2")
        
        # Clean and validate data
        standardized_df = self._clean_standardized_data(standardized_df, standardization_info)
        
        # Add US qualification assessment
        standardized_df = self._add_qualification_assessment(standardized_df, standardization_info)
        
        self.log(f"✅ Standardization complete: {len(standardized_df)} rows standardized")
        return standardized_df, standardization_info
    
    def _add_qualification_assessment(self, df: pd.DataFrame, info: Dict) -> pd.DataFrame:
        """Add US address qualification assessment to each row"""
        
        self.log("🎯 Assessing US address qualification for all rows")
        
        qualification_results = []
        qualified_count = 0
        error_counts = {}
        
        for idx, row in df.iterrows():
            row_dict = row.to_dict()
            qualification = self.qualify_us_address(row_dict)
            
            # Update the original row with any corrections made during qualification
            for col in ['state', 'zip_code']:
                if col in row_dict:
                    df.loc[idx, col] = row_dict[col]
            
            qualification_results.append(qualification)
            
            if qualification['qualified']:
                qualified_count += 1
            
            # Count error types
            for error in qualification['qualification_errors']:
                if error not in error_counts:
                    error_counts[error] = 0
                error_counts[error] += 1
        
        # Add qualification columns to DataFrame
        df['us_qualified'] = [r['qualified'] for r in qualification_results]
        df['qualification_errors'] = ['; '.join(r['qualification_errors']) if r['qualification_errors'] else '' for r in qualification_results]
        df['qualification_warnings'] = ['; '.join(r['qualification_warnings']) if r['qualification_warnings'] else '' for r in qualification_results]
        df['qualification_score'] = [r['qualification_score'] for r in qualification_results]
        
        # Update summary
        info['qualification_summary'] = {
            'total_rows': len(df),
            'qualified_rows': qualified_count,
            'disqualified_rows': len(df) - qualified_count,
            'qualification_rate': qualified_count / len(df) if len(df) > 0 else 0,
            'common_errors': error_counts
        }
        
        self.log(f"🎯 Qualification complete: {qualified_count}/{len(df)} rows qualified ({qualified_count/len(df)*100:.1f}%)")
        
        return df
    
    def _clean_standardized_data(self, df: pd.DataFrame, info: Dict) -> pd.DataFrame:
        """Clean and validate standardized data"""
        
        self.log("🧹 Cleaning standardized data")
        
        # Convert all to string and strip whitespace
        for col in df.columns:
            df[col] = df[col].astype(str).str.strip()
        
        # Clean state codes
        if 'state' in df.columns:
            df['state'] = df['state'].str.upper()
            # Validate states
            invalid_states = df[~df['state'].isin(self.us_states) & (df['state'] != '')]['state'].unique()
            if len(invalid_states) > 0:
                info['standardization_errors'].append(f"Invalid state codes found: {list(invalid_states)}")
        
        # Clean ZIP codes
        if 'zip_code' in df.columns:
            df['zip_code'] = df['zip_code'].apply(self._clean_zip_code)
        
        # Clean names (title case)
        for name_col in ['first_name', 'last_name']:
            if name_col in df.columns:
                df[name_col] = df[name_col].apply(lambda x: x.title() if x and x != 'nan' else '')
        
        # Remove rows where all address fields are empty
        address_cols = ['street_address', 'city', 'state', 'zip_code']
        before_count = len(df)
        
        mask = df[address_cols].apply(lambda row: any(row.astype(str).str.strip() != ''), axis=1)
        df = df[mask].reset_index(drop=True)
        
        after_count = len(df)
        if before_count != after_count:
            removed = before_count - after_count
            info['standardization_errors'].append(f"Removed {removed} rows with no address data")
            self.log(f"🗑️ Removed {removed} rows with no address data")
        
        return df
    
    def _clean_zip_code(self, zip_code: str) -> str:
        """Clean and format ZIP code"""
        if not zip_code or zip_code == 'nan':
            return ''
        
        # Remove non-digit characters except hyphens
        cleaned = re.sub(r'[^\d\-]', '', str(zip_code))
        
        # Handle different formats
        if len(cleaned) == 5 and cleaned.isdigit():
            return cleaned
        elif len(cleaned) == 9 and cleaned.isdigit():
            return f"{cleaned[:5]}-{cleaned[5:]}"
        elif '-' in cleaned:
            parts = cleaned.split('-')
            if len(parts) == 2 and len(parts[0]) == 5 and len(parts[1]) == 4:
                return cleaned
        
        # Return as-is if we can't clean it properly
        return cleaned
    
    def standardize_multiple_files(self, file_data_list: List[Tuple[pd.DataFrame, str]]) -> Tuple[pd.DataFrame, List[Dict]]:
        """
        Standardize multiple CSV files and combine them with qualification assessment
        
        Args:
            file_data_list: List of (DataFrame, filename) tuples
            
        Returns:
            Tuple of (combined_standardized_df, list_of_standardization_info)
        """
        self.log(f"🎯 Starting batch standardization for {len(file_data_list)} files")
        
        standardized_dfs = []
        all_standardization_info = []
        
        for i, (df, filename) in enumerate(file_data_list):
            self.log(f"📄 Processing file {i+1}/{len(file_data_list)}: {filename}")
            
            try:
                std_df, std_info = self.standardize_dataframe(df, filename)
                
                # Add source file info
                std_df['source_file'] = filename
                std_df['source_row_number'] = range(1, len(std_df) + 1)
                
                standardized_dfs.append(std_df)
                all_standardization_info.append(std_info)
                
                self.log(f"✅ File {filename}: {len(std_df)} rows standardized")
                
            except Exception as e:
                error_info = {
                    'file_name': filename,
                    'error': str(e),
                    'status': 'failed'
                }
                all_standardization_info.append(error_info)
                self.log(f"❌ Failed to process {filename}: {str(e)}")
        
        # Combine all standardized DataFrames
        if standardized_dfs:
            combined_df = pd.concat(standardized_dfs, ignore_index=True)
            self.log(f"🎉 Batch standardization complete: {len(combined_df)} total rows from {len(standardized_dfs)} files")
        else:
            combined_df = pd.DataFrame(columns=list(self.standard_columns.keys()) + ['source_file', 'source_row_number', 'us_qualified', 'qualification_errors', 'qualification_warnings', 'qualification_score'])
            self.log("⚠️ No files were successfully standardized")
        
        return combined_df, all_standardization_info
    
    def get_qualification_summary(self, standardized_df: pd.DataFrame, standardization_info_list: List[Dict]) -> Dict:
        """Generate comprehensive qualification summary"""
        
        if standardized_df.empty:
            return {
                'total_files': len(standardization_info_list),
                'total_rows': 0,
                'qualified_rows': 0,
                'disqualified_rows': 0,
                'qualification_rate': 0,
                'common_errors': {},
                'files_summary': []
            }
        
        # Overall qualification stats
        total_rows = len(standardized_df)
        qualified_rows = len(standardized_df[standardized_df['us_qualified'] == True])
        disqualified_rows = total_rows - qualified_rows
        
        # Error analysis
        all_errors = []
        for errors_str in standardized_df['qualification_errors']:
            if errors_str:
                all_errors.extend(errors_str.split('; '))
        
        error_counts = {}
        for error in all_errors:
            error_counts[error] = error_counts.get(error, 0) + 1
        
        # Per-file summary
        files_summary = []
        for info in standardization_info_list:
            if 'error' not in info and 'qualification_summary' in info:
                files_summary.append({
                    'file_name': info['file_name'],
                    'total_rows': info['qualification_summary']['total_rows'],
                    'qualified_rows': info['qualification_summary']['qualified_rows'],
                    'qualification_rate': info['qualification_summary']['qualification_rate'],
                    'common_errors': info['qualification_summary']['common_errors']
                })
        
        return {
            'total_files': len(standardization_info_list),
            'total_rows': total_rows,
            'qualified_rows': qualified_rows,
            'disqualified_rows': disqualified_rows,
            'qualification_rate': qualified_rows / total_rows if total_rows > 0 else 0,
            'common_errors': error_counts,
            'files_summary': files_summary,
            'ready_for_usps': qualified_rows > 0
        }
    
    def filter_qualified_addresses(self, standardized_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Split standardized data into qualified and disqualified addresses
        
        Returns:
            Tuple of (qualified_df, disqualified_df)
        """
        
        if standardized_df.empty:
            return pd.DataFrame(), pd.DataFrame()
        
        qualified_df = standardized_df[standardized_df['us_qualified'] == True].copy()
        disqualified_df = standardized_df[standardized_df['us_qualified'] == False].copy()
        
        self.log(f"🎯 Filtered addresses: {len(qualified_df)} qualified, {len(disqualified_df)} disqualified")
        
        return qualified_df, disqualified_df
    
    def get_standardization_summary(self, standardization_info_list: List[Dict]) -> Dict:
        """Generate a summary of standardization results including qualification"""
        
        summary = {
            'total_files_processed': len(standardization_info_list),
            'successful_files': 0,
            'failed_files': 0,
            'total_rows_processed': 0,
            'total_qualified_rows': 0,
            'total_disqualified_rows': 0,
            'overall_qualification_rate': 0,
            'files_with_combined_addresses': 0,
            'common_errors': {},
            'common_qualification_errors': {},
            'column_mapping_patterns': {},
            'files_details': []
        }
        
        for info in standardization_info_list:
            if 'error' in info:
                summary['failed_files'] += 1
                summary['files_details'].append({
                    'file': info['file_name'],
                    'status': 'failed',
                    'error': info['error']
                })
            else:
                summary['successful_files'] += 1
                summary['total_rows_processed'] += info['row_count']
                
                if 'qualification_summary' in info:
                    qual_summary = info['qualification_summary']
                    summary['total_qualified_rows'] += qual_summary['qualified_rows']
                    summary['total_disqualified_rows'] += qual_summary['disqualified_rows']
                    
                    # Track qualification errors
                    for error, count in qual_summary['common_errors'].items():
                        summary['common_qualification_errors'][error] = summary['common_qualification_errors'].get(error, 0) + count
                
                if info.get('combined_address_parsed', False):
                    summary['files_with_combined_addresses'] += 1
                
                # Track column patterns
                for std_col, source_col in info['detected_mapping'].items():
                    if std_col not in summary['column_mapping_patterns']:
                        summary['column_mapping_patterns'][std_col] = {}
                    
                    if source_col not in summary['column_mapping_patterns'][std_col]:
                        summary['column_mapping_patterns'][std_col][source_col] = 0
                    summary['column_mapping_patterns'][std_col][source_col] += 1
                
                # Track errors
                for error in info.get('standardization_errors', []):
                    if error not in summary['common_errors']:
                        summary['common_errors'][error] = 0
                    summary['common_errors'][error] += 1
                
                summary['files_details'].append({
                    'file': info['file_name'],
                    'status': 'success',
                    'rows': info['row_count'],
                    'qualified': qual_summary['qualified_rows'] if 'qualification_summary' in info else 0,
                    'combined_address': info.get('combined_address_parsed', False),
                    'errors': len(info.get('standardization_errors', []))
                })
        
        # Calculate overall qualification rate
        if summary['total_rows_processed'] > 0:
            summary['overall_qualification_rate'] = summary['total_qualified_rows'] / summary['total_rows_processed']
        
        return summary