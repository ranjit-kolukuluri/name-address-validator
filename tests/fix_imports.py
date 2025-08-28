# quick_test_app.py
import streamlit as st
import sys
sys.path.insert(0, 'src')

st.set_page_config(page_title="Test App", layout="wide")

# Simple CSS fix
st.markdown("""
<style>
.stTabs [data-baseweb="tab-list"] {
    background: rgba(59, 130, 246, 0.1);
    border-radius: 16px;
    padding: 6px;
    margin-bottom: 1.5rem;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 12px;
    padding: 0.5rem 1rem;
    margin: 0 2px;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
    color: white;
}
</style>
""", unsafe_allow_html=True)

st.title("🔍 Test App - Tab Formatting")

# Test tabs
tab1, tab2, tab3 = st.tabs(["👤 Single Validation", "📊 Multi-File", "🔧 Monitoring"])

with tab1:
    st.write("Tab 1 content - formatting should look good!")

with tab2:
    st.write("Tab 2 content - tabs should be styled!")

with tab3:
    st.write("Tab 3 content - check the tab styling!")