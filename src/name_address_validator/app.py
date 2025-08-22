# src/name_address_validator/app.py - Fixed Path Handling
"""
Enterprise SaaS Name and Address Validator - Enhanced with Multi-File Address Standardization
Fixed version with robust path handling
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

# Enhanced Python path setup - more robust
def setup_python_path():
    """Enhanced path setup that works in various deployment scenarios"""
    
    current_file = Path(__file__).resolve()
    
    # Method 1: Try to find the src directory relative to current file
    # If app.py is in src/name_address_validator/app.py, then src is 2 levels up
    potential_src = current_file.parent.parent
    if potential_src.name == "src" and (potential_src / "name_address_validator").exists():
        if str(potential_src) not in sys.path:
            sys.path.insert(0, str(potential_src))
        print(f"✅ Added to path: {potential_src}")
        return potential_src
    
    # Method 2: Try parent of src directory (project root)
    project_root = current_file.parent.parent.parent
    src_dir = project_root / "src"
    if src_dir.exists() and (src_dir / "name_address_validator").exists():
        if str(src_dir) not in sys.path:
            sys.path.insert(0, str(src_dir))
        print(f"✅ Added to path: {src_dir}")
        return src_dir
    
    # Method 3: Current working directory
    cwd = Path.cwd()
    cwd_src = cwd / "src"
    if cwd_src.exists() and (cwd_src / "name_address_validator").exists():
        if str(cwd_src) not in sys.path:
            sys.path.insert(0, str(cwd_src))
        print(f"✅ Added to path: {cwd_src}")
        return cwd_src
    
    # Method 4: Try if we're already in the right place
    if (current_file.parent.parent / "services").exists():
        parent_dir = current_file.parent.parent
        if str(parent_dir) not in sys.path:
            sys.path.insert(0, str(parent_dir))
        print(f"✅ Added to path: {parent_dir}")
        return parent_dir
    
    # Method 5: Streamlit Cloud specific paths
    streamlit_paths = [
        Path("/mount/src") / "name-address-validator" / "src",
        Path("/mount/src") / os.environ.get("STREAMLIT_REPO_NAME", "name-address-validator") / "src",
        Path("/app") / "src"
    ]
    
    for path in streamlit_paths:
        if path.exists() and (path / "name_address_validator").exists():
            if str(path) not in sys.path:
                sys.path.insert(0, str(path))
            print(f"✅ Added to path: {path}")
            return path
    
    # Debugging information
    print("🔍 Path debugging information:")
    print(f"Current file: {current_file}")
    print(f"Current working directory: {Path.cwd()}")
    print(f"Python path: {sys.path}")
    print(f"Parent directories: {[str(p) for p in current_file.parents]}")
    
    # List what's actually in the current directory structure
    for parent in current_file.parents[:3]:
        if parent.exists():
            print(f"Contents of {parent}: {[p.name for p in parent.iterdir() if p.is_dir()]}")
    
    return None

# Setup path before importing
print("🔧 Setting up Python path...")
setup_result = setup_python_path()

# Try imports with better error handling
try:
    print("📦 Attempting to import validation service...")
    from name_address_validator.services.validation_service import ValidationService
    print("✅ ValidationService imported successfully")
    
    print("📦 Attempting to import config...")
    from name_address_validator.utils.config import load_usps_credentials
    print("✅ Config imported successfully")
    
    print("📦 Attempting to import logger...")
    from name_address_validator.utils.logger import DebugLogger
    print("✅ Logger imported successfully")
    
    imports_successful = True
    print("🎉 All imports successful!")
    
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print(f"Current Python path: {sys.path}")
    
    # Try to give more specific guidance
    st.error(f"Import Error: {e}")
    st.error("**Troubleshooting Steps:**")
    st.write("1. Make sure you're running from the project root directory")
    st.write("2. Try: `cd` to your project directory first")
    st.write("3. Then run: `streamlit run src/name_address_validator/app.py`")
    st.write("4. Or try: `python -m streamlit run src/name_address_validator/app.py`")
    st.write("5. Check that all files are in the correct directory structure")
    
    # Show current directory structure for debugging
    st.write("**Current directory structure:**")
    current_dir = Path.cwd()
    st.code(f"Current working directory: {current_dir}")
    
    if (current_dir / "src").exists():
        st.write("✅ src/ directory found")
        if (current_dir / "src" / "name_address_validator").exists():
            st.write("✅ src/name_address_validator/ directory found")
            nav_contents = list((current_dir / "src" / "name_address_validator").iterdir())
            st.write(f"Contents: {[p.name for p in nav_contents]}")
        else:
            st.write("❌ src/name_address_validator/ directory NOT found")
    else:
        st.write("❌ src/ directory NOT found")
    
    imports_successful = False

if not imports_successful:
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
                'files_processed': 0,
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
    """Apply modern enterprise SaaS styling with enhanced multi-file support"""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    .main {
        font-family: 'Inter', sans-serif;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
    }
    
    /* Compact Header Styles */
    .enterprise-header {
        background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
        padding: 1.5rem 2rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        position: relative;
        display: flex;
        flex-direction: column;
        align-items: center;
        max-width: fit-content;
        margin-left: auto;
        margin-right: auto;
    }
    
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #ffffff;
        text-align: center;
        margin-bottom: 0.3rem;
        letter-spacing: -0.025em;
        white-space: nowrap;
        line-height: 1.2;
    }
    
    .subtitle {
        font-size: 1rem;
        color: #cbd5e1;
        text-align: center;
        font-weight: 400;
        margin-bottom: 0.5rem;
        white-space: nowrap;
        opacity: 0.9;
    }
    
    .api-status {
        background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
        color: #ffffff;
        padding: 0.5rem 1.2rem;
        border-radius: 25px;
        font-weight: 600;
        font-size: 0.8rem;
        text-align: center;
        margin-top: 0.5rem;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
        border: 2px solid #60a5fa;
        animation: pulse-glow 2s infinite;
        white-space: nowrap;
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
    
    /* Card and other styles */
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
        font-size: 1.4rem;
        font-weight: 600;
        color: #1e40af;
        margin-bottom: 1.2rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e2e8f0;
        position: relative;
        display: inline-block;
        width: auto;
        min-width: fit-content;
    }
    
    .section-header::after {
        content: '';
        position: absolute;
        bottom: -2px;
        left: 0;
        width: 100%;
        height: 2px;
        background: linear-gradient(90deg, #3b82f6, #8b5cf6);
        border-radius: 1px;
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
        gap: 0;
        background: rgba(255, 255, 255, 0.9);
        border-radius: 16px;
        padding: 6px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        margin-bottom: 1.5rem;
        justify-content: center;
        width: fit-content;
        margin-left: auto;
        margin-right: auto;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        background: transparent;
        border-radius: 12px;
        color: #64748b;
        font-weight: 500;
        border: none;
        transition: all 0.3s ease;
        margin: 0 2px;
        padding: 0 1.5rem;
        position: relative;
        overflow: hidden;
        min-width: 140px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.95rem;
        cursor: pointer;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(59, 130, 246, 0.1);
        color: #3b82f6;
        transform: translateY(-1px);
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
        color: white;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
        transform: translateY(-2px);
        font-weight: 600;
    }
    
    /* Tab icons */
    .stTabs [data-baseweb="tab"]:first-child::before {
        content: "👤";
        margin-right: 0.5rem;
        font-size: 1rem;
    }
    
    .stTabs [data-baseweb="tab"]:nth-child(2)::before {
        content: "📊";
        margin-right: 0.5rem;
        font-size: 1rem;
    }
    
    .stTabs [data-baseweb="tab"]:nth-child(3)::before {
        content: "🔧";
        margin-right: 0.5rem;
        font-size: 1rem;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
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
    """Render single validation form"""
    
    st.markdown('''
    <div class="glass-card">
        <div class="section-header">Single Record Validation</div>
    </div>
    ''', unsafe_allow_html=True)
    
    # Personal Information Section
    st.markdown("**Personal Information**")
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
    
    # Address Information Section
    st.markdown("**Address Information**")
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
    
    # Validation Logic
    all_fields_have_content = all([
        first_name and first_name.strip(),
        last_name and last_name.strip(),
        street_address and street_address.strip(),
        city and city.strip(),
        state and state.strip(),
        zip_code and zip_code.strip()
    ])
    
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
            display_status_message(f"Please complete the following required fields: {', '.join(missing_fields)}", "info")
    
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


def process_single_validation(first_name: str, last_name: str, street_address: str, city: str, state: str, zip_code: str):
    """Process single record validation"""
    
    debug_monitor.log("INFO", "Starting single validation process", "VALIDATION")
    start_time = time.time()
    
    # Check if we have a validation service available
    try:
        validation_service = ValidationService(debug_callback=lambda msg, cat="SERVICE": debug_monitor.log("INFO", msg, cat))
        
        if not validation_service.is_address_validation_available():
            display_status_message("USPS API credentials not configured. Please contact administrator.", "error")
            debug_monitor.log("ERROR", "USPS credentials not available for validation", "CONFIG")
            debug_monitor.update_stats('failed_validations')
            return
        
        # Progress tracking
        with st.container():
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Validate name
            status_text.text("Validating name...")
            progress_bar.progress(25)
            time.sleep(0.3)
            
            # Validate address
            status_text.text("Validating address with USPS...")
            progress_bar.progress(75)
            time.sleep(0.3)
            
            result = validation_service.validate_single_record(
                first_name, last_name, street_address, city, state, zip_code
            )
            
            progress_bar.progress(100)
            status_text.text("Validation complete")
            time.sleep(0.5)
            
            # Clear progress
            progress_bar.empty()
            status_text.empty()
            
            # Log performance
            total_duration = int((time.time() - start_time) * 1000)
            debug_monitor.log_performance("single_validation_complete", total_duration, result['overall_valid'])
            debug_monitor.update_stats('successful_validations' if result['overall_valid'] else 'failed_validations')
            
            # Display results
            display_single_validation_results(result)
            
    except Exception as e:
        debug_monitor.log("ERROR", f"Single validation process failed: {str(e)}", "VALIDATION")
        debug_monitor.update_stats('failed_validations')
        display_status_message(f"Validation error: {str(e)}", "error")


def display_single_validation_results(result: Dict):
    """Display single validation results"""
    
    debug_monitor.log("INFO", "Displaying single validation results", "UI")
    
    st.markdown("### 🎉 Validation Results")
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    
    name_result = result.get('name_result', {})
    address_result = result.get('address_result', {})
    
    with col1:
        name_valid = name_result.get('valid', False)
        name_status = "Valid" if name_valid else "Invalid"
        st.metric("Name Status", name_status)
    
    with col2:
        address_deliverable = address_result.get('deliverable', False)
        address_status = "Deliverable" if address_deliverable else "Not Deliverable"
        st.metric("Address Status", address_status)
    
    with col3:
        overall_confidence = result.get('overall_confidence', 0)
        st.metric("Overall Confidence", f"{overall_confidence:.1%}")
    
    # Detailed results
    col_name, col_address = st.columns(2)
    
    with col_name:
        st.markdown("**Name Validation Details**")
        
        if name_result.get('valid'):
            display_status_message("Name validation passed", "success")
            normalized = name_result.get('normalized', {})
            st.write(f"**Normalized:** {normalized.get('first_name', '')} {normalized.get('last_name', '')}")
            st.write(f"**Confidence:** {name_result.get('confidence', 0):.1%}")
        else:
            display_status_message("Name validation failed", "error")
            for error in name_result.get('errors', []):
                st.write(f"• {error}")
        
        if name_result.get('suggestions'):
            st.write("**Suggestions:**")
            for field, suggestions in name_result['suggestions'].items():
                if suggestions:
                    st.write(f"**{field.replace('_', ' ').title()}:**")
                    for suggestion in suggestions[:3]:
                        st.write(f"• {suggestion['suggestion']} ({suggestion['confidence']:.1%})")
    
    with col_address:
        st.markdown("**Address Validation Details**")
        
        if address_result.get('success', False):
            if address_result.get('deliverable', False):
                display_status_message("Address is valid and deliverable", "success")
                
                std = address_result.get('standardized', {})
                if std:
                    st.write("**Standardized Address:**")
                    st.write(f"{std.get('street_address', '')}")
                    st.write(f"{std.get('city', '')}, {std.get('state', '')} {std.get('zip_code', '')}")
                
                metadata = address_result.get('metadata', {})
                if metadata.get('business'):
                    display_status_message("Business address", "info")
                if metadata.get('vacant'):
                    display_status_message("Vacant property", "warning")
            else:
                display_status_message("Address found but may not be deliverable", "warning")
        else:
            display_status_message(f"Address validation failed: {address_result.get('error', 'Unknown error')}", "error")


def render_bulk_validation():
    """Enhanced bulk validation interface with multi-file support and standardization"""
    debug_monitor.log("INFO", "Rendering enhanced bulk validation interface", "UI")
    
    st.markdown('''
    <div class="glass-card">
        <div class="section-header">Enhanced Batch Processing with Address Standardization</div>
    </div>
    ''', unsafe_allow_html=True)
    
    st.write("Upload multiple CSV files with various address formats. Our system will automatically standardize them before validation.")
    
    # Template section
    with st.expander("📄 Download CSV Template & Format Guide"):
        st.write("**Standard Format Template:**")
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
            label="📥 Download Standard Template",
            data=csv_template,
            file_name="validation_template.csv",
            mime="text/csv",
            use_container_width=True
        )
        
        st.write("**Supported Column Variations:**")
        st.write("Our system automatically detects and maps these column variations:")
        
        variations_info = """
        - **Names**: first_name, first, fname, given_name, last_name, last, lname, surname
        - **Address**: street_address, street, address, addr, address1, full_address
        - **City**: city, town, municipality, locality
        - **State**: state, st, state_code, province (2-letter codes)
        - **ZIP**: zip_code, zip, zipcode, postal_code, postcode
        - **Combined Address**: Full addresses like "123 Main St, City, ST 12345"
        """
        st.markdown(variations_info)
    
    # Multi-file upload
    st.markdown("### 📁 Upload CSV Files")
    
    uploaded_files = st.file_uploader(
        "Choose CSV files",
        type=['csv'],
        accept_multiple_files=True,
        help="Upload multiple CSV files with various address formats",
    )
    
    if uploaded_files:
        debug_monitor.log("INFO", f"Multiple CSV files uploaded: {len(uploaded_files)} files", "BULK_VALIDATION")
        debug_monitor.update_stats('files_processed', len(uploaded_files))
        
        # Process uploaded files
        try:
            file_data_list = []
            total_rows = 0
            
            # Display file list
            st.markdown("### 📋 Uploaded Files")
            
            for i, uploaded_file in enumerate(uploaded_files):
                try:
                    df = pd.read_csv(uploaded_file)
                    file_data_list.append((df, uploaded_file.name))
                    total_rows += len(df)
                    
                    # Display file info
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.write(f"📄 **{uploaded_file.name}**")
                    with col2:
                        st.write(f"{len(df)} rows")
                    with col3:
                        st.write(f"{len(df.columns)} columns")
                    
                except Exception as e:
                    st.error(f"❌ Error reading {uploaded_file.name}: {str(e)}")
            
            if file_data_list:
                display_status_message(f"Successfully loaded {len(file_data_list)} files with {total_rows} total records.", "success")
                
                # Preview first file
                st.markdown("### 👀 Data Preview (First File)")
                preview_df = file_data_list[0][0]
                st.dataframe(preview_df.head(5), use_container_width=True)
                
                # Processing options
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    max_records = st.number_input(
                        "Maximum records to process",
                        min_value=1,
                        max_value=min(1000, total_rows),
                        value=min(100, total_rows),
                        help="Limit processing to prevent timeout"
                    )
                
                with col2:
                    include_suggestions = st.checkbox("Include suggestions", value=True)
                
                with col3:
                    show_standardization = st.checkbox("Show standardization preview", value=True)
                
                # Action buttons
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("🔄 Preview Standardization", type="secondary", use_container_width=True):
                        preview_standardization(file_data_list[:2])  # Preview first 2 files
                
                with col2:
                    if st.button("🚀 Start Complete Processing", type="primary", use_container_width=True):
                        process_multiple_csv_files(file_data_list, include_suggestions, max_records, show_standardization)
            else:
                display_status_message("No valid CSV files could be loaded.", "error")
                
        except Exception as e:
            display_status_message(f"Error processing uploaded files: {str(e)}", "error")
            debug_monitor.log("ERROR", "Failed to process uploaded CSV files", "BULK_VALIDATION", error=str(e))


def preview_standardization(file_data_list: List[Tuple[pd.DataFrame, str]]):
    """Preview standardization results for uploaded files"""
    
    debug_monitor.log("INFO", "Previewing standardization for uploaded files", "STANDARDIZATION")
    
    try:
        validation_service = ValidationService(debug_callback=lambda msg, cat="SERVICE": debug_monitor.log("INFO", msg, cat))
        
        with st.spinner("🔄 Analyzing address formats and generating standardization preview..."):
            standardization_result = validation_service.standardize_csv_files(file_data_list)
        
        if standardization_result['success']:
            standardized_df = standardization_result['standardized_data']
            standardization_info = standardization_result['standardization_info']
            summary = standardization_result['summary']
            
            st.markdown("### 🔄 Standardization Preview")
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Files Processed", summary['successful_files'])
            
            with col2:
                st.metric("Total Rows", summary['total_rows_processed'])
            
            with col3:
                st.metric("Combined Addresses", summary['files_with_combined_addresses'])
            
            with col4:
                error_count = len(summary['common_errors'])
                st.metric("Issues Found", error_count)
            
            # Column mapping details
            st.markdown("### 📋 Column Mapping Analysis")
            
            for info in standardization_info:
                if 'error' not in info:
                    st.markdown(f"**File: {info['file_name']}**")
                    
                    mapping_text = []
                    for std_col, source_col in info['detected_mapping'].items():
                        if source_col != 'combined_address':
                            mapping_text.append(f"• {source_col} → {std_col}")
                    
                    if info.get('combined_address_parsed', False):
                        combined_col = info['detected_mapping'].get('combined_address', 'unknown')
                        mapping_text.append(f"• {combined_col} (parsed) → street, city, state, zip")
                    
                    st.write("\n".join(mapping_text))
                    
                    if info.get('standardization_errors'):
                        for error in info['standardization_errors']:
                            display_status_message(f"⚠️ {error}", "warning")
            
            # Preview standardized data
            st.markdown("### 📊 Standardized Data Preview")
            st.dataframe(standardized_df.head(10), use_container_width=True)
            
            if summary['common_errors']:
                st.markdown("### ⚠️ Issues Found")
                for error, count in summary['common_errors'].items():
                    st.write(f"• {error} ({count} occurrences)")
            
            display_status_message("✅ Standardization preview complete. Data is ready for validation.", "success")
            
        else:
            display_status_message(f"Standardization preview failed: {standardization_result.get('error', 'Unknown error')}", "error")
            
    except Exception as e:
        display_status_message(f"Error generating standardization preview: {str(e)}", "error")
        debug_monitor.log("ERROR", "Standardization preview failed", "STANDARDIZATION", error=str(e))


def process_multiple_csv_files(file_data_list: List[Tuple[pd.DataFrame, str]], include_suggestions: bool, 
                             max_records: int, show_standardization: bool):
    """Process multiple CSV files with standardization and validation"""
    
    debug_monitor.log("INFO", f"Starting complete processing pipeline for {len(file_data_list)} files", "PIPELINE")
    
    try:
        validation_service = ValidationService(debug_callback=lambda msg, cat="SERVICE": debug_monitor.log("INFO", msg, cat))
        
        if not validation_service.is_address_validation_available():
            display_status_message("USPS API credentials not configured. Please contact administrator.", "error")
            return
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Step 1: Standardization
        status_text.text("🔄 Step 1/2: Standardizing address formats across all files...")
        progress_bar.progress(25)
        
        pipeline_result = validation_service.process_multiple_csv_files(
            file_data_list=file_data_list,
            include_suggestions=include_suggestions,
            max_records=max_records
        )
        
        progress_bar.progress(75)
        status_text.text("🔍 Step 2/2: Validating standardized data with USPS...")
        
        if pipeline_result['success']:
            progress_bar.progress(100)
            status_text.text("✅ Processing complete!")
            time.sleep(1)
            
            # Clear progress
            progress_bar.empty()
            status_text.empty()
            
            # Display results
            display_pipeline_results(pipeline_result, show_standardization)
            
        else:
            progress_bar.empty()
            status_text.empty()
            display_status_message(f"Processing failed at {pipeline_result.get('stage', 'unknown')} stage: {pipeline_result.get('error', 'Unknown error')}", "error")
            
    except Exception as e:
        debug_monitor.log("ERROR", f"Pipeline processing failed: {str(e)}", "PIPELINE")
        display_status_message(f"Processing error: {str(e)}", "error")


def display_pipeline_results(pipeline_result: Dict, show_standardization: bool):
    """Display complete pipeline results with standardization and validation"""
    
    st.markdown("### 🎉 Processing Results")
    
    summary = pipeline_result['summary']
    validation_result = pipeline_result['validation']
    standardization_result = pipeline_result['standardization']
    
    # Overall summary metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Files Processed", summary['files_processed'])
    
    with col2:
        st.metric("Source Rows", summary['total_source_rows'])
    
    with col3:
        st.metric("Standardized", summary['standardized_rows'])
    
    with col4:
        st.metric("Valid Records", summary['successful_validations'])
    
    with col5:
        success_rate = summary['successful_validations'] / summary['validated_rows'] if summary['validated_rows'] > 0 else 0
        st.metric("Success Rate", f"{success_rate:.1%}")
    
    # Performance metrics
    standardization_time = standardization_result.get('processing_time_ms', 0)
    validation_time = validation_result.get('processing_time_ms', 0)
    total_time = pipeline_result.get('pipeline_duration_ms', 0)
    
    st.markdown("### ⚡ Performance Metrics")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Standardization Time", f"{standardization_time / 1000:.1f}s")
    
    with col2:
        st.metric("Validation Time", f"{validation_time / 1000:.1f}s")
    
    with col3:
        st.metric("Total Time", f"{total_time / 1000:.1f}s")
    
    # Validation results
    display_enhanced_bulk_results(validation_result, pipeline_result)


def display_enhanced_bulk_results(validation_result: Dict, pipeline_result: Dict):
    """Display enhanced bulk validation results with pipeline context"""
    
    results_df = pd.DataFrame(validation_result['records'])
    
    if results_df.empty:
        display_status_message("No validation results to display.", "warning")
        return
    
    # Address type breakdown
    business_count = len(results_df[results_df['address_type'] == 'Business']) if 'address_type' in results_df.columns else 0
    residential_count = len(results_df[results_df['address_type'] == 'Residential']) if 'address_type' in results_df.columns else 0
    unknown_count = len(results_df) - business_count - residential_count
    total_records = len(results_df)
    
    st.markdown("### 🏠 Address Classification")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        business_rate = business_count / total_records if total_records > 0 else 0
        st.metric("Business", f"{business_count} ({business_rate:.1%})")
    
    with col2:
        residential_rate = residential_count / total_records if total_records > 0 else 0
        st.metric("Residential", f"{residential_count} ({residential_rate:.1%})")
    
    with col3:
        unknown_rate = unknown_count / total_records if total_records > 0 else 0
        st.metric("Unknown/Error", f"{unknown_count} ({unknown_rate:.1%})")
    
    # Enhanced info about the process
    has_suggestions = 'first_name_suggestions' in results_df.columns
    if has_suggestions:
        display_status_message("✅ Enhanced results with suggestions, USPS corrections, and detailed address analysis", "info")
        
        # Calculate correction statistics
        if 'address_corrections' in results_df.columns:
            corrections_made = len(results_df[
                (results_df['address_corrections'] != 'No corrections needed') & 
                (results_df['address_corrections'] != 'Error') &
                (results_df['address_corrections'] != 'Unable to standardize')
            ])
            
            if corrections_made > 0:
                display_status_message(f"📝 USPS made corrections to {corrections_made} addresses ({corrections_made/total_records:.1%})", "warning")
    
    # Source file breakdown
    if 'source_file' in results_df.columns:
        st.markdown("### 📁 Results by Source File")
        file_summary = results_df.groupby('source_file').agg({
            'overall_status': lambda x: (x == 'Valid').sum(),
            'row': 'count'
        }).rename(columns={'overall_status': 'valid_count', 'row': 'total_count'})
        
        file_summary['success_rate'] = file_summary['valid_count'] / file_summary['total_count']
        
        for file_name, stats in file_summary.iterrows():
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.write(f"**{file_name}**")
            with col2:
                st.write(f"{stats['valid_count']}/{stats['total_count']} valid")
            with col3:
                rate_text = f"{stats['success_rate']:.1%}"
                if stats['success_rate'] > 0.8:
                    st.write(f"✅ {rate_text}")
                elif stats['success_rate'] > 0.5:
                    st.write(f"⚠️ {rate_text}")
                else:
                    st.write(f"❌ {rate_text}")
    
    # Results table
    st.markdown("### 📊 Detailed Results")
    
    # Display the results table
    st.dataframe(results_df, use_container_width=True)
    
    # Download options
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    file_suffix = "_enhanced" if has_suggestions else "_basic"
    
    col1, col2 = st.columns(2)
    
    with col1:
        csv_results = results_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Results (CSV)",
            data=csv_results,
            file_name=f"multi_file_validation_results{file_suffix}_{timestamp}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        # Create comprehensive Excel download
        try:
            import io
            
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                # Main results
                results_df.to_excel(writer, sheet_name='Validation Results', index=False)
                
                # Pipeline summary
                pipeline_summary_data = {
                    'Metric': [
                        'Files Processed', 'Total Source Rows', 'Standardized Rows',
                        'Validated Rows', 'Successful Validations', 'Failed Validations',
                        'Success Rate', 'Business Addresses', 'Residential Addresses',
                        'Pipeline Duration (ms)', 'Standardization Time (ms)', 'Validation Time (ms)'
                    ],
                    'Value': [
                        pipeline_result['summary']['files_processed'],
                        pipeline_result['summary']['total_source_rows'],
                        pipeline_result['summary']['standardized_rows'],
                        pipeline_result['summary']['validated_rows'],
                        pipeline_result['summary']['successful_validations'],
                        pipeline_result['summary']['failed_validations'],
                        f"{pipeline_result['summary']['successful_validations']/pipeline_result['summary']['validated_rows']:.1%}" if pipeline_result['summary']['validated_rows'] > 0 else "0%",
                        business_count,
                        residential_count,
                        pipeline_result.get('pipeline_duration_ms', 0),
                        pipeline_result['standardization'].get('processing_time_ms', 0),
                        pipeline_result['validation'].get('processing_time_ms', 0)
                    ]
                }
                summary_df = pd.DataFrame(pipeline_summary_data)
                summary_df.to_excel(writer, sheet_name='Pipeline Summary', index=False)
            
            excel_data = excel_buffer.getvalue()
            
            st.download_button(
                label="📊 Download Complete Report (Excel)",
                data=excel_data,
                file_name=f"multi_file_complete_report{file_suffix}_{timestamp}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        except ImportError:
            st.info("Excel download requires xlsxwriter. Install with: pip install xlsxwriter")
    """Render monitoring dashboard"""
    
    st.markdown('''
    <div class="glass-card">
        <div class="section-header">System Monitoring</div>
    </div>
    ''', unsafe_allow_html=True)
    
    # Display some basic stats
    stats = st.session_state.validation_stats
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Validations", stats['total_validations'])
    with col2:
        st.metric("Successful", stats['successful_validations'])
    with col3:
        st.metric("Failed", stats['failed_validations'])
def render_complete_monitoring_dashboard():
    """Complete monitoring dashboard with advanced features"""
    
    st.markdown('''
    <div class="glass-card">
        <div class="section-header">Advanced System Monitoring & Debug Logs</div>
    </div>
    ''', unsafe_allow_html=True)
    
    # System Statistics
    stats = st.session_state.validation_stats
    uptime = datetime.now() - stats['session_start']
    
    st.markdown("### 📊 System Statistics")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric("Total Validations", stats['total_validations'])
    
    with col2:
        st.metric("Successful", stats['successful_validations'])
    
    with col3:
        st.metric("Failed", stats['failed_validations'])
    
    with col4:
        st.metric("API Calls", stats['api_calls'])
    
    with col5:
        st.metric("Files Processed", stats['files_processed'])
    
    with col6:
        uptime_str = f"{uptime.total_seconds() / 3600:.1f}h"
        st.metric("Session Uptime", uptime_str)
    
    # Performance Metrics
    if st.session_state.performance_metrics:
        st.markdown("### ⚡ Performance Metrics (Last 10)")
        
        recent_metrics = st.session_state.performance_metrics[-10:]
        metrics_df = pd.DataFrame(recent_metrics)
        
        if not metrics_df.empty:
            metrics_df['timestamp'] = metrics_df['timestamp'].dt.strftime('%H:%M:%S')
            st.dataframe(metrics_df, use_container_width=True)
    
    # Debug Logs
    st.markdown("### 🔍 Debug Logs")
    
    # Log filtering
    col1, col2, col3 = st.columns(3)
    
    with col1:
        log_level = st.selectbox("Log Level", ["ALL", "ERROR", "WARNING", "INFO", "DEBUG"])
    
    with col2:
        log_category = st.selectbox("Category", ["ALL", "VALIDATION", "UI", "CONFIG", "USPS_API", "BULK_VALIDATION", "STANDARDIZATION", "PIPELINE"])
    
    with col3:
        log_minutes = st.selectbox("Time Range", [5, 15, 30, 60], index=1)
    
    # Filter logs
    recent_logs = debug_monitor.get_recent_logs(log_minutes)
    
    if log_level != "ALL":
        recent_logs = [log for log in recent_logs if log['level'] == log_level]
    
    if log_category != "ALL":
        recent_logs = [log for log in recent_logs if log['category'] == log_category]
    
    # Display logs
    if recent_logs:
        for log in recent_logs[-20:]:  # Show last 20 logs
            timestamp = log['timestamp'].strftime('%H:%M:%S.%f')[:-3]
            level_icon = {"ERROR": "❌", "WARNING": "⚠️", "INFO": "ℹ️", "DEBUG": "🔧"}.get(log['level'], "📝")
            
            details_str = ""
            if log['details']:
                details_str = f" | {json.dumps(log['details'], default=str)}"
            
            st.text(f"{level_icon} [{timestamp}] {log['level']} {log['category']}: {log['message']}{details_str}")
    else:
        st.info("No logs found for the selected criteria.")
    
    # Error Summary
    error_summary = debug_monitor.get_error_summary()
    if error_summary:
        st.markdown("### ⚠️ Error Summary (Last Hour)")
        for category, count in error_summary.items():
            st.write(f"**{category}**: {count} errors")
    
    # Controls
    st.markdown("### 🛠️ Controls")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🗑️ Clear Debug Logs"):
            st.session_state.debug_logs = []
            st.success("Debug logs cleared")
            st.rerun()
    
    with col2:
        if st.button("📊 Clear Performance Metrics"):
            st.session_state.performance_metrics = []
            st.success("Performance metrics cleared")
            st.rerun()
    
    with col3:
        if st.button("🔄 Reset Statistics"):
            st.session_state.validation_stats = {
                'total_validations': 0,
                'successful_validations': 0,
                'failed_validations': 0,
                'api_calls': 0,
                'api_errors': 0,
                'files_processed': 0,
                'session_start': datetime.now()
            }
            st.success("Statistics reset")
            st.rerun()
    
    # System Information
    st.markdown("### 🖥️ System Information")
    
    try:
        validation_service = ValidationService()
        status = validation_service.get_service_status()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Service Capabilities:**")
            st.write(f"• Name validation: {'✅' if status['name_validation_available'] else '❌'}")
            st.write(f"• Address validation: {'✅' if status['address_validation_available'] else '❌'}")
            st.write(f"• Address standardization: {'✅' if status.get('address_standardization_available', False) else '❌'}")
            st.write(f"• Multi-file processing: {'✅' if status.get('multi_file_processing_available', False) else '❌'}")
        
        with col2:
            st.write("**Configuration:**")
            st.write(f"• USPS configured: {'✅' if status['usps_configured'] else '❌'}")
            st.write(f"• Performance tracking: {'✅' if status['performance_tracking'] else '❌'}")
            st.write(f"• Debug logging: {'✅' if status['debug_logging'] else '❌'}")
            st.write(f"• Service uptime: {status['service_uptime']}")
        
    except Exception as e:
        st.error(f"Could not get service status: {e}")


# To use the complete monitoring dashboard, replace the monitoring tab code in main() with:
# render_complete_monitoring_dashboard()

def main():
    """Main application"""
    st.set_page_config(
        page_title="Name and Address Validator - Enhanced",
        page_icon="🔍",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    debug_monitor.log("INFO", "Enhanced application started", "SYSTEM")
    
    # Apply enterprise styling
    apply_enterprise_saas_css()
    
    # Check credentials first
    try:
        client_id, client_secret = load_usps_credentials()
    except Exception as e:
        st.error(f"Error loading credentials: {e}")
        client_id, client_secret = None, None
    
    # Header with API status
    st.markdown('''
    <div class="enterprise-header">
        <div class="main-title">Enhanced Name and Address Validator</div>
        <div class="subtitle">Multi-File Processing • Address Standardization • Powered by ML and USPS</div>
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
    tab1, tab2, tab3 = st.tabs(["Single Validation", "Multi-File Batch Processing", "Monitoring"])
    
    with tab1:
        render_single_validation()
    
    with tab2:
        render_bulk_validation()
    
    with tab3:
        render_complete_monitoring_dashboard()
        

if __name__ == "__main__":
    main()