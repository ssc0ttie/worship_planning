from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

import streamlit as st

from io import BytesIO
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

        # Create PDF in memory instead of file
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)

        # ... rest of your PDF generation code remains the same ...
        width, height = letter
        margin = 18
        line_height = 16
        column_width = (width - (margin * 2) - 15) / 2
        column_gap = 15
        col1_x = margin
        col2_x = margin + column_width + column_gap
        current_x = col1_x
        current_col = 1
        y = height - margin

        # Title
        c.setFont("Helvetica-Bold", 16)
        title_width = c.stringWidth(title, "Helvetica-Bold", 16)
        title_x = (width - title_width) / 2
        c.drawString(title_x, y, title)
        y -= 24

        # Content
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

        # Get PDF bytes from buffer
        buffer.seek(0)
        pdf_bytes = buffer.getvalue()
        buffer.close()

        return pdf_bytes

    except Exception as e:
        st.error(f"Error creating PDF: {e}")
        return None
