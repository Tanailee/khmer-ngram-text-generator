from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from khmer_ngram import (
    build_artifacts,
    build_artifacts_from_text,
    clean_for_reading,
    explain_lm1_prediction,
    explain_lm2_prediction,
    generate,
    top_next_words,
)


CORPUS_PATH = ROOT / "data" / "combined_angkor_corpus.txt"


st.set_page_config(
    page_title="Khmer 4-Gram Text Generator",
    page_icon="📘",
    layout="wide",
)


@st.cache_resource(show_spinner="Training models from default corpus...")
def load_default_models(vocab_cap: int):
    return build_artifacts(CORPUS_PATH, vocab_cap=vocab_cap)


@st.cache_resource(show_spinner="Training models from uploaded corpus...")
def load_uploaded_models(raw_text: str, vocab_cap: int):
    return build_artifacts_from_text(raw_text, vocab_cap=vocab_cap)


def selected_model(artifacts, model_name: str):
    return artifacts.backoff_model if model_name == "LM1 Backoff" else artifacts.interpolation_model


def make_probability_table(artifacts, seed_text: str, model_name: str, limit: int):
    rows = top_next_words(selected_model(artifacts, model_name), seed_text, artifacts.vocab, limit=limit)
    return pd.DataFrame(rows, columns=["Candidate next token", "Probability"])


def csv_download(dataframe: pd.DataFrame) -> bytes:
    return dataframe.to_csv(index=False).encode("utf-8-sig")


st.markdown(
    """
    <style>
    .block-container { padding-top: 1.2rem; }
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
        border-left: 5px solid #1960be;
        border-radius: 6px;
        padding: 12px 16px;
        background: #f6f9ff;
        color: #263344;
    }
    .risk-box {
        border-left: 5px solid #d04c56;
        border-radius: 6px;
        padding: 12px 16px;
        background: #fff7f7;
        color: #263344;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


st.title("Khmer Classical NLP Baseline")
st.caption("4-gram autocomplete-style text generation and language-model explainability")

with st.sidebar:
    st.header("Corpus")
    uploaded_file = st.file_uploader("Upload Khmer .txt corpus", type=["txt"])
    vocab_cap = st.slider("Vocabulary cap", min_value=100, max_value=1000, value=500, step=100)
    st.divider()
    st.header("Generation")
    model_name = st.selectbox("Model", ["LM1 Backoff", "LM2 Interpolation"])
    seed_text = st.text_input("Seed text", value="ប្រាសាទ អង្គរវត្ត")
    length = st.slider("Generated length", min_value=5, max_value=80, value=25, step=5)
    random_seed = st.number_input("Random seed", min_value=1, max_value=999999, value=7, step=1)
    top_n = st.slider("Top next-token candidates", min_value=5, max_value=20, value=10, step=5)

if uploaded_file is not None:
    raw_uploaded = uploaded_file.read().decode("utf-8", errors="ignore")
    artifacts = load_uploaded_models(raw_uploaded, vocab_cap)
    corpus_label = f"Uploaded corpus: {uploaded_file.name}"
else:
    artifacts = load_default_models(vocab_cap)
    corpus_label = "Default Angkor-related Khmer Wikipedia corpus"

metric_cols = st.columns(6)
metric_cols[0].metric("Corpus", "Uploaded" if uploaded_file else "Default")
metric_cols[1].metric("Tokens", f"{len(artifacts.tokens):,}")
metric_cols[2].metric("Vocabulary", f"{artifacts.vocab_size:,}")
metric_cols[3].metric("Tokenizer", artifacts.tokenizer_name)
metric_cols[4].metric("LM1 test PP", f"{artifacts.backoff_test_perplexity:.2f}")
metric_cols[5].metric("LM2 test PP", f"{artifacts.interpolation_test_perplexity:.2f}")

st.markdown(
    f"""
    <div class="note-box">
    <b>{corpus_label}</b><br>
    This project is positioned as a transparent Khmer classical NLP baseline for
    autocomplete-style text generation and model explainability. It is not a factual chatbot.
    </div>
    """,
    unsafe_allow_html=True,
)

tabs = st.tabs(
    [
        "Generate",
        "Explain Prediction",
        "Vocabulary Explorer",
        "Model Comparison",
        "Export",
        "Real-Life Positioning",
    ]
)

with tabs[0]:
    st.subheader("Generate Khmer Text")
    st.write("The model starts from your seed and predicts the next token repeatedly.")
    model = selected_model(artifacts, model_name)

    if st.button("Generate Text", type="primary"):
        raw_text = generate(
            model,
            seed_text=seed_text,
            vocab=artifacts.vocab,
            length=length,
            random_seed=int(random_seed),
        )
        clean_text = clean_for_reading(raw_text)
        st.session_state["last_raw_text"] = raw_text
        st.session_state["last_clean_text"] = clean_text

    raw_text = st.session_state.get("last_raw_text", "")
    clean_text = st.session_state.get("last_clean_text", "")
    if raw_text:
        unk_count = raw_text.split().count("<UNK>")
        st.markdown("#### Raw Model Output")
        st.caption(f"<UNK> count: {unk_count}")
        st.markdown(f'<div class="khmer-box">{raw_text}</div>', unsafe_allow_html=True)

        st.markdown("#### Clean Readable Output")
        st.caption("This display version removes <UNK> for easier reading.")
        st.markdown(f'<div class="khmer-box">{clean_text}</div>', unsafe_allow_html=True)

with tabs[1]:
    st.subheader("Explain Next-Token Prediction")
    st.write("This section connects the app output to the formulas in the notebook and presentation.")
    prob_df = make_probability_table(artifacts, seed_text, model_name, top_n)
    st.markdown("#### Top next-token candidates")
    st.dataframe(prob_df, use_container_width=True, hide_index=True)

    default_candidate = prob_df.iloc[0]["Candidate next token"] if not prob_df.empty else "<UNK>"
    candidate = st.selectbox(
        "Candidate token to explain",
        options=prob_df["Candidate next token"].tolist() if not prob_df.empty else ["<UNK>"],
        index=0,
    )

    if model_name == "LM1 Backoff":
        explanation = explain_lm1_prediction(artifacts.backoff_model, seed_text, artifacts.vocab, candidate)
        st.markdown("#### LM1 Backoff calculation")
        st.write(f"Context used by 4-gram model: `{explanation['context']}`")
        st.write(f"Candidate token: `{explanation['candidate_word']}`")
        st.write(f"Selected order: `{explanation['selected_order']}-gram`")
        st.write(f"Final probability: `{explanation['final_probability']:.8f}`")
        explanation_df = pd.DataFrame(explanation["rows"])
    else:
        explanation = explain_lm2_prediction(artifacts.interpolation_model, seed_text, artifacts.vocab, candidate)
        st.markdown("#### LM2 Interpolation calculation")
        st.write(f"Context used by 4-gram model: `{explanation['context']}`")
        st.write(f"Candidate token: `{explanation['candidate_word']}`")
        st.write(f"Final probability: `{explanation['final_probability']:.8f}`")
        st.write(
            f"Formula: `P(next)=λ1P1+λ2P2+λ3P3+λ4P4`, "
            f"lambdas=`{artifacts.best_lambdas}`, k=`{artifacts.best_k}`"
        )
        explanation_df = pd.DataFrame(explanation["rows"])

    st.dataframe(explanation_df, use_container_width=True, hide_index=True)
    st.download_button(
        "Download explanation table CSV",
        data=csv_download(explanation_df),
        file_name="prediction_explanation.csv",
        mime="text/csv",
    )

with tabs[2]:
    st.subheader("Vocabulary Explorer")
    token_counts = Counter(artifacts.train_raw)
    vocab_df = pd.DataFrame(
        [(word, token_counts[word]) for word in artifacts.vocab if word not in {"<s>", "</s>"}],
        columns=["Vocabulary token", "Training frequency"],
    ).sort_values("Training frequency", ascending=False)

    rare_tokens = [token for token in artifacts.tokens if token not in artifacts.vocab]
    rare_df = pd.DataFrame(
        Counter(rare_tokens).most_common(100),
        columns=["Token mapped to <UNK>", "Corpus frequency"],
    )

    vcols = st.columns(3)
    vcols[0].metric("Vocabulary size", f"{len(artifacts.vocab):,}")
    vcols[1].metric("Rare tokens mapped to <UNK>", f"{len(rare_tokens):,}")
    vcols[2].metric("Unique rare tokens", f"{len(set(rare_tokens)):,}")

    st.markdown("#### Top vocabulary tokens")
    st.dataframe(vocab_df.head(100), use_container_width=True, hide_index=True)
    st.markdown("#### Common rare tokens mapped to `<UNK>`")
    st.dataframe(rare_df, use_container_width=True, hide_index=True)

    st.download_button(
        "Download vocabulary CSV",
        data=csv_download(vocab_df),
        file_name="vocabulary.csv",
        mime="text/csv",
    )
    st.download_button(
        "Download rare-word table CSV",
        data=csv_download(rare_df),
        file_name="rare_words_mapped_to_unk.csv",
        mime="text/csv",
    )

with tabs[3]:
    st.subheader("Model Comparison")
    result_df = pd.DataFrame(
        [
            {
                "Model": "LM1",
                "Method": "Unsmoothed backoff 4-gram",
                "Best parameters": "No lambda/k",
                "Validation perplexity": "-",
                "Test perplexity": round(artifacts.backoff_test_perplexity, 4),
                "Strength": "Strong with repeated local phrases",
                "Weakness": "Can assign zero probability to unseen test events",
            },
            {
                "Model": "LM2",
                "Method": "Interpolation + add-k smoothing",
                "Best parameters": f"lambdas={artifacts.best_lambdas}, k={artifacts.best_k}",
                "Validation perplexity": round(artifacts.validation_perplexity, 4),
                "Test perplexity": round(artifacts.interpolation_test_perplexity, 4),
                "Strength": "Combines multiple context lengths",
                "Weakness": "Smoothing can spread probability too widely",
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
    st.markdown(
        """
        Lower perplexity is better. In the default Angkor corpus, LM1 performs better because the
        corpus contains repeated local phrases that the backoff model can exploit directly.
        """
    )

with tabs[4]:
    st.subheader("Export Results")
    raw_text = st.session_state.get("last_raw_text", "")
    clean_text = st.session_state.get("last_clean_text", "")
    prob_df = make_probability_table(artifacts, seed_text, model_name, top_n)
    summary_df = pd.DataFrame(
        [
            ["Corpus label", corpus_label],
            ["Tokenizer", artifacts.tokenizer_name],
            ["Tokens", len(artifacts.tokens)],
            ["Vocabulary size", artifacts.vocab_size],
            ["LM1 test perplexity", artifacts.backoff_test_perplexity],
            ["LM2 validation perplexity", artifacts.validation_perplexity],
            ["LM2 test perplexity", artifacts.interpolation_test_perplexity],
            ["LM2 lambdas", artifacts.best_lambdas],
            ["LM2 k", artifacts.best_k],
        ],
        columns=["Metric", "Value"],
    )
    st.download_button(
        "Download top next-token probabilities CSV",
        data=csv_download(prob_df),
        file_name="top_next_token_probabilities.csv",
        mime="text/csv",
    )
    st.download_button(
        "Download result summary CSV",
        data=csv_download(summary_df),
        file_name="model_result_summary.csv",
        mime="text/csv",
    )
    if raw_text:
        export_text = f"Raw output:\n{raw_text}\n\nClean output:\n{clean_text}\n"
        st.download_button(
            "Download generated text TXT",
            data=export_text.encode("utf-8"),
            file_name="generated_khmer_text.txt",
            mime="text/plain",
        )
    else:
        st.info("Generate text first to enable TXT export.")

with tabs[5]:
    st.subheader("Real-Life Positioning")
    st.markdown(
        """
        This project is most useful as a **transparent Khmer classical NLP baseline**.

        Good real-life uses:

        - teaching how n-gram language models work
        - showing autocomplete-style Khmer next-token prediction
        - explaining vocabulary limits and `<UNK>`
        - comparing backoff and interpolation with perplexity
        - creating a baseline before testing modern neural models
        """
    )
    st.markdown(
        """
        <div class="risk-box">
        <b>Important limitation:</b> this is not a factual chatbot. It does not understand meaning
        like a modern neural language model. Generated text should be reviewed by a human.
        </div>
        """,
        unsafe_allow_html=True,
    )

