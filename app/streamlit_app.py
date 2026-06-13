from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from khmer_ngram import build_artifacts, clean_for_reading, generate, top_next_words


CORPUS_PATH = ROOT / "data" / "combined_angkor_corpus.txt"


st.set_page_config(
    page_title="Khmer 4-Gram Text Generator",
    page_icon="📘",
    layout="wide",
)


@st.cache_resource(show_spinner="Training 4-gram models...")
def load_models(vocab_cap: int):
    return build_artifacts(CORPUS_PATH, vocab_cap=vocab_cap)


def probability_table(artifacts, seed_text: str, model_name: str, limit: int):
    model = artifacts.backoff_model if model_name == "LM1 Backoff" else artifacts.interpolation_model
    rows = top_next_words(model, seed_text, artifacts.vocab, limit=limit)
    return pd.DataFrame(rows, columns=["Candidate next token", "Probability"])


st.markdown(
    """
    <style>
    .block-container { padding-top: 1.4rem; }
    .khmer-box {
        border: 1px solid #d0d7de;
        border-radius: 8px;
        padding: 16px;
        background: #ffffff;
        line-height: 1.9;
        font-size: 20px;
        font-family: "Khmer OS Siemreap", "Noto Sans Khmer", Arial, sans-serif;
    }
    .note-box {
        border-left: 5px solid #1f77b4;
        border-radius: 6px;
        padding: 12px 16px;
        background: #f6f9ff;
        color: #263344;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


st.title("Khmer 4-Gram Text Generator")
st.caption("Portfolio demo: classical NLP language modeling with LM1 Backoff and LM2 Interpolation")

with st.sidebar:
    st.header("Model Settings")
    vocab_cap = st.slider("Vocabulary cap", min_value=100, max_value=1000, value=500, step=100)
    model_name = st.selectbox("Model", ["LM1 Backoff", "LM2 Interpolation"])
    length = st.slider("Generated length", min_value=5, max_value=80, value=25, step=5)
    random_seed = st.number_input("Random seed", min_value=1, max_value=999999, value=7, step=1)
    top_n = st.slider("Top next-word candidates", min_value=5, max_value=20, value=10, step=5)

artifacts = load_models(vocab_cap)

metric_cols = st.columns(5)
metric_cols[0].metric("Corpus tokens", f"{len(artifacts.tokens):,}")
metric_cols[1].metric("Vocabulary", f"{artifacts.vocab_size:,}")
metric_cols[2].metric("Tokenizer", artifacts.tokenizer_name)
metric_cols[3].metric("LM1 test PP", f"{artifacts.backoff_test_perplexity:.2f}")
metric_cols[4].metric("LM2 test PP", f"{artifacts.interpolation_test_perplexity:.2f}")

st.markdown(
    """
    <div class="note-box">
    This app demonstrates a transparent n-gram language model. It is useful for explaining
    Khmer autocomplete-style text generation, vocabulary limitation, and perplexity. It is not
    a semantic chatbot and should not be used as a factual writing assistant without human review.
    </div>
    """,
    unsafe_allow_html=True,
)

st.subheader("Generate Khmer Text")
seed_text = st.text_input("Seed text", value="ប្រាសាទ អង្គរវត្ត")

model = artifacts.backoff_model if model_name == "LM1 Backoff" else artifacts.interpolation_model

if st.button("Generate Text", type="primary"):
    raw_text = generate(
        model,
        seed_text=seed_text,
        vocab=artifacts.vocab,
        length=length,
        random_seed=int(random_seed),
    )
    clean_text = clean_for_reading(raw_text)
    unk_count = raw_text.split().count("<UNK>")

    st.markdown("#### Raw Model Output")
    st.caption(f"<UNK> count: {unk_count}")
    st.markdown(f'<div class="khmer-box">{raw_text}</div>', unsafe_allow_html=True)

    st.markdown("#### Clean Readable Output")
    st.caption("This display version removes <UNK> for easier reading.")
    st.markdown(f'<div class="khmer-box">{clean_text}</div>', unsafe_allow_html=True)

st.subheader("Next-Word Probability Explorer")
st.write(
    "This table shows which tokens the selected model considers most likely after the current seed."
)
candidate_df = probability_table(artifacts, seed_text, model_name, top_n)
st.dataframe(candidate_df, use_container_width=True, hide_index=True)

st.subheader("Project Results")
result_df = pd.DataFrame(
    [
        {
            "Model": "LM1",
            "Method": "Unsmoothed backoff 4-gram",
            "Validation perplexity": "-",
            "Test perplexity": round(artifacts.backoff_test_perplexity, 4),
        },
        {
            "Model": "LM2",
            "Method": "Interpolation + add-k smoothing",
            "Validation perplexity": round(artifacts.validation_perplexity, 4),
            "Test perplexity": round(artifacts.interpolation_test_perplexity, 4),
        },
    ]
)
st.dataframe(result_df, use_container_width=True, hide_index=True)

chart_df = pd.DataFrame(
    {
        "Model": ["LM1 Backoff", "LM2 Interpolation"],
        "Test perplexity": [
            artifacts.backoff_test_perplexity,
            artifacts.interpolation_test_perplexity,
        ],
    }
)
st.bar_chart(chart_df, x="Model", y="Test perplexity")

with st.expander("How this model works"):
    st.markdown(
        """
        - A **4-gram** model uses the previous three tokens to predict the next token.
        - **LM1 Backoff** tries the longest context first, then falls back to shorter context.
        - **LM2 Interpolation** combines unigram, bigram, trigram, and 4-gram probabilities.
        - `<UNK>` means the model predicted a rare or unseen word class.
        - Lower perplexity means the model is less confused when predicting the test text.
        """
    )

with st.expander("Portfolio positioning"):
    st.markdown(
        """
        This project is best presented as a classical NLP baseline for Khmer text generation.
        For real-life production use, the next step would be training on a larger Khmer corpus,
        adding better segmentation quality checks, and comparing this n-gram baseline with a
        neural language model.
        """
    )

