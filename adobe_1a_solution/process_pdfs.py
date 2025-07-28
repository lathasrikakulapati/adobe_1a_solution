import fitz  # PyMuPDF
import os
import json
import time
import string
import re
from collections import Counter

# ---------------------- TITLE DETECTION ----------------------

def is_title_candidate(span, page_num):
    if page_num != 1:
        return False

    text = span['text'].strip()
    if not text or not any(c.isalpha() or c.isdigit() for c in text):
        return False
    if sum(1 for c in text if c in string.punctuation) / len(text) > 0.6:
        return False
    # Multilingual character ranges (add more as needed)
    if re.fullmatch(r'[^\w\u0600-\u06FF\u0900-\u097F\u4e00-\u9fff\u0400-\u04FF\uAC00-\uD7AF]', text):
        return False
    lowered = text.lower()
    if any(s in lowered for s in ["www.", ".com", ".org", ".net"]):
        return False
    if text.isupper() and len(text.split()) <= 5:
        return False

    bbox_width = span['bbox'][2] - span['bbox'][0]
    font_size = span.get("size", 0)

    return font_size >= 10 and bbox_width >= 100

def extract_title_only(doc):
    title_spans = []
    page = doc[0]
    blocks = page.get_text("dict")["blocks"]

    for block in blocks:
        if "lines" not in block:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                if is_title_candidate(span, 1):
                    title_spans.append({
                        "text": span["text"].strip(),
                        "y": span["bbox"][1],
                        "font_size": span["size"]
                    })

    if not title_spans:
        return ""

    max_font = max(span["font_size"] for span in title_spans)
    filtered = [s for s in title_spans if s["font_size"] >= max_font - 1]
    filtered.sort(key=lambda s: s["y"])

    seen = set()
    lines = []
    for span in filtered:
        t = span["text"]
        if t not in seen:
            lines.append(t)
            seen.add(t)

    return " ".join(lines)

# ---------------------- HEADING DETECTION ----------------------

def is_heading_candidate(span, body_font_size):
    text = span["text"].strip()

    if not text or len(text) < 3:
        return False
        
    # Skip common non-heading text in multiple languages
    non_heading = ["page", "continued", "footer", "header", "copyright", "©", 
                   "página", "continuación", "pie de página", "encabezado",
                   "页", "页脚", "页眉", "版权"]
    if any(nh.lower() in text.lower() for nh in non_heading):
        return False
    
    # Skip page numbers and dates in various formats
    if re.match(r'^\d{1,2}$', text):  # Page numbers
        return False
    if re.match(r'^\d{1,2}[-/]\d{1,2}[-/]\d{2,4}$', text):  # Dates
        return False
    if re.match(r'^\d{4}[-/]\d{1,2}[-/]\d{1,2}$', text):  # YYYY-MM-DD
        return False
    
    # Skip table-like content
    if span.get("span_count_on_line", 1) > 3:
        return False
    if span.get("avg_span_width", 100) < 50:
        return False
    
    # Skip if it's just a single word that's not a numbered heading
    if len(text.split()) == 1 and not re.match(r'^\d+\.', text):
        return False
    
    # Font size must be significantly larger than body text
    if span["font_size"] <= body_font_size + 1:
        return False
        
    return True

def extract_outline(doc):
    spans_info = []
    font_sizes = []


    for page_num in range(len(doc)):
        page = doc[page_num]
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if "lines" not in block:
                continue
            for line in block["lines"]:
                spans = line["spans"]
                clean_spans = [s["text"].strip() for s in spans if s["text"].strip()]
                span_count = len(clean_spans)
                total_width = sum(s["bbox"][2] - s["bbox"][0] for s in spans)
                avg_width = total_width / span_count if span_count else 100
                for span in spans:
                    span["text"] = span["text"].strip()
                    span["font_size"] = span.get("size", 0)
                    span["y"] = span["bbox"][1]
                    span["page"] = page_num + 1
                    span["span_count_on_line"] = span_count
                    span["avg_span_width"] = avg_width
                    font_sizes.append(span["font_size"])
                    spans_info.append(span)

    if not font_sizes:
        return []

    body_font = Counter(font_sizes).most_common(1)[0][0]
    sizes_sorted = sorted(set(font_sizes), reverse=True)
    h1_font = sizes_sorted[0] if sizes_sorted else body_font + 4
    h2_font = next((s for s in sizes_sorted if s < h1_font), body_font + 2)
    h3_font = next((s for s in sizes_sorted if s < h2_font), body_font + 1)

    headings = []
    title_text = extract_title_only(doc)

    for span in spans_info:
        if not is_heading_candidate(span, body_font):
            continue
        if span["page"] == 1 and span["text"].strip() in title_text:
            continue

        size = span["font_size"]
        text = span["text"]
        level = None

        # Priority to numeric structure (works across languages)
        if re.match(r"^\d+\.\d+\s", text):     # e.g., 2.1 Intended Audience
            level = "H3"
        elif re.match(r"^\d+\s", text):        # e.g., 1 Introduction
            level = "H2"
        elif abs(size - h1_font) < 0.5:        # e.g., Table of Contents
            level = "H1"
        elif abs(size - h2_font) < 0.5:
            level = "H2"
        elif abs(size - h3_font) < 0.5:
            level = "H3"

        if level:
            headings.append({
                "level": level,
                "text": text,
                "page": span["page"]
            })

    return headings

# ---------------------- PROCESS PDF ----------------------

def process_all_pdfs(input_dir, output_dir):
    start_time = time.time()

    for file in os.listdir(input_dir):
        if file.lower().endswith(".pdf"):
            pdf_path = os.path.join(input_dir, file)
            try:
                doc = fitz.open(pdf_path)
                title = extract_title_only(doc)
                outline = extract_outline(doc)

                result = {
                    "title": title,
                    "outline": outline
                }

                output_file = os.path.join(output_dir, file.replace(".pdf", ".json"))
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=4, ensure_ascii=False)
            except Exception as e:
                print(f"Error processing {file}: {str(e)}")

    print(f"✅ Execution Time: {time.time() - start_time:.2f} seconds")

# ---------------------- MAIN ----------------------

if __name__ == "__main__":
    input_dir = "input"
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    process_all_pdfs(input_dir, output_dir)