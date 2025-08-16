import os
import streamlit as st
from typing import Tuple, Optional

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