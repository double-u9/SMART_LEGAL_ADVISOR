import fitz
import os

pdf_path = r"C:\Users\moham\Desktop\smart legal advisor\data\legal-ai-dataset\books_hidden\القانون المدني 40 لسنة 1951.pdf"
out_path = r"C:\Users\moham\Desktop\smart legal advisor\data\legal-ai-dataset\books\القانون المدني 40 لسنة 1951.txt"

doc = fitz.open(pdf_path)
full_text = []
for i in range(len(doc)):
    page = doc[i]
    text = page.get_text()
    if text:
        full_text.append(text)

with open(out_path, "w", encoding="utf-8") as f:
    f.write("\n\n".join(full_text))

print(f"Extracted {len(full_text)} pages to {out_path}")
