# src/name_address_validator/app.py - Enhanced with Bulk Validation Tab
"""
Enhanced Streamlit web application for name and address validation
NEW: Added bulk validation tab with tabular input/output
"""

import streamlit as st
import pandas as pd
import time
import sys
import os
import io
from datetime import datetime
from typing import Dict, Optional, Tuple, List
from pathlib import Path

# Fix Python path for both local and Streamlit Cloud environments
def setup_python_path():
    """Setup Python path to find our modules"""
    current_file = Path(__file__).resolve()
    
    # Try different path configurations for different environments
    possible_src_dirs = [
        # Local development: /path/to/project/src/name_address_validator/app.py -> /path/to/project/src
        current_file.parent.parent.parent / "src",
        # Local development alternative: current parent's parent
        current_file.parent.parent,
        # Streamlit Cloud: /mount/src/repo-name/src/name_address_validator/app.py
        current_file.parent.parent.parent / "src",
        # Streamlit Cloud alternative
        Path("/mount/src") / "name-address-validator" / "src",
        # Another Streamlit Cloud possibility
        Path("/mount/src") / os.environ.get("STREAMLIT_REPO_NAME", "name-address-validator") / "src",
    ]
    
    for src_dir in possible_src_dirs:
        if src_dir.exists() and (src_dir / "name_address_validator").exists():
            if str(src_dir) not in sys.path:
                sys.path.insert(0, str(src_dir))
            return src_dir
    
    # Fallback: just add the current directory structure
    fallback_paths = [
        str(current_file.parent.parent.parent),  # Go up to project root
        str(current_file.parent.parent),         # Go up to src level
    ]
    
    for path in fallback_paths:
        if path not in sys.path:
            sys.path.insert(0, path)
    
    return None

# Setup the path before importing our modules
setup_python_path()

# Now try to import our modules with error handling
try:
    from name_address_validator.validators.name_validator import EnhancedNameValidator
    from name_address_validator.validators.address_validator import USPSAddressValidator
    imports_successful = True
except ImportError as e:
    st.error(f"Import Error: {e}")
    st.error("Debug info:")
    st.write("Python path:", sys.path)
    st.write("Current file:", __file__)
    st.write("Current working directory:", os.getcwd())
    
    # Try direct file imports as fallback
    try:
        current_dir = Path(__file__).parent
        validators_dir = current_dir / "validators"
        
        # Add validators directory to path
        sys.path.insert(0, str(validators_dir))
        sys.path.insert(0, str(current_dir))
        
        # Try importing directly
        import name_validator as nv
        import address_validator as av
        
        EnhancedNameValidator = nv.EnhancedNameValidator
        USPSAddressValidator = av.USPSAddressValidator
        imports_successful = True
        st.success("Fallback imports successful!")
        
    except Exception as fallback_error:
        st.error(f"Fallback import also failed: {fallback_error}")
        imports_successful = False

if not imports_successful:
    st.error("❌ Unable to import required modules. Please check the deployment.")
    st.stop()


class DebugLogger:
    """Simple debug logger for Streamlit"""
    
    def __init__(self):
        self.logs = []
        self.enabled = False
    
    def log(self, message: str):
        if not self.enabled:
            return
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.logs.append(f"[{timestamp}] {message}")
    
    def clear(self):
        self.logs = []
    
    def display(self):
        if self.logs:
            st.subheader("🔍 Debug Logs")
            st.code("\n".join(self.logs), language="text")


def load_usps_credentials() -> Tuple[Optional[str], Optional[str]]:
    """Load USPS credentials from secrets or environment"""
    try:
        if hasattr(st, 'secrets'):
            client_id = st.secrets.get("USPS_CLIENT_ID", "")
            client_secret = st.secrets.get("USPS_CLIENT_SECRET", "")
            if client_id and client_secret:
                return client_id, client_secret
    except Exception:
        pass
    
    client_id = os.getenv('USPS_CLIENT_ID', '')
    client_secret = os.getenv('USPS_CLIENT_SECRET', '')
    
    if client_id and client_secret:
        return client_id, client_secret
    
    return None, None


def safe_extract(value):
    """Safely extract string value, handling NaN and None"""
    if pd.isna(value) or value is None or str(value).lower() == 'nan':
        return ''
    return str(value).strip()


def validate_single_record(name_validator, address_validator, record: Dict, debug_logger) -> Dict:
    """Validate a single name/address record"""
    
    try:
        # Extract data and handle NaN/empty values safely
        first_name = safe_extract(record.get('first_name', ''))
        last_name = safe_extract(record.get('last_name', ''))
        street_address = safe_extract(record.get('street_address', ''))
        city = safe_extract(record.get('city', ''))
        state = safe_extract(record.get('state', '')).upper()
        zip_code = safe_extract(record.get('zip_code', ''))
        
        # Validate name
        name_result = name_validator.validate(first_name, last_name)
        
        # Validate address
        address_data = {
            'street_address': street_address,
            'city': city,
            'state': state,
            'zip_code': zip_code
        }
        address_result = address_validator.validate_address(address_data)
        
        # Compile results
        result = {
            'original_first_name': first_name,
            'original_last_name': last_name,
            'original_street_address': street_address,
            'original_city': city,
            'original_state': state,
            'original_zip_code': zip_code,
            
            # Name validation results
            'name_valid': name_result['valid'],
            'name_confidence': name_result['confidence'],
            'name_errors': '; '.join(name_result['errors']) if name_result['errors'] else '',
            'name_warnings': '; '.join(name_result['warnings']) if name_result['warnings'] else '',
            'normalized_first_name': name_result['normalized']['first_name'],
            'normalized_last_name': name_result['normalized']['last_name'],
            
            # Address validation results
            'address_valid': address_result.get('success', False),
            'address_deliverable': address_result.get('deliverable', False),
            'address_confidence': address_result.get('confidence', 0.0),
            'address_error': address_result.get('error', ''),
            'standardized_street_address': '',
            'standardized_city': '',
            'standardized_state': '',
            'standardized_zip_code': '',
            
            # Overall status
            'overall_status': '',
            'suggestions': '',
        }
        
        # Add standardized address if available
        if address_result.get('standardized'):
            std = address_result['standardized']
            result['standardized_street_address'] = std.get('street_address', '')
            result['standardized_city'] = std.get('city', '')
            result['standardized_state'] = std.get('state', '')
            result['standardized_zip_code'] = std.get('zip_code', '')
        
        # Determine overall status
        if result['name_valid'] and result['address_deliverable']:
            result['overall_status'] = '✅ Valid'
        elif result['name_valid'] and result['address_valid']:
            result['overall_status'] = '⚠️ Name Valid, Address Uncertain'
        elif result['name_valid']:
            result['overall_status'] = '❌ Name Valid, Address Invalid'
        elif result['address_deliverable']:
            result['overall_status'] = '❌ Address Valid, Name Invalid'
        else:
            result['overall_status'] = '❌ Both Invalid'
        
        # Compile suggestions
        suggestions = []
        
        # Name suggestions
        if name_result.get('suggestions'):
            for field, field_suggestions in name_result['suggestions'].items():
                if field_suggestions:
                    best_suggestion = field_suggestions[0]
                    suggestions.append(f"{field.replace('_', ' ').title()}: {best_suggestion['suggestion']}")
        
        # Address suggestions (basic)
        if not result['address_deliverable'] and result['address_error']:
            suggestions.append(f"Address: {result['address_error']}")
        
        result['suggestions'] = '; '.join(suggestions[:3])  # Limit to top 3
        
        return result
        
    except Exception as e:
        debug_logger.log(f"❌ Error validating record: {e}")
        return {
            'original_first_name': safe_extract(record.get('first_name', '')),
            'original_last_name': safe_extract(record.get('last_name', '')),
            'original_street_address': safe_extract(record.get('street_address', '')),
            'original_city': safe_extract(record.get('city', '')),
            'original_state': safe_extract(record.get('state', '')),
            'original_zip_code': safe_extract(record.get('zip_code', '')),
            'overall_status': f'❌ Error: {str(e)[:50]}...',
            'suggestions': 'Fix data format and try again',
            'name_valid': False,
            'address_deliverable': False,
            'name_confidence': 0.0,
            'address_confidence': 0.0,
            'name_errors': str(e),
            'name_warnings': '',
            'address_error': str(e),
            'normalized_first_name': '',
            'normalized_last_name': '',
            'standardized_street_address': '',
            'standardized_city': '',
            'standardized_state': '',
            'standardized_zip_code': ''
        }


def render_bulk_validation_tab(name_validator, address_validator, debug_logger):
    """Render the bulk validation tab with CSV upload"""
    st.header("📊 Bulk Validation")
    st.write("Upload a CSV file to validate multiple names and addresses at once")
    
    # CSV Upload Section
    st.subheader("📁 CSV File Upload")
    
    # Template download
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.write("**Step 1:** Download the template CSV file")
        
        # Create sample template
        template_data = {
            'first_name': ['John', 'Jane', 'Michael'],
            'last_name': ['Smith', 'Doe', 'Johnson'],
            'street_address': ['1600 Pennsylvania Ave NW', '350 Fifth Avenue', '123 Main Street'],
            'city': ['Washington', 'New York', 'Chicago'],
            'state': ['DC', 'NY', 'IL'],
            'zip_code': ['20500', '10118', '60601']
        }
        template_df = pd.DataFrame(template_data)
        
        csv_template = template_df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV Template",
            data=csv_template,
            file_name="name_address_template.csv",
            mime="text/csv",
            help="Download this template and fill in your data"
        )
    
    with col2:
        st.write("**Step 2:** Upload your completed CSV file")
        uploaded_file = st.file_uploader(
            "Choose CSV file",
            type=['csv'],
            help="Upload a CSV file with columns: first_name, last_name, street_address, city, state, zip_code"
        )
    
    # CSV Format Requirements
    with st.expander("📋 CSV Format Requirements", expanded=False):
        st.markdown("""
        **Required Columns:**
        - `first_name`: Person's first name
        - `last_name`: Person's last name  
        - `street_address`: Street address with number and street name
        - `city`: City name
        - `state`: Two-letter state code (e.g., CA, NY, TX)
        - `zip_code`: ZIP code (5 or 9 digits)
        
        **Example:**
        ```
        first_name,last_name,street_address,city,state,zip_code
        John,Smith,1600 Pennsylvania Ave NW,Washington,DC,20500
        Jane,Doe,350 Fifth Avenue,New York,NY,10118
        ```
        
        **Notes:**
        - Column names must match exactly (case-sensitive)
        - Missing values will be treated as empty strings
        - ZIP codes can include dashes (e.g., 12345-6789)
        """)
    
    # Process uploaded file
    if uploaded_file is not None:
        try:
            # Read CSV file
            df = pd.read_csv(uploaded_file)
            
            st.success(f"✅ File uploaded successfully! Found {len(df)} records.")
            
            # Validate CSV format
            required_columns = ['first_name', 'last_name', 'street_address', 'city', 'state', 'zip_code']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                st.error(f"❌ Missing required columns: {', '.join(missing_columns)}")
                st.info("Please ensure your CSV has all required columns with exact names (case-sensitive)")
                return
            
            # Clean and prepare data - Fill NaN values with empty strings
            for col in required_columns:
                df[col] = df[col].fillna('').astype(str)
            
            # Show preview of uploaded data
            st.subheader("📋 Data Preview")
            st.write(f"Showing first 5 rows of {len(df)} total records:")
            st.dataframe(df.head(), use_container_width=True)
            
            # Data quality check
            st.subheader("🔍 Data Quality Check")
            
            quality_issues = []
            
            # Check for empty values
            for col in required_columns:
                empty_count = (df[col] == '').sum() + (df[col] == 'nan').sum()
                if empty_count > 0:
                    quality_issues.append(f"**{col}**: {empty_count} empty values")
            
            # Check state format (only for non-empty values)
            state_mask = (df['state'] != '') & (df['state'] != 'nan')
            if state_mask.any():
                state_regex = r'^[A-Z]{2}$'
                invalid_state_mask = state_mask & ~df['state'].str.match(state_regex, na=False)
                if invalid_state_mask.any():
                    invalid_states = df[invalid_state_mask]['state'].unique()
                    # Filter out any remaining NaN or empty values
                    invalid_states = [s for s in invalid_states if s and str(s) not in ['nan', 'NaN', '']]
                    if len(invalid_states) > 0:
                        quality_issues.append(f"**state**: Invalid formats found: {', '.join(map(str, invalid_states[:5]))}")
            
            # Check ZIP code format (only for non-empty values)
            zip_mask = (df['zip_code'] != '') & (df['zip_code'] != 'nan')
            if zip_mask.any():
                zip_regex = r'^\d{5}(-\d{4})?$'
                invalid_zip_mask = zip_mask & ~df['zip_code'].str.match(zip_regex, na=False)
                if invalid_zip_mask.any():
                    invalid_zips = df[invalid_zip_mask]['zip_code'].unique()
                    # Filter out any remaining NaN or empty values
                    invalid_zips = [z for z in invalid_zips if z and str(z) not in ['nan', 'NaN', '']]
                    if len(invalid_zips) > 0:
                        quality_issues.append(f"**zip_code**: Invalid formats found: {', '.join(map(str, invalid_zips[:5]))}")
            
            if quality_issues:
                st.warning("⚠️ Data quality issues detected:")
                for issue in quality_issues:
                    st.write(f"• {issue}")
                st.info("You can still proceed with validation, but these issues may affect results.")
            else:
                st.success("✅ No data quality issues detected!")
            
            # Validation controls
            st.subheader("⚙️ Validation Settings")
            
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                max_records = st.number_input(
                    "Maximum records to validate",
                    min_value=1,
                    max_value=len(df),
                    value=min(100, len(df)),
                    help="Limit number of records to avoid timeout"
                )
            
            with col2:
                include_suggestions = st.checkbox(
                    "Include suggestions",
                    value=True,
                    help="Include name/address suggestions in results"
                )
            
            with col3:
                detailed_results = st.checkbox(
                    "Detailed results",
                    value=False,
                    help="Include confidence scores and metadata"
                )
            
            # Validate button
            if st.button("🚀 Start Validation", type="primary", use_container_width=True):
                validate_csv_data(
                    df.head(max_records), 
                    name_validator, 
                    address_validator, 
                    debug_logger,
                    include_suggestions,
                    detailed_results
                )
                
        except Exception as e:
            st.error(f"❌ Error reading CSV file: {str(e)}")
            st.info("Please ensure your file is a valid CSV format.")
    
    else:
        # Show sample data when no file is uploaded
        st.subheader("📝 Sample Data")
        st.write("Here's what your CSV data should look like:")
        
        sample_data = {
            'first_name': ['John', 'Jane', 'Michael', 'Sarah'],
            'last_name': ['Smith', 'Doe', 'Johnson', 'Williams'],
            'street_address': ['1600 Pennsylvania Ave NW', '350 Fifth Avenue', '123 Main Street', '456 Oak Drive'],
            'city': ['Washington', 'New York', 'Chicago', 'Los Angeles'],
            'state': ['DC', 'NY', 'IL', 'CA'],
            'zip_code': ['20500', '10118', '60601', '90210']
        }
        sample_df = pd.DataFrame(sample_data)
        st.dataframe(sample_df, use_container_width=True)


def validate_csv_data(df, name_validator, address_validator, debug_logger, include_suggestions=True, detailed_results=False):
    """Process and validate CSV data with progress tracking"""
    
    st.subheader("🔄 Validation Progress")
    
    total_records = len(df)
    progress_bar = st.progress(0)
    status_text = st.empty()
    results_container = st.container()
    
    debug_logger.log(f"🚀 Starting bulk validation of {total_records} records")
    
    # Initialize results list
    results = []
    
    # Process each record
    for i, (_, row) in enumerate(df.iterrows()):
        # Update progress
        progress = (i + 1) / total_records
        progress_bar.progress(progress)
        status_text.text(f"Validating record {i + 1} of {total_records}: {row.get('first_name', '')} {row.get('last_name', '')}")
        
        # Convert row to dict
        record = row.to_dict()
        
        # Validate the record
        result = validate_single_record(name_validator, address_validator, record, debug_logger)
        results.append(result)
        
        # Brief pause to show progress (optional)
        if i % 10 == 0:  # Every 10 records
            time.sleep(0.1)
    
    # Complete progress
    progress_bar.progress(1.0)
    status_text.text("✅ Validation complete!")
    
    # Convert results to DataFrame
    results_df = pd.DataFrame(results)
    
    # Display results
    with results_container:
        display_validation_results(results_df, include_suggestions, detailed_results, debug_logger)
    
    debug_logger.log(f"✅ Bulk validation completed for {total_records} records")


def display_validation_results(results_df, include_suggestions, detailed_results, debug_logger):
    """Display validation results in tabular format"""
    
    st.subheader("📊 Validation Results")
    
    # Summary statistics
    col1, col2, col3, col4 = st.columns(4)
    
    total_records = len(results_df)
    valid_names = (results_df['name_valid'] == True).sum()
    valid_addresses = (results_df['address_deliverable'] == True).sum()
    fully_valid = ((results_df['name_valid'] == True) & (results_df['address_deliverable'] == True)).sum()
    
    with col1:
        st.metric("📊 Total Records", total_records)
    
    with col2:
        st.metric("👤 Valid Names", f"{valid_names}/{total_records}", f"{valid_names/total_records:.1%}")
    
    with col3:
        st.metric("📮 Valid Addresses", f"{valid_addresses}/{total_records}", f"{valid_addresses/total_records:.1%}")
    
    with col4:
        st.metric("✅ Fully Valid", f"{fully_valid}/{total_records}", f"{fully_valid/total_records:.1%}")
    
    # Filter options
    st.subheader("🔍 Filter Results")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.selectbox(
            "Filter by status:",
            ["All Records", "✅ Fully Valid", "⚠️ Partially Valid", "❌ Invalid"],
            index=0
        )
    
    with col2:
        name_filter = st.selectbox(
            "Filter by name validation:",
            ["All", "Valid Names Only", "Invalid Names Only"],
            index=0
        )
    
    with col3:
        address_filter = st.selectbox(
            "Filter by address validation:",
            ["All", "Deliverable Only", "Non-deliverable Only"],
            index=0
        )
    
    # Apply filters
    filtered_df = results_df.copy()
    
    if status_filter == "✅ Fully Valid":
        filtered_df = filtered_df[(filtered_df['name_valid'] == True) & (filtered_df['address_deliverable'] == True)]
    elif status_filter == "⚠️ Partially Valid":
        filtered_df = filtered_df[((filtered_df['name_valid'] == True) & (filtered_df['address_deliverable'] == False)) | 
                                  ((filtered_df['name_valid'] == False) & (filtered_df['address_deliverable'] == True))]
    elif status_filter == "❌ Invalid":
        filtered_df = filtered_df[(filtered_df['name_valid'] == False) & (filtered_df['address_deliverable'] == False)]
    
    if name_filter == "Valid Names Only":
        filtered_df = filtered_df[filtered_df['name_valid'] == True]
    elif name_filter == "Invalid Names Only":
        filtered_df = filtered_df[filtered_df['name_valid'] == False]
    
    if address_filter == "Deliverable Only":
        filtered_df = filtered_df[filtered_df['address_deliverable'] == True]
    elif address_filter == "Non-deliverable Only":
        filtered_df = filtered_df[filtered_df['address_deliverable'] == False]
    
    st.write(f"**Showing {len(filtered_df)} of {total_records} records**")
    
    # Choose columns to display
    if detailed_results:
        display_columns = [
            'overall_status',
            'original_first_name', 'original_last_name',
            'normalized_first_name', 'normalized_last_name',
            'original_street_address', 'original_city', 'original_state', 'original_zip_code',
            'standardized_street_address', 'standardized_city', 'standardized_state', 'standardized_zip_code',
            'name_confidence', 'address_confidence',
            'name_errors', 'name_warnings', 'address_error'
        ]
        if include_suggestions:
            display_columns.append('suggestions')
    else:
        display_columns = [
            'overall_status',
            'original_first_name', 'original_last_name',
            'original_street_address', 'original_city', 'original_state', 'original_zip_code',
            'standardized_street_address', 'standardized_city', 'standardized_state', 'standardized_zip_code'
        ]
        if include_suggestions:
            display_columns.append('suggestions')
    
    # Display the filtered results
    if len(filtered_df) > 0:
        # Make the dataframe more readable
        display_df = filtered_df[display_columns].copy()
        
        # Rename columns for better readability
        column_mapping = {
            'overall_status': 'Status',
            'original_first_name': 'Original First Name',
            'original_last_name': 'Original Last Name',
            'normalized_first_name': 'Normalized First Name',
            'normalized_last_name': 'Normalized Last Name',
            'original_street_address': 'Original Street',
            'original_city': 'Original City',
            'original_state': 'Original State',
            'original_zip_code': 'Original ZIP',
            'standardized_street_address': 'Standardized Street',
            'standardized_city': 'Standardized City',
            'standardized_state': 'Standardized State',
            'standardized_zip_code': 'Standardized ZIP',
            'name_confidence': 'Name Confidence',
            'address_confidence': 'Address Confidence',
            'name_errors': 'Name Errors',
            'name_warnings': 'Name Warnings',
            'address_error': 'Address Error',
            'suggestions': 'Suggestions'
        }
        
        display_df = display_df.rename(columns=column_mapping)
        
        # Format confidence scores as percentages
        if 'Name Confidence' in display_df.columns:
            display_df['Name Confidence'] = display_df['Name Confidence'].apply(lambda x: f"{x:.1%}" if pd.notnull(x) else "")
        if 'Address Confidence' in display_df.columns:
            display_df['Address Confidence'] = display_df['Address Confidence'].apply(lambda x: f"{x:.1%}" if pd.notnull(x) else "")
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Status": st.column_config.TextColumn(width="medium"),
                "Suggestions": st.column_config.TextColumn(width="large")
            }
        )
        
        # Download results
        st.subheader("📥 Download Results")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Full results CSV
            csv_full = results_df.to_csv(index=False)
            st.download_button(
                label="📄 Download Full Results (CSV)",
                data=csv_full,
                file_name=f"validation_results_full_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                help="Download all validation results with detailed information"
            )
        
        with col2:
            # Filtered results CSV
            csv_filtered = filtered_df.to_csv(index=False)
            st.download_button(
                label="📄 Download Filtered Results (CSV)",
                data=csv_filtered,
                file_name=f"validation_results_filtered_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                help="Download currently filtered results"
            )
    
    else:
        st.info("No records match the current filters.")


def main():
    """Main Streamlit application with tabs"""
    
    st.set_page_config(
        page_title="Name & Address Validator",
        page_icon="📮👤",
        layout="wide"
    )
    
    # Initialize debug logger
    if 'debug_logger' not in st.session_state:
        st.session_state.debug_logger = DebugLogger()
    
    debug_logger = st.session_state.debug_logger
    
    # Title and header
    st.title("📮👤 Name & Address Validator")
    st.write("Validate names and addresses with comprehensive analysis")
    
    # Load credentials
    client_id, client_secret = load_usps_credentials()
    
    if not client_id or not client_secret:
        debug_logger.log("❌ Credentials not found")
        st.error("❌ USPS API credentials not configured")
        
        with st.expander("📋 Setup Instructions"):
            st.markdown("""
            **For Streamlit Cloud:**
            1. Click "Manage app" (bottom right)
            2. Go to "App settings" → "Secrets"
            3. Add your credentials:
            ```toml
            USPS_CLIENT_ID = "your_actual_client_id"
            USPS_CLIENT_SECRET = "your_actual_client_secret"
            ```
            4. Click "Save" and restart the app
            
            **For Local Development:**
            Create `.streamlit/secrets.toml` file with the same format.
            """)
        return
    
    debug_logger.log("✅ Credentials loaded successfully")
    debug_logger.log(f"🔧 Client ID: {client_id[:8]}...{client_id[-4:]}")
    
    # Initialize validators
    try:
        name_validator = EnhancedNameValidator()
        address_validator = USPSAddressValidator(
            client_id, 
            client_secret, 
            debug_callback=debug_logger.log if st.session_state.get('debug_mode', False) else lambda x: None
        )
        debug_logger.log("🔧 Validators initialized")
    except Exception as e:
        st.error(f"❌ Error initializing validators: {e}")
        return
    
    # Show credential status
    st.success("✅ USPS API configured")
    
    # Create tabs
    tab1, tab2 = st.tabs(["🔍 Single Validation", "📊 Bulk Validation"])
    
    with tab1:
        render_single_validation_tab(name_validator, address_validator, debug_logger)
    
    with tab2:
        render_bulk_validation_tab(name_validator, address_validator, debug_logger)
    
    # Debug options in sidebar
    with st.sidebar:
        st.header("🔧 Debug Options")
        debug_mode = st.checkbox("Enable debug mode", value=st.session_state.get('debug_mode', False))
        st.session_state.debug_mode = debug_mode
        debug_logger.enabled = debug_mode
        
        if st.button("Clear debug logs"):
            debug_logger.clear()
            st.success("Debug logs cleared!")
        
        if st.button("Show Environment Info"):
            st.write("**Environment Debug Info:**")
            st.write(f"Current file: {__file__}")
            st.write(f"Working directory: {os.getcwd()}")
            st.write(f"Python path: {sys.path[:3]}...")  # First few entries
            st.write(f"Platform: {os.name}")
        
        st.markdown("---")
        st.header("ℹ️ About")
        st.markdown("""
        **Name Validation:**
        - US Census database
        - Typo corrections
        - Cultural variations
        
        **Address Validation:**
        - USPS API v3
        - Real-time verification
        - Address standardization
        """)
        
        # Display debug logs if enabled
        if debug_mode:
            st.markdown("---")
            debug_logger.display()


def render_single_validation_tab(name_validator, address_validator, debug_logger):
    """Render the single validation tab (original functionality)"""
    
    debug_logger.log("🚀 Single validation tab loaded")
    
    # Main validation form
    st.header("🔍 Single Validation")
    
    with st.form("validation_form"):
        # Name section
        st.subheader("👤 Name Information")
        col1, col2 = st.columns(2)
        
        with col1:
            first_name = st.text_input(
                "First Name *", 
                value="Michael",
                help="Enter the person's first name"
            )
        
        with col2:
            last_name = st.text_input(
                "Last Name *", 
                value="Johnson",
                help="Enter the person's last name"
            )
        
        st.markdown("---")
        
        # Address section
        st.subheader("📮 Address Information")
        street_address = st.text_input(
            "Street Address *", 
            value="1600 Pennsylvania Ave NW",
            help="Include apartment/unit number if applicable"
        )
        
        col3, col4, col5 = st.columns([2, 1, 1])
        
        with col3:
            city = st.text_input(
                "City *", 
                value="Washington",
                help="City name"
            )
        
        with col4:
            state = st.text_input(
                "State *", 
                value="DC",
                max_chars=2,
                help="2-letter state code"
            ).upper()
        
        with col5:
            zip_code = st.text_input(
                "ZIP Code *", 
                value="20500",
                help="5 or 9-digit ZIP code"
            )
        
        # Submit button
        submitted = st.form_submit_button(
            "🔍 Validate Name & Address", 
            use_container_width=True,
            type="primary"
        )
    
    # Process validation
    if submitted:
        debug_logger.log("🔄 Starting single validation process...")
        
        if not all([first_name, last_name, street_address, city, state, zip_code]):
            st.error("❌ Please fill in all required fields")
            debug_logger.log("❌ Missing required fields")
        else:
            # Show progress
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                # Validate name
                status_text.text("👤 Validating name...")
                debug_logger.log(f"👤 Validating name: {first_name} {last_name}")
                progress_bar.progress(25)
                
                name_result = name_validator.validate(first_name, last_name)
                debug_logger.log(f"👤 Name validation result: valid={name_result['valid']}, confidence={name_result['confidence']:.1%}")
                
                # Validate address
                status_text.text("📮 Validating address...")
                debug_logger.log(f"📮 Validating address: {street_address}, {city}, {state} {zip_code}")
                progress_bar.progress(50)
                
                address_data = {
                    'street_address': street_address,
                    'city': city,
                    'state': state,
                    'zip_code': zip_code
                }
                
                address_result = address_validator.validate_address(address_data)
                debug_logger.log(f"📮 Address validation result: success={address_result.get('success', False)}, deliverable={address_result.get('deliverable', False)}")
                
                progress_bar.progress(100)
                status_text.text("✅ Validation complete!")
                
                # Display results
                time.sleep(0.5)
                progress_bar.empty()
                status_text.empty()
                
                display_single_validation_results(name_result, address_result, debug_logger)
                
            except Exception as e:
                st.error(f"❌ Validation error: {e}")
                if st.session_state.get('debug_mode', False):
                    st.exception(e)
                progress_bar.empty()
                status_text.empty()
    
    # Quick test examples
    else:
        render_quick_tests()


def render_quick_tests():
    """Render quick test examples"""
    st.markdown("---")
    st.header("🧪 Quick Tests")
    st.write("Try these example combinations:")
    
    col1, col2, col3 = st.columns(3)
    
    test_data = [
        {
            "name": "🏛️ Government Official",
            "first": "John",
            "last": "Smith", 
            "street": "1600 Pennsylvania Ave NW",
            "city": "Washington",
            "state": "DC",
            "zip": "20500"
        },
        {
            "name": "🏢 Business Address",
            "first": "Jane",
            "last": "Johnson",
            "street": "350 Fifth Avenue",
            "city": "New York",
            "state": "NY", 
            "zip": "10118"
        },
        {
            "name": "❌ Invalid Data",
            "first": "Jhonny",
            "last": "Smithh",
            "street": "123 Fake Street",
            "city": "Nowhere",
            "state": "XX",
            "zip": "00000"
        }
    ]
    
    for i, data in enumerate(test_data):
        with [col1, col2, col3][i]:
            if st.button(data["name"], use_container_width=True, key=f"test_{i}"):
                st.info(f"Test example: {data['first']} {data['last']}, {data['street']}")


def display_single_validation_results(name_result: Dict, address_result: Dict, debug_logger):
    """Display validation results for single validation"""
    st.markdown("---")
    st.header("📊 Validation Results")
    
    # Split results into columns
    col_name, col_address = st.columns(2)
    
    with col_name:
        st.subheader("👤 Name Results")
        display_name_results(name_result, debug_logger)
    
    with col_address:
        st.subheader("📮 Address Results")
        display_address_results(address_result, debug_logger)
    
    # Overall summary
    st.markdown("---")
    st.subheader("📋 Summary")
    
    name_valid = name_result['valid']
    address_valid = address_result.get('success', False) and address_result.get('deliverable', False)
    
    if name_valid and address_valid:
        st.success("🎉 **Both name and address are valid!**")
        st.balloons()
    elif name_valid:
        st.warning("⚠️ **Name is valid, but address has issues**")
    elif address_valid:
        st.warning("⚠️ **Address is valid, but name has issues**")
    else:
        st.error("❌ **Both name and address have validation issues**")
    
    debug_logger.log("✅ Validation process completed")


def display_name_results(result: Dict, debug_logger):
    """Display name validation results"""
    debug_logger.log("📊 Displaying name validation results")
    
    if result['valid']:
        st.success("✅ **Name is valid!**")
        normalized = result['normalized']
        st.write(f"**Normalized:** {normalized['first_name']} {normalized['last_name']}")
        st.write(f"**Confidence:** {result['confidence']:.1%}")
        
        # Name analysis
        if result.get('analysis'):
            analysis = result['analysis']
            col1, col2 = st.columns(2)
            
            with col1:
                if 'first_name' in analysis:
                    first_info = analysis['first_name']
                    st.write("**First Name:**")
                    st.write(f"• Common: {'Yes' if first_info['is_common'] else 'No'}")
                    st.write(f"• Frequency: {first_info.get('frequency', 'unknown').replace('_', ' ').title()}")
                    if first_info.get('rank'):
                        st.write(f"• Rank: #{first_info['rank']}")
            
            with col2:
                if 'last_name' in analysis:
                    last_info = analysis['last_name']
                    st.write("**Last Name:**")
                    st.write(f"• Common: {'Yes' if last_info['is_common'] else 'No'}")
                    st.write(f"• Frequency: {last_info.get('frequency', 'unknown').replace('_', ' ').title()}")
                    if last_info.get('rank'):
                        st.write(f"• Rank: #{last_info['rank']}")
    else:
        st.error("❌ **Name validation failed**")
        for error in result['errors']:
            st.error(f"• {error}")
    
    # Warnings and suggestions
    if result.get('warnings'):
        for warning in result['warnings']:
            st.warning(f"⚠️ {warning}")
    
    if result.get('suggestions'):
        st.subheader("💡 Suggestions")
        for field, suggestions in result['suggestions'].items():
            if suggestions:
                st.write(f"**{field.replace('_', ' ').title()}:**")
                for suggestion in suggestions[:3]:
                    st.write(f"• {suggestion['suggestion']} ({suggestion['confidence']:.1%}) - {suggestion['reason']}")


def display_address_results(result: Dict, debug_logger):
    """Display address validation results"""
    debug_logger.log("📊 Displaying address validation results")
    
    if result['success']:
        if result['deliverable']:
            st.success("✅ **Address is valid and deliverable!**")
            
            std = result['standardized']
            st.write("**Standardized Address:**")
            st.write(f"**{std['street_address']}**")
            st.write(f"**{std['city']}, {std['state']} {std['zip_code']}**")
            
            # Address metadata
            metadata = result['metadata']
            if any([metadata['business'], metadata['vacant'], metadata['centralized']]):
                st.write("**Additional Information:**")
                if metadata['business']:
                    st.info("📦 Business address")
                if metadata['vacant']:
                    st.warning("🏚️ Vacant property")
                if metadata['centralized']:
                    st.info("📮 Centralized delivery")
        
        elif result['valid']:
            st.warning("⚠️ **Address found but may not be deliverable**")
            if 'standardized' in result:
                std = result['standardized']
                st.write(f"**{std['street_address']}**")
                st.write(f"**{std['city']}, {std['state']} {std['zip_code']}**")
        
        else:
            st.error("❌ **Address not valid**")
    
    else:
        st.error(f"❌ **Address validation failed:** {result['error']}")
        if result.get('details'):
            st.write(f"**Details:** {result['details']}")


if __name__ == "__main__":
    main()