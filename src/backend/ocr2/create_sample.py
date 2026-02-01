from PIL import Image, ImageDraw, ImageFont
import os

def create_sample_report(path):
    img = Image.new('RGB', (800, 1000), color='white')
    d = ImageDraw.Draw(img)
    
    # Load default font (careful about font availability, fallback to default)
    try:
        # Try to load a generic font, or use default
        font = ImageFont.load_default()
        # Scale is tricky with default font, better to simply draw
    except:
        pass

    # Header
    d.text((50, 50), "City Health Laboratory", fill="black")
    d.text((50, 80), "Patient Name: John Doe", fill="black")
    d.text((50, 100), "Age: 45   Gender: Male", fill="black")
    d.text((50, 120), "Date: 2024-03-15", fill="black")
    
    # Table Header
    d.text((50, 180), "Test Name          Value    Unit    Reference Range", fill="black")
    d.line((50, 195, 750, 195), fill="black", width=2)
    
    # Rows
    y = 210
    tests = [
        ("Hemoglobin", "14.2", "g/dL", "13.0-17.0"),
        ("Total Cholesterol", "185", "mg/dL", "<200"),
        ("Glucose Fasting", "98", "mg/dL", "70-100"),
    ]
    
    for test in tests:
        # Simple spacing
        line = f"{test[0]:<20} {test[1]:<8} {test[2]:<8} {test[3]}"
        d.text((50, y), line, fill="black")
        y += 30

    img.save(path)
    print(f"Sample report created at {path}")

if __name__ == "__main__":
    create_sample_report("sample_report.png")
