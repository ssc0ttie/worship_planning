import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv
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

# with tab0:

#     st.subheader("Library")

#     with st.expander("Upload a Song"):
#         "test"
#         song = st.text_area("Paste Song Here")
#         converte_song = to_chordpro.ug_to_chordpro(song)
#         st.code(converte_song, language="")


with tab1:
    st.subheader("Transpose")

    transpose_steps = int(st.number_input("Transpose Step:"))
    key = st.text_input("Enter Song Key")

    song = st.text_area("Paste Song Here")

    # print("--- Original ---")
    "Original Song:"

    song
    # print("\n--- Transposed up 2 ---")

    transposed = transpose.transform_chordpro(song, transpose_steps=transpose_steps)

    nashville = transpose.transform_chordpro(song, nashville=True, key=key)

    "Transposed"
    transposed
    "NAshville"
    "\n"
    nashville

    test = st.subheader(transpose.parse_chord("Am"))

    chords = ["Am", "D"]

    test2 = st.subheader(transpose.chord_to_nashville(chords, key="G"))
