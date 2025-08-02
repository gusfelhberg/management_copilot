
from dotenv import load_dotenv
import os
# Load environment variables from .env file
load_dotenv()
import streamlit as st


# dynamically configure the root folder
import os
ROOT_FOLDER = os.path.dirname(os.path.abspath(__file__))

NOTION_API_KEY = st.secrets['NOTION_API_KEY']
MEETINGS_DATABASE_ID = st.secrets['MEETINGS_DATABASE_ID']
PROJECT_UPDATES_DATABASE_ID = st.secrets['PROJECT_UPDATES_DATABASE_ID']
PEOPLE_UPDATES_DATABASE_ID = st.secrets['PEOPLE_UPDATES_DATABASE_ID']
# INVESTMENT_HOLDINGS_DATABASE_ID = st.secrets['INVESTMENT_HOLDINGS_DATABASE_ID']
# CURRENCY_CONVERSIONS_PAGE_ID = st.secrets['CURRENCY_CONVERSIONS_PAGE_ID']
PEOPLE_DATABASE_ID = st.secrets['PEOPLE_DATABASE_ID']
# OPENAI_API_KEY = st.secrets['OPENAI_API_KEY']
MCP_APP_HOST = st.secrets['MCP_APP_HOST']