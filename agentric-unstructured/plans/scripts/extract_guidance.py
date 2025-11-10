import os
import pandas as pd
from docx import Document
from pypdf import PdfReader
import shutil

# Create output directory
os.makedirs('text_outputs', exist_ok=True)

# Process each guidance document
for filename in os.listdir('Guidance documents'):
    file_path = os.path.join('Guidance documents', filename)
    output_path = os.path.join('text_outputs', f"{os.path.splitext(filename)[0]}.txt")
    
    try:
        if filename.endswith('.xlsx'):
            df = pd.read_excel(file_path, sheet_name=None)
            with open(output_path, 'w') as f:
                for sheet_name, sheet_data in df.items():
                    f.write(f"=== {sheet_name} ===\\n")
                    f.write(sheet_data.to_csv() + '\\n\\n')
                    
        elif filename.endswith('.docx'):
            doc = Document(file_path)
            with open(output_path, 'w') as f:
                f.write('=== Document Content ===\\n')
                for para in doc.paragraphs:
                    f.write(para.text + '\\n')
                    
        elif filename.endswith('.pdf'):
            reader = PdfReader(file_path)
            with open(output_path, 'w') as f:
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        f.write(text + '\\n')
                        
        # Add more formats if needed
        
    except Exception as e:
        with open(output_path, 'w') as f:
            f.write(f"Error processing file: {str(e)}")

print("Extraction complete. Text files saved in 'text_outputs' directory")
