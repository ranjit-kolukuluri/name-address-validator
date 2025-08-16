# src/name_address_validator/app.py - FIXED with absolute imports
"""
Streamlit web application for name and address validation
FIXED: Uses absolute imports that work with direct execution
"""

import streamlit as st
import time
import sys
import os
from datetime import datetime
from typing import Dict, Optional, Tuple
from pathlib import Path

# Add the src directory to Python path for absolute imports
current_dir = Path(__file__).parent
src_dir = current_dir.parent.parent
sys.path.insert(0, str(src_dir))

# Now use absolute imports
from name_address_validator.validators.name_validator import EnhancedNameValidator
from name_address_validator.validators.address_validator import USPSAddressValidator


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
        else:
            st.info("No debug logs yet. Enable debug mode and run validation.")


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


def main():
    """Main Streamlit application"""
    
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
    
    # Sidebar with debug options
    with st.sidebar:
        st.header("🔧 Debug Options")
        debug_mode = st.checkbox("Enable debug mode", value=False)
        
        if st.button("Clear debug logs"):
            debug_logger.clear()
            st.success("Debug logs cleared!")
        
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
    
    debug_logger.enabled = debug_mode
    debug_logger.log("🚀 App started")
    
    # Load credentials
    client_id, client_secret = load_usps_credentials()
    
    if not client_id or not client_secret:
        debug_logger.log("❌ Credentials not found")
        st.error("❌ USPS API credentials not configured")
        
        with st.expander("📋 Setup Instructions"):
            st.markdown("""
            **Step 1:** Get USPS API credentials at [developer.usps.com](https://developer.usps.com/)
            
            **Step 2:** Create `.streamlit/secrets.toml` file:
            ```toml
            USPS_CLIENT_ID = "your_actual_client_id"
            USPS_CLIENT_SECRET = "your_actual_client_secret"
            ```
            
            **Step 3:** Restart the Streamlit app
            """)
        
        if debug_mode:
            debug_logger.display()
        return
    
    debug_logger.log("✅ Credentials loaded successfully")
    debug_logger.log(f"🔧 Client ID: {client_id[:8]}...{client_id[-4:]}")
    
    # Initialize validators
    name_validator = EnhancedNameValidator()
    address_validator = USPSAddressValidator(
        client_id, 
        client_secret, 
        debug_callback=debug_logger.log if debug_mode else lambda x: None
    )
    
    debug_logger.log("🔧 Validators initialized")
    
    # Show credential status
    st.success("✅ USPS API configured")
    
    # Main validation form
    st.header("🔍 Combined Validation")
    
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
        debug_logger.log("🔄 Starting validation process...")
        
        if not all([first_name, last_name, street_address, city, state, zip_code]):
            st.error("❌ Please fill in all required fields")
            debug_logger.log("❌ Missing required fields")
        else:
            # Show progress
            progress_bar = st.progress(0)
            status_text = st.empty()
            
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
            
            display_results(name_result, address_result, debug_logger)
    
    # Quick test examples
    else:
        render_quick_tests()
    
    # Display debug logs if enabled
    if debug_mode:
        st.markdown("---")
        debug_logger.display()


def display_results(name_result: Dict, address_result: Dict, debug_logger):
    """Display validation results"""
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
                # Set session state to populate form with test data
                st.session_state.test_first = data["first"]
                st.session_state.test_last = data["last"]
                st.session_state.test_street = data["street"]
                st.session_state.test_city = data["city"]
                st.session_state.test_state = data["state"]
                st.session_state.test_zip = data["zip"]
                st.experimental_rerun()


if __name__ == "__main__":
    main()