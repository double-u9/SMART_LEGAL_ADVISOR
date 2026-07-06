from pdfminer.high_level import extract_text
try:
    text = extract_text(r"C:\Users\moham\Desktop\smart legal advisor\data\legal-ai-dataset\books\القانون المدني 40 لسنة 1951.pdf", maxpages=1)
    with open("output.txt", "w", encoding="utf-8") as f:
        f.write(text or "No text")
except Exception as e:
    print("Error:", e)
