import streamlit as st
import pandas as pd
import datetime
from datetime import timedelta
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import time
from io import BytesIO


from supabase_client import supabase


# Database functions
def get_users():
    try:
        response = supabase.table("users").select("*").execute()
        return response.data
    except Exception as e:
        st.error(f"Error fetching users: {e}")
        return []


def get_services():
    try:
        response = supabase.table("service_sched").select("*").execute()
        return response.data
    except Exception as e:
        st.error(f"Error fetching services: {e}")
        return []


def get_availability():
    try:
        response = supabase.table("availability").select("*").execute()
        return response.data
    except Exception as e:
        st.error(f"Error fetching availability: {e}")
        return []


def get_assignments():
    try:
        response = supabase.table("assignments").select("*").execute()
        return response.data
    except Exception as e:
        st.error(f"Error fetching assignments: {e}")
        return []


def get_roles():
    try:
        response = supabase.table("role").select("*").execute()
        return response.data
    except Exception as e:
        st.error(f"Error fetching assignments: {e}")
        return []


def add_user(name, email, role, instruments):
    try:
        user_data = {
            "name": name,
            "email": email,
            "role": role,
            "instruments": instruments,
        }
        response = supabase.table("users").insert(user_data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        st.error(f"Error adding user: {e}")
        return None


def add_service(name, date):
    try:
        service_data = {"service_name": name, "service_date": date}
        response = supabase.table("service_sched").insert(service_data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        st.error(f"Error adding service: {e}")
        return None


def add_availability(user_id, service_id, availability, instruments):
    try:
        availability_data = {
            "user_id": user_id,
            "service_id": service_id,
            "availability_status": availability,
            "instruments": instruments,
        }
        response = supabase.table("availability").insert(availability_data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        st.error(f"Error adding availability: {e}")
        return None


def update_availability(availability_id, availability, instruments):
    try:
        availability_data = {
            "availability_status": availability,
            "instruments": instruments,
        }
        response = (
            supabase.table("availability")
            .update(availability_data)
            .eq("id", availability_id)
            .execute()
        )
        return response.data[0] if response.data else None
    except Exception as e:
        st.error(f"Error updating availability: {e}")
        return None


def add_assignment(service_id, user_id, roles):
    try:
        assignment_data = {"service_id": service_id, "user_id": user_id, "roles": roles}
        response = supabase.table("assignments").insert(assignment_data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        st.error(f"Error adding assignment: {e}")
        return None


def update_assignment(assignment_id, roles):
    try:
        assignment_data = {"roles": roles}
        response = (
            supabase.table("assignments")
            .update(assignment_data)
            .eq("id", assignment_id)
            .execute()
        )
        return response.data[0] if response.data else None
    except Exception as e:
        st.error(f"Error updating assignment: {e}")
        return None


def delete_assignment(assignment_id):
    try:
        response = (
            supabase.table("assignments").delete().eq("id", assignment_id).execute()
        )
        return True
    except Exception as e:
        st.error(f"Error deleting assignment: {e}")
        return False
