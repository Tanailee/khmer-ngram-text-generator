# Mini Project 1: 4-gram Text Generation on Khmer Wikipedia Text

Student: ____________________  
Program: Master of Data Science  
Course: Natural Language Processing  
Corpus source: Khmer Wikipedia article "ខ្មែរក្រហម", accessed 2026-05-04. The page states that it was last edited on 2025-05-22.

## 1. Objective and Corpus

The goal of this mini project is to build and evaluate two 4-gram language models for text generation. I used the Khmer Wikipedia article about "ខ្មែរក្រហម" as the main corpus because it is a Khmer-language historical article with repeated named entities, dates, and political terms. The extracted article text was cleaned by removing references and webpage navigation text.

Because Khmer text often does not mark word boundaries with spaces, this experiment follows the assignment instruction and uses a simple whitespace-based tokenizer after light punctuation normalization. Digits in Khmer and Arabic forms were replaced with `<NUM>`. The corpus was split sequentially into 70% training, 10% validation, and 20% testing.

## 2. Preprocessing

| Item | Value |
|---|---:|
| Total tokens | 309 |
| Training tokens | 216 |
| Validation tokens | 30 |
| Testing tokens | 63 |
| Vocabulary cap | 100 |
| Validation `<UNK>` tokens | 23 |
| Test `<UNK>` tokens | 49 |

The vocabulary was created from the most frequent training tokens, including the special tokens `<s>`, `</s>`, and `<UNK>`. Any token outside the vocabulary was replaced with `<UNK>`. Sentence boundary tokens were added so that each 4-gram model could learn sentence starts and endings.

## 3. Language Models

**LM1: Unsmoothed backoff 4-gram.**  
For each next-token prediction, LM1 first tries the 4-gram probability. If the 4-gram was unseen, it backs off to the 3-gram, then the 2-gram, and finally the unigram. The n-gram probability is:

`P(w_i | h) = count(h, w_i) / count(h)`

This model is unsmoothed, so unseen higher-order n-grams receive probability only through shorter observed histories.

**LM2: Interpolated 4-gram with add-k smoothing.**  
LM2 combines unigram, bigram, trigram, and 4-gram probabilities:

`P(w_i | h) = λ1P1 + λ2P2 + λ3P3 + λ4P4`

Each n-gram term uses add-k smoothing:

`P_k(w_i | h) = (count(h, w_i) + k) / (count(h) + k|V|)`

The validation set was used to search a small grid of lambda weights and k values. The best validation setting was:

| λ1 | λ2 | λ3 | λ4 | k | Validation perplexity |
|---:|---:|---:|---:|---:|---:|
| 0.25 | 0.25 | 0.25 | 0.25 | 0.01 | 4.9652 |

## 4. Evaluation

Perplexity was computed on the test set:

`PP(W) = exp(-1/N * Σ log P(w_i | history))`

| Model | Test perplexity |
|---|---:|
| LM1: Backoff, unsmoothed | 2.3182 |
| LM2: Interpolation, add-k | 3.4084 |

LM1 achieved lower test perplexity in this run. This is reasonable for a very small corpus because many test tokens collapse into `<UNK>`, and the backoff model can strongly reuse observed local patterns. LM2 is safer for unseen events because smoothing avoids zero probabilities, but interpolation distributes some probability mass across the whole vocabulary, which increased perplexity on this small test set.

## 5. Generated Text Examples

**LM1 backoff sample**

ខ្មែរក្រហម ជា ភាសាបារាំង ៖ Khmer Rouge គឺជាឈ្មោះដែលសម្តេចព្រះបាទ នរោត្តម សីហនុ មានព្រះរាជបន្ទូលសំដៅលើក្រុមកុម្មុយនីស្ត ពោលជាសមាជិកនៃ បក្សកុម្មុយនីស្តកម្ពុជា ដែលប្រឆាំងនឹងព្រះអង្គនៅទសវត្សរ៍ឆ្នាំ `<NUM>` ហើយក្រុមនេះបានឡើងកាន់កាប់ ប្រទេសកម្ពុជា នៅ ថ្ងៃទី `<NUM>` ខែមេសា ឆ្នាំ `<NUM>`។

**LM2 interpolation sample**

ខ្មែរក្រហម កងកម្លាំងកុម្មុយនីស្តវៀតណាម ថ្នាក់ដឹកនាំបក្សតែងសម្តៅលើខ្លួនថា អង្គការបដិវត្តន៍ នៅក្នុងទសវត្សរ៍ឆ្នាំ ជា នៅទីបំផុត Rouge ជាពិសេសគឺមន្ត្រីរដ្ឋាភិបាលសាធារណរដ្ឋខ្មែរ ប្រទេសកម្ពុជា ពោលជាសមាជិកនៃ `<UNK>` `<UNK>` ពត បក្សកុម្មុយនីស្តកម្ពុជា `<NUM>`។ អង្គការ បានស្បថថានឹងជួយមើលថែរក្សាប្រជាជន ប៉ុន្តែតាមពិតវាបែរជាផ្ទុយពីនោះទៅវិញ

## 6. Conclusion

Both models satisfy the assignment requirements for 4-gram language modeling and text generation. On this corpus, the unsmoothed backoff model performed better on test perplexity, while the interpolated add-k model produced more varied but less stable text. The experiment also shows an important limitation for Khmer NLP: whitespace tokenization is simple and reproducible, but it creates long tokens and many `<UNK>` items. A future improvement would be to use a Khmer word segmenter before building the n-gram models.

Reference: Khmer Wikipedia, "ខ្មែរក្រហម", https://km.wikipedia.org/wiki/ខ្មែរក្រហម
