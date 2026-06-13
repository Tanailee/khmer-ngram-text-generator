# Khmer 4-Gram Text Generator

Portfolio version of an NLP mini project for Khmer text generation using classical n-gram language models.

The project trains and compares two 4-gram language models on Khmer Wikipedia articles related to Angkor Wat:

- **LM1:** unsmoothed backoff 4-gram language model
- **LM2:** interpolation 4-gram language model with add-k smoothing

It includes a Jupyter notebook, reports, presentation files, reusable Python model code, and a Streamlit app for interactive demonstration.

## Portfolio App

Run the Streamlit demo:

```powershell
cd C:\Users\MSI\Documents\nlp_mini_project_1
python -m streamlit run app\streamlit_app.py
```

The app supports:

- Khmer seed-based text generation
- LM1 Backoff vs LM2 Interpolation selection
- raw output with `<UNK>`
- clean readable output
- top next-token probability table
- model perplexity comparison
- vocabulary cap control

## Project Results

Final project settings:

| Item | Value |
|---|---:|
| Corpus topic | Angkor Wat and related Khmer articles |
| Articles | 5 |
| Tokens after preprocessing | 19,681 |
| Train / validation / test split | 70% / 10% / 20% |
| Vocabulary cap | 500 |
| Best LM2 lambdas | `(0.4, 0.3, 0.2, 0.1)` |
| Best LM2 k | `0.001` |

Final evaluation:

| Model | Method | Test perplexity |
|---|---|---:|
| LM1 | Unsmoothed backoff 4-gram | 27.2196 |
| LM2 | Interpolation + add-k smoothing | 45.7879 |

Lower perplexity is better. In this corpus, LM1 Backoff performs better than LM2 Interpolation.

## How It Works

A 4-gram language model predicts the next token using the previous three tokens.

Example:

```text
ប្រាសាទ អង្គរវត្ត មាន -> កម្ពស់
```

LM1 Backoff first tries the longest context. If it cannot find enough evidence, it backs off to a shorter context.

LM2 Interpolation combines unigram, bigram, trigram, and 4-gram probabilities:

```text
P(next) = λ1P1 + λ2P2 + λ3P3 + λ4P4
```

`<UNK>` means unknown token. It represents rare or unseen words outside the selected vocabulary.

## Repository Structure

```text
nlp_mini_project_1/
├── app/
│   └── streamlit_app.py
├── data/
│   └── combined_angkor_corpus.txt
├── report_assets/
│   ├── human_dataset_split.png
│   ├── human_model_perplexity.png
│   └── human_vocab_perplexity.png
├── src/
│   └── khmer_ngram/
│       ├── __init__.py
│       └── model.py
├── NLP_Mini_Project_1_Text_Generation.ipynb
├── NLP_Mini_Project_1_Final_Report_Human_Style.docx
├── NLP_Mini_Project_1_Canva_Style_Final_Presentation.pptx
├── requirements.txt
└── README.md
```

## Install

```powershell
cd C:\Users\MSI\Documents\nlp_mini_project_1
python -m pip install -r requirements.txt
```

## GitHub Push

Initialize and push the project:

```powershell
git init
git add .
git commit -m "Portfolio-ready Khmer n-gram text generator"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/khmer-ngram-text-generator.git
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username.

## Real-Life Use Case

This is a transparent classical NLP baseline for Khmer autocomplete-style text generation and education. It is useful for:

- demonstrating n-gram language modeling
- explaining vocabulary limitation and `<UNK>`
- comparing backoff and interpolation
- teaching perplexity evaluation

It should not be presented as a modern semantic chatbot. A production-grade system would require a much larger Khmer corpus, stronger segmentation validation, and comparison with neural language models.

