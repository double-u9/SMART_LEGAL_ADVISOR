import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import fitz

doc = fitz.open(r"C:\Users\moham\Desktop\smart legal advisor\data\legal-ai-dataset\books\لدستور العراقي.pdf")
text = doc[10].get_text()
with open("output_pdf.txt", "w", encoding="utf-8") as f:
    f.write(text[:500])
print("Saved output to output_pdf.txt")
