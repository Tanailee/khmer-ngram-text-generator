from pathlib import Path
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile


PROJECT_DIR = Path(__file__).resolve().parent
REPORT_MD = PROJECT_DIR / "report.md"
DOCX_PATH = PROJECT_DIR / "NLP_Mini_Project_1_Report.docx"


def paragraph(text, style=None):
    style_xml = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ""
    runs = []
    for part in text.split("`"):
        if part in {"<NUM>", "<UNK>", "<s>", "</s>"}:
            runs.append(
                f"<w:r><w:rPr><w:rStyle w:val=\"Code\"/></w:rPr><w:t>{escape(part)}</w:t></w:r>"
            )
        else:
            runs.append(f"<w:r><w:t xml:space=\"preserve\">{escape(part)}</w:t></w:r>")
    return f"<w:p>{style_xml}{''.join(runs)}</w:p>"


def table(rows):
    xml = [
        "<w:tbl>",
        "<w:tblPr><w:tblStyle w:val=\"TableGrid\"/><w:tblW w:w=\"0\" w:type=\"auto\"/></w:tblPr>",
    ]
    for row in rows:
        xml.append("<w:tr>")
        for cell in row:
            xml.append(f"<w:tc><w:p><w:r><w:t>{escape(cell.strip())}</w:t></w:r></w:p></w:tc>")
        xml.append("</w:tr>")
    xml.append("</w:tbl>")
    return "".join(xml)


def markdown_to_docx_body(markdown: str):
    body = []
    lines = markdown.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith("# "):
            body.append(paragraph(line[2:], "Title"))
        elif line.startswith("## "):
            body.append(paragraph(line[3:], "Heading1"))
        elif line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [cell for cell in lines[i].strip().strip("|").split("|")]
                if not all(set(cell.strip()) <= {"-", ":"} for cell in cells):
                    rows.append(cells)
                i += 1
            body.append(table(rows))
            continue
        elif line.startswith("**") and line.endswith("**"):
            body.append(paragraph(line.replace("**", ""), "Heading2"))
        else:
            body.append(paragraph(line))
        i += 1
    return "\n".join(body)


def build_docx():
    body = markdown_to_docx_body(REPORT_MD.read_text(encoding="utf-8"))
    document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    {body}
    <w:sectPr>
      <w:pgSz w:w="11906" w:h="16838"/>
      <w:pgMar w:top="720" w:right="720" w:bottom="720" w:left="720"/>
    </w:sectPr>
  </w:body>
</w:document>"""

    styles_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:style w:type="paragraph" w:default="1" w:styleId="Normal">
    <w:name w:val="Normal"/>
    <w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:cs="Khmer OS Siemreap"/><w:sz w:val="22"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Title">
    <w:name w:val="Title"/><w:basedOn w:val="Normal"/>
    <w:rPr><w:b/><w:sz w:val="32"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading1">
    <w:name w:val="heading 1"/><w:basedOn w:val="Normal"/>
    <w:pPr><w:spacing w:before="180" w:after="80"/></w:pPr>
    <w:rPr><w:b/><w:sz w:val="26"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading2">
    <w:name w:val="heading 2"/><w:basedOn w:val="Normal"/>
    <w:rPr><w:b/><w:sz w:val="23"/></w:rPr>
  </w:style>
  <w:style w:type="character" w:styleId="Code">
    <w:name w:val="Code"/>
    <w:rPr><w:rFonts w:ascii="Consolas" w:hAnsi="Consolas"/><w:sz w:val="20"/></w:rPr>
  </w:style>
  <w:style w:type="table" w:styleId="TableGrid">
    <w:name w:val="Table Grid"/>
    <w:tblPr><w:tblBorders>
      <w:top w:val="single" w:sz="4"/><w:left w:val="single" w:sz="4"/>
      <w:bottom w:val="single" w:sz="4"/><w:right w:val="single" w:sz="4"/>
      <w:insideH w:val="single" w:sz="4"/><w:insideV w:val="single" w:sz="4"/>
    </w:tblBorders></w:tblPr>
  </w:style>
</w:styles>"""

    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>"""

    rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

    doc_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>"""

    output_path = DOCX_PATH
    try:
        docx_file = ZipFile(output_path, "w", ZIP_DEFLATED)
    except PermissionError:
        output_path = PROJECT_DIR / "NLP_Mini_Project_1_Report_RESTORED.docx"
        docx_file = ZipFile(output_path, "w", ZIP_DEFLATED)

    with docx_file as docx:
        docx.writestr("[Content_Types].xml", content_types)
        docx.writestr("_rels/.rels", rels)
        docx.writestr("word/_rels/document.xml.rels", doc_rels)
        docx.writestr("word/document.xml", document_xml)
        docx.writestr("word/styles.xml", styles_xml)
    return output_path


if __name__ == "__main__":
    print(build_docx())
