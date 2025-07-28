import fitz
import os
import json
import time
import string
import re
from collections import Counter

def _is_possible_heading(span_data, page_index):
    if page_index != 1:
        return False

    txt = span_data['text'].strip()
    if not txt or not any(ch.isalnum() for ch in txt):
        return False
    if sum(1 for ch in txt if ch in string.punctuation) / len(txt) > 0.6:
        return False
    if re.fullmatch(r'[^\w\u0600-\u06FF\u0900-\u097F\u4e00-\u9fff\u0400-\u04FF\uAC00-\uD7AF]', txt):
        return False
    lower_txt = txt.lower()
    if any(sub in lower_txt for sub in ["www.", ".com", ".org", ".net"]):
        return False
    if txt.isupper() and len(txt.split()) <= 5:
        return False

    width = span_data['bbox'][2] - span_data['bbox'][0]
    font_sz = span_data.get("size", 0)

    return font_sz >= 10 and width >= 100

def _extract_doc_title(pdf_obj):
    lines_with_fonts = []
    pg = pdf_obj[0]
    items = pg.get_text("dict")["blocks"]

    for itm in items:
        if "lines" not in itm:
            continue
        for ln in itm["lines"]:
            for sp in ln["spans"]:
                if _is_possible_heading(sp, 1):
                    lines_with_fonts.append({
                        "text": sp["text"].strip(),
                        "y": sp["bbox"][1],
                        "font_size": sp["size"]
                    })

    if not lines_with_fonts:
        return ""

    max_font = max(obj["font_size"] for obj in lines_with_fonts)
    cleaned = [v for v in lines_with_fonts if v["font_size"] >= max_font - 1]
    cleaned.sort(key=lambda d: d["y"])

    used = set()
    final_text = []
    for entry in cleaned:
        txt = entry["text"]
        if txt not in used:
            final_text.append(txt)
            used.add(txt)

    return " ".join(final_text)

def _is_heading_text(span_obj, base_font_size):
    content = span_obj["text"].strip()

    if not content or len(content) < 3:
        return False

    banned = ["page", "continued", "footer", "header", "copyright", "©",
              "página", "continuación", "pie de página", "encabezado",
              "页", "页脚", "页眉", "版权"]
    if any(b.lower() in content.lower() for b in banned):
        return False
    if re.match(r'^\d{1,2}$', content):
        return False
    if re.match(r'^\d{1,2}[-/]\d{1,2}[-/]\d{2,4}$', content):
        return False
    if re.match(r'^\d{4}[-/]\d{1,2}[-/]\d{1,2}$', content):
        return False
    if span_obj.get("span_count_on_line", 1) > 3:
        return False
    if span_obj.get("avg_span_width", 100) < 50:
        return False
    if len(content.split()) == 1 and not re.match(r'^\d+\.', content):
        return False
    if span_obj["font_size"] <= base_font_size + 1:
        return False

    return True

def _extract_section_headings(document):
    span_list = []
    all_fonts = []

    for pg_idx in range(len(document)):
        pg = document[pg_idx]
        blks = pg.get_text("dict")["blocks"]
        for blk in blks:
            if "lines" not in blk:
                continue
            for ln in blk["lines"]:
                spn_arr = ln["spans"]
                filtered = [s["text"].strip() for s in spn_arr if s["text"].strip()]
                total_count = len(filtered)
                combined_width = sum(s["bbox"][2] - s["bbox"][0] for s in spn_arr)
                average = combined_width / total_count if total_count else 100
                for spn in spn_arr:
                    spn["text"] = spn["text"].strip()
                    spn["font_size"] = spn.get("size", 0)
                    spn["y"] = spn["bbox"][1]
                    spn["page"] = pg_idx + 1
                    spn["span_count_on_line"] = total_count
                    spn["avg_span_width"] = average
                    all_fonts.append(spn["font_size"])
                    span_list.append(spn)

    if not all_fonts:
        return []

    base_font = Counter(all_fonts).most_common(1)[0][0]
    sorted_sizes = sorted(set(all_fonts), reverse=True)
    font_h1 = sorted_sizes[0] if sorted_sizes else base_font + 4
    font_h2 = next((f for f in sorted_sizes if f < font_h1), base_font + 2)
    font_h3 = next((f for f in sorted_sizes if f < font_h2), base_font + 1)

    extracted = []
    doc_title = _extract_doc_title(document)

    for sp in span_list:
        if not _is_heading_text(sp, base_font):
            continue
        if sp["page"] == 1 and sp["text"].strip() in doc_title:
            continue

        txt = sp["text"]
        fs = sp["font_size"]
        label = None

        if re.match(r"^\d+\.\d+\s", txt):
            label = "H3"
        elif re.match(r"^\d+\s", txt):
            label = "H2"
        elif abs(fs - font_h1) < 0.5:
            label = "H1"
        elif abs(fs - font_h2) < 0.5:
            label = "H2"
        elif abs(fs - font_h3) < 0.5:
            label = "H3"

        if label:
            extracted.append({
                "level": label,
                "text": txt,
                "page": sp["page"]
            })

    return extracted

def _batch_process_pdfs(in_dir, out_dir):
    st = time.time()

    for fname in os.listdir(in_dir):
        if fname.lower().endswith(".pdf"):
            full_path = os.path.join(in_dir, fname)
            try:
                docx = fitz.open(full_path)
                doc_title = _extract_doc_title(docx)
                doc_outline = _extract_section_headings(docx)

                parsed = {
                    "title": doc_title,
                    "outline": doc_outline
                }

                result_path = os.path.join(out_dir, fname.replace(".pdf", ".json"))
                with open(result_path, "w", encoding="utf-8") as fp:
                    json.dump(parsed, fp, indent=4, ensure_ascii=False)
            except Exception as err:
                print(f"Could not parse {fname}: {str(err)}")

    print(f"⏱ Finished in {time.time() - st:.2f}s")

if __name__ == "__main__":
    source_folder = "input"
    output_folder = "output"
    os.makedirs(output_folder, exist_ok=True)
    _batch_process_pdfs(source_folder, output_folder)
