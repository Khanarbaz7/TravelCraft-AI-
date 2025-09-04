import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from utils import parse_llm_output

def export_itinerary_pdf(itinerary_text, filename="itinerary.pdf", banner_image=None):
    """
    Export itinerary (parsed JSON or raw text) into a PDF.
    Handles both structured (JSON) and free-form text.
    """
    parsed = None
    if isinstance(itinerary_text, str):
        parsed = parse_llm_output(itinerary_text)
    elif isinstance(itinerary_text, dict):
        parsed = itinerary_text
    else:
        parsed = {"raw": str(itinerary_text)}

    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    if banner_image and os.path.exists(banner_image):
        try:
            story.append(Image(banner_image, width=500, height=100))
            story.append(Spacer(1, 20))
        except Exception as e:
            print(f"⚠️ Could not load banner: {e}")

    story.append(Paragraph("✈️ Travel Planner AI - Itinerary", styles["Title"]))
    story.append(Spacer(1, 20))

    if isinstance(parsed, dict) and "day_wise_plan" in parsed:
        for day in parsed["day_wise_plan"]:
            story.append(Paragraph(f"Day {day['day']}", styles["Heading2"]))
            story.append(Paragraph(f"Morning: {day.get('morning', '')}", styles["Normal"]))
            story.append(Paragraph(f"Afternoon: {day.get('afternoon', '')}", styles["Normal"]))
            story.append(Paragraph(f"Evening: {day.get('evening', '')}", styles["Normal"]))
            story.append(Paragraph(f"Meals: {day.get('meals', '')}", styles["Normal"]))
            story.append(Paragraph(f"Estimated Cost: {day.get('est_cost', '')}", styles["Normal"]))
            story.append(Spacer(1, 12))

        
        if parsed.get("weather_summary"):
            story.append(Paragraph(f"Weather Summary: {parsed['weather_summary']}", styles["Italic"]))
        if parsed.get("top_attractions"):
            story.append(Paragraph("Top Attractions:", styles["Heading3"]))
            for att in parsed["top_attractions"]:
                story.append(Paragraph(f"• {att}", styles["Normal"]))

    else:
        raw_text = parsed.get("raw", itinerary_text)
        for line in str(raw_text).split("\n"):
            story.append(Paragraph(line, styles["Normal"]))
            story.append(Spacer(1, 6))

    doc.build(story)
    return filename
