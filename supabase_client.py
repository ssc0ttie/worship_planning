# db.py
import streamlit as st
from supabase import create_client, Client


# Initialize connection to Supabase
@st.cache_resource
def init_connection():
    try:
        supabase_url: str = st.secrets["supabase"]["url"]
        supabase_key: str = st.secrets["supabase"]["service_key"]
        return create_client(supabase_url, supabase_key)
    except Exception as e:
        st.error(f"Connection error: {e}")
        return None


supabase = init_connection()
