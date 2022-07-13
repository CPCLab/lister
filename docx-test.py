from docx import Document
document = Document("spaghetti.docx")
section = document.sections[0]
header = section.header
print(header)
for paragraph in header.paragraphs:
    print(paragraph.text)