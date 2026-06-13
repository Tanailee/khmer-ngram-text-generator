from pathlib import Path
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile


PROJECT_DIR = Path(__file__).resolve().parent
DOCX_PATH = PROJECT_DIR / "NLP_Mini_Project_1_Notebook_Explanation_Guide.docx"
PDF_PATH = PROJECT_DIR / "NLP_Mini_Project_1_Notebook_Explanation_Guide.pdf"


def run(text, bold=False, italic=False, code=False):
    props = []
    if bold:
        props.append("<w:b/>")
    if italic:
        props.append("<w:i/>")
    if code:
        props.append('<w:rStyle w:val="Code"/>')
    props_xml = f"<w:rPr>{''.join(props)}</w:rPr>" if props else ""
    return f'<w:r>{props_xml}<w:t xml:space="preserve">{escape(str(text))}</w:t></w:r>'


def paragraph(text="", style=None, bold=False):
    style_xml = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ""
    return f"<w:p>{style_xml}{run(text, bold=bold)}</w:p>"


def bullets(items):
    xml = []
    for item in items:
        xml.append(
            '<w:p><w:pPr><w:ind w:left="360" w:hanging="180"/></w:pPr>'
            + run("• ", bold=True)
            + run(item)
            + "</w:p>"
        )
    return "\n".join(xml)


def code_block(text):
    xml = []
    for line in str(text).splitlines():
        xml.append(f'<w:p><w:pPr><w:pStyle w:val="CodePara"/></w:pPr>{run(line, code=True)}</w:p>')
    return "\n".join(xml)


def table(rows):
    xml = [
        "<w:tbl>",
        '<w:tblPr><w:tblStyle w:val="TableGrid"/><w:tblW w:w="0" w:type="auto"/></w:tblPr>',
    ]
    for row_index, row in enumerate(rows):
        xml.append("<w:tr>")
        for cell in row:
            shading = '<w:shd w:fill="EAF2F8"/>' if row_index == 0 else ""
            xml.append(
                f"<w:tc><w:tcPr>{shading}</w:tcPr>"
                f"<w:p>{run(cell, bold=(row_index == 0))}</w:p></w:tc>"
            )
        xml.append("</w:tr>")
    xml.append("</w:tbl>")
    return "\n".join(xml)


def section(title, body_parts):
    return "\n".join([paragraph(title, "Heading1"), *body_parts])


def build_body():
    parts = [
        paragraph("NLP Mini Project 1 Notebook Explanation Guide", "Title"),
        paragraph("Text Generation with 4-gram Language Models"),
        paragraph("Notebook: C:\\Users\\MSI\\Documents\\nlp_mini_project_1\\NLP_Mini_Project_1_Text_Generation.ipynb"),
        paragraph("Corpus: Khmer Wikipedia article about ប្រាសាទ អង្គរវត្ត"),
        paragraph("Purpose: This guide explains what each notebook section/cell does and how to interpret the results."),
        section(
            "1. Project Overview",
            [
                paragraph(
                    "The notebook completes the NLP assignment using one corpus from Khmer Wikipedia. It builds two 4-gram language models, evaluates them with perplexity, and demonstrates text generation."
                ),
                bullets(
                    [
                        "LM1 is an unsmoothed backoff 4-gram language model.",
                        "LM2 is an interpolated 4-gram language model using add-k smoothing.",
                        "The corpus is split into 70% training, 10% validation, and 20% testing.",
                        "Vocabulary is limited, and rare/out-of-vocabulary tokens are replaced with <UNK> as required.",
                    ]
                ),
            ],
        ),
        section(
            "2. Cell-by-Cell Explanation",
            [
                table(
                    [
                        ["Notebook Section", "What the Code Does", "Why It Matters"],
                        [
                            "Title and Assignment Tasks",
                            "Introduces the project, corpus, and required assignment tasks.",
                            "Shows the notebook is aligned with the project instruction.",
                        ],
                        [
                            "Import Libraries and Set URL",
                            "Imports math, random, re, pandas, Counter/defaultdict, requests, and BeautifulSoup. Stores the Angkor Wat Wikipedia URL.",
                            "Prepares tools for scraping, preprocessing, counting n-grams, evaluation, and result tables.",
                        ],
                        [
                            "Load Corpus",
                            "Defines FALLBACK_CORPUS and fetch_wikipedia_text(). The function tries to scrape the Wikipedia page and falls back to stored text if internet is unavailable.",
                            "Makes the notebook self-contained and reliable for presentation/grading.",
                        ],
                        [
                            "Preprocess, Tokenize, and Split",
                            "Removes bracket references, separates punctuation, normalizes spaces, tokenizes with split(), then splits tokens into train/validation/test.",
                            "Creates clean token sequences for language modeling while following the assignment tokenizer option.",
                        ],
                        [
                            "Vocabulary Limiting",
                            "Builds a vocabulary of the most frequent training tokens and replaces other tokens with <UNK>.",
                            "Directly satisfies the assignment requirement to limit vocabulary and use <UNK>.",
                        ],
                        [
                            "N-gram Counting",
                            "Counts unigrams, bigrams, trigrams, and 4-grams, plus context counts and possible next-token followers.",
                            "Provides the statistics needed for probability calculation and generation.",
                        ],
                        [
                            "LM1 Backoff Model",
                            "Tries 4-gram probability first; if unseen, backs off to 3-gram, 2-gram, then unigram.",
                            "Handles unseen higher-order contexts without smoothing.",
                        ],
                        [
                            "LM2 Interpolation Model",
                            "Combines unigram, bigram, trigram, and 4-gram probabilities with lambda weights and add-k smoothing.",
                            "Tests a smoother model that can assign probability to unseen n-grams.",
                        ],
                        [
                            "Perplexity and Generate Functions",
                            "Computes perplexity and generates text token-by-token from a seed phrase.",
                            "Supports the evaluation and text generator requirements.",
                        ],
                        [
                            "Train and Tune Models",
                            "Trains LM1 and searches several lambda/k combinations for LM2 using validation perplexity.",
                            "Uses validation data to choose hyperparameters as required.",
                        ],
                        [
                            "Test Evaluation Results",
                            "Evaluates both models on the test set and displays a comparison table.",
                            "Shows which model predicts unseen test text better.",
                        ],
                        [
                            "Vocabulary Size Experiment",
                            "Compares vocabulary caps of 50, 100, and 150.",
                            "Adds deeper analysis of how vocabulary size affects <UNK> and perplexity.",
                        ],
                        [
                            "Text Generation Examples",
                            "Generates text from several seed phrases: អង្គរវត្ត, ប្រាសាទ, and ស្ថាបត្យកម្ម.",
                            "Demonstrates the text generator requirement with multiple examples.",
                        ],
                        [
                            "Interactive Demo UI",
                            "Provides a text box, model selector, length slider, and generate button.",
                            "Makes the project easier to present live.",
                        ],
                        [
                            "Conclusion",
                            "Summarizes model comparison, limitations, and future improvements.",
                            "Shows understanding beyond simply running code.",
                        ],
                    ]
                )
            ],
        ),
        section(
            "3. Main Result Explanation",
            [
                table(
                    [
                        ["Metric", "Value", "Meaning"],
                        ["Corpus characters", "8,711", "Amount of raw article text loaded from the Angkor Wat article."],
                        ["Total tokens", "572", "Number of tokens after preprocessing and split-based tokenization."],
                        ["Training tokens", "400", "70% of the corpus used to learn n-gram counts."],
                        ["Validation tokens", "57", "10% used to choose lambda and k for LM2."],
                        ["Testing tokens", "115", "20% used for final model evaluation."],
                        ["Vocabulary size", "100", "Maximum vocabulary size used in the main experiment."],
                        ["Validation <UNK>", "37", "Number of validation tokens outside the training vocabulary."],
                        ["Test <UNK>", "91", "Number of test tokens outside the training vocabulary."],
                    ]
                ),
                paragraph(
                    "The high number of <UNK> tokens shows that many words in validation/testing were not among the most frequent training tokens. This is expected because the corpus is small and the vocabulary is limited as required by the assignment."
                ),
            ],
        ),
        section(
            "4. Model Comparison Result",
            [
                table(
                    [
                        ["Model", "Method", "Best Parameters", "Validation Perplexity", "Test Perplexity"],
                        ["LM1", "Unsmoothed backoff 4-gram", "No lambda/k", "-", "2.6255"],
                        ["LM2", "Interpolation + add-k smoothing", "lambdas=(0.4, 0.3, 0.2, 0.1), k=0.01", "6.3922", "3.7461"],
                    ]
                ),
                paragraph(
                    "Interpretation: lower perplexity means better next-token prediction. LM1 has lower test perplexity than LM2, so LM1 performs better in this experiment."
                ),
                paragraph(
                    "Reason: the corpus is small, so LM1 can benefit from exact local patterns. LM2 is smoother and more flexible, but it spreads probability across more vocabulary items, which can reduce accuracy on this small test set."
                ),
            ],
        ),
        section(
            "5. Vocabulary Size Experiment",
            [
                table(
                    [
                        ["Vocabulary Cap", "Actual Vocab", "Validation <UNK>", "Test <UNK>", "LM1 Test PP", "LM2 Test PP", "Best k"],
                        ["50", "50", "38", "91", "2.4669", "3.3655", "0.01"],
                        ["100", "100", "37", "91", "2.6255", "3.7461", "0.01"],
                        ["150", "150", "37", "91", "2.7391", "4.2633", "0.01"],
                    ]
                ),
                paragraph(
                    "Interpretation: a smaller vocabulary creates more <UNK> tokens, while a larger vocabulary keeps more words but can make n-gram counts more sparse. In this experiment, vocabulary cap 50 gives the lowest perplexity, but cap 100 is a reasonable main choice because it preserves more real vocabulary while still keeping the model simple."
                ),
            ],
        ),
        section(
            "6. Text Generation Result Explanation",
            [
                paragraph("The generator starts with a seed phrase and repeatedly predicts the next token using the selected language model."),
                table(
                    [
                        ["Seed", "LM1 Behavior", "LM2 Behavior"],
                        [
                            "អង្គរវត្ត",
                            "Shorter and more pattern-based; often follows phrases seen in the corpus.",
                            "More varied, but can include more <UNK> and less readable transitions.",
                        ],
                        [
                            "ប្រាសាទ",
                            "Produces a clearer sentence about Angkor Wat as a temple.",
                            "Produces a longer mixed sentence with historical and source terms.",
                        ],
                        [
                            "ស្ថាបត្យកម្ម",
                            "Uses corpus phrases related to architecture when context is found.",
                            "Can be more random because interpolation samples from more possible tokens.",
                        ],
                    ]
                ),
                paragraph(
                    "For live demonstration, use LM1 Backoff with length 20-30. Longer output is possible, but it becomes less readable because this is a simple n-gram model trained on a small corpus."
                ),
            ],
        ),
        section(
            "7. Why <UNK> Appears",
            [
                paragraph(
                    "<UNK> appears because the assignment requires limiting vocabulary size and replacing the remaining tokens with <UNK>. It is not an error. It shows that rare or unseen tokens are being handled according to the project instruction."
                ),
                code_block("Limit the vocabulary size and replace the rest of the tokens as <UNK>."),
            ],
        ),
        section(
            "8. Limitations and Future Improvement",
            [
                bullets(
                    [
                        "Khmer tokenization with split() is simple but not ideal because Khmer word boundaries are not always separated by spaces.",
                        "The corpus is small, so generated text cannot be as natural as modern neural language models.",
                        "Some English words and source labels remain because they are present in the Wikipedia article.",
                        "Future improvement: use a Khmer word segmentation tool and a larger Khmer corpus.",
                    ]
                )
            ],
        ),
        section(
            "9. Short Presentation Script",
            [
                paragraph(
                    "This notebook builds two 4-gram language models using the Khmer Wikipedia article about Angkor Wat. I cleaned and tokenized the text, split it into training, validation, and testing sets, limited the vocabulary, and replaced rare tokens with <UNK>. LM1 uses backoff, while LM2 uses interpolation with add-k smoothing. I used the validation set to choose lambda and k for LM2, then evaluated both models on the test set using perplexity. LM1 achieved lower test perplexity, so it performed better in this experiment. The generator demo shows how the trained model predicts new text from a seed phrase."
                )
            ],
        ),
    ]
    return "\n".join(parts)


def build_docx():
    document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    {build_body()}
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
    <w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:cs="Noto Sans Khmer"/><w:sz w:val="21"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Title">
    <w:name w:val="Title"/><w:basedOn w:val="Normal"/>
    <w:pPr><w:spacing w:after="160"/></w:pPr>
    <w:rPr><w:b/><w:sz w:val="34"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading1">
    <w:name w:val="heading 1"/><w:basedOn w:val="Normal"/>
    <w:pPr><w:spacing w:before="220" w:after="100"/></w:pPr>
    <w:rPr><w:b/><w:color w:val="1F4E79"/><w:sz w:val="26"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="CodePara">
    <w:name w:val="CodePara"/><w:basedOn w:val="Normal"/>
    <w:pPr><w:spacing w:before="60" w:after="60"/></w:pPr>
    <w:rPr><w:rFonts w:ascii="Consolas" w:hAnsi="Consolas"/><w:sz w:val="19"/></w:rPr>
  </w:style>
  <w:style w:type="character" w:styleId="Code">
    <w:name w:val="Code"/>
    <w:rPr><w:rFonts w:ascii="Consolas" w:hAnsi="Consolas"/><w:sz w:val="19"/></w:rPr>
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

    with ZipFile(DOCX_PATH, "w", ZIP_DEFLATED) as docx:
        docx.writestr("[Content_Types].xml", content_types)
        docx.writestr("_rels/.rels", rels)
        docx.writestr("word/_rels/document.xml.rels", doc_rels)
        docx.writestr("word/document.xml", document_xml)
        docx.writestr("word/styles.xml", styles_xml)


def convert_to_pdf():
    import win32com.client

    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    try:
        doc = word.Documents.Open(str(DOCX_PATH))
        doc.SaveAs(str(PDF_PATH), FileFormat=17)
        doc.Close(False)
    finally:
        word.Quit()


if __name__ == "__main__":
    build_docx()
    convert_to_pdf()
    print(PDF_PATH)
