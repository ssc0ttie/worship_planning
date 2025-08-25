import streamlit as st
from supabase import create_client, Client
import os
import re
import json


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


# --- Database functions ---
def get_songs():
    try:
        response = supabase.table("song").select("*").execute()
        return response.data
    except Exception as e:
        st.error(f"Error fetching songs: {e}")
        return []


def get_song_by_id(song_id):
    try:
        response = supabase.table("song").select("*").eq("id", song_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        st.error(f"Error fetching song: {e}")
        return None


def add_song(title, artist, arrangement, default_key=""):
    try:
        song_data = {
            "title": title,
            "artist": artist,
            "arrangement": arrangement,
            "default_key": default_key,
        }
        response = supabase.table("song").insert(song_data).execute()
        st.success("Song added to database!")
        return response.data[0] if response.data else None
    except Exception as e:
        st.error(f"Error adding song: {e}")
        return None


def update_song(song_id, title, artist, arrangement, default_key=""):
    try:
        song_data = {
            "title": title,
            "artist": artist,
            "arrangement": arrangement,
            "default_key": default_key,
        }
        response = supabase.table("song").update(song_data).eq("id", song_id).execute()
        st.success("Song updated!")
        return response.data[0] if response.data else None
    except Exception as e:
        st.error(f"Error updating song: {e}")
        return None
