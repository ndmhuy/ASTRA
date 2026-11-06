"""Small local BM25 passage index. Offsets refer to the unchanged source text."""

from collections import Counter
from dataclasses import dataclass
import math
import re

from .models import CONFIG
from .query_parser import normalize


def tokens(text):
    return re.findall(r"\w+", normalize(text))


@dataclass(frozen=True)
class Passage:
    start: int
    end: int
    text: str


def split_passages(content):
    """Prefer paragraph/sentence boundaries; overlap long paragraphs by words."""
    limit, overlap = CONFIG["passage_chars"], CONFIG["passage_overlap_chars"]
    start = 0
    while start < len(content):
        end = min(start + limit, len(content))
        if end < len(content):
            for separator in ("\n\n", ". ", "\n", " "):
                boundary = content.rfind(separator, start + limit // 2, end)
                if boundary != -1:
                    end = boundary + len(separator)
                    break
        yield Passage(start, end, content[start:end])
        if end == len(content):
            break
        next_start = max(start + 1, end - overlap)
        # Do not begin within a word or a combining Vietnamese accent sequence.
        while next_start < end and not content[next_start - 1].isspace():
            next_start += 1
        start = next_start


class PassageIndex:
    def __init__(self, documents):
        self.entries = [(d, p) for d in documents for p in split_passages(d.content)]
        self.counts = [Counter(tokens(p.text)) for _, p in self.entries]
        self.lengths = [sum(c.values()) for c in self.counts]
        self.average_length = sum(self.lengths) / max(len(self.lengths), 1) or 1
        self.document_frequency = Counter()
        for counts in self.counts:
            self.document_frequency.update(counts.keys())

    def ranked(self, keywords):
        query = set(keywords)
        k1, b = CONFIG["bm25_k1"], CONFIG["bm25_b"]
        rows = []
        for (document, passage), counts, length in zip(self.entries, self.counts, self.lengths):
            title = set(tokens(document.title))
            matched = sorted(query & (title | counts.keys()))
            if query and not matched:
                continue
            score = 0.0
            for word in matched:
                df = self.document_frequency[word]
                idf = math.log(1 + (len(self.entries) - df + 0.5) / (df + 0.5))
                tf = counts[word]
                denominator = tf + k1 * (1 - b + b * length / self.average_length)
                score += CONFIG["content_weight"] * idf * tf * (k1 + 1) / denominator
                score += CONFIG["title_weight"] * idf * (word in title)
            if keywords and " ".join(keywords) in normalize(document.title + " " + passage.text):
                score += CONFIG["phrase_bonus"]
            rows.append((score, document, passage, matched))
        return sorted(rows, key=lambda row: (-row[0], row[1].document_id, row[2].start))
