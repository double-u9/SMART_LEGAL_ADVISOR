from pdfminer.high_level import extract_text
text = extract_text(r"C:\Users\moham\Desktop\smart legal advisor\data\legal-ai-dataset\books_hidden\لدستور العراقي.pdf")
print(text[:500])
