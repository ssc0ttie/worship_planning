import streamlit as st
from supabase import create_client, Client

# from dotenv import load_dotenv
import os
import re
import json

import pandas as pd
import datetime
from datetime import timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import time
from io import BytesIO

### page config ####
st.set_page_config(
    page_title="Worship Team Manager",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded",
)


# st.title("Worship Team Manager")

######################TABS########################
# tab0, tab1, tab2 = st.tabs(["Library", "Setlists", "Rehersal View"])


#### Library Tab #####
from functions import to_chordpro
from functions import transpose
from functions import export_to_pdf
from functions import song_manager
from functions import setlist_manager
from functions import roster_manager
from streamlit_pdf_viewer import pdf_viewer
import tempfile
import os


# st.title("Song Transposer")

# Initialize active page state
if "active_page" not in st.session_state:
    st.session_state.active_page = "Manage Roster"

with st.sidebar:
    st.header("Navigation")
    page = st.radio(
        "Go to:",
        [
            "Manage Roster",
            "Manage Songs",
            "Manage Setlist",
            "Adhoc : Transpose Song",
            "Settings  *place holder",
            "Help *place holder",
        ],
    )

##PAGE##
st.session_state.active_page = page


if page == "Adhoc : Transpose Song":
    # Choose input source
    input_mode = st.radio(
        "Choose Song Input Method:",
        ["Paste Song", "Select from Songbank"],
        horizontal=True,
    )

    if input_mode == "Paste Song":
        col1, col2 = st.columns(2)
        with col1:
            song_title = st.text_input(
                "Enter Song Title*", placeholder="e.g., Amazing Grace"
            )
            artist = st.text_input("Enter Artist", placeholder="e.g., John Newton")
            transpose_steps = st.number_input(
                "Transpose Steps*", min_value=-11, max_value=11, value=0, step=1
            )
            key = st.text_input("Enter Song Key*", placeholder="e.g., C, G, Am, etc.")

        with col2:
            song = st.text_area(
                "Paste Song Here*",
                height=400,
                placeholder="""[C]Amazing [G]grace, how [C]sweet the [F]sound...""",
            )
        ##if new song##
        newsong_title = song_title
        newsong_artist = artist
        newsong_arrangement = song
        newsong_key = key
    else:
        # Songbank option
        songs = song_manager.get_songs()
        song_options = {f"{s['title']} by {s['artist']}": s for s in songs}
        selected_song = st.selectbox(
            "Select Song from Songbank", options=list(song_options.keys())
        )
        song_data = song_options[selected_song] if selected_song else None
        song = song_data["arrangement"] if song_data else ""
        ## CLEAN SONGS
        special_chars = ["■", "●", "◆", "▲", "▼", "○", "•", "▪", "▫", "◼", "◻"]
        for char in special_chars:
            song = song.replace(char, "")

        song_title = song_data["title"] if song_data else ""
        key = song_data["default_key"] if song_data else ""

        transpose_steps = st.number_input(
            "Transpose Steps*", min_value=-11, max_value=11, value=0, step=1
        )

        # # Auto-fill title and artist if not manually entered
        # if song_data:
        #     if not song_title:
        #         song_title = song_data["title"]
        #     if not artist:
        #         artist = song_data["artist"]

    # Add to bank option
    if input_mode == "Paste Song":
        if st.button(
            "🎵 Add Song to Library", type="primary", use_container_width=True
        ):
            if song_manager.add_song(
                newsong_title, newsong_artist, newsong_arrangement, newsong_key
            ):

                st.success(f"Added song: {newsong_title} by {newsong_artist}")
    # Add a transpose button
    transpose_button = st.button(
        "🎵 Transpose Song", type="primary", use_container_width=True
    )

    # Initialize session state to track if transposition was successful
    if "transposed_song" not in st.session_state:
        st.session_state.transposed_song = None
    if "nashville_song" not in st.session_state:
        st.session_state.nashville_song = None
    if "transpose_success" not in st.session_state:
        st.session_state.transpose_success = False

    if transpose_button:
        # Validate required fields
        required_fields = [song_title, key, song]
        if not all(required_fields):
            st.error("❌ Please fill in all required fields (marked with *)")
        else:
            try:
                with st.spinner("Transposing song..."):
                    # Convert pasted song to ChordPro first
                    # chordpro_song = to_chordpro.ug_to_chordpro(song)
                    # Perform Transpose and Nashville
                    transposed = transpose.transform_chordpro(
                        song, transpose_steps=transpose_steps
                    )
                    nashville = transpose.transform_chordpro(
                        song, nashville=True, key=key
                    )

                    # Generate PDFs in memory
                    transposed_pdf = export_to_pdf.export_to_pdf_compact_2(
                        transposed,
                        title=f"{song_title} (Transposed +{transpose_steps})",
                    )

                    nashville_pdf = export_to_pdf.export_to_pdf_compact_2(
                        nashville, title=f"{song_title} (Nashville - Key {key})"
                    )

                    # Store in session state
                    st.session_state.transposed_song = transposed
                    st.session_state.nashville_song = nashville
                    st.session_state.transposed_pdf = transposed_pdf
                    st.session_state.nashville_pdf = nashville_pdf
                    st.session_state.transpose_success = True

                    st.success("✅ Song transposed successfully! PDFs generated.")

            except Exception as e:
                st.error(f"❌ Error during transposition: {str(e)}")
                st.session_state.transpose_success = False

    # Display results if transposition was successful
    if st.session_state.transpose_success:
        st.divider()
        st.subheader("Transposition Results")

        # Create tabs for different views
        tab1, tab2 = st.tabs(["Transposed Version", "Nashville Numbers"])

        with tab1:
            st.write(f"**Transposed by {transpose_steps} steps:**")
            st.code(st.session_state.transposed_song, language=None)

            if st.session_state.transposed_pdf:
                if st.button("Preview PDF", use_container_width=True):
                    pdf_bytes = st.session_state.transposed_pdf
                    if pdf_bytes:
                        # Create a temporary file
                        with tempfile.NamedTemporaryFile(
                            delete=False, suffix=".pdf"
                        ) as tmp:
                            tmp.write(pdf_bytes)
                            tmp_path = tmp.name

                        # Display PDF
                        pdf_viewer(tmp_path, width=700)

                        # Clean up
                        os.unlink(tmp_path)

                st.download_button(
                    label="📥 Download Transposed PDF",
                    data=st.session_state.transposed_pdf,
                    file_name=f"{song_title}_transposed.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )

        with tab2:
            st.write(f"**Nashville numbers (Key: {key}):**")
            st.code(st.session_state.nashville_song, language=None)

            if st.session_state.nashville_pdf:
                st.download_button(
                    label="📥 Download Nashville PDF",
                    data=st.session_state.nashville_pdf,
                    file_name=f"{song_title}_nashville.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )

        # Clear results button
        if st.button("🔄 Clear Results", use_container_width=True):
            st.session_state.transposed_song = None
            st.session_state.nashville_song = None
            st.session_state.transpose_success = False
            st.rerun()

elif page == "Settings":
    st.subheader("Settings")
    st.write("Configure your transposition preferences here.")
    # Add settings options if needed

elif page == "Help":
    st.subheader("Help & Instructions")
    st.markdown(
        """
    ### How to use this app:
    
    1. **Fill in required fields** (marked with *)
    - **Song Title**: Name of the song
    - **Song Key**: Original key of the song (e.g., C, G, Am)
    - **Paste Song**: UltimateGuitar Format Song
    
    2. **Optional fields**:
    - **Artist**: Song artist name
    - **Transpose Steps**: Number of semitones to transpose (-11 to +11)
    
    3. **Click "Transpose Song"** to process
    
    4. **Download** the transposed versions as PDF
    
    ### ChordPro Format Example:
    ```
    [C]Amazing [G]grace, how [C]sweet the [F]sound
    [C]That saved a [G]wretch like [C]me
    ```
    """
    )


elif page == "Manage Songs":

    # # Initialize active tab state
    # if "active_tab" not in st.session_state:
    #     st.session_state.active_tab = "Ma"
    col1, col2 = st.columns(2)
    with col1:
        st.header("Manage Songs in Database")
    with col2:
        ###########ADD SONG #################
        with st.expander("🎵Add Song"):
            with st.form("add_song_form", clear_on_submit=True):
                from functions import song_manager

                col1, col2 = st.columns(2)
                with col1:
                    newsong_title = st.text_input(
                        "Enter Song Title*", placeholder="e.g., Amazing Grace"
                    )
                    newsong_artist = st.text_input(
                        "Enter Artist", placeholder="e.g., John Newton"
                    )
                    # transpose_steps = st.number_input(
                    #     "Transpose Steps*", min_value=-11, max_value=11, value=0, step=1
                    # )
                    newsong_key = st.text_input(
                        "Enter Song Key*", placeholder="e.g., C, G, Am, etc."
                    )

                with col2:
                    newsong_arrangement = st.text_area(
                        "Paste Song Here*",
                        height=400,
                        placeholder="""[C]Amazing [G]grace, how [C]sweet the [F]sound...""",
                    )

                # # Add a transpose button
                # addsong_button = st.button(
                #     "🎵 Add Song", type="primary", use_container_width=True
                # )

                if st.form_submit_button("Add Song"):
                    if song_manager.add_song(
                        newsong_title, newsong_artist, newsong_arrangement, newsong_key
                    ):

                        st.success(f"Added song: {newsong_title} by {newsong_artist}")
                        st.rerun()

    songs = song_manager.get_songs()
    if songs:
        for song in sorted(songs, key=lambda x: x["title"]):
            with st.expander(f"{song['title']} by {song['artist']}"):
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.write(f"**ID:** {song['id']}")
                    st.write(
                        f"**Default Key:** {song.get('default_key', 'Not specified')}"
                    )

                with col2:
                    if st.button("Edit", key=f"edit_{song['id']}"):
                        st.session_state.edit_mode = True
                        st.session_state.editing_song = song

                    if st.button("Delete", key=f"delete_{song['id']}"):
                        # In a real app, you'd add a confirmation and delete function
                        st.warning("Delete functionality would be implemented here")

                    if st.button("View Song", key=f"view_{song['id']}"):
                        st.session_state.view_mode = True
                        st.session_state.edit_mode = False
                        st.session_state.viewing_song = song

                # Edit form (if in edit mode for this song)
                if (
                    st.session_state.get("edit_mode")
                    and st.session_state.get("editing_song", {}).get("id") == song["id"]
                ):
                    with st.form(key=f"edit_form_{song['id']}"):
                        new_title = st.text_input("Title", value=song["title"])
                        new_artist = st.text_input("Artist", value=song["artist"])
                        new_key = st.text_input(
                            "Default Key", value=song.get("default_key", "")
                        )
                        new_arrangement = st.text_area(
                            "Lyrics", value=song["arrangement"], height=200
                        )

                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("Save Changes"):
                                song_manager.update_song(
                                    song["id"],
                                    new_title,
                                    new_artist,
                                    new_arrangement,
                                    new_key,
                                )
                                st.session_state.edit_mode = False
                                st.rerun()
                        with col2:
                            if st.form_submit_button("Cancel"):
                                st.session_state.edit_mode = False
                                st.rerun()

                # --- View mode ---
                if (
                    st.session_state.get("view_mode")
                    and st.session_state.get("viewing_song", {}).get("id") == song["id"]
                ):
                    st.subheader(f"{song['title']} - {song['artist']}")
                    st.markdown(f"**Key:** {song.get('default_key', '')}")
                    st.text_area(
                        "Lyrics (read-only)",
                        value=song["arrangement"],
                        height=300,
                        disabled=True,
                    )

                    if st.button("Close View", key=f"close_view_{song['id']}"):
                        st.session_state.view_mode = False
                        st.rerun()

    else:
        st.info("No songs found in the database.")


elif page == "Manage Roster":
    from functions import roster_manager

    # Initialize active tab state
    if "active_tab" not in st.session_state:
        st.session_state.active_tab = "Dashboard"

    # st.header("Manage Roster")

    users = roster_manager.get_users()
    services = roster_manager.get_services()
    availability = roster_manager.get_availability()
    assignments = roster_manager.get_assignments()
    roles = roster_manager.get_roles()
    # update_availability = roster_manager.update_availability()
    # add_availability = roster_manager.add_availability()

    # Initialize session state for UI elements only
    if "editing_user" not in st.session_state:
        st.session_state.editing_user = None
    if "edit_mode" not in st.session_state:
        st.session_state.edit_mode = False
    if "new_song_mode" not in st.session_state:
        st.session_state.new_song_mode = False

    ###################### STREAMLIT ###################
    # App title and description
    st.header("🎵 Worship Team Roster Manager")
    st.markdown(
        """
    Streamline your worship team scheduling process. 
    Team members can submit availability, and leaders can create optimized rosters.
    """
    )

    # Tabs for navigation
    # st.title("Navigation")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "Dashboard",
            "Submit Availability",
            "Manage Schedule",
            "View Roster",
            "Admin Settings",
        ]
    )

    # define active tab
    active_tab = st.session_state.active_tab

    # app_mode = tab1, tab2, tab3, tab4, tab5

    # Dashboard
    with tab1:  ##APP MODE "Dashboard"##
        st.header("Dashboard")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Team Members",
                len([u for u in users if u["role"] in ["Member", "Admin"]]),
            )

        with col2:
            # Count upcoming services in next 30 days
            upcoming_services = [
                s
                for s in services
                if datetime.datetime.strptime(s["service_date"], "%Y-%m-%d").date()
                >= datetime.date.today()
                and datetime.datetime.strptime(s["service_date"], "%Y-%m-%d").date()
                <= datetime.date.today() + timedelta(days=30)
            ]

            st.metric("Upcoming Services", len(upcoming_services))

        with col3:
            # Calculate response rate for next service
            if services and availability:
                # Convert string dates to date objects for comparison
                services_with_dates = []
                for s in services:
                    s_copy = s.copy()
                    s_copy["service_date"] = datetime.datetime.strptime(
                        s["service_date"], "%Y-%m-%d"
                    ).date()
                    services_with_dates.append(s_copy)

                next_service = min(
                    [
                        s
                        for s in services_with_dates
                        if s["service_date"] >= datetime.date.today()
                    ],
                    key=lambda x: x["service_date"],
                    default=None,
                )
                if next_service:
                    responded = len(
                        [
                            a
                            for a in availability
                            if a["service_id"] == next_service["id"]
                        ]
                    )
                    total_members = len([u for u in users if u["role"] == "Member"])
                    response_rate = (
                        (responded / total_members) * 100 if total_members > 0 else 0
                    )
                    st.metric("Response Rate", f"{response_rate:.1f}%")

        st.subheader("Recent Activity")

        # Placeholder for activity feed
        st.info("Activity feed will show recent submissions and changes here.")

        st.subheader("Upcoming Services")

        # Display next 4 services
        if services:
            # Convert string dates to date objects for sorting
            services_with_dates = []
            for s in services:
                s_copy = s.copy()
                s_copy["service_date"] = datetime.datetime.strptime(
                    s["service_date"], "%Y-%m-%d"
                ).date()
                services_with_dates.append(s_copy)

            upcoming = sorted(
                [
                    s
                    for s in services_with_dates
                    if s["service_date"] >= datetime.date.today()
                ],
                key=lambda x: x["service_date"],
            )[:4]

            for service in upcoming:
                with st.expander(
                    f"{service['service_date']} - {service['service_name']}"
                ):
                    # Check if roster is created
                    service_assignments = [
                        a for a in assignments if a["service_id"] == service["id"]
                    ]
                    if service_assignments:
                        st.success("Roster created")
                        for assignment in service_assignments:
                            member = next(
                                (u for u in users if u["id"] == assignment["user_id"]),
                                None,
                            )
                            if member:

                                def get_roles(assignment):
                                    return json.loads(assignment["roles"])

                                assigned_roles = get_roles(assignment)

                                st.write(
                                    f"• {member['name']} - {', '.join(assigned_roles)}"
                                )
                    else:
                        st.warning("Roster not yet created")

                    # Show response count
                    responses = len(
                        [a for a in availability if a["service_id"] == service["id"]]
                    )
                    total_members = len([u for u in users if u["role"] == "Member"])
                    st.write(f"Availability responses: {responses}/{total_members}")
        else:
            st.info("No upcoming services scheduled. Add services in Admin Settings.")

    # Submit Availability
    with tab2:  ## APP MODE "Submit Availability":
        st.header("Submit Your Availability")

        # User selection (in real app, this would be based on login)
        user_options = {
            f"{u['name']} ({u['email']})": u
            for u in users
            if u["role"] in ["Member", "Admin"]
        }

        # Build a mapping: user_id -> [list of roles]
        user_roles_map = {}
        for r in roles:
            user_roles_map.setdefault(r["user_id"], []).append(r["instrument"])

        if not user_options:
            st.warning("No team members found. Please add members in Admin Settings.")
        else:
            selected_user = st.selectbox(
                "Select your name", options=list(user_options.keys())
            )
            user = user_options[selected_user]

            st.subheader(f"Availability for {user['name']}")

            # Display upcoming services
            if services:
                # Convert string dates to date objects for sorting
                services_with_dates = []
                for s in services:
                    s_copy = s.copy()
                    s_copy["service_date"] = datetime.datetime.strptime(
                        s["service_date"], "%Y-%m-%d"
                    ).date()
                    services_with_dates.append(s_copy)

                upcoming_services = sorted(
                    [
                        s
                        for s in services_with_dates
                        if s["service_date"] >= datetime.date.today()
                    ],
                    key=lambda x: x["service_date"],
                )

                for service in upcoming_services:
                    # Check if already submitted
                    existing_response = next(
                        (
                            a
                            for a in availability
                            if a["service_id"] == service["id"]
                            and a["user_id"] == user["id"]
                        ),
                        None,
                    )

                    with st.expander(
                        f"{service['service_date']} - {service['service_name']}"
                    ):
                        if existing_response:
                            st.success(
                                f"You've already submitted: {existing_response['availability_status']}"
                            )
                            if st.button(
                                f"Change Response for {service['service_date']}",
                                key=f"change_{service['id']}",
                            ):
                                # In a real app, you would update the availability in Supabase
                                if roster_manager.update_availability(
                                    existing_response["id"], "Not Available", []
                                ):
                                    st.success("Response updated!")
                                    active_tab
                                    st.rerun()
                        else:
                            availability_status = st.radio(
                                "Are you available?",
                                ["Available", "Not Available", "If needed"],
                                key=f"avail_{service['id']}",
                            )

                            if availability_status == "Available":
                                available_roles = user_roles_map.get(user["id"], [])
                                instruments = st.multiselect(
                                    "Which instruments/roles?",
                                    options=available_roles,
                                    default=available_roles,  # default selects all their roles
                                    key=f"instr_{service['id']}",
                                )

                            else:
                                instruments = []

                            if st.button("Submit", key=f"submit_{service['id']}"):
                                # Save availability to Supabase
                                if roster_manager.add_availability(
                                    user["id"],
                                    service["id"],
                                    availability_status,
                                    instruments,
                                ):
                                    st.success("Availability submitted!")
                                    time.sleep(1)
                                    active_tab
                                    st.rerun()
            else:
                st.info("No upcoming services to respond to.")
    # Manage Schedule (Leaders only)
    with tab3:  # APP MODE "Manage Schedule":
        st.header("Manage Service Schedule")

        # Check if user is a leader (simplified for demo)
        leaders = [u for u in users if u["role"] == "Admin"]
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
                    if roster_manager.add_service(
                        service_name, service_date.isoformat()
                    ):
                        st.success(f"Added service: {service_name} on {service_date}")
                        active_tab
                        st.rerun()

            st.subheader("Upcoming Services")

            # Refresh services data
            services = roster_manager.get_services()

            if services:
                # Convert string dates to date objects for sorting
                services_with_dates = []
                for s in services:
                    s_copy = s.copy()
                    s_copy["service_date"] = datetime.datetime.strptime(
                        s["service_date"], "%Y-%m-%d"
                    ).date()
                    services_with_dates.append(s_copy)

                upcoming_services = sorted(
                    [
                        s
                        for s in services_with_dates
                        if s["service_date"] >= datetime.date.today()
                    ],
                    key=lambda x: x["service_date"],
                )

                for service in upcoming_services:
                    with st.expander(
                        f"{service['service_date']} - {service['service_name']} (ID: {service['id']})"
                    ):
                        # Show availability responses
                        responses = [
                            a for a in availability if a["service_id"] == service["id"]
                        ]

                        st.write(
                            f"**Responses: {len(responses)}/{len([u for u in users if u['role'] == 'Member'])}**"
                        )

                        available_members = []
                        not_available_members = []
                        if_needed_members = []

                        for response in responses:
                            member = next(
                                (u for u in users if u["id"] == response["user_id"]),
                                None,
                            )
                            if member:
                                if response["availability_status"] == "Available":
                                    available_members.append(
                                        {
                                            "member": member,
                                            "instruments": response["instruments"],
                                            "response_id": response["id"],
                                        }
                                    )
                                elif response["availability_status"] == "Not Available":
                                    not_available_members.append(member)
                                else:
                                    if_needed_members.append(
                                        {
                                            "member": member,
                                            "instruments": response["instruments"],
                                            "response_id": response["id"],
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

                        # Manual assignment
                        st.subheader("Manual Assignment")

                        # Check if roster already exists
                        existing_assignments = [
                            a for a in assignments if a["service_id"] == service["id"]
                        ]

                        if existing_assignments:
                            st.write("Current assignments:")
                            for assignment in existing_assignments:
                                member = next(
                                    (
                                        u
                                        for u in users
                                        if u["id"] == assignment["user_id"]
                                    ),
                                    None,
                                )
                                if member:
                                    roles = assignment["roles"]
                                    # If it's a string, convert it back to list
                                    if isinstance(roles, str):
                                        try:
                                            roles = json.loads(roles)
                                        except:
                                            roles = [roles]  # fallback, single string

                                    st.write(f"• {member['name']}: {', '.join(roles)}")
                                    if st.button(
                                        "Remove", key=f"remove_{assignment['id']}"
                                    ):
                                        if roster_manager.delete_assignment(
                                            assignment["id"]
                                        ):
                                            st.success("Assignment removed!")
                                            active_tab
                                            st.rerun()

                        member_options = {
                            f"{m['name']}": m
                            for m in users
                            if m["role"] in ["Member", "Admin"]
                        }
                        selected_member = st.selectbox(
                            "Select member",
                            options=list(member_options.keys()),
                            key=f"member_select_{service['id']}",
                        )
                        member = member_options[selected_member]

                        # fetch instruments for this member
                        roles_data = roster_manager.get_roles()
                        user_roles_map = {}
                        for r in roles_data:
                            user_roles_map.setdefault(r["user_id"], []).append(
                                r["instrument"]
                            )
                        instrument_options = user_roles_map.get(member["id"], [])

                        with st.form(f"assign_form_{service['id']}"):
                            roles = st.multiselect(
                                "Roles (instruments/parts for this service)",
                                options=instrument_options,
                                default=instrument_options,
                                key=f"roles_{service['id']}_{selected_member}",
                            )
                            if st.form_submit_button("Assign to Service"):
                                if roster_manager.add_assignment(
                                    service["id"], member["id"], roles
                                ):
                                    st.success(
                                        f"Assigned {member['name']} to {service['service_name']}"
                                    )
                                    active_tab
                                    st.rerun()

                        # Send reminders button
                        if st.button(
                            "Send Reminders: Not Yet Live",
                            key=f"remind_{service['id']}",
                        ):
                            # In a real app, this would send emails
                            non_responders = [
                                u
                                for u in users
                                if u["role"] == "Member"
                                and not any(
                                    a["user_id"] == u["id"]
                                    and a["service_id"] == service["id"]
                                    for a in availability
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

    with tab4:  # APP MODE "View Roster":
        st.header("View Service Rosters")

        if services:
            # Convert string dates to date objects for display
            services_with_dates = []
            for s in services:
                s_copy = s.copy()
                s_copy["service_date"] = datetime.datetime.strptime(
                    s["service_date"], "%Y-%m-%d"
                ).date()
                services_with_dates.append(s_copy)

            # Select service to view
            service_options = {
                f"{s['service_date']} - {s['service_name']}": s
                for s in services_with_dates
            }
            selected_service = st.selectbox(
                "Select Service",
                options=sorted(service_options.keys()),
                # default="",
            )
            service = service_options[selected_service]

            # Get assignments for this service
            service_assignments = [
                a for a in assignments if a["service_id"] == service["id"]
            ]

            if service_assignments:
                st.subheader(
                    f"Roster for {service['service_date']} - {service['service_name']}"
                )

                # Display assignments
                for assignment in service_assignments:
                    member = next(
                        (u for u in users if u["id"] == assignment["user_id"]),
                        None,
                    )
                    if member:

                        roles = assignment["roles"]
                        # If it's a string, convert it back to list
                        if isinstance(roles, str):
                            try:
                                roles = json.loads(roles)
                            except:
                                roles = [roles]  # fallback, single string
                        st.write(f"**{member['name']}** - {', '.join(roles)}")

                # Export options
                col1, col2 = st.columns(2)

                with col1:
                    if st.button("Export as PDF : Not Yet Live"):
                        # In a real app, this would generate a PDF
                        st.success("PDF export functionality would be implemented here")

                with col2:
                    if st.button("Email to Team: Not Yet Live"):
                        # In a real app, this would send emails
                        st.success("Email functionality would be implemented here")

            else:
                st.info(
                    "No roster created for this service yet. Go to Manage Schedule to create one."
                )

        else:
            st.info("No services scheduled. Add services in Admin Settings.")

    with tab5:  # APP MODE "Admin Settings":
        st.subheader("Admin Settings")

        (rostertab1,) = st.tabs(
            ["Team Members"]
            #  , "Service Templates", "System Settings"
        )

        with rostertab1:
            st.subheader("Manage Team Members")

            # Display current members
            for user in users:
                with st.expander(f"{user['name']} ({user['role']})"):
                    st.write(f"Email: {user['email']}")

                    # fetch instruments for this member
                    roles_data = roster_manager.get_roles()
                    user_roles_map = {}
                    for r in roles_data:
                        user_roles_map.setdefault(r["user_id"], []).append(
                            r["instrument"]
                        )
                    instrument_options = user_roles_map.get(member["id"], [])

                    st.write(f"Instruments: {', '.join(instrument_options)}")

                    if st.button("Edit", key=f"edit_{user['id']}"):
                        st.session_state.editing_user = user["id"]
                        st.warning("Edit functionality would be implemented here")

                    if st.button("Remove", key=f"remove_{user['name']}"):
                        # In a real app, you'd add a delete function for Supabase
                        st.warning("Delete functionality would be implemented here")

            # Add new member form
            with st.form("add_member_form"):
                st.subheader("Add New Team Member")
                col1, col2 = st.columns(2)
                with col1:
                    new_name = st.text_input("Name")
                    new_email = st.text_input("Email")
                with col2:
                    new_role = st.selectbox("Role", ["Admin", "Member"])
                    instruments_options = [
                        "Backup Vocals",
                        "Worhip Lead",
                        "Guitar",
                        "Keys",
                        "Bass",
                        "Drums",
                        "Sound",
                        "Media",
                    ]
                    new_instruments = st.multiselect(
                        "Instruments/Roles", instruments_options
                    )

                if st.form_submit_button("Add Member"):

                    new_user = roster_manager.add_user(new_name, new_email, new_role)
                    if new_user:
                        st.success(f"Added {new_name} to the team")

                    # if roster_manager.add_role(new_user["id"], new_instruments):
                    #     st.success(f"Added {new_instruments} to {new_name}")

                    active_tab
                    st.rerun()


elif page == "Manage Setlist":
    # Fetch data
    songs = song_manager.get_songs()
    services = roster_manager.get_services()
    existing_setlists = setlist_manager.get_setlists()

    setlisttab1, setlisttab2 = st.tabs(["Create Setlist", "View Setlist"])

    with setlisttab1:
        col1, col2 = st.columns([1, 1])
        with col1:
            st.subheader("Create New Setlist")

            # Service selection
            sorted_services = sorted(services, key=lambda x: x["service_date"])

            service_options = {
                f"{s['service_name']} - {s['service_date']}": s for s in sorted_services
            }
            selected_service = st.selectbox(
                "Select Service:",
                options=list(service_options.keys()),
                index=0 if service_options else None,
            )
            service_info = (
                service_options[selected_service] if selected_service else None
            )

            # Setlist name
            setlist_name = st.text_input(
                "Setlist Name",
                value=f"Setlist for {selected_service}" if selected_service else "",
            )

            # Song selection
            st.subheader("Add Songs to Setlist")

            if not songs:
                st.info("No songs available. Add songs in the 'Add New Song' tab.")
            else:
                # Initialize session state for setlist
                if "current_setlist" not in st.session_state:
                    st.session_state.current_setlist = []

                # Song selection
                song_options = {f"{s['title']} by {s['artist']}": s for s in songs}
                selected_song = st.selectbox(
                    "Select Song:", options=list(song_options.keys())
                )
                song_data = song_options[selected_song] if selected_song else None

                # Key selection for this song
                from functions.transpose import NOTES_FLAT, NOTES_SHARP

                if song_data:
                    original_key = song_data.get("default_key", "C")
                    col_key1, col_key2 = st.columns([2, 1])
                    with col_key1:
                        selected_key = st.selectbox(
                            "Select Key:",
                            options=NOTES_SHARP,
                            index=(
                                NOTES_SHARP.index(original_key)
                                if original_key in NOTES_SHARP
                                else 0
                            ),
                        )
                    with col_key2:
                        # Calculate transpose steps
                        if original_key in NOTES_SHARP and selected_key in NOTES_SHARP:
                            original_idx = NOTES_SHARP.index(original_key)
                            selected_idx = NOTES_SHARP.index(selected_key)
                            transpose_steps = selected_idx - original_idx
                            st.write(f"Transpose: {transpose_steps} steps")
                            # Add to setlist button

                if st.button("Add to Setlist") and song_data:
                    # Transpose the lyrics
                    transposed_lyrics = transpose.transform_chordpro(
                        song_data["arrangement"], transpose_steps
                    )

                    # Add to current setlist
                    setlist_item = {
                        "id": song_data["id"],
                        "title": song_data["title"],
                        "artist": song_data.get("artist", ""),
                        "original_key": original_key,
                        "selected_key": selected_key,
                        "transpose_steps": transpose_steps,
                        "original_lyrics": song_data["arrangement"],
                        "transposed_lyrics": transposed_lyrics,
                    }

                    # setlist_manager.create_setlist(setlist_item)
                    st.session_state.current_setlist.append(setlist_item)
                    st.success(f"Added '{song_data['title']}' to setlist!")
        with col2:
            st.subheader("Current Setlist")

            if not st.session_state.current_setlist:
                st.info("No songs in setlist. Add songs from the left column.")
            else:
                # Display current setlist
                for i, item in enumerate(st.session_state.current_setlist):
                    with st.expander(
                        f"{i+1}. {item['title']} - {item['selected_key']}"
                    ):
                        st.write(f"**Artist:** {item.get('artist', 'Unknown')}")
                        st.write(f"**Original Key:** {item['original_key']}")
                        st.write(
                            f"**Transposed to:** {item['selected_key']} ({item['transpose_steps']} steps)"
                        )
                        # Show preview of transposed lyrics
                        preview_lines = item["transposed_lyrics"].split("\n")[:10]
                        preview_text = "\n".join(preview_lines)
                        if len(item["transposed_lyrics"].split("\n")) > 10:
                            preview_text += "\n..."
                        st.text_area(
                            "Preview",
                            value=preview_text,
                            height=150,
                            key=f"preview_{i}",
                        )

                        # Remove button
                        if st.button("Remove", key=f"remove_{i}"):
                            st.session_state.current_setlist.pop(i)
                            st.rerun()
                # Setlist actions
                st.divider()

                # Save setlist
                if st.button("💾 Save Setlist"):
                    if setlist_name and st.session_state.current_setlist:
                        setlist_data = {
                            "name": setlist_name,
                            "service_id": service_info["id"] if service_info else None,
                            "service_name": (
                                service_info["service_name"] if service_info else ""
                            ),
                            "service_date": (
                                service_info["service_date"] if service_info else ""
                            ),
                            "song": ", ".join(
                                s["title"] for s in st.session_state.current_setlist
                            ),
                            "song_id": ", ".join(
                                s["id"] for s in st.session_state.current_setlist
                            ),
                        }

                        from functions.setlist_manager import create_setlist

                        if create_setlist(setlist_data):
                            st.success("Setlist saved successfully!")
                        else:
                            st.error("Failed to save setlist.")
                    else:
                        st.warning(
                            "Please provide a setlist name and add at least one song."
                        )

                # Export to PDF
                if st.button("📄 Preview Songbook"):
                    from functions.export_to_pdf import export_setlist_to_pdf_compact

                    if st.session_state.current_setlist:
                        pdf_bytes = export_setlist_to_pdf_compact(
                            st.session_state.current_setlist,
                            service_info,
                            f"{setlist_name.replace(' ', '_')}.pdf",
                        )

                        # pdf_bytes = st.session_state.current_setlist
                        if pdf_bytes:
                            # Create a temporary file
                            with tempfile.NamedTemporaryFile(
                                delete=False, suffix=".pdf"
                            ) as tmp:
                                tmp.write(pdf_bytes)
                                tmp_path = tmp.name

                            # Display PDF
                            pdf_viewer(tmp_path, width=700)

                            # Clean up
                            os.unlink(tmp_path)

                        if pdf_bytes:
                            st.download_button(
                                label="Download PDF",
                                data=pdf_bytes,
                                file_name=f"{setlist_name.replace(' ', '_')}.pdf",
                                mime="application/pdf",
                            )
                    else:
                        st.warning("No songs in setlist to export.")

                # Clear setlist
                if st.button("🗑️ Clear Setlist"):
                    st.session_state.current_setlist = []
                    st.rerun()

    with setlisttab2:
        st.subheader("Existing Setlists")

        if not existing_setlists:
            st.info("No setlists available.")
        else:
            setlist_options = {
                f"{s['name']} - {s['service_date']}": s for s in existing_setlists
            }
            selected_label = st.selectbox(
                "Select a Setlist:", list(setlist_options.keys())
            )
            selected_setlist = setlist_options[selected_label]

            st.write(
                f"**Service:** {selected_setlist['service_name']} ({selected_setlist['service_date']})"
            )
            st.write(f"**Songs:** {selected_setlist['song']}")

            if st.button("📄 Preview Songbook (Saved)"):
                from functions.setlist_manager import get_setlist_songs

                setlist_items = get_setlist_songs(selected_setlist, song_manager)

                from functions.export_to_pdf import export_setlist_to_pdf_compact

                pdf_bytes = export_setlist_to_pdf_compact(
                    setlist_items,
                    selected_setlist,
                    f"{selected_setlist['name'].replace(' ', '_')}.pdf",
                )

                if pdf_bytes:
                    with tempfile.NamedTemporaryFile(
                        delete=False, suffix=".pdf"
                    ) as tmp:
                        tmp.write(pdf_bytes)
                        tmp_path = tmp.name

                    pdf_viewer(tmp_path, width=700)
                    os.unlink(tmp_path)

                    st.download_button(
                        label="Download PDF",
                        data=pdf_bytes,
                        file_name=f"{selected_setlist['name'].replace(' ', '_')}.pdf",
                        mime="application/pdf",
                    )
