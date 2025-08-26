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


# --- Database functions ---
def get_roster():
    try:
        response = supabase.table("song").select("*").execute()
        return response.data
    except Exception as e:
        st.error(f"Error fetching songs: {e}")
        return []


# Initialize session state for data persistence
if "users" not in st.session_state:
    st.session_state.users = []
if "services" not in st.session_state:
    st.session_state.services = []
if "availability" not in st.session_state:
    st.session_state.availability = {}
if "assignments" not in st.session_state:
    st.session_state.assignments = {}


# Sample data for demonstration
if not st.session_state.users:
    st.session_state.users = [
        {
            "id": 1,
            "name": "John Doe",
            "email": "john@example.com",
            "role": "Leader",
            "instruments": ["Guitar", "Vocals"],
        },
        {
            "id": 2,
            "name": "Jane Smith",
            "email": "jane@example.com",
            "role": "Member",
            "instruments": ["Piano", "Vocals"],
        },
        {
            "id": 3,
            "name": "Mike Johnson",
            "email": "mike@example.com",
            "role": "Member",
            "instruments": ["Drums"],
        },
        {
            "id": 4,
            "name": "Sarah Wilson",
            "email": "sarah@example.com",
            "role": "Member",
            "instruments": ["Bass", "Vocals"],
        },
        {
            "id": 5,
            "name": "Tom Brown",
            "email": "tom@example.com",
            "role": "Member",
            "instruments": ["Guitar", "Vocals"],
        },
    ]

# App title and description
st.title("🎵 Worship Team Roster Manager")
st.markdown(
    """
Streamline your worship team scheduling process. 
Team members can submit availability, and leaders can create optimized rosters.
"""
)

# Sidebar for navigation
st.sidebar.title("Navigation")
app_mode = st.sidebar.radio(
    "Go to",
    [
        "Dashboard",
        "Submit Availability",
        "Manage Schedule",
        "View Roster",
        "Admin Settings",
    ],
)

# Dashboard
if app_mode == "Dashboard":
    st.header("Dashboard")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Team Members",
            len([u for u in st.session_state.users if u["role"] == "Member"]),
        )

    with col2:
        # Count upcoming services in next 30 days
        upcoming_services = [
            s
            for s in st.session_state.services
            if s["date"] >= datetime.date.today()
            and s["date"] <= datetime.date.today() + timedelta(days=30)
        ]
        st.metric("Upcoming Services", len(upcoming_services))

    with col3:
        # Calculate response rate for next service
        if st.session_state.services and st.session_state.availability:
            next_service = min(
                [
                    s
                    for s in st.session_state.services
                    if s["date"] >= datetime.date.today()
                ],
                key=lambda x: x["date"],
                default=None,
            )
            if next_service:
                responded = len(
                    [
                        a
                        for a in st.session_state.availability
                        if a["service_id"] == next_service["id"]
                    ]
                )
                total_members = len(
                    [u for u in st.session_state.users if u["role"] == "Member"]
                )
                response_rate = (
                    (responded / total_members) * 100 if total_members > 0 else 0
                )
                st.metric("Response Rate", f"{response_rate:.1f}%")

    st.subheader("Recent Activity")

    # Placeholder for activity feed
    st.info("Activity feed will show recent submissions and changes here.")

    st.subheader("Upcoming Services")

    # Display next 4 services
    if st.session_state.services:
        upcoming = sorted(
            [
                s
                for s in st.session_state.services
                if s["date"] >= datetime.date.today()
            ],
            key=lambda x: x["date"],
        )[:4]

        for service in upcoming:
            with st.expander(f"{service['date']} - {service['name']}"):
                # Check if roster is created
                service_assignments = [
                    a
                    for a in st.session_state.assignments
                    if a["service_id"] == service["id"]
                ]
                if service_assignments:
                    st.success("Roster created")
                    for assignment in service_assignments:
                        member = next(
                            (
                                u
                                for u in st.session_state.users
                                if u["id"] == assignment["user_id"]
                            ),
                            None,
                        )
                        if member:
                            st.write(
                                f"• {member['name']} - {', '.join(assignment['roles'])}"
                            )
                else:
                    st.warning("Roster not yet created")

                # Show response count
                responses = len(
                    [
                        a
                        for a in st.session_state.availability
                        if a["service_id"] == service["id"]
                    ]
                )
                total_members = len(
                    [u for u in st.session_state.users if u["role"] == "Member"]
                )
                st.write(f"Availability responses: {responses}/{total_members}")
    else:
        st.info("No upcoming services scheduled. Add services in Admin Settings.")

# Submit Availability
elif app_mode == "Submit Availability":
    st.header("Submit Your Availability")

    # User selection (in real app, this would be based on login)
    user_options = {
        f"{u['name']} ({u['email']})": u
        for u in st.session_state.users
        if u["role"] == "Member"
    }
    selected_user = st.selectbox("Select your name", options=list(user_options.keys()))
    user = user_options[selected_user]

    st.subheader(f"Availability for {user['name']}")

    # Display upcoming services
    if st.session_state.services:
        upcoming_services = sorted(
            [
                s
                for s in st.session_state.services
                if s["date"] >= datetime.date.today()
            ],
            key=lambda x: x["date"],
        )

        for service in upcoming_services:
            # Check if already submitted
            existing_response = next(
                (
                    a
                    for a in st.session_state.availability
                    if a["service_id"] == service["id"] and a["user_id"] == user["id"]
                ),
                None,
            )

            with st.expander(f"{service['date']} - {service['name']}"):
                if existing_response:
                    st.success(
                        f"You've already submitted: {existing_response['availability']}"
                    )
                    if st.button(
                        f"Change Response for {service['date']}",
                        key=f"change_{service['id']}",
                    ):
                        # Remove existing response
                        st.session_state.availability = [
                            a
                            for a in st.session_state.availability
                            if not (
                                a["service_id"] == service["id"]
                                and a["user_id"] == user["id"]
                            )
                        ]
                        st.rerun()
                else:
                    availability = st.radio(
                        "Are you available?",
                        ["Available", "Not Available", "If needed"],
                        key=f"avail_{service['id']}",
                    )

                    if availability == "Available":
                        instruments = st.multiselect(
                            "Which instruments/roles?",
                            user["instruments"],
                            default=user["instruments"],
                            key=f"instr_{service['id']}",
                        )

                    if st.button("Submit", key=f"submit_{service['id']}"):
                        # Save availability
                        response = {
                            "user_id": user["id"],
                            "service_id": service["id"],
                            "availability": availability,
                            "instruments": (
                                instruments if availability == "Available" else []
                            ),
                        }
                        st.session_state.availability.append(response)
                        st.success("Availability submitted!")
                        time.sleep(1)
                        st.rerun()
    else:
        st.info("No upcoming services to respond to.")

# Manage Schedule (Leaders only)
elif app_mode == "Manage Schedule":
    st.header("Manage Service Schedule")

    # Check if user is a leader (simplified for demo)
    leaders = [u for u in st.session_state.users if u["role"] == "Leader"]
    if not leaders:
        st.warning("No leaders defined. Please add leaders in Admin Settings.")
    else:
        # Add new service form
        with st.form("add_service_form"):
            st.subheader("Add New Service")
            col1, col2 = st.columns(2)
            with col1:
                service_name = st.text_input("Service Name", "Sunday Service")
            with col2:
                service_date = st.date_input(
                    "Service Date", min_value=datetime.date.today()
                )

            if st.form_submit_button("Add Service"):
                new_service = {
                    "id": max([s["id"] for s in st.session_state.services], default=0)
                    + 1,
                    "name": service_name,
                    "date": service_date,
                }
                st.session_state.services.append(new_service)
                st.success(f"Added service: {service_name} on {service_date}")

        st.subheader("Upcoming Services")

        if st.session_state.services:
            upcoming_services = sorted(
                [
                    s
                    for s in st.session_state.services
                    if s["date"] >= datetime.date.today()
                ],
                key=lambda x: x["date"],
            )

            for service in upcoming_services:
                with st.expander(
                    f"{service['date']} - {service['name']} (ID: {service['id']})"
                ):
                    # Show availability responses
                    responses = [
                        a
                        for a in st.session_state.availability
                        if a["service_id"] == service["id"]
                    ]

                    st.write(
                        f"**Responses: {len(responses)}/{len([u for u in st.session_state.users if u['role'] == 'Member'])}**"
                    )

                    available_members = []
                    not_available_members = []
                    if_needed_members = []

                    for response in responses:
                        member = next(
                            (
                                u
                                for u in st.session_state.users
                                if u["id"] == response["user_id"]
                            ),
                            None,
                        )
                        if member:
                            if response["availability"] == "Available":
                                available_members.append(
                                    {
                                        "member": member,
                                        "instruments": response["instruments"],
                                    }
                                )
                            elif response["availability"] == "Not Available":
                                not_available_members.append(member)
                            else:
                                if_needed_members.append(
                                    {
                                        "member": member,
                                        "instruments": response["instruments"],
                                    }
                                )

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.subheader("Available")
                        for avail in available_members:
                            st.write(
                                f"• {avail['member']['name']} ({', '.join(avail['instruments'])})"
                            )

                    with col2:
                        st.subheader("If Needed")
                        for avail in if_needed_members:
                            st.write(
                                f"• {avail['member']['name']} ({', '.join(avail['instruments'])})"
                            )

                    with col3:
                        st.subheader("Not Available")
                        for member in not_available_members:
                            st.write(f"• {member['name']}")

                    # Auto-generate roster button
                    if st.button("Auto-Generate Roster", key=f"auto_{service['id']}"):
                        # Simple auto-assignment logic
                        assignments = []
                        needed_roles = ["Vocals", "Guitar", "Piano", "Bass", "Drums"]

                        # Prioritize available members
                        for role in needed_roles:
                            # Find available members who can fill this role
                            suitable_members = [
                                avail
                                for avail in available_members
                                if role in avail["instruments"]
                            ]

                            if suitable_members:
                                selected = random.choice(suitable_members)
                                assignments.append(
                                    {
                                        "service_id": service["id"],
                                        "user_id": selected["member"]["id"],
                                        "roles": [role],
                                    }
                                )
                                # Remove from available to avoid double assignment
                                available_members.remove(selected)

                        st.session_state.assignments = [
                            a
                            for a in st.session_state.assignments
                            if a["service_id"] != service["id"]
                        ] + assignments
                        st.success("Roster generated! Check View Roster tab.")

                    # Manual assignment
                    st.subheader("Manual Assignment")

                    # Check if roster already exists
                    existing_assignments = [
                        a
                        for a in st.session_state.assignments
                        if a["service_id"] == service["id"]
                    ]

                    if existing_assignments:
                        st.write("Current assignments:")
                        for assignment in existing_assignments:
                            member = next(
                                (
                                    u
                                    for u in st.session_state.users
                                    if u["id"] == assignment["user_id"]
                                ),
                                None,
                            )
                            if member:
                                st.write(
                                    f"• {member['name']}: {', '.join(assignment['roles'])}"
                                )

                    # Form to add new assignment
                    with st.form(f"assign_form_{service['id']}"):
                        member_options = {
                            f"{m['name']}": m
                            for m in st.session_state.users
                            if m["role"] == "Member"
                        }
                        selected_member = st.selectbox(
                            "Select member", options=list(member_options.keys())
                        )
                        member = member_options[selected_member]

                        roles = st.multiselect("Roles", member["instruments"])

                        if st.form_submit_button("Assign to Service"):
                            new_assignment = {
                                "service_id": service["id"],
                                "user_id": member["id"],
                                "roles": roles,
                            }
                            # Remove any existing assignment for this user for this service
                            st.session_state.assignments = [
                                a
                                for a in st.session_state.assignments
                                if not (
                                    a["service_id"] == service["id"]
                                    and a["user_id"] == member["id"]
                                )
                            ]
                            st.session_state.assignments.append(new_assignment)
                            st.success(
                                f"Assigned {member['name']} to {service['name']}"
                            )
                            st.rerun()

                    # Send reminders button
                    if st.button("Send Reminders", key=f"remind_{service['id']}"):
                        # In a real app, this would send emails
                        non_responders = [
                            u
                            for u in st.session_state.users
                            if u["role"] == "Member"
                            and not any(
                                a["user_id"] == u["id"]
                                and a["service_id"] == service["id"]
                                for a in st.session_state.availability
                            )
                        ]

                        if non_responders:
                            st.warning(
                                f"Would send reminders to: {', '.join([u['name'] for u in non_responders])}"
                            )
                        else:
                            st.success("Everyone has responded!")
        else:
            st.info("No services scheduled. Add a service using the form above.")

# View Roster
elif app_mode == "View Roster":
    st.header("View Service Rosters")

    if st.session_state.services:
        # Select service to view
        service_options = {
            f"{s['date']} - {s['name']}": s for s in st.session_state.services
        }
        selected_service = st.selectbox(
            "Select Service", options=list(service_options.keys())
        )
        service = service_options[selected_service]

        # Get assignments for this service
        service_assignments = [
            a for a in st.session_state.assignments if a["service_id"] == service["id"]
        ]

        if service_assignments:
            st.subheader(f"Roster for {service['date']} - {service['name']}")

            # Display assignments
            for assignment in service_assignments:
                member = next(
                    (
                        u
                        for u in st.session_state.users
                        if u["id"] == assignment["user_id"]
                    ),
                    None,
                )
                if member:
                    st.write(f"**{member['name']}** - {', '.join(assignment['roles'])}")

            # Export options
            col1, col2 = st.columns(2)

            with col1:
                if st.button("Export as PDF"):
                    # In a real app, this would generate a PDF
                    st.success("PDF export functionality would be implemented here")

            with col2:
                if st.button("Email to Team"):
                    # In a real app, this would send emails
                    st.success("Email functionality would be implemented here")

        else:
            st.info(
                "No roster created for this service yet. Go to Manage Schedule to create one."
            )

    else:
        st.info("No services scheduled. Add services in Admin Settings.")

# Admin Settings
elif app_mode == "Admin Settings":
    st.header("Admin Settings")

    tab1, tab2, tab3 = st.tabs(["Team Members", "Service Templates", "System Settings"])

    with tab1:
        st.subheader("Manage Team Members")

        # Display current members
        for user in st.session_state.users:
            with st.expander(f"{user['name']} ({user['role']})"):
                st.write(f"Email: {user['email']}")
                st.write(f"Instruments: {', '.join(user['instruments'])}")

                if st.button("Edit", key=f"edit_{user['id']}"):
                    st.session_state.editing_user = user["id"]

                if st.button("Remove", key=f"remove_{user['id']}"):
                    st.session_state.users = [
                        u for u in st.session_state.users if u["id"] != user["id"]
                    ]
                    st.success("Member removed")
                    st.rerun()

        # Add new member form
        with st.form("add_member_form"):
            st.subheader("Add New Team Member")
            col1, col2 = st.columns(2)
            with col1:
                new_name = st.text_input("Name")
                new_email = st.text_input("Email")
            with col2:
                new_role = st.selectbox("Role", ["Leader", "Member"])
                instruments_options = [
                    "Vocals",
                    "Guitar",
                    "Piano",
                    "Bass",
                    "Drums",
                    "Sound",
                    "Visuals",
                ]
                new_instruments = st.multiselect(
                    "Instruments/Roles", instruments_options
                )

            if st.form_submit_button("Add Member"):
                new_member = {
                    "id": max([u["id"] for u in st.session_state.users], default=0) + 1,
                    "name": new_name,
                    "email": new_email,
                    "role": new_role,
                    "instruments": new_instruments,
                }
                st.session_state.users.append(new_member)
                st.success(f"Added {new_name} to the team")
                st.rerun()

    with tab2:
        st.subheader("Service Templates")
        st.info("Template functionality would be implemented here")

        # Example template setup
        template_roles = st.multiselect(
            "Default Roles Needed per Service",
            [
                "Lead Vocals",
                "Backing Vocals",
                "Acoustic Guitar",
                "Electric Guitar",
                "Bass",
                "Piano",
                "Drums",
                "Sound",
                "Visuals",
            ],
            default=[
                "Lead Vocals",
                "Backing Vocals",
                "Acoustic Guitar",
                "Bass",
                "Piano",
                "Drums",
            ],
        )

        if st.button("Save Template"):
            st.success("Template saved!")

    with tab3:
        st.subheader("System Settings")

        # Notification settings
        st.checkbox("Enable email notifications", value=True)
        st.number_input(
            "Reminder days before service", min_value=1, max_value=7, value=3
        )

        # Data management
        if st.button("Export Data"):
            # In a real app, this would export to CSV/JSON
            st.success("Data export functionality would be implemented here")

        if st.button("Import Data"):
            # In a real app, this would import from file
            st.success("Data import functionality would be implemented here")

        if st.button("Clear All Data"):
            if st.checkbox("I understand this will delete all data"):
                st.session_state.users = []
                st.session_state.services = []
                st.session_state.availability = []
                st.session_state.assignments = []
                st.success("All data cleared")
                st.rerun()

# Footer
st.markdown("---")
st.markdown(
    "Worship Team Roster App • Streamlit • [Get Help](mailto:support@example.com)"
)
