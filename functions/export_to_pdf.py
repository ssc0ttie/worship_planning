from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import blue, black
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import textwrap
import random
import time
import json
import re
from io import BytesIO
from supabase import create_client, Client
import streamlit as st
import tempfile
import os


def export_to_pdf_simple_2(
    text, filename="transposed_song.pdf", title="Transposed Song"
):
    """
    Simple PDF export with chord formatting (bold and blue).
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from reportlab.lib.colors import blue, black
        import re

        c = canvas.Canvas(filename, pagesize=letter)
        width, height = letter

        # Set up margins and line spacing
        margin = 72
        line_height = 15
        x = margin
        y = height - margin

        # Add title
        c.setFont("Helvetica-Bold", 16)
        c.drawString(x, y, title)
        y -= 30

        # Set default font for lyrics
        c.setFont("Courier", 10)
        c.setFillColor(black)

        # Regex to find chord tags
        chord_pattern = re.compile(r"\[([^\]]+)\]")

        # Split text into lines
        lines = text.split("\n")

        for line in lines:
            if y < margin + line_height:  # New page if needed
                c.showPage()
                c.setFont("Courier", 10)
                c.setFillColor(black)
                y = height - margin

            if not line.strip():  # Empty line
                y -= line_height
                continue

            # Process the line to handle chords
            current_x = x
            segments = []
            last_end = 0

            # Find all chords in the line
            for match in chord_pattern.finditer(line):
                # Text before chord
                if match.start() > last_end:
                    segments.append(
                        {"text": line[last_end : match.start()], "is_chord": False}
                    )

                # The chord itself
                segments.append(
                    {
                        "text": match.group(1),  # Chord text without brackets
                        "is_chord": True,
                    }
                )

                last_end = match.end()

            # Add remaining text after last chord
            if last_end < len(line):
                segments.append({"text": line[last_end:], "is_chord": False})

            # Draw each segment
            for segment in segments:
                if segment["is_chord"]:
                    # Draw chord in blue and bold
                    c.setFont("Courier-Bold", 10)
                    c.setFillColor(blue)
                else:
                    # Draw lyrics in regular black
                    c.setFont("Courier", 10)
                    c.setFillColor(black)

                # Draw the text segment
                c.drawString(current_x, y, segment["text"])

                # Calculate width of this segment to position next segment
                text_width = c.stringWidth(
                    segment["text"],
                    "Courier-Bold" if segment["is_chord"] else "Courier",
                    10,
                )
                current_x += text_width

            y -= line_height
            current_x = x  # Reset x position for next line

        c.save()
        print(f"PDF exported successfully: {filename}")
        return True

    except Exception as e:
        print(f"Error exporting PDF: {e}")
        return False


def export_to_pdf_compact(
    text, filename="transposed_song.pdf", title="Transposed Song"
):
    """
    Ultra-compact PDF export with minimal margins and 2 columns.
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from reportlab.lib.colors import blue, black
        import re

        c = canvas.Canvas(filename, pagesize=letter)
        width, height = letter

        # Ultra-reduced margins (very close to paper edge)
        margin = 18  # Only 0.25 inch margins
        line_height = 16
        column_width = (width - (margin * 2) - 15) / 2  # Width for each column
        column_gap = 15

        # Starting positions
        col1_x = margin
        col2_x = margin + column_width + column_gap
        current_x = col1_x
        current_col = 1

        y = height - margin

        # Title with larger font but compact spacing
        c.setFont("Helvetica-Bold", 16)
        title_width = c.stringWidth(title, "Helvetica-Bold", 16)
        title_x = (width - title_width) / 2
        c.drawString(title_x, y, title)
        y -= 24  # Compact spacing after title

        # Larger fonts for better readability
        c.setFont("Courier", 11)
        c.setFillColor(black)

        chord_pattern = re.compile(r"\[([^\]]+)\]")
        lines = text.split("\n")

        for line in lines:
            if y < margin + line_height:
                if current_col == 1:
                    current_x = col2_x
                    current_col = 2
                    y = height - margin
                else:
                    c.showPage()
                    c.setFont("Courier", 11)
                    c.setFillColor(black)
                    current_x = col1_x
                    current_col = 1
                    y = height - margin

            if not line.strip():
                y -= line_height
                continue

            segments = []
            last_end = 0

            for match in chord_pattern.finditer(line):
                if match.start() > last_end:
                    segments.append(
                        {"text": line[last_end : match.start()], "is_chord": False}
                    )

                segments.append({"text": match.group(1), "is_chord": True})

                last_end = match.end()

            if last_end < len(line):
                segments.append({"text": line[last_end:], "is_chord": False})

            segment_x = current_x
            for segment in segments:
                if segment["is_chord"]:
                    c.setFont("Courier-Bold", 11)
                    c.setFillColor(blue)
                else:
                    c.setFont("Courier", 11)
                    c.setFillColor(black)

                text_width = c.stringWidth(
                    segment["text"],
                    "Courier-Bold" if segment["is_chord"] else "Courier",
                    11,
                )

                if segment_x + text_width > current_x + column_width:
                    y -= line_height
                    segment_x = current_x

                    if y < margin + line_height:
                        if current_col == 1:
                            current_x = col2_x
                            current_col = 2
                            y = height - margin
                        else:
                            c.showPage()
                            c.setFont("Courier", 11)
                            c.setFillColor(black)
                            current_x = col1_x
                            current_col = 1
                            y = height - margin
                        segment_x = current_x

                c.drawString(segment_x, y, segment["text"])
                segment_x += text_width

            y -= line_height

        c.save()
        print(f"PDF exported successfully: {filename}")
        return True

    except Exception as e:
        print(f"Error exporting PDF: {e}")
        return False


def export_to_pdf_compact_2(text, title="Transposed Song"):
    """
    Modified to return PDF bytes instead of saving to file
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from reportlab.lib.colors import blue, black
        import re
        from io import BytesIO

        # Create PDF in memory instead of file
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)

        width, height = letter
        margin = 36  # Increased margin by 2 (from 18 to 36)
        line_height = 20  # Increased line height for larger font
        column_width = width - (
            margin * 2
        )  # Single column uses full width minus margins
        current_x = margin
        y = height - margin

        # Title - increased font size by 2 (from 16 to 18)
        c.setFont("Helvetica-Bold", 18)
        title_width = c.stringWidth(title, "Helvetica-Bold", 18)
        title_x = (width - title_width) / 2
        c.drawString(title_x, y, title)
        y -= 30  # Increased spacing after title

        # Content - increased font size by 2 (from 11 to 13)
        c.setFont("Courier", 13)
        c.setFillColor(black)

        chord_pattern = re.compile(r"\[([^\]]+)\]")
        # Clean the input text by removing any special characters that might cause issues
        # Remove various types of special characters that might appear as black squares
        cleaned_text = text
        special_chars = ["■", "●", "◆", "▲", "▼", "○", "•", "▪", "▫", "◼", "◻"]
        for char in special_chars:
            cleaned_text = cleaned_text.replace(char, "")

        lines = cleaned_text.split("\n")

        for line in lines:
            # Check if we need a new page
            if y < margin + line_height:
                c.showPage()
                c.setFont("Courier", 13)
                c.setFillColor(black)
                current_x = margin
                y = height - margin

            # Skip empty lines but maintain spacing
            if not line.strip():
                y -= line_height
                continue

            # Process chords and text
            segments = []
            last_end = 0

            for match in chord_pattern.finditer(line):
                # Add text before chord
                if match.start() > last_end:
                    segments.append(
                        {"text": line[last_end : match.start()], "is_chord": False}
                    )

                # Add chord
                segments.append({"text": match.group(1), "is_chord": True})
                last_end = match.end()

            # Add remaining text after last chord
            if last_end < len(line):
                segments.append({"text": line[last_end:], "is_chord": False})

            # Draw the segments
            segment_x = current_x
            for segment in segments:
                if segment["is_chord"]:
                    c.setFont("Courier-Bold", 13)
                    c.setFillColor(blue)
                else:
                    c.setFont("Courier", 13)
                    c.setFillColor(black)

                text_width = c.stringWidth(
                    segment["text"],
                    "Courier-Bold" if segment["is_chord"] else "Courier",
                    13,
                )

                # Handle text wrapping
                if segment_x + text_width > margin + column_width:
                    y -= line_height
                    segment_x = margin

                    # Check if we need a new page
                    if y < margin + line_height:
                        c.showPage()
                        c.setFont("Courier", 13)
                        c.setFillColor(black)
                        segment_x = margin
                        y = height - margin

                # Draw the text
                c.drawString(segment_x, y, segment["text"])
                segment_x += text_width

            # Move to next line
            y -= line_height

        c.save()

        # Get PDF bytes from buffer
        buffer.seek(0)
        pdf_bytes = buffer.getvalue()
        buffer.close()

        return pdf_bytes

    except Exception as e:
        st.error(f"Error creating PDF: {e}")
        return None


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


def export_setlist_to_pdf_compact(setlist_data, service_info, filename="setlist.pdf"):
    """Export setlist to a compact PDF format similar to export_to_pdf_compact"""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from reportlab.lib.colors import blue, black
        import re
        from io import BytesIO

        # Create PDF in memory instead of file
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)

        width, height = letter
        margin = 36
        line_height = 20
        column_width = width - (margin * 2)
        current_x = margin
        y = height - margin

        # Title
        c.setFont("Helvetica-Bold", 18)
        title = "WORSHIP SETLIST"
        title_width = c.stringWidth(title, "Helvetica-Bold", 18)
        title_x = (width - title_width) / 2
        c.drawString(title_x, y, title)
        y -= 30

        # Service info
        if service_info:
            c.setFont("Helvetica", 14)
            service_text = f"{service_info.get('name', 'Service')} - {service_info.get('date', 'Date')}"
            service_width = c.stringWidth(service_text, "Helvetica", 14)
            service_x = (width - service_width) / 2
            c.drawString(service_x, y, service_text)
            y -= 24

        # Process each song
        for i, song_data in enumerate(setlist_data):
            # Check if we need a new page
            if y < margin + (line_height * 3):  # Leave space for at least 3 lines
                c.showPage()
                c.setFont("Courier", 13)
                c.setFillColor(black)
                current_x = margin
                y = height - margin

            # Song title and key
            c.setFont("Helvetica-Bold", 14)
            key_info = (
                f" (Key: {song_data['selected_key']})"
                if song_data.get("selected_key")
                else ""
            )
            song_title = f"{i+1}. {song_data['title']}{key_info}"
            c.drawString(current_x, y, song_title)
            y -= line_height

            # Artist
            if song_data.get("artist"):
                c.setFont("Helvetica-Oblique", 10)
                artist_text = f"by {song_data['artist']}"
                c.drawString(current_x, y, artist_text)
                y -= line_height

            # Add some space before lyrics
            y -= 6

            # Lyrics with chords
            c.setFont("Courier", 13)
            c.setFillColor(black)

            # Clean and process lyrics
            lyrics = song_data["transposed_lyrics"]
            cleaned_lyrics = re.sub(
                r"[^\x00-\x7F]+", "", lyrics
            )  # Remove non-ASCII chars
            lines = cleaned_lyrics.split("\n")

            chord_pattern = re.compile(r"\[([^\]]+)\]")

            for line in lines:
                # Check if we need a new page
                if y < margin + line_height:
                    c.showPage()
                    c.setFont("Courier", 13)
                    c.setFillColor(black)
                    current_x = margin
                    y = height - margin

                # Skip empty lines but maintain spacing
                if not line.strip():
                    y -= line_height
                    continue

                # Process chords and text
                segments = []
                last_end = 0

                for match in chord_pattern.finditer(line):
                    # Add text before chord
                    if match.start() > last_end:
                        segments.append(
                            {"text": line[last_end : match.start()], "is_chord": False}
                        )

                    # Add chord
                    segments.append({"text": match.group(1), "is_chord": True})
                    last_end = match.end()

                # Add remaining text after last chord
                if last_end < len(line):
                    segments.append({"text": line[last_end:], "is_chord": False})

                # Draw the segments
                segment_x = current_x
                for segment in segments:
                    if segment["is_chord"]:
                        c.setFont("Courier-Bold", 13)
                        c.setFillColor(blue)
                    else:
                        c.setFont("Courier", 13)
                        c.setFillColor(black)

                    text_width = c.stringWidth(
                        segment["text"],
                        "Courier-Bold" if segment["is_chord"] else "Courier",
                        13,
                    )

                    # Handle text wrapping
                    if segment_x + text_width > margin + column_width:
                        y -= line_height
                        segment_x = margin

                        # Check if we need a new page
                        if y < margin + line_height:
                            c.showPage()
                            c.setFont("Courier", 13)
                            c.setFillColor(black)
                            segment_x = margin
                            y = height - margin

                    # Draw the text
                    c.drawString(segment_x, y, segment["text"])
                    segment_x += text_width

                # Move to next line
                y -= line_height

            # Add space between songs
            y -= 12

            # Add page break if not last song and running out of space
            if i < len(setlist_data) - 1 and y < margin + (line_height * 10):
                c.showPage()
                current_x = margin
                y = height - margin

        c.save()

        # Get PDF bytes from buffer
        buffer.seek(0)
        pdf_bytes = buffer.getvalue()
        buffer.close()

        return pdf_bytes

    except Exception as e:
        st.error(f"Error creating PDF: {e}")
        return None
