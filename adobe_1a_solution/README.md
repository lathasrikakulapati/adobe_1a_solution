# 🔍 Adobe Hackathon 2025 - Round 1A: Understand Your Document

## 🧠 Challenge Overview

You're handed a PDF — but instead of just reading it, you're tasked with **extracting the document’s structure like a machine would**. Your job is to:

- Extract the **Title**
- Detect headings (`H1`, `H2`, `H3`) with corresponding **page numbers**
- Output the result in a **clean JSON format**

---

## 📂 Project Structure

```

adobe_1a_solution/
├── input/                         # Contains input PDF(s)
│   └── sample.pdf
├── output/                        # JSON outputs will be saved here
│   └── sample.json
├── process_pdfs.py               # Main Python script
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Docker configuration
└── README.md                     # This file

````

---

## 🛠️ Approach

1. **Text Extraction:**
   - Extracts all text and metadata (font size, style, position) using `PyMuPDF`.
   - Identifies the **title** heuristically as the **largest font-size text on the first page**.

2. **Heading Detection:**
   - Uses **font size and style patterns** to cluster and categorize text lines as H1, H2, or H3.
   - The logic generalizes across documents by comparing relative font sizes, not absolute values.

3. **JSON Output:**
   - Saves output in the required format:
   ```json
   {
     "title": "Sample Document Title",
     "outline": [
       { "level": "H1", "text": "Section Name", "page": 1 },
       ...
     ]
   }```

---

## 📦 Dependencies

Install dependencies locally using:

```bash
pip install -r requirements.txt
```

### `requirements.txt`

```
PyMuPDF==1.24.9
```

---

## 🐳 Docker Instructions

### 🔨 Build Docker Image

```bash
docker build --platform linux/amd64 -t pdf-processor .
```

### 🚀 Run Container

```bash
docker run --rm -v "$(pwd)/input:/app/input:ro" -v "$(pwd)/output:/app/output" --network none pdf-processor
```

(For Windows CMD):

```cmd
docker run --rm -v "%cd%/input:/app/input:ro" -v "%cd%/output:/app/output" --network none pdf-processor
```

(For PowerShell):

```powershell
docker run --rm -v "${PWD}/input:/app/input:ro" -v "${PWD}/output:/app/output" --network none pdf-processor
```

---

## ✅ Expected Output Format

Each `.pdf` in the `/app/input` directory will generate a `.json` file in `/app/output` with the following structure:

```json
{
  "title": "Understanding AI",
  "outline": [
    { "level": "H1", "text": "Introduction", "page": 1 },
    { "level": "H2", "text": "What is AI?", "page": 2 },
    { "level": "H3", "text": "History of AI", "page": 3 }
  ]
}
```

---

## ⏱️ Performance & Constraints

| Constraint           | Requirement                      |
| -------------------- | -------------------------------- |
| Execution Time       | ≤ 10 seconds for 50-page PDF     |
| Model Size (if used) | ≤ 200 MB                         |
| Offline Execution    | ✅ Required (no internet access)  |
| CPU Architecture     | amd64 (CPU-only, no GPU)         |
| RAM                  | ≤ 16 GB                          |
| Accuracy Metric      | High heading detection precision |

---

## 🧪 Testing Strategy

* ✅ Works on both **simple** and **complex** PDFs.
* ✅ Handles **multi-column**, **mixed-font**, and **heading-styled** layouts.
* ❌ No hardcoded PDF logic — completely dynamic.
* ⚠️ Font size detection may vary in scanned/image-based PDFs (OCR not included).

---

## 🔍 Example Input PDF

Place your PDF(s) in the `input/` folder. For example:

```
input/
└── sample.pdf
```

### Example Output

```
output/
└── sample.json
```

---

## 🔒 Submission Notes

* ❗ No internet access allowed inside Docker
* ❗ No API/web calls used
* ✅ Works offline
* ✅ Meets all Adobe Hackathon 1A constraints

---

## 📚 Libraries Used

* [`PyMuPDF`](https://pymupdf.readthedocs.io/en/latest/) — PDF parsing and font metadata extraction
* [`Docker`](https://www.docker.com/) — For containerizing the solution

---

## 👨‍💻 Author

Mounika Karri
[GitHub](https://github.com/mounika281005) | [LinkedIn](https://www.linkedin.com/in/mounika-karri-04a897256)
Hackathon Participant — Adobe India Hackathon 2025
