from __future__ import annotations

import math
import random
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


try:
    from khmernltk import word_tokenize as khmer_word_tokenize

    KHMER_TOKENIZER_AVAILABLE = True
except Exception:
    khmer_word_tokenize = None
    KHMER_TOKENIZER_AVAILABLE = False


SENTENCE_ENDINGS = {"។", "៕", "!", "?"}
SPECIAL_TOKENS = {"<UNK>", "<s>", "</s>"}


@dataclass
class NgramArtifacts:
    raw_text: str
    tokens: list[str]
    train_raw: list[str]
    valid_raw: list[str]
    test_raw: list[str]
    train: list[str]
    valid: list[str]
    test: list[str]
    vocab: set[str]
    backoff_model: "BackoffLM"
    interpolation_model: "InterpolationLM"
    best_lambdas: tuple[float, float, float, float]
    best_k: float
    validation_perplexity: float
    backoff_test_perplexity: float
    interpolation_test_perplexity: float
    tokenizer_name: str
    vocab_size: int


def remove_english_only_lines(text: str) -> str:
    cleaned_lines: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("ARTICLE_TITLE:"):
            continue
        if re.fullmatch(r"[A-Za-z0-9\s,:;()'\".\-/%]+", line):
            continue
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines)


def normalize_text(text: str) -> str:
    text = remove_english_only_lines(text)
    text = re.sub(r"\[[^\]]*\]", " ", text)
    text = re.sub(r"([។៕!?])", r" \1 ", text)
    text = re.sub(r"[()\[\]{}\"“”'‘’,:;–\-]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def tokenize(text: str) -> list[str]:
    text = normalize_text(text)
    if KHMER_TOKENIZER_AVAILABLE and khmer_word_tokenize is not None:
        return [token.strip() for token in khmer_word_tokenize(text) if token.strip()]
    return text.split()


def tokenize_seed(seed_text: str) -> list[str]:
    tokens = tokenize(seed_text)
    return [token for token in tokens if token not in SPECIAL_TOKENS]


def split_tokens(tokens: list[str], train_ratio: float = 0.70, valid_ratio: float = 0.10):
    n_tokens = len(tokens)
    train_end = int(n_tokens * train_ratio)
    valid_end = train_end + int(n_tokens * valid_ratio)
    return tokens[:train_end], tokens[train_end:valid_end], tokens[valid_end:]


def build_vocab(tokens: list[str], vocab_size: int) -> set[str]:
    most_common = [
        token
        for token, _ in Counter(tokens).most_common(max(0, vocab_size - len(SPECIAL_TOKENS)))
    ]
    return set(most_common) | SPECIAL_TOKENS


def replace_unk(tokens: Iterable[str], vocab: set[str]) -> list[str]:
    return [token if token in vocab else "<UNK>" for token in tokens]


def add_sentence_boundaries(tokens: list[str], n: int = 4) -> list[str]:
    output = ["<s>"] * (n - 1)
    for token in tokens:
        output.append(token)
        if token in SENTENCE_ENDINGS:
            output.extend(["</s>"] + ["<s>"] * (n - 1))
    output.append("</s>")
    return output


def count_ngrams(tokens: list[str], max_order: int = 4):
    counts = {order: Counter() for order in range(1, max_order + 1)}
    context_counts = {order: Counter() for order in range(2, max_order + 1)}
    followers = {order: defaultdict(list) for order in range(2, max_order + 1)}

    for order in range(1, max_order + 1):
        for i in range(len(tokens) - order + 1):
            gram = tuple(tokens[i : i + order])
            counts[order][gram] += 1
            if order > 1:
                context_counts[order][gram[:-1]] += 1

    for order in range(2, max_order + 1):
        seen = defaultdict(set)
        for gram, count in counts[order].items():
            context, token = gram[:-1], gram[-1]
            if token not in seen[context]:
                followers[order][context].append((token, count))
                seen[context].add(token)

    return counts, context_counts, followers


class BackoffLM:
    def __init__(self, tokens: list[str], vocab: set[str], max_order: int = 4):
        self.max_order = max_order
        self.vocab = sorted(vocab)
        self.counts, self.context_counts, self.followers = count_ngrams(tokens, max_order)
        self.unigram_total = sum(self.counts[1].values())

    def probability(self, context: tuple[str, ...], token: str) -> float:
        for order in range(min(self.max_order, len(context) + 1), 1, -1):
            current_context = context[-(order - 1) :]
            gram = current_context + (token,)
            gram_count = self.counts[order].get(gram, 0)
            context_count = self.context_counts[order].get(current_context, 0)
            if gram_count > 0 and context_count > 0:
                return gram_count / context_count
        return self.counts[1].get((token,), 0) / self.unigram_total if self.unigram_total else 0.0

    def next_token(self, context: tuple[str, ...], rng: random.Random) -> str:
        for order in range(min(self.max_order, len(context) + 1), 1, -1):
            current_context = context[-(order - 1) :]
            choices = self.followers[order].get(current_context)
            if choices:
                tokens, weights = zip(*choices)
                return rng.choices(tokens, weights=weights, k=1)[0]
        tokens, weights = zip(*self.counts[1].items())
        return rng.choices([token[0] for token in tokens], weights=weights, k=1)[0]


class InterpolationLM:
    def __init__(
        self,
        tokens: list[str],
        vocab: set[str],
        lambdas: tuple[float, float, float, float],
        k: float,
        max_order: int = 4,
    ):
        self.max_order = max_order
        self.vocab = sorted(vocab)
        self.lambdas = lambdas
        self.k = k
        self.counts, self.context_counts, self.followers = count_ngrams(tokens, max_order)
        self.unigram_total = sum(self.counts[1].values())

    def order_probability(self, order: int, context: tuple[str, ...], token: str) -> float:
        vocab_n = len(self.vocab)
        if order == 1:
            return (self.counts[1].get((token,), 0) + self.k) / (
                self.unigram_total + self.k * vocab_n
            )
        current_context = context[-(order - 1) :]
        gram = current_context + (token,)
        return (self.counts[order].get(gram, 0) + self.k) / (
            self.context_counts[order].get(current_context, 0) + self.k * vocab_n
        )

    def probability(self, context: tuple[str, ...], token: str) -> float:
        return sum(
            self.lambdas[order - 1] * self.order_probability(order, context, token)
            for order in range(1, self.max_order + 1)
        )

    def next_token(self, context: tuple[str, ...], rng: random.Random) -> str:
        weights = [self.probability(context, token) for token in self.vocab]
        return rng.choices(self.vocab, weights=weights, k=1)[0]


def perplexity(model, tokens: list[str], max_order: int = 4) -> float:
    bounded_tokens = add_sentence_boundaries(tokens, max_order)
    log_prob = 0.0
    evaluated = 0
    for i in range(max_order - 1, len(bounded_tokens)):
        token = bounded_tokens[i]
        if token == "<s>":
            continue
        context = tuple(bounded_tokens[i - (max_order - 1) : i])
        probability = model.probability(context, token)
        if probability <= 0.0:
            return float("inf")
        log_prob += math.log(probability)
        evaluated += 1
    return math.exp(-log_prob / max(1, evaluated))


def clean_for_reading(text: str) -> str:
    text = text.replace("<UNK>", "")
    text = re.sub(r"\s+", " ", text)
    return text.replace(" ។", "។").replace(" ៕", "៕").strip()


def generate(model, seed_text: str, vocab: set[str], length: int = 30, random_seed: int = 7) -> str:
    rng = random.Random(random_seed)
    seed = replace_unk(tokenize_seed(seed_text), vocab)
    if not seed:
        seed = ["<s>"]
    context = tuple((["<s>", "<s>", "<s>"] + seed)[-3:])
    generated = [token for token in seed if token != "<s>"]
    for _ in range(length):
        token = model.next_token(context, rng)
        if token == "</s>":
            break
        if token != "<s>":
            generated.append(token)
        context = tuple((list(context) + [token])[-3:])
    return " ".join(generated).replace(" ។", "។").replace(" ៕", "៕")


def top_next_words(model, seed_text: str, vocab: set[str], limit: int = 10):
    seed = replace_unk(tokenize_seed(seed_text), vocab)
    context = tuple((["<s>", "<s>", "<s>"] + seed)[-3:])
    rows = []
    for token in model.vocab:
        if token in {"<s>", "</s>"}:
            continue
        rows.append((token, model.probability(context, token)))
    return sorted(rows, key=lambda item: item[1], reverse=True)[:limit]


def tune_interpolation(
    train: list[str],
    valid: list[str],
    vocab: set[str],
    lambda_grid: list[tuple[float, float, float, float]] | None = None,
    k_grid: list[float] | None = None,
):
    lambda_grid = lambda_grid or [
        (0.40, 0.30, 0.20, 0.10),
        (0.35, 0.30, 0.20, 0.15),
        (0.30, 0.30, 0.25, 0.15),
        (0.25, 0.25, 0.25, 0.25),
        (0.20, 0.30, 0.30, 0.20),
        (0.15, 0.25, 0.30, 0.30),
        (0.10, 0.20, 0.30, 0.40),
        (0.05, 0.15, 0.30, 0.50),
        (0.10, 0.10, 0.30, 0.50),
        (0.05, 0.10, 0.25, 0.60),
    ]
    k_grid = k_grid or [0.001, 0.005, 0.01, 0.02, 0.05, 0.10]

    best: dict | None = None
    experiments = []
    for lambdas in lambda_grid:
        for k in k_grid:
            model = InterpolationLM(train, vocab, lambdas=lambdas, k=k)
            pp = perplexity(model, valid)
            row = {"lambdas": lambdas, "k": k, "validation_perplexity": pp}
            experiments.append(row)
            if best is None or pp < best["validation_perplexity"]:
                best = row
    assert best is not None
    return best, experiments


def build_artifacts(corpus_path: Path, vocab_cap: int = 500) -> NgramArtifacts:
    raw_text = corpus_path.read_text(encoding="utf-8")
    tokens = tokenize(raw_text)
    train_raw, valid_raw, test_raw = split_tokens(tokens)
    vocab_size = min(vocab_cap, max(50, len(set(train_raw))))
    vocab = build_vocab(train_raw, vocab_size)

    train = add_sentence_boundaries(replace_unk(train_raw, vocab))
    valid = replace_unk(valid_raw, vocab)
    test = replace_unk(test_raw, vocab)

    backoff_model = BackoffLM(train, vocab)
    best, _ = tune_interpolation(train, valid, vocab)
    interpolation_model = InterpolationLM(
        train,
        vocab,
        lambdas=best["lambdas"],
        k=best["k"],
    )

    return NgramArtifacts(
        raw_text=raw_text,
        tokens=tokens,
        train_raw=train_raw,
        valid_raw=valid_raw,
        test_raw=test_raw,
        train=train,
        valid=valid,
        test=test,
        vocab=vocab,
        backoff_model=backoff_model,
        interpolation_model=interpolation_model,
        best_lambdas=best["lambdas"],
        best_k=best["k"],
        validation_perplexity=best["validation_perplexity"],
        backoff_test_perplexity=perplexity(backoff_model, test),
        interpolation_test_perplexity=perplexity(interpolation_model, test),
        tokenizer_name="khmernltk.word_tokenize" if KHMER_TOKENIZER_AVAILABLE else "Python split() fallback",
        vocab_size=len(vocab),
    )

