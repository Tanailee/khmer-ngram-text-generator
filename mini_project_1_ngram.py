import argparse
import math
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import requests
from bs4 import BeautifulSoup


sys.stdout.reconfigure(encoding="utf-8")

URL = "https://km.wikipedia.org/wiki/%E1%9E%81%E1%9F%92%E1%9E%98%E1%9F%82%E1%9E%9A%E1%9E%80%E1%9F%92%E1%9E%9A%E1%9E%A0%E1%9E%98"
PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"
OUTPUT_DIR = PROJECT_DIR / "outputs"
RAW_CORPUS = DATA_DIR / "khmer_rouge_wikipedia.txt"


def fetch_wikipedia_text(url: str) -> str:
    response = requests.get(url, timeout=30, headers={"User-Agent": "M-DAS NLP mini project"})
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    content = soup.select_one("#mw-content-text")
    if content is None:
        content = soup

    unwanted = [
        "style",
        "script",
        "table.infobox",
        ".navbox",
        ".reflist",
        ".mw-editsection",
        ".reference",
        ".metadata",
        ".catlinks",
    ]
    for selector in unwanted:
        for element in content.select(selector):
            element.decompose()

    parts = []
    for element in content.select("p, h2, h3"):
        text = element.get_text(" ", strip=True)
        if text and "ឯកសារយោង" not in text:
            parts.append(text)
    return "\n".join(parts)


def normalize_text(text: str) -> str:
    text = re.sub(r"\[[^\]]*\]", " ", text)
    text = re.sub(r"([។៕!?])", r" \1 ", text)
    text = re.sub(r"[()\[\]{}\"“”'‘’,:;–\-]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def tokenize(text: str) -> list[str]:
    return normalize_text(text).split()


def split_tokens(tokens: list[str], train_ratio=0.70, valid_ratio=0.10):
    n = len(tokens)
    train_end = int(n * train_ratio)
    valid_end = train_end + int(n * valid_ratio)
    return tokens[:train_end], tokens[train_end:valid_end], tokens[valid_end:]


def build_vocab(tokens: list[str], vocab_size: int) -> set[str]:
    special = {"<UNK>", "<s>", "</s>"}
    most_common = [token for token, _ in Counter(tokens).most_common(max(0, vocab_size - len(special)))]
    return set(most_common) | special


def replace_unk(tokens: list[str], vocab: set[str]) -> list[str]:
    return [token if token in vocab else "<UNK>" for token in tokens]


def add_sentence_boundaries(tokens: list[str], n: int = 4) -> list[str]:
    output = ["<s>"] * (n - 1)
    for token in tokens:
        output.append(token)
        if token in {"។", "៕", "!", "?"}:
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
                context = gram[:-1]
                context_counts[order][context] += 1

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
    def __init__(self, tokens: list[str], vocab: set[str], lambdas: tuple[float, ...], k: float, max_order: int = 4):
        self.max_order = max_order
        self.vocab = sorted(vocab)
        self.lambdas = lambdas
        self.k = k
        self.counts, self.context_counts, self.followers = count_ngrams(tokens, max_order)
        self.unigram_total = sum(self.counts[1].values())

    def order_probability(self, order: int, context: tuple[str, ...], token: str) -> float:
        vocab_n = len(self.vocab)
        if order == 1:
            return (self.counts[1].get((token,), 0) + self.k) / (self.unigram_total + self.k * vocab_n)
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
    tokens = add_sentence_boundaries(tokens, max_order)
    log_prob = 0.0
    evaluated = 0
    for i in range(max_order - 1, len(tokens)):
        token = tokens[i]
        if token == "<s>":
            continue
        context = tuple(tokens[i - (max_order - 1) : i])
        probability = model.probability(context, token)
        if probability <= 0.0:
            return float("inf")
        log_prob += math.log(probability)
        evaluated += 1
    return math.exp(-log_prob / max(1, evaluated))


def generate(model, seed: list[str], length: int = 45, random_seed: int = 7) -> str:
    rng = random.Random(random_seed)
    context = tuple((["<s>", "<s>", "<s>"] + seed)[-3:])
    generated = list(seed)
    for _ in range(length):
        token = model.next_token(context, rng)
        if token == "</s>":
            break
        if token != "<s>":
            generated.append(token)
        context = tuple((list(context) + [token])[-3:])
    return " ".join(generated).replace(" ។", "។").replace(" ៕", "៕")


def build_models():
    DATA_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)

    if RAW_CORPUS.exists():
        text = RAW_CORPUS.read_text(encoding="utf-8")
    else:
        text = fetch_wikipedia_text(URL)
        RAW_CORPUS.write_text(text, encoding="utf-8")

    tokens = tokenize(text)
    train_raw, valid_raw, test_raw = split_tokens(tokens)
    vocab_size = min(100, max(50, len(set(train_raw))))
    vocab = build_vocab(train_raw, vocab_size)
    train = add_sentence_boundaries(replace_unk(train_raw, vocab))
    valid = replace_unk(valid_raw, vocab)
    test = replace_unk(test_raw, vocab)

    backoff = BackoffLM(train, vocab)
    lambda_grid = [
        (0.10, 0.20, 0.30, 0.40),
        (0.05, 0.15, 0.30, 0.50),
        (0.25, 0.25, 0.25, 0.25),
        (0.40, 0.30, 0.20, 0.10),
        (0.15, 0.20, 0.25, 0.40),
    ]
    k_grid = [0.01, 0.05, 0.10, 0.50, 1.00]

    experiments = []
    best = None
    for lambdas in lambda_grid:
        for k in k_grid:
            model = InterpolationLM(train, vocab, lambdas=lambdas, k=k)
            pp = perplexity(model, valid)
            row = {"lambdas": lambdas, "k": k, "validation_perplexity": pp}
            experiments.append(row)
            if best is None or pp < best["validation_perplexity"]:
                best = row

    interpolation = InterpolationLM(train, vocab, lambdas=best["lambdas"], k=best["k"])
    return {
        "tokens": tokens,
        "train_raw": train_raw,
        "valid_raw": valid_raw,
        "test_raw": test_raw,
        "valid": valid,
        "test": test,
        "vocab": vocab,
        "backoff": backoff,
        "interpolation": interpolation,
        "best": best,
        "experiments": experiments,
    }


def interactive_generator(backoff, interpolation):
    print("\nInteractive text generator")
    print("Type Khmer starting words, then press Enter.")
    print("Example: ខ្មែរក្រហម")
    print("Type q to stop.\n")

    while True:
        seed_text = input("Starting word/text: ").strip()
        if seed_text.lower() in {"q", "quit", "exit"}:
            break
        if not seed_text:
            continue

        model_name = input("Model (backoff/interpolation) [backoff]: ").strip().lower() or "backoff"
        model = interpolation if model_name.startswith("i") else backoff
        seed_tokens = tokenize(seed_text)

        print("\nGenerated text:")
        print(generate(model, seed_tokens, length=45, random_seed=random.randint(1, 100000)))
        print()


def main():
    parser = argparse.ArgumentParser(description="4-gram Khmer language model mini project")
    parser.add_argument("--interactive", action="store_true", help="type a starting word and generate text live")
    parser.add_argument("--seed", default=None, help="starting word/text for one generated sample")
    parser.add_argument("--seed-file", default=None, help="UTF-8 text file containing the starting word/text")
    parser.add_argument("--output", default=None, help="write generated text to a UTF-8 output file")
    parser.add_argument("--model", choices=["backoff", "interpolation"], default="backoff")
    parser.add_argument("--length", type=int, default=45, help="maximum number of generated tokens")
    args = parser.parse_args()

    project = build_models()
    tokens = project["tokens"]
    train_raw = project["train_raw"]
    valid_raw = project["valid_raw"]
    test_raw = project["test_raw"]
    valid = project["valid"]
    test = project["test"]
    vocab = project["vocab"]
    backoff = project["backoff"]
    interpolation = project["interpolation"]
    best = project["best"]
    experiments = project["experiments"]

    if args.interactive:
        interactive_generator(backoff, interpolation)
        return

    seed_text = args.seed
    if args.seed_file:
        seed_text = Path(args.seed_file).read_text(encoding="utf-8").strip()

    if seed_text:
        model = interpolation if args.model == "interpolation" else backoff
        generated_text = generate(model, tokenize(seed_text), length=args.length, random_seed=random.randint(1, 100000))
        if args.output:
            Path(args.output).write_text(generated_text, encoding="utf-8")
            print(f"Wrote generated text to {args.output}")
        else:
            print(generated_text)
        return

    results = {
        "source_url": URL,
        "tokens_total": len(tokens),
        "train_tokens": len(train_raw),
        "validation_tokens": len(valid_raw),
        "test_tokens": len(test_raw),
        "vocabulary_size": len(vocab),
        "unknown_validation_tokens": valid.count("<UNK>"),
        "unknown_test_tokens": test.count("<UNK>"),
        "backoff_test_perplexity": perplexity(backoff, test),
        "interpolation_test_perplexity": perplexity(interpolation, test),
        "best_lambdas": best["lambdas"],
        "best_k": best["k"],
        "best_validation_perplexity": best["validation_perplexity"],
        "backoff_sample": generate(backoff, ["ខ្មែរក្រហម"], random_seed=11),
        "interpolation_sample": generate(interpolation, ["ខ្មែរក្រហម"], random_seed=11),
    }

    experiment_lines = ["l1,l2,l3,l4,k,validation_perplexity"]
    for row in experiments:
        experiment_lines.append(
            ",".join([*(f"{value:.2f}" for value in row["lambdas"]), f"{row['k']:.2f}", f"{row['validation_perplexity']:.4f}"])
        )
    (OUTPUT_DIR / "validation_experiments.csv").write_text("\n".join(experiment_lines), encoding="utf-8")

    summary_lines = [f"{key}: {value}" for key, value in results.items()]
    (OUTPUT_DIR / "results_summary.txt").write_text("\n".join(summary_lines), encoding="utf-8")
    print("\n".join(summary_lines))


if __name__ == "__main__":
    main()
