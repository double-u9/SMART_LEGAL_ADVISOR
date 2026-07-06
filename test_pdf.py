import fitz

doc = fitz.open(r"C:\Users\moham\Desktop\smart legal advisor\data\legal-ai-dataset\books_hidden\لدستور العراقي.pdf")
text = doc[10].get_text()
print(text[:500])
