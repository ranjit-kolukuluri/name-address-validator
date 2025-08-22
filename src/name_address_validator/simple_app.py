# src/name_address_validator/simple_app.py - Standalone version
"""
Simplified Streamlit app with relative imports - use this if having path issues
"""

import streamlit as st
import pandas as pd
import sys
import os
from pathlib import Path

# Add current directory to path for relative imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

try:
    # Try relative imports first
    from services.validation_service import ValidationService
    from utils.config import load_usps_credentials
    print("✅ Using relative imports")
except ImportError:
    try:
        # Fallback to absolute imports
        sys.path.insert(0, str(current_dir.parent))
        from name_address_validator.services.validation_service import ValidationService
        from name_address_validator.utils.config import load_usps_credentials
        print("✅ Using absolute imports")
    except ImportError as e:
        st.error(f"❌ Could not import required modules: {e}")
        st.error("**To fix this:**")
        st.write("1. Make sure you're in the project root directory")
        st.write("2. Run: `streamlit run src/name_address_validator/simple_app.py`")
        st.write("3. Or install the package: `pip install -e .`")
        st.stop()

def main():
    st.set_page_config(
        page_title="Name and Address Validator",
        page_icon="🔍",
        layout="wide"
    )
    
    st.title("🔍 Name and Address Validator")
    st.write("Simplified version for testing imports")
    
    # Test USPS credentials
    try:
        client_id, client_secret = load_usps_credentials()
        if client_id and client_secret:
            st.success("✅ USPS API credentials configured")
        else:
            st.warning("⚠️ USPS API credentials not found")
    except Exception as e:
        st.error(f"❌ Error loading credentials: {e}")
    
    # Test validation service
    try:
        service = ValidationService()
        st.success("✅ ValidationService loaded successfully")
        
        # Simple single validation form
        st.subheader("Single Record Validation")
        
        col1, col2 = st.columns(2)
        with col1:
            first_name = st.text_input("First Name", "John")
        with col2:
            last_name = st.text_input("Last Name", "Doe")
        
        street_address = st.text_input("Street Address", "123 Main Street")
        
        col3, col4, col5 = st.columns(3)
        with col3:
            city = st.text_input("City", "New York")
        with col4:
            state = st.text_input("State", "NY")
        with col5:
            zip_code = st.text_input("ZIP Code", "10001")
        
        if st.button("Validate", type="primary"):
            if all([first_name, last_name, street_address, city, state, zip_code]):
                try:
                    with st.spinner("Validating..."):
                        result = service.validate_single_record(
                            first_name, last_name, street_address, city, state, zip_code
                        )
                    
                    st.success("✅ Validation completed!")
                    
                    # Show results
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Overall Valid", "✅" if result['overall_valid'] else "❌")
                    with col2:
                        st.metric("Confidence", f"{result['overall_confidence']:.1%}")
                    
                    # Show detailed results
                    with st.expander("Detailed Results"):
                        st.json(result)
                        
                except Exception as e:
                    st.error(f"❌ Validation error: {e}")
            else:
                st.warning("Please fill in all fields")
    
    except Exception as e:
        st.error(f"❌ Error initializing ValidationService: {e}")
    
    # File upload test
    st.subheader("File Upload Test")
    uploaded_file = st.file_uploader("Upload a CSV file", type=['csv'])
    
    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            st.success(f"✅ File loaded: {len(df)} rows, {len(df.columns)} columns")
            st.dataframe(df.head())
        except Exception as e:
            st.error(f"❌ Error reading file: {e}")

if __name__ == "__main__":
    main()