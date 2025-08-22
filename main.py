import streamlit as st

# from supabase import create_client, Client
# from dotenv import load_dotenv
import os


# load_dotenv()

# url = os.getenv("SUPABASE_URL")
# key = os.getenv("SUPABASE_KEY")

# supabase: Client = create_client(url, key)

st.title("Atril")

######################TABS########################
tab0, tab1, tab2 = st.tabs(["Library", "Setlists", "Rehersal View"])


#### Library Tab #####
from functions import to_chordpro
from functions import transpose
from functions import export_to_pdf

# with tab0:

#     st.subheader("Library")

#     with st.expander("Upload a Song"):
#         "test"
#         song = st.text_area("Paste Song Here")
#         converte_song = to_chordpro.ug_to_chordpro(song)
#         st.code(converte_song, language="")


# with tab1:
#     st.subheader("Transpose Song")

#     col1, col2 = st.columns(2)
#     with col1:
#         song_title = st.text_input("Enter Song Title")
#         artist = st.text_input("Enter Artist")
#         transpose_steps = int(st.number_input("Transpose Step:"))
#         key = st.text_input("Enter Song Key")

#     with col2:
#         song = st.text_area("Paste Song Here", height=400)

#     ########## Perform Transpose and Nashville ###############
#     transposed = transpose.transform_chordpro(song, transpose_steps=2)
#     nashville = transpose.transform_chordpro(song, nashville=True, key=key)

#     # Export to PDF
#     export_to_pdf.export_to_pdf_compact(
#         transposed, filename=song_title + "_transposed.pdf", title=song_title
#     )
#     export_to_pdf.export_to_pdf_compact(
#         nashville, filename=song_title + "_nashville.pdf", title=song_title
#     )


st.title("Song Transposer")

with st.sidebar:
    st.header("Navigation")
    tab = st.radio("Go to:", ["Transpose Song", "Settings", "Help"])

if tab == "Transpose Song":
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
            placeholder="[C]Amazing [G]grace, how [C]sweet the [F]sound...",
        )

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

                    # # Export to PDF
                    # export_to_pdf.export_to_pdf_compact_2(
                    #     transposed,
                    #     filename=f"{song_title}_transposed.pdf",
                    #     title=f"{song_title} (Transposed +{transpose_steps} steps)",
                    # )
                    # export_to_pdf.export_to_pdf_compact_2(
                    #     nashville,
                    #     filename=f"{song_title}_nashville.pdf",
                    #     title=f"{song_title} (Nashville - Key {key})",
                    # )

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

            # Download button for transposed version
            # st.download_button(
            #     label="📥 Download Transposed PDF",
            #     data=open(f"{song_title}_transposed.pdf", "rb").read(),
            #     file_name=f"{song_title}_transposed.pdf",
            #     mime="application/pdf",
            #     use_container_width=True,
            # )
            if st.session_state.transposed_pdf:
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

            # Download button for Nashville version
            # st.download_button(
            #     label="📥 Download Nashville PDF",
            #     data=open(f"{song_title}_nashville.pdf", "rb").read(),
            #     file_name=f"{song_title}_nashville.pdf",
            #     mime="application/pdf",
            #     use_container_width=True,
            # )
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

elif tab == "Settings":
    st.subheader("Settings")
    st.write("Configure your transposition preferences here.")
    # Add settings options if needed

elif tab == "Help":
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
