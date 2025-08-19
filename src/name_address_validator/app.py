# src/name_address_validator/app.py - Enterprise SaaS UI (UI Only)
"""
Enterprise SaaS Name and Address Validator - Streamlit Interface
Clean, modularized version with validation logic in separate modules
"""

import streamlit as st
import pandas as pd
import time
import sys
import os
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, List
from pathlib import Path

# Setup Python path
def setup_python_path():
    current_file = Path(__file__).resolve()
    possible_src_dirs = [
        current_file.parent.parent.parent / "src",
        current_file.parent.parent,
        current_file.parent.parent.parent / "src",
        Path("/mount/src") / "name-address-validator" / "src",
        Path("/mount/src") / os.environ.get("STREAMLIT_REPO_NAME", "name-address-validator") / "src",
    ]
    
    for src_dir in possible_src_dirs:
        if src_dir.exists() and (src_dir / "name_address_validator").exists():
            if str(src_dir) not in sys.path:
                sys.path.insert(0, str(src_dir))
            return src_dir
    
    fallback_paths = [
        str(current_file.parent.parent.parent),
        str(current_file.parent.parent),
    ]
    
    for path in fallback_paths:
        if path not in sys.path:
            sys.path.insert(0, path)
    
    return None

setup_python_path()

# Import modules
try:
    from name_address_validator.validators.name_validator import EnhancedNameValidator
    from name_address_validator.validators.address_validator import USPSAddressValidator
    from name_address_validator.utils.config import load_usps_credentials
    from name_address_validator.utils.logger import DebugLogger
    imports_successful = True
except ImportError as e:
    st.error(f"Import Error: {e}")
    imports_successful = False

if not imports_successful:
    st.error("Unable to import required modules. Please check the deployment.")
    st.stop()


# Debug and Monitoring System (UI-specific)
class DebugMonitor:
    """Comprehensive debug and monitoring system for UI"""
    
    def __init__(self):
        if 'debug_logs' not in st.session_state:
            st.session_state.debug_logs = []
        if 'performance_metrics' not in st.session_state:
            st.session_state.performance_metrics = []
        if 'validation_stats' not in st.session_state:
            st.session_state.validation_stats = {
                'total_validations': 0,
                'successful_validations': 0,
                'failed_validations': 0,
                'api_calls': 0,
                'api_errors': 0,
                'session_start': datetime.now()
            }
    
    def log(self, level: str, message: str, category: str = "GENERAL", **kwargs):
        """Add a debug log entry"""
        log_entry = {
            'timestamp': datetime.now(),
            'level': level.upper(),
            'category': category.upper(),
            'message': message,
            'details': kwargs
        }
        
        st.session_state.debug_logs.append(log_entry)
        
        # Keep only last 500 logs to prevent memory issues
        if len(st.session_state.debug_logs) > 500:
            st.session_state.debug_logs = st.session_state.debug_logs[-500:]
        
        # Also log to console for server-side monitoring
        timestamp = log_entry['timestamp'].strftime("%H:%M:%S")
        print(f"[{timestamp}] {level.upper()} {category}: {message}")
    
    def log_performance(self, operation: str, duration_ms: int, success: bool = True):
        """Log performance metrics"""
        metric = {
            'timestamp': datetime.now(),
            'operation': operation,
            'duration_ms': duration_ms,
            'success': success
        }
        
        st.session_state.performance_metrics.append(metric)
        
        # Keep only last 100 metrics
        if len(st.session_state.performance_metrics) > 100:
            st.session_state.performance_metrics = st.session_state.performance_metrics[-100:]
    
    def update_stats(self, stat_type: str, increment: int = 1):
        """Update validation statistics"""
        if stat_type in st.session_state.validation_stats:
            st.session_state.validation_stats[stat_type] += increment
    
    def get_recent_logs(self, minutes: int = 5) -> List[Dict]:
        """Get logs from the last N minutes"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        return [log for log in st.session_state.debug_logs if log['timestamp'] > cutoff_time]
    
    def get_error_summary(self) -> Dict:
        """Get summary of recent errors"""
        recent_logs = self.get_recent_logs(60)  # Last hour
        errors = [log for log in recent_logs if log['level'] in ['ERROR', 'CRITICAL']]
        
        error_summary = {}
        for error in errors:
            category = error['category']
            if category not in error_summary:
                error_summary[category] = 0
            error_summary[category] += 1
        
        return error_summary

# Global debug monitor
debug_monitor = DebugMonitor()


def apply_enterprise_saas_css():
    """Apply modern enterprise SaaS styling"""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    .main {
        font-family: 'Inter', sans-serif;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
    }
    
    /* Header Styles */
    .enterprise-header {
        background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
        padding: 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        position: relative;
    }
    
    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: #ffffff;
        text-align: center;
        margin-bottom: 0.5rem;
        letter-spacing: -0.025em;
    }
    
    .subtitle {
        font-size: 1.1rem;
        color: #cbd5e1;
        text-align: center;
        font-weight: 400;
        margin-bottom: 1rem;
    }
    
    .api-status {
        background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
        color: #ffffff;
        padding: 0.75rem 1.5rem;
        border-radius: 50px;
        font-weight: 600;
        font-size: 0.875rem;
        text-align: center;
        margin: 0 auto;
        max-width: 300px;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
        border: 2px solid #60a5fa;
        animation: pulse-glow 2s infinite;
    }
    
    .api-status.error {
        background: linear-gradient(135deg, #991b1b 0%, #dc2626 100%);
        border: 2px solid #ef4444;
        box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
    }
    
    @keyframes pulse-glow {
        0%, 100% { box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3); }
        50% { box-shadow: 0 6px 20px rgba(59, 130, 246, 0.5); }
    }
    
    /* Card Styles */
    .glass-card {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(20px);
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        margin: 1rem 0;
        transition: all 0.3s ease;
    }
    
    .glass-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
    }
    
    .section-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #1e40af;
        margin-bottom: 1.5rem;
        padding-bottom: 0.75rem;
        border-bottom: 2px solid #e2e8f0;
        position: relative;
    }
    
    .section-header::after {
        content: '';
        position: absolute;
        bottom: -2px;
        left: 0;
        width: 60px;
        height: 2px;
        background: linear-gradient(90deg, #3b82f6, #8b5cf6);
        border-radius: 1px;
    }
    
    /* Form Styles */
    .form-section {
        background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid #e2e8f0;
    }
    
    .form-group-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1e40af;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
    }
    
    .form-group-title::before {
        content: '';
        width: 4px;
        height: 20px;
        background: linear-gradient(135deg, #3b82f6, #8b5cf6);
        border-radius: 2px;
        margin-right: 0.75rem;
    }
    
    /* Status Messages */
    .status-success {
        background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
        border: 1px solid #86efac;
        color: #065f46;
        padding: 1rem;
        border-radius: 12px;
        margin: 0.5rem 0;
        font-weight: 500;
        display: flex;
        align-items: center;
        box-shadow: 0 4px 6px rgba(16, 185, 129, 0.1);
    }
    
    .status-error {
        background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
        border: 1px solid #fca5a5;
        color: #991b1b;
        padding: 1rem;
        border-radius: 12px;
        margin: 0.5rem 0;
        font-weight: 500;
        display: flex;
        align-items: center;
        box-shadow: 0 4px 6px rgba(239, 68, 68, 0.1);
    }
    
    .status-warning {
        background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
        border: 1px solid #fed7aa;
        color: #92400e;
        padding: 1rem;
        border-radius: 12px;
        margin: 0.5rem 0;
        font-weight: 500;
        display: flex;
        align-items: center;
        box-shadow: 0 4px 6px rgba(245, 158, 11, 0.1);
    }
    
    .status-info {
        background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
        border: 1px solid #93c5fd;
        color: #1e40af;
        padding: 1rem;
        border-radius: 12px;
        margin: 0.5rem 0;
        font-weight: 500;
        display: flex;
        align-items: center;
        box-shadow: 0 4px 6px rgba(59, 130, 246, 0.1);
    }
    
    /* Metrics Cards */
    .metric-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #3b82f6, #8b5cf6, #ec4899);
    }
    
    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #1e40af;
        margin-bottom: 0.25rem;
    }
    
    .metric-label {
        font-size: 0.875rem;
        color: #64748b;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Status Values */
    .status-valid {
        color: #1e40af;
        font-weight: 600;
    }
    
    .status-invalid {
        color: #991b1b;
        font-weight: 600;
    }
    
    .status-warning {
        color: #92400e;
        font-weight: 600;
    }
    
    /* Button Styles */
    .stButton > button {
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 14px rgba(59, 130, 246, 0.3);
        text-transform: none;
        letter-spacing: 0.025em;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(59, 130, 246, 0.4);
        background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
    }
    
    .stButton > button:disabled {
        background: linear-gradient(135deg, #9ca3af 0%, #6b7280 100%);
        cursor: not-allowed;
        transform: none;
        box-shadow: none;
    }
    
    /* Progress Bar */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #3b82f6, #8b5cf6, #ec4899);
    }
    
    /* Tab Styles */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 4px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background: transparent;
        border-radius: 8px;
        color: #64748b;
        font-weight: 500;
        border: none;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
        color: white;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
    }
    
    /* Data Frame Styling */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    }
    
    /* Expander Styling */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        border-radius: 8px;
        border: 1px solid #e2e8f0;
    }
    
    /* Debug Panel Styling */
    .debug-panel {
        background: #f8fafc;
        border-radius: 12px;
        padding: 1rem;
        margin: 1rem 0;
        border: 2px solid #3b82f6;
    }
    
    .debug-log {
        font-family: 'Monaco', 'Menlo', monospace;
        font-size: 0.8rem;
        color: #1e293b;
        background: #ffffff;
        padding: 0.5rem;
        border-radius: 6px;
        margin: 0.25rem 0;
        border-left: 4px solid #3b82f6;
        border: 1px solid #e2e8f0;
    }
    
    .debug-log.error {
        border-left-color: #ef4444;
        background: #fef2f2;
        color: #991b1b;
    }
    
    .debug-log.warning {
        border-left-color: #f59e0b;
        background: #fffbeb;
        color: #92400e;
    }
    
    .debug-log.info {
        border-left-color: #3b82f6;
        background: #eff6ff;
        color: #1e40af;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .main-title {
            font-size: 2rem;
        }
        
        .glass-card {
            padding: 1.5rem;
            margin: 0.5rem 0;
        }
        
        .metric-card {
            padding: 1rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)


def display_status_message(message: str, status_type: str = "info"):
    """Display styled status messages"""
    icons = {
        "success": "✓",
        "error": "✗", 
        "warning": "⚠",
        "info": "ℹ"
    }
    
    icon = icons.get(status_type, "ℹ")
    st.markdown(f'<div class="status-{status_type}">{icon} {message}</div>', unsafe_allow_html=True)


def render_api_status(client_id: Optional[str], client_secret: Optional[str]):
    """Render USPS API connection status"""
    if client_id and client_secret:
        st.markdown('''
        <div class="api-status">
            ✓ Connected to USPS API - Real-time Address Validation Active
        </div>
        ''', unsafe_allow_html=True)
        debug_monitor.log("INFO", "USPS API status displayed as connected", "UI")
    else:
        st.markdown('''
        <div class="api-status error">
            ✗ USPS API Not Connected - Please Configure Credentials
        </div>
        ''', unsafe_allow_html=True)
        debug_monitor.log("WARNING", "USPS API status displayed as disconnected", "UI")


def render_single_validation():
    """Render single validation form - Clean Professional Version"""
    
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">Single Record Validation</div>', unsafe_allow_html=True)
    
    # Personal Information Section
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    st.markdown('<div class="form-group-title">Personal Information</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        first_name = st.text_input(
            "First Name", 
            key="fn",
            placeholder="Enter first name",
            help="Enter the person's first name"
        )
    with col2:
        last_name = st.text_input(
            "Last Name", 
            key="ln",
            placeholder="Enter last name", 
            help="Enter the person's last name"
        )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Address Information Section
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    st.markdown('<div class="form-group-title">Address Information</div>', unsafe_allow_html=True)
    
    street_address = st.text_input(
        "Street Address", 
        key="sa",
        placeholder="123 Main Street, Apt 4B",
        help="Enter the complete street address including apartment/unit number if applicable"
    )
    
    col3, col4, col5 = st.columns([3, 1, 2])
    with col3:
        city = st.text_input(
            "City", 
            key="city",
            placeholder="Enter city",
            help="Enter the city name"
        )
    with col4:
        state = st.text_input(
            "State", 
            key="state",
            placeholder="CA",
            help="Enter 2-letter state code (e.g., CA, NY, TX)",
            max_chars=2
        )
    with col5:
        zip_code = st.text_input(
            "ZIP Code", 
            key="zip",
            placeholder="12345 or 12345-6789",
            help="Enter 5-digit ZIP code or ZIP+4 format"
        )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Validation Logic
    all_fields_have_content = (
        first_name and len(first_name.strip()) > 0 and
        last_name and len(last_name.strip()) > 0 and
        street_address and len(street_address.strip()) > 0 and
        city and len(city.strip()) > 0 and
        state and len(state.strip()) > 0 and
        zip_code and len(zip_code.strip()) > 0
    )
    
    # Validation Button
    button_col1, button_col2, button_col3 = st.columns([1, 2, 1])
    
    with button_col2:
        if st.button(
            "🔍 Validate Record", 
            disabled=not all_fields_have_content, 
            type="primary",
            use_container_width=True
        ):
            process_single_validation(first_name, last_name, street_address, city, state, zip_code)
    
    # Helpful guidance (only if fields are missing)
    if not all_fields_have_content:
        missing_fields = []
        if not first_name or not first_name.strip():
            missing_fields.append("First Name")
        if not last_name or not last_name.strip():
            missing_fields.append("Last Name")
        if not street_address or not street_address.strip():
            missing_fields.append("Street Address")
        if not city or not city.strip():
            missing_fields.append("City")
        if not state or not state.strip():
            missing_fields.append("State")
        if not zip_code or not zip_code.strip():
            missing_fields.append("ZIP Code")
        
        if missing_fields:
            st.markdown('<div class="form-section">', unsafe_allow_html=True)
            display_status_message(
                f"Please complete the following required fields: {', '.join(missing_fields)}", 
                "info"
            )
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Usage Instructions
    with st.expander("ℹ️ How to Use This Tool"):
        st.markdown("""
        **Step-by-step Instructions:**
        
        1. **Enter Personal Information**: Fill in the person's first and last name
        2. **Enter Address Details**: Provide the complete street address, city, state, and ZIP code
        3. **Validate**: Click the "Validate Record" button to check the information
        4. **Review Results**: The system will validate both name and address data using:
           - US Census name databases for name validation
           - USPS API for real-time address verification
        
        **Tips for Best Results:**
        - Use complete street addresses (include apartment/unit numbers if applicable)
        - Enter state as 2-letter codes (CA, NY, TX, etc.)
        - ZIP codes can be 5-digit (12345) or ZIP+4 format (12345-6789)
        - Ensure all fields are filled before validation
        """)
    
    st.markdown('</div>', unsafe_allow_html=True)


def process_single_validation(first_name: str, last_name: str, street_address: str, city: str, state: str, zip_code: str):
    """Process single record validation"""
    
    debug_monitor.log("INFO", "Starting single validation process", "VALIDATION")
    start_time = time.time()
    
    # Load credentials
    client_id, client_secret = load_usps_credentials()
    if not client_id or not client_secret:
        display_status_message("USPS API credentials not configured. Please contact administrator.", "error")
        debug_monitor.log("ERROR", "USPS credentials not available for validation", "CONFIG")
        debug_monitor.update_stats('failed_validations')
        return
    
    try:
        name_validator = EnhancedNameValidator()
        address_validator = USPSAddressValidator(
            client_id, 
            client_secret,
            debug_callback=lambda msg: debug_monitor.log("INFO", msg, "USPS_API")
        )
        
        debug_monitor.log("INFO", "Validators initialized successfully", "VALIDATION")
        
        # Progress tracking
        with st.container():
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Validate name
            status_text.text("Validating name...")
            progress_bar.progress(25)
            time.sleep(0.3)
            
            name_start = time.time()
            name_result = name_validator.validate(first_name, last_name)
            name_duration = int((time.time() - name_start) * 1000)
            
            debug_monitor.log_performance("name_validation_full", name_duration, name_result['valid'])
            
            # Validate address
            status_text.text("Validating address with USPS...")
            progress_bar.progress(75)
            time.sleep(0.3)
            
            address_start = time.time()
            debug_monitor.update_stats('api_calls')
            
            address_data = {
                'street_address': street_address,
                'city': city,
                'state': state,
                'zip_code': zip_code
            }
            
            address_result = address_validator.validate_address(address_data)
            address_duration = int((time.time() - address_start) * 1000)
            
            if address_result.get('success', False):
                debug_monitor.log_performance("address_validation_full", address_duration, True)
            else:
                debug_monitor.log_performance("address_validation_full", address_duration, False)
                debug_monitor.update_stats('api_errors')
            
            progress_bar.progress(100)
            status_text.text("Validation complete")
            time.sleep(0.5)
            
            # Clear progress
            progress_bar.empty()
            status_text.empty()
            
            # Log overall performance
            total_duration = int((time.time() - start_time) * 1000)
            debug_monitor.log_performance("single_validation_complete", total_duration, True)
            debug_monitor.update_stats('successful_validations')
            
            # Display results
            display_results(name_result, address_result)
            
    except Exception as e:
        debug_monitor.log("ERROR", f"Single validation process failed: {str(e)}", "VALIDATION")
        debug_monitor.update_stats('failed_validations')
        display_status_message(f"Validation error: {str(e)}", "error")


def display_results(name_result: Dict, address_result: Dict):
    """Display validation results with enterprise styling"""
    
    debug_monitor.log("INFO", "Displaying validation results", "UI")
    
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">Validation Results</div>', unsafe_allow_html=True)
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        name_valid = name_result['valid']
        status_class = "valid" if name_valid else "invalid"
        name_status = "Valid" if name_valid else "Invalid"
        
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-value status-{status_class}">{name_status}</div>
            <div class="metric-label">Name Status</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        address_deliverable = address_result.get('deliverable', False)
        status_class = "valid" if address_deliverable else "invalid"
        address_status = "Deliverable" if address_deliverable else "Not Deliverable"
        
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-value status-{status_class}">{address_status}</div>
            <div class="metric-label">Address Status</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col3:
        overall_confidence = (name_result.get('confidence', 0) + address_result.get('confidence', 0)) / 2
        confidence_class = "valid" if overall_confidence > 0.8 else "warning" if overall_confidence > 0.5 else "invalid"
        
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-value status-{confidence_class}">{overall_confidence:.1%}</div>
            <div class="metric-label">Overall Confidence</div>
        </div>
        ''', unsafe_allow_html=True)
    
    # Detailed results
    col_name, col_address = st.columns(2)
    
    with col_name:
        st.markdown('<div class="form-section">', unsafe_allow_html=True)
        st.markdown('<div class="form-group-title">Name Validation Details</div>', unsafe_allow_html=True)
        
        if name_result['valid']:
            display_status_message("Name validation passed", "success")
            normalized = name_result['normalized']
            st.write(f"**Normalized:** {normalized['first_name']} {normalized['last_name']}")
            st.write(f"**Confidence:** {name_result['confidence']:.1%}")
        else:
            display_status_message("Name validation failed", "error")
            for error in name_result['errors']:
                st.write(f"• {error}")
        
        if name_result.get('suggestions'):
            st.write("**Suggestions:**")
            for field, suggestions in name_result['suggestions'].items():
                if suggestions:
                    st.write(f"**{field.replace('_', ' ').title()}:**")
                    for suggestion in suggestions[:3]:
                        st.write(f"• {suggestion['suggestion']} ({suggestion['confidence']:.1%})")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_address:
        st.markdown('<div class="form-section">', unsafe_allow_html=True)
        st.markdown('<div class="form-group-title">Address Validation Details</div>', unsafe_allow_html=True)
        
        if address_result.get('success', False):
            if address_result.get('deliverable', False):
                display_status_message("Address is valid and deliverable", "success")
                
                std = address_result['standardized']
                st.write("**Standardized Address:**")
                st.write(f"{std['street_address']}")
                st.write(f"{std['city']}, {std['state']} {std['zip_code']}")
                
                metadata = address_result.get('metadata', {})
                if metadata.get('business'):
                    display_status_message("Business address", "info")
                if metadata.get('vacant'):
                    display_status_message("Vacant property", "warning")
            else:
                display_status_message("Address found but may not be deliverable", "warning")
        else:
            display_status_message(f"Address validation failed: {address_result.get('error', 'Unknown error')}", "error")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)


def render_bulk_validation():
    """Render bulk validation interface"""
    debug_monitor.log("INFO", "Rendering bulk validation interface", "UI")
    
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">Batch Processing</div>', unsafe_allow_html=True)
    
    st.write("Upload a CSV file to validate multiple records simultaneously")
    
    # Template section
    with st.expander("Download CSV Template"):
        st.write("Use this template for consistent data formatting:")
        
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
            label="Download Template",
            data=csv_template,
            file_name="validation_template.csv",
            mime="text/csv"
        )
    
    # File upload
    uploaded_file = st.file_uploader(
        "Choose CSV file",
        type=['csv'],
        help="CSV file with required columns: first_name, last_name, street_address, city, state, zip_code"
    )
    
    if uploaded_file is not None:
        debug_monitor.log("INFO", "CSV file uploaded", "BULK_VALIDATION", filename=uploaded_file.name)
        
        try:
            df = pd.read_csv(uploaded_file)
            
            required_columns = ['first_name', 'last_name', 'street_address', 'city', 'state', 'zip_code']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                display_status_message(f"Missing required columns: {', '.join(missing_columns)}", "error")
                debug_monitor.log("ERROR", "CSV missing required columns", "BULK_VALIDATION", missing_columns=missing_columns)
                return
            
            display_status_message(f"File uploaded successfully. Found {len(df)} records.", "success")
            debug_monitor.log("INFO", "CSV file processed successfully", "BULK_VALIDATION", record_count=len(df))
            
            # Data preview
            st.markdown('<div class="form-section">', unsafe_allow_html=True)
            st.markdown('<div class="form-group-title">Data Preview</div>', unsafe_allow_html=True)
            st.dataframe(df.head(10), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Processing options
            col1, col2 = st.columns(2)
            
            with col1:
                max_records = st.number_input(
                    "Maximum records to process",
                    min_value=1,
                    max_value=min(500, len(df)),
                    value=min(50, len(df)),
                    help="Limit processing to prevent timeout"
                )
            
            with col2:
                include_suggestions = st.checkbox("Include suggestions", value=True)
            
            if st.button("Start Batch Validation", type="primary"):
                debug_monitor.log("INFO", "Starting batch validation", "BULK_VALIDATION", max_records=max_records)
                process_bulk_validation(df.head(max_records), include_suggestions)
                
        except Exception as e:
            display_status_message(f"Error reading CSV file: {str(e)}", "error")
            debug_monitor.log("ERROR", "Failed to process CSV file", "BULK_VALIDATION", error=str(e))
    
    st.markdown('</div>', unsafe_allow_html=True)


def process_bulk_validation(df: pd.DataFrame, include_suggestions: bool):
    """Process bulk validation with enhanced features"""
    
    debug_monitor.log("INFO", "Starting bulk validation process", "BULK_VALIDATION", record_count=len(df))
    batch_start_time = time.time()
    
    client_id, client_secret = load_usps_credentials()
    if not client_id or not client_secret:
        display_status_message("USPS API credentials not configured.", "error")
        return
    
    try:
        name_validator = EnhancedNameValidator()
        address_validator = USPSAddressValidator(
            client_id, 
            client_secret,
            debug_callback=lambda msg: debug_monitor.log("DEBUG", msg, "USPS_API")
        )
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        results = []
        success_count = 0
        error_count = 0
        
        for i, (_, row) in enumerate(df.iterrows()):
            progress = (i + 1) / len(df)
            progress_bar.progress(progress)
            status_text.text(f"Processing record {i + 1} of {len(df)}")
            
            debug_monitor.update_stats('total_validations')
            debug_monitor.update_stats('api_calls', 2)
            
            try:
                # Clean and validate data
                first_name = str(row.get('first_name', '')).strip()
                last_name = str(row.get('last_name', '')).strip()
                street_address = str(row.get('street_address', '')).strip()
                city = str(row.get('city', '')).strip()
                state = str(row.get('state', '')).strip().upper()
                zip_code = str(row.get('zip_code', '')).strip()
                
                # Store original address for comparison
                original_address = f"{street_address}, {city}, {state} {zip_code}"
                
                # Validate
                name_result = name_validator.validate(first_name, last_name)
                address_result = address_validator.validate_address({
                    'street_address': street_address,
                    'city': city,
                    'state': state,
                    'zip_code': zip_code
                })
                
                # Determine address type (Business/Residential)
                address_type = "Unknown"
                if address_result.get('success') and address_result.get('metadata'):
                    metadata = address_result['metadata']
                    if metadata.get('business'):
                        address_type = "Business"
                    else:
                        address_type = "Residential"
                
                # Compile result
                overall_valid = name_result['valid'] and address_result.get('deliverable', False)
                
                # Base result structure
                result = {
                    'Row': i + 1,
                    'First Name': first_name,
                    'Last Name': last_name,
                    'Original Address': original_address,
                    'Name Status': 'Valid' if name_result['valid'] else 'Invalid',
                    'Address Status': 'Deliverable' if address_result.get('deliverable', False) else 'Not Deliverable',
                    'Address Type': address_type,
                    'Overall Status': 'Valid' if overall_valid else 'Invalid',
                    'Confidence': f"{((name_result.get('confidence', 0) + address_result.get('confidence', 0)) / 2):.1%}"
                }
                
                # Add suggestions only if checkbox is checked
                if include_suggestions:
                    # Add name suggestions
                    first_name_suggestions = []
                    last_name_suggestions = []
                    
                    if name_result.get('suggestions'):
                        if 'first_name' in name_result['suggestions'] and name_result['suggestions']['first_name']:
                            first_name_suggestions = [s['suggestion'] for s in name_result['suggestions']['first_name'][:3]]
                        if 'last_name' in name_result['suggestions'] and name_result['suggestions']['last_name']:
                            last_name_suggestions = [s['suggestion'] for s in name_result['suggestions']['last_name'][:3]]
                    
                    result['First Name Suggestions'] = ', '.join(first_name_suggestions) if first_name_suggestions else 'None'
                    result['Last Name Suggestions'] = ', '.join(last_name_suggestions) if last_name_suggestions else 'None'
                    
                    # Add address standardization and corrections
                    if address_result.get('success') and address_result.get('standardized'):
                        std = address_result['standardized']
                        standardized_address = f"{std['street_address']}, {std['city']}, {std['state']} {std['zip_code']}"
                        result['USPS Standardized Address'] = standardized_address
                        
                        # Compare original vs standardized to show corrections
                        corrections = []
                        
                        # Check street address changes
                        if street_address.upper() != std['street_address'].upper():
                            corrections.append(f"Street: '{street_address}' → '{std['street_address']}'")
                        
                        # Check city changes
                        if city.upper() != std['city'].upper():
                            corrections.append(f"City: '{city}' → '{std['city']}'")
                        
                        # Check state changes
                        if state.upper() != std['state'].upper():
                            corrections.append(f"State: '{state}' → '{std['state']}'")
                        
                        # Check ZIP changes
                        original_zip = zip_code.split('-')[0]
                        standardized_zip = std['zip_code'].split('-')[0]
                        if original_zip != standardized_zip:
                            corrections.append(f"ZIP: '{zip_code}' → '{std['zip_code']}'")
                        elif len(std['zip_code']) > len(zip_code):
                            corrections.append(f"ZIP+4: '{zip_code}' → '{std['zip_code']}'")
                        
                        result['Address Corrections'] = '; '.join(corrections) if corrections else 'No corrections needed'
                        
                    else:
                        result['USPS Standardized Address'] = 'Not Available'
                        if address_result.get('error'):
                            result['Address Corrections'] = f"Error: {address_result['error']}"
                        else:
                            result['Address Corrections'] = 'Unable to standardize'
                    
                    # Add detailed metadata
                    metadata_details = []
                    if address_result.get('metadata'):
                        metadata = address_result['metadata']
                        
                        if metadata.get('vacant'):
                            metadata_details.append('Vacant Property')
                        if metadata.get('centralized'):
                            metadata_details.append('Centralized Delivery')
                        if metadata.get('carrier_route'):
                            metadata_details.append(f"Route: {metadata['carrier_route']}")
                        if metadata.get('dpv_confirmation'):
                            dpv_meanings = {
                                'Y': 'Deliverable',
                                'N': 'Not Deliverable', 
                                'D': 'Deliverable (Missing Unit)'
                            }
                            dpv_meaning = dpv_meanings.get(metadata['dpv_confirmation'], metadata['dpv_confirmation'])
                            metadata_details.append(f"DPV: {dpv_meaning}")
                    
                    result['Address Details'] = '; '.join(metadata_details) if metadata_details else 'Standard delivery'
                    
                    # Add delivery point information if available
                    if address_result.get('metadata', {}).get('delivery_point'):
                        result['Delivery Point'] = address_result['metadata']['delivery_point']
                    else:
                        result['Delivery Point'] = 'Not Available'
                
                if overall_valid:
                    success_count += 1
                    debug_monitor.update_stats('successful_validations')
                else:
                    error_count += 1
                    debug_monitor.update_stats('failed_validations')
                
                results.append(result)
                
            except Exception as e:
                error_count += 1
                debug_monitor.log("ERROR", f"Error processing record {i + 1}", "BULK_VALIDATION", error=str(e))
                debug_monitor.update_stats('failed_validations')
                debug_monitor.update_stats('api_errors')
                
                # Error result structure
                error_result = {
                    'Row': i + 1,
                    'First Name': str(row.get('first_name', '')),
                    'Last Name': str(row.get('last_name', '')),
                    'Original Address': f"{row.get('street_address', '')}, {row.get('city', '')}, {row.get('state', '')} {row.get('zip_code', '')}",
                    'Name Status': 'Error',
                    'Address Status': 'Error',
                    'Address Type': 'Error',
                    'Overall Status': f'Error: {str(e)[:50]}',
                    'Confidence': '0%'
                }
                
                # Add empty suggestion columns if suggestions are enabled
                if include_suggestions:
                    error_result['First Name Suggestions'] = 'Error'
                    error_result['Last Name Suggestions'] = 'Error'
                    error_result['USPS Standardized Address'] = 'Error'
                    error_result['Address Corrections'] = 'Error'
                    error_result['Address Details'] = 'Error'
                    error_result['Delivery Point'] = 'Error'
                
                results.append(error_result)
        
        # Complete processing
        progress_bar.progress(1.0)
        status_text.text("Batch validation complete")
        time.sleep(0.5)
        progress_bar.empty()
        status_text.empty()
        
        # Log batch completion
        batch_duration = int((time.time() - batch_start_time) * 1000)
        debug_monitor.log_performance("bulk_validation_complete", batch_duration, True)
        debug_monitor.log("INFO", "Batch validation completed", "BULK_VALIDATION", 
                         total_records=len(df), success_count=success_count, error_count=error_count)
        
        # Display results
        display_bulk_results(pd.DataFrame(results), success_count, error_count, include_suggestions)
        
    except Exception as e:
        debug_monitor.log("ERROR", f"Bulk validation process failed: {str(e)}", "BULK_VALIDATION")
        display_status_message(f"Batch validation error: {str(e)}", "error")


def display_bulk_results(results_df: pd.DataFrame, success_count: int, error_count: int, include_suggestions: bool = False):
    """Display bulk validation results with enhanced metrics"""
    
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">Batch Validation Results</div>', unsafe_allow_html=True)
    
    # Summary metrics
    total_records = len(results_df)
    success_rate = success_count / total_records if total_records > 0 else 0
    
    # Calculate address type statistics
    business_count = len(results_df[results_df['Address Type'] == 'Business'])
    residential_count = len(results_df[results_df['Address Type'] == 'Residential'])
    unknown_count = len(results_df[results_df['Address Type'] == 'Unknown']) + len(results_df[results_df['Address Type'] == 'Error'])
    
    # Top row metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-value">{total_records}</div>
            <div class="metric-label">Total Records</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-value status-valid">{success_count}</div>
            <div class="metric-label">Valid Records</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col3:
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-value status-invalid">{error_count}</div>
            <div class="metric-label">Invalid Records</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col4:
        rate_class = "valid" if success_rate > 0.8 else "warning" if success_rate > 0.5 else "invalid"
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-value status-{rate_class}">{success_rate:.1%}</div>
            <div class="metric-label">Success Rate</div>
        </div>
        ''', unsafe_allow_html=True)
    
    # Address type breakdown
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    st.markdown('<div class="form-group-title">Address Type Breakdown</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        business_rate = business_count / total_records if total_records > 0 else 0
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-value status-valid">{business_count}</div>
            <div class="metric-label">Business ({business_rate:.1%})</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        residential_rate = residential_count / total_records if total_records > 0 else 0
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-value status-valid">{residential_count}</div>
            <div class="metric-label">Residential ({residential_rate:.1%})</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col3:
        unknown_rate = unknown_count / total_records if total_records > 0 else 0
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-value status-warning">{unknown_count}</div>
            <div class="metric-label">Unknown/Error ({unknown_rate:.1%})</div>
        </div>
        ''', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Show info about suggestions and corrections
    if include_suggestions:
        display_status_message("✅ Enhanced results with suggestions, USPS corrections, and detailed address analysis", "info")
        
        # Calculate correction statistics
        if 'Address Corrections' in results_df.columns:
            corrections_made = len(results_df[
                (results_df['Address Corrections'] != 'No corrections needed') & 
                (results_df['Address Corrections'] != 'Error') &
                (results_df['Address Corrections'] != 'Unable to standardize')
            ])
            
            if corrections_made > 0:
                display_status_message(f"📝 USPS made corrections to {corrections_made} addresses ({corrections_made/total_records:.1%})", "warning")
    else:
        display_status_message("ℹ️ Basic validation results only (suggestions and corrections disabled)", "info")
    
    # Results table with improved formatting
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    st.markdown('<div class="form-group-title">Detailed Results</div>', unsafe_allow_html=True)
    
    # Apply conditional formatting for better readability
    def highlight_status(val):
        if val == 'Valid' or val == 'Deliverable':
            return 'background-color: #d1fae5; color: #065f46'
        elif val in ['Invalid', 'Not Deliverable', 'Error']:
            return 'background-color: #fee2e2; color: #991b1b'
        elif val == 'Business':
            return 'background-color: #dbeafe; color: #1e40af'
        elif val == 'Residential':
            return 'background-color: #f3e8ff; color: #6b21a8'
        return ''
    
    # Apply styling to key columns
    styled_df = results_df.style.applymap(
        highlight_status, 
        subset=['Name Status', 'Address Status', 'Overall Status', 'Address Type']
    )
    
    st.dataframe(styled_df, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Download results
    csv_results = results_df.to_csv(index=False)
    filename_suffix = "_enhanced" if include_suggestions else "_basic"
    
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="📥 Download Results (CSV)",
            data=csv_results,
            file_name=f"validation_results{filename_suffix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        # Create Excel download with multiple sheets
        try:
            import io
            
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                # Main results
                results_df.to_excel(writer, sheet_name='Validation Results', index=False)
                
                # Summary statistics
                summary_data = {
                    'Metric': ['Total Records', 'Valid Records', 'Invalid Records', 'Success Rate', 
                              'Business Addresses', 'Residential Addresses', 'Unknown/Error Addresses'],
                    'Value': [total_records, success_count, error_count, f"{success_rate:.1%}",
                             business_count, residential_count, unknown_count]
                }
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                if include_suggestions and 'Address Corrections' in results_df.columns:
                    # Corrections summary
                    corrections_df = results_df[results_df['Address Corrections'] != 'No corrections needed'].copy()
                    corrections_df = corrections_df[['Row', 'Original Address', 'USPS Standardized Address', 'Address Corrections']]
                    corrections_df.to_excel(writer, sheet_name='Address Corrections', index=False)
            
            excel_data = excel_buffer.getvalue()
            
            st.download_button(
                label="📊 Download Results (Excel)",
                data=excel_data,
                file_name=f"validation_results{filename_suffix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        except ImportError:
            st.info("Excel download requires xlsxwriter. Install with: pip install xlsxwriter")
    
    st.markdown('</div>', unsafe_allow_html=True)


def render_monitoring_dashboard():
    """Render comprehensive monitoring dashboard"""
    
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">System Monitoring & Debug Logs</div>', unsafe_allow_html=True)
    
    # System Statistics
    stats = st.session_state.validation_stats
    uptime = datetime.now() - stats['session_start']
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-value">{stats['total_validations']}</div>
            <div class="metric-label">Total Validations</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-value status-valid">{stats['successful_validations']}</div>
            <div class="metric-label">Successful</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col3:
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-value status-invalid">{stats['failed_validations']}</div>
            <div class="metric-label">Failed</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col4:
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-value">{stats['api_calls']}</div>
            <div class="metric-label">API Calls</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col5:
        uptime_str = f"{uptime.total_seconds() / 3600:.1f}h"
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-value">{uptime_str}</div>
            <div class="metric-label">Session Uptime</div>
        </div>
        ''', unsafe_allow_html=True)
    
    # Performance Metrics
    if st.session_state.performance_metrics:
        st.markdown('<div class="form-section">', unsafe_allow_html=True)
        st.markdown('<div class="form-group-title">Performance Metrics (Last 10)</div>', unsafe_allow_html=True)
        
        recent_metrics = st.session_state.performance_metrics[-10:]
        metrics_df = pd.DataFrame(recent_metrics)
        
        if not metrics_df.empty:
            metrics_df['timestamp'] = metrics_df['timestamp'].dt.strftime('%H:%M:%S')
            st.dataframe(metrics_df, use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Debug Logs
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    st.markdown('<div class="form-group-title">Debug Logs</div>', unsafe_allow_html=True)
    
    # Log filtering
    col1, col2, col3 = st.columns(3)
    
    with col1:
        log_level = st.selectbox("Log Level", ["ALL", "ERROR", "WARNING", "INFO", "DEBUG"])
    
    with col2:
        log_category = st.selectbox("Category", ["ALL", "VALIDATION", "UI", "CONFIG", "USPS_API", "BULK_VALIDATION"])
    
    with col3:
        log_minutes = st.selectbox("Time Range", [5, 15, 30, 60], index=1)
    
    # Filter logs
    recent_logs = debug_monitor.get_recent_logs(log_minutes)
    
    if log_level != "ALL":
        recent_logs = [log for log in recent_logs if log['level'] == log_level]
    
    if log_category != "ALL":
        recent_logs = [log for log in recent_logs if log['category'] == log_category]
    
    # Display logs
    st.markdown('<div class="debug-panel">', unsafe_allow_html=True)
    
    if recent_logs:
        for log in recent_logs[-50:]:  # Show last 50 logs
            timestamp = log['timestamp'].strftime('%H:%M:%S.%f')[:-3]
            level_class = log['level'].lower()
            
            details_str = ""
            if log['details']:
                details_str = f" | {json.dumps(log['details'], default=str)}"
            
            st.markdown(f'''
            <div class="debug-log {level_class}">
                [{timestamp}] {log['level']} {log['category']}: {log['message']}{details_str}
            </div>
            ''', unsafe_allow_html=True)
    else:
        st.markdown('<div class="debug-log info">No logs found for the selected criteria.</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Error Summary
    error_summary = debug_monitor.get_error_summary()
    if error_summary:
        st.markdown('<div class="form-group-title">Error Summary (Last Hour)</div>', unsafe_allow_html=True)
        for category, count in error_summary.items():
            st.write(f"**{category}**: {count} errors")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Controls
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Clear Debug Logs"):
            st.session_state.debug_logs = []
            st.success("Debug logs cleared")
    
    with col2:
        if st.button("Clear Performance Metrics"):
            st.session_state.performance_metrics = []
            st.success("Performance metrics cleared")
    
    with col3:
        if st.button("Reset Statistics"):
            st.session_state.validation_stats = {
                'total_validations': 0,
                'successful_validations': 0,
                'failed_validations': 0,
                'api_calls': 0,
                'api_errors': 0,
                'session_start': datetime.now()
            }
            st.success("Statistics reset")
    
    st.markdown('</div>', unsafe_allow_html=True)


def main():
    """Main application with enterprise SaaS styling"""
    st.set_page_config(
        page_title="Enterprise Validator",
        page_icon="🔍",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    debug_monitor.log("INFO", "Application started", "SYSTEM")
    
    # Apply enterprise styling
    apply_enterprise_saas_css()
    
    # Check credentials first
    client_id, client_secret = load_usps_credentials()
    
    # Header with API status
    st.markdown('''
    <div class="enterprise-header">
        <div class="main-title">Enterprise Validator</div>
        <div class="subtitle">Professional-grade name and address validation platform</div>
    </div>
    ''', unsafe_allow_html=True)
    
    # API Connection Status
    render_api_status(client_id, client_secret)
    
    if not client_id or not client_secret:
        display_status_message("Please configure USPS API credentials to enable validation services.", "error")
        
        with st.expander("Configuration Guide"):
            st.markdown("""
            **For Streamlit Cloud:**
            1. Go to App settings → Secrets
            2. Add your credentials:
            ```
            USPS_CLIENT_ID = "your_client_id"
            USPS_CLIENT_SECRET = "your_client_secret"
            ```
            
            **For Local Development:**
            Create `.streamlit/secrets.toml` with the same format.
            """)
        return
    
    # Main application tabs
    tab1, tab2, tab3 = st.tabs(["Single Validation", "Batch Processing", "Monitoring"])
    
    with tab1:
        render_single_validation()
    
    with tab2:
        render_bulk_validation()
    
    with tab3:
        render_monitoring_dashboard()


if __name__ == "__main__":
    main()