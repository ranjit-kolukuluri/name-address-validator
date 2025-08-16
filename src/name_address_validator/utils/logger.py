import streamlit as st
from datetime import datetime
from typing import List

class DebugLogger:
    def __init__(self):
        self.logs: List[str] = []
        self.enabled: bool = False
    
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