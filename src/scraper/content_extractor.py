from typing import Dict
from readability import Document
from bs4 import BeautifulSoup

def extract_readable(html: str) -> Dict[str, str]:
  title, main_html = "", ""
  try:
    doc = Document(html)
    title = (doc.title() or "").strip()
    main_html = doc.summary() or ""
  except Exception as e:
    pass

  if not main_html:
    soup = BeautifulSoup(html, 'html.parser')
    return {
      "title": (soup.title.string or "").strip() if soup.title else "",
      "text": soup.get_text(separator="\n", strip=True),
      "html": html,
    }

  soup = BeautifulSoup(main_html, "html.parser")
  text = soup.get_text(separator="\n", strip=True)
  return {
    "title": title,
    "text": text,
    "html": main_html,
  }
  
