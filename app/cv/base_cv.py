from docx import Document
from functools import lru_cache

@lru_cache(maxsize=1)
def load_base_cv_text(path: str = 'data/CV_Vialkov_Fullstack.docx') -> str:
    doc = Document(path)
    return '\n'.join(p.text for p in doc.paragraphs if p.text.strip())