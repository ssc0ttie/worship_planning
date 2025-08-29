import streamlit as st
import pandas as pd
import json
import re
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import blue, black
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.units import inch
import textwrap


from supabase_client import supabase


def create_setlist(setlist_data):
    try:
        response = supabase.table("setlist").insert(setlist_data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        st.error(f"Error creating setlist: {e}")
        return None


def get_setlists():
    try:
        response = supabase.table("setlist").select("*").execute()
        return response.data
    except Exception as e:
        st.error(f"Error fetching setlists: {e}")
        return []


# --- PDF Export Functions ---
def export_setlist_to_pdf(setlist_data, service_info, filename="setlist.pdf"):
    """Export setlist to a nicely formatted PDF"""
    try:
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )

        styles = getSampleStyleSheet()
        story = []

        # Title
        title_style = ParagraphStyle(
            "TitleStyle",
            parent=styles["Title"],
            fontSize=18,
            spaceAfter=30,
            alignment=1,
        )
        story.append(Paragraph("WORSHIP SETLIST", title_style))

        # Service info
        service_style = ParagraphStyle(
            "ServiceStyle",
            parent=styles["Heading2"],
            fontSize=14,
            spaceAfter=20,
            alignment=1,
        )
        if service_info:
            service_text = f"{service_info.get('name', 'Service')} - {service_info.get('date', 'Date')}"
            story.append(Paragraph(service_text, service_style))

        # Add each song
        for i, song_data in enumerate(setlist_data):
            # Song title
            song_title_style = ParagraphStyle(
                "SongTitleStyle",
                parent=styles["Heading2"],
                fontSize=14,
                spaceAfter=6,
                spaceBefore=20 if i > 0 else 0,
            )
            key_info = (
                f" (Key: {song_data['selected_key']})"
                if song_data.get("selected_key")
                else ""
            )
            story.append(
                Paragraph(f"{i+1}. {song_data['title']}{key_info}", song_title_style)
            )

            # Artist
            if song_data.get("artist"):
                artist_style = ParagraphStyle(
                    "ArtistStyle", parent=styles["Italic"], fontSize=10, spaceAfter=12
                )
                story.append(Paragraph(f"by {song_data['artist']}", artist_style))

            # Lyrics with chords
            lyrics_style = ParagraphStyle(
                "LyricsStyle",
                parent=styles["Normal"],
                fontSize=11,
                spaceAfter=12,
                leading=14,
            )

            # Format lyrics with proper line breaks
            lyrics = song_data["transposed_lyrics"]
            lines = lyrics.split("\n")
            for line in lines:
                if line.strip():  # Only add non-empty lines
                    # Process chords to make them bold
                    formatted_line = line
                    chord_matches = re.findall(r"\[(.*?)\]", line)
                    for chord in chord_matches:
                        formatted_line = formatted_line.replace(
                            f"[{chord}]", f"<b>[{chord}]</b>"
                        )
                    story.append(Paragraph(formatted_line, lyrics_style))
                else:
                    story.append(Spacer(1, 6))

            # Add page break if not last song
            if i < len(setlist_data) - 1:
                story.append(PageBreak())

        doc.build(story)
        buffer.seek(0)
        pdf_bytes = buffer.getvalue()
        buffer.close()

        return pdf_bytes

    except Exception as e:
        st.error(f"Error creating PDF: {e}")
        return None
