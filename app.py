import streamlit as st

st.set_page_config(page_title="Personal Agent Platform", layout="wide")

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent))

st.title("🤖 Personal Agent Platform")

st.markdown("""
Welcome to your multi-agent control center.

Use the sidebar to navigate between domains:
- 👔 Management Support
""")