"""Local BM25-v2, subword/concept Embedding, and Hybrid RRF passage index."""

from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
import math
import re
import unicodedata

from .models import CONFIG
from .query_parser import accented_tokens, normalize

QUESTION_BOUNDARY = re.compile(
    r"(?im)^[ \t>*_#]*((?:C(?:â|a\u0302|a)u|Question)\s+\d+|(?:PH(?:Ầ|Â\u0300|A)N|Part)\s+(?:[IVX]+|\d+))\b"
)
SUFFIX_IGNORE = frozenset({"tion", "atio", "ment", "ness", "able", "ible", "ings", "ance", "ence"})
GENERIC_BOUND_SYLLABLES = frozenset(
    {
        "dinh",
        "vat",
        "so",
        "the",
        "dong",
        "hop",
        "chat",
        "phan",
        "ung",
        "co",
        "diem",
        "nhiet",
        "anh",
        "sang",
        "cac",
        "mot",
        "hai",
        "ba",
        "khi",
        "trong",
        "tren",
        "duoi",
        "giua",
        "theo",
        "cung",
        "khac",
        "nhung",
        "nhieu",
        "lon",
        "nho",
        "cao",
        "thap",
        "moi",
        "cu",
        "dung",
        "sai",
        "tinh",
        "do",
        "he",
        "dang",
        "loai",
        "nhom",
        "vung",
        "mien",
        "qua",
        "trinh",
        "hien",
        "tuong",
        "su",
        "viec",
        "hoat",
        "thanh",
        "tao",
        "bien",
        "doi",
    }
)


def tokens(text):
    return re.findall(r"\w+", normalize(text))


@dataclass(frozen=True)
class Passage:
    start: int
    end: int
    text: str
    label: str | None = None


def _split_window(content, seg_start, seg_end, label=None):
    limit, overlap = CONFIG["passage_chars"], CONFIG["passage_overlap_chars"]
    start = seg_start
    while start < seg_end:
        end = min(start + limit, seg_end)
        if end < seg_end:
            for separator in ("\n\n", ". ", "\n", " "):
                boundary = content.rfind(separator, start + limit // 2, end)
                if boundary != -1:
                    end = boundary + len(separator)
                    break
        yield Passage(start, end, content[start:end], label)
        if end == seg_end:
            break
        next_start = max(start + 1, end - overlap)
        # Do not begin within a word or a combining Vietnamese accent sequence.
        while next_start < end and not content[next_start - 1].isspace():
            next_start += 1
        start = next_start


def split_passages(content, structured=False):
    """Split on exam question markers when structured=True; otherwise by bounded windows."""
    if structured:
        matches = list(QUESTION_BOUNDARY.finditer(content))
        if len(matches) >= 2:
            raw_segments = []
            if matches[0].start() > 0:
                raw_segments.append((0, matches[0].start(), None))
            for i, match in enumerate(matches):
                seg_end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
                clean_label = re.sub(
                    r"\s+", " ", unicodedata.normalize("NFC", match.group(1))
                ).strip()
                raw_segments.append((match.start(), seg_end, clean_label))
            min_chars = CONFIG.get("min_passage_chars", 120)
            merged = []
            i = 0
            while i < len(raw_segments):
                s_start, s_end, s_label = raw_segments[i]
                while s_end - s_start < min_chars and i + 1 < len(raw_segments):
                    i += 1
                    _, s_end, next_label = raw_segments[i]
                    s_label = next_label or s_label
                merged.append((s_start, s_end, s_label))
                i += 1
            for s_start, s_end, s_label in merged:
                yield from _split_window(content, s_start, s_end, s_label)
            return
    yield from _split_window(content, 0, len(content), None)


def _matched_concepts(norm_text, word_set):
    clusters = set()
    for cluster_id, phrases in CONFIG.get("concept_synonyms", {}).items():
        for phrase in phrases:
            norm_phrase = normalize(phrase)
            if " " in norm_phrase:
                if re.search(r"(?<!\w)" + re.escape(norm_phrase) + r"(?!\w)", norm_text):
                    clusters.add(cluster_id)
                    break
            elif norm_phrase in word_set:
                clusters.add(cluster_id)
                break
    return frozenset(clusters)


def _char_ngrams(word_set):
    grams = set()
    for w in word_set:
        if len(w) < 4 or w.isdigit() or w in GENERIC_BOUND_SYLLABLES:
            continue
        padded = f"^{w}$"
        for i in range(len(padded) - 3):
            g = padded[i : i + 4]
            if g.strip("^$") not in SUFFIX_IGNORE:
                grams.add(g)
    return frozenset(grams)


@dataclass(frozen=True)
class _AnalyzedPassage:
    passage: Passage
    counts: Counter
    length: int
    title_tokens: frozenset[str]
    bigrams: frozenset[tuple[str, str]]
    accented: frozenset[str]
    norm_full: str
    concepts: frozenset[str]
    char_grams: frozenset[str]


@lru_cache(maxsize=4096)
def _analyze_document(title: str, content: str, structured: bool) -> tuple[_AnalyzedPassage, ...]:
    # For structured exam papers, title is a directory path slug, not passage knowledge.
    t_tokens = [] if structured else tokens(title)
    t_set = frozenset(t_tokens)
    t_bigrams = frozenset(zip(t_tokens, t_tokens[1:]))
    t_acc = frozenset() if structured else frozenset(accented_tokens(title))
    t_norm = "" if structured else normalize(title)
    analyzed = []
    for p in split_passages(content, structured=structured):
        p_tokens = tokens(p.text)
        counts = Counter(p_tokens)
        word_union = frozenset(counts.keys()) | t_set
        norm_full = t_norm + " " + normalize(p.text)
        analyzed.append(
            _AnalyzedPassage(
                passage=p,
                counts=counts,
                length=sum(counts.values()),
                title_tokens=t_set,
                bigrams=frozenset(zip(p_tokens, p_tokens[1:])) | t_bigrams,
                accented=frozenset(accented_tokens(p.text)) | t_acc,
                norm_full=norm_full,
                concepts=_matched_concepts(norm_full, word_union),
                char_grams=_char_ngrams(word_union),
            )
        )
    return tuple(analyzed)


@lru_cache(maxsize=16)
def _build_corpus_stats(doc_key: tuple[tuple[str, str, bool], ...]):
    items = []
    df = Counter()
    total_len = 0
    for idx, (title, content, structured) in enumerate(doc_key):
        for ap in _analyze_document(title, content, structured):
            items.append((idx, ap))
            df.update(ap.counts.keys())
            total_len += ap.length
    n_items = len(items)
    avg_len = (total_len / max(n_items, 1)) or 1.0
    idf_map = {w: math.log(1 + (n_items - count + 0.5) / (count + 0.5)) for w, count in df.items()}
    default_idf = math.log(1 + (n_items + 0.5) / 0.5)

    p_norms_base = []
    p_norms_with_cg = []
    for _, ap in items:
        word_union = ap.title_tokens | ap.counts.keys()
        sq = 0.0
        for w in word_union:
            idf = idf_map.get(w, default_idf)
            tf = ap.counts[w]
            pw = (1.0 + math.log(1 + tf)) * idf * (1.35 if w in ap.title_tokens else 1.0)
            sq += pw * pw
        for w1, w2 in ap.bigrams:
            pw = 1.2 * min(idf_map.get(w1, default_idf), idf_map.get(w2, default_idf))
            sq += pw * pw
        for aw in ap.accented:
            pw = 0.6 * idf_map.get(normalize(aw), default_idf)
            sq += pw * pw
        sq += len(ap.concepts) * (1.15 * 1.15)
        sq_cg = sq + len(ap.char_grams) * (0.35 * 0.35)
        p_norms_base.append(math.sqrt(sq) if sq > 0 else 0.0)
        p_norms_with_cg.append(math.sqrt(sq_cg) if sq_cg > 0 else 0.0)

    return items, df, avg_len, idf_map, default_idf, tuple(p_norms_base), tuple(p_norms_with_cg)


class PassageIndex:
    def __init__(self, documents):
        self._docs = tuple(documents)
        doc_key = tuple(
            (d.title, d.content, getattr(d, "content_kind", None) == "exam") for d in self._docs
        )
        (
            raw_items,
            self.document_frequency,
            self.average_length,
            self._idf_map,
            self._default_idf,
            self._p_norms_base,
            self._p_norms_cg,
        ) = _build_corpus_stats(doc_key)
        self.items: list[tuple[object, _AnalyzedPassage]] = [
            (self._docs[doc_idx], ap) for doc_idx, ap in raw_items
        ]
        self.entries = [(d, ap.passage) for d, ap in self.items]
        self.counts = [ap.counts for _, ap in self.items]
        self.lengths = [ap.length for _, ap in self.items]

    def _idf(self, word: str) -> float:
        return self._idf_map.get(word, self._default_idf)

    def ranked_detailed(self, keywords, accented=(), mode="bm25"):
        """Return (relevance_score, bm25_score, embedding_score, document, passage, matched_terms)."""
        query_list = list(keywords)
        query_set = set(query_list)
        if not query_list:
            return [(0.0, 0.0, 0.0, d, ap.passage, []) for d, ap in self.items]

        k1, b = CONFIG["bm25_k1"], CONFIG["bm25_b"]
        bigram_weight = CONFIG.get("bigram_weight", 1.5)
        accent_weight = CONFIG.get("accent_weight", 1.0)
        min_emb = CONFIG.get("min_embedding_score", 0.12)

        q_bigrams = list(zip(query_list, query_list[1:]))
        q_norm_str = " ".join(query_list)
        q_concepts = _matched_concepts(q_norm_str, query_set)
        q_cgrams = _char_ngrams(query_set)

        # Build query vector for embedding cosine similarity.
        q_vec: dict[str, float] = {}
        for w in query_list:
            q_vec[f"w:{w}"] = self._idf(w)
        for w1, w2 in q_bigrams:
            q_vec[f"bg:{w1}_{w2}"] = 1.2 * min(self._idf(w1), self._idf(w2))
        for aw in accented:
            q_vec[f"ac:{aw}"] = 0.6 * self._idf(normalize(aw))
        for cid in q_concepts:
            q_vec[f"c:{cid}"] = 1.15
        for cg in q_cgrams:
            q_vec[f"cg:{cg}"] = 0.35
        q_norm = math.sqrt(sum(v * v for v in q_vec.values())) or 1.0

        candidates = []
        for p_idx, (d, ap) in enumerate(self.items):
            word_union = ap.title_tokens | ap.counts.keys()
            matched = sorted(query_set & word_union)
            shared_concepts = q_concepts & ap.concepts
            if (
                len(query_list) >= 2
                and len(matched) == 1
                and matched[0] in GENERIC_BOUND_SYLLABLES
                and not shared_concepts
            ):
                matched = []

            # 1. BM25-v2 score (lexical + adjacent Vietnamese bigrams + exact diacritics)
            bm25_score = 0.0
            if matched:
                for word in matched:
                    idf = self._idf(word)
                    tf = ap.counts[word]
                    denom = tf + k1 * (1 - b + b * ap.length / self.average_length)
                    bm25_score += CONFIG["content_weight"] * idf * tf * (k1 + 1) / denom
                    bm25_score += CONFIG["title_weight"] * idf * (word in ap.title_tokens)
                for w1, w2 in q_bigrams:
                    if (w1, w2) in ap.bigrams:
                        bm25_score += bigram_weight * min(self._idf(w1), self._idf(w2))
                for aw in accented:
                    if aw in ap.accented:
                        bm25_score += accent_weight * self._idf(normalize(aw))
                if q_norm_str in ap.norm_full:
                    bm25_score += CONFIG["phrase_bonus"]

            # 2. Embedding cosine similarity (word + bigram + concept cluster + OCR-tolerant 4-grams)
            shared_concepts = q_concepts & ap.concepts
            shared_cgrams = q_cgrams & ap.char_grams
            has_semantic_signal = bool(matched or shared_concepts or len(shared_cgrams) >= 2)
            emb_score = 0.0
            matched_set = set(matched)
            if has_semantic_signal:
                dot = 0.0
                for w in matched:
                    idf = self._idf(w)
                    tf = ap.counts[w]
                    pw = (1.0 + math.log(1 + tf)) * idf * (1.35 if w in ap.title_tokens else 1.0)
                    dot += q_vec.get(f"w:{w}", 0.0) * pw
                for w1, w2 in q_bigrams:
                    if (w1, w2) in ap.bigrams:
                        pw = 1.2 * min(self._idf(w1), self._idf(w2))
                        dot += q_vec.get(f"bg:{w1}_{w2}", 0.0) * pw
                for aw in accented:
                    if aw in ap.accented and normalize(aw) in matched_set:
                        pw = 0.6 * self._idf(normalize(aw))
                        dot += q_vec.get(f"ac:{aw}", 0.0) * pw
                dot += len(shared_concepts) * (1.15 * 1.15)
                use_cg = len(shared_cgrams) >= 2 or matched or shared_concepts
                if use_cg:
                    dot += len(shared_cgrams) * (0.35 * 0.35)
                p_norm = self._p_norms_cg[p_idx] if use_cg else self._p_norms_base[p_idx]
                if p_norm > 0 and dot > 0:
                    raw_cos = dot / (q_norm * p_norm)
                    if matched or shared_concepts or raw_cos >= min_emb:
                        emb_score = min(1.0, raw_cos)

            if mode == "bm25" and not matched:
                continue
            if mode == "embedding" and emb_score < min_emb and not matched and not shared_concepts:
                continue
            if mode == "hybrid" and not matched and emb_score < min_emb and not shared_concepts:
                continue

            effective_matched = matched or sorted(shared_concepts)
            candidates.append((bm25_score, emb_score, d, ap.passage, effective_matched))

        if not candidates:
            return []

        if mode == "bm25":
            rows = [(bm25, bm25, emb, d, p, m) for bm25, emb, d, p, m in candidates]
            return sorted(rows, key=lambda r: (-r[0], r[3].document_id, r[4].start))

        if mode == "embedding":
            rows = [(emb, bm25, emb, d, p, m) for bm25, emb, d, p, m in candidates]
            return sorted(rows, key=lambda r: (-r[0], -r[1], r[3].document_id, r[4].start))

        # Hybrid mode: Reciprocal Rank Fusion (RRF) + normalized linear blend
        rrf_k = CONFIG.get("rrf_k", 60)
        alpha = CONFIG.get("hybrid_alpha", 0.55)
        max_bm25 = max((c[0] for c in candidates), default=1.0) or 1.0

        bm25_order = sorted(
            range(len(candidates)),
            key=lambda i: (-candidates[i][0], candidates[i][2].document_id, candidates[i][3].start),
        )
        emb_order = sorted(
            range(len(candidates)),
            key=lambda i: (-candidates[i][1], candidates[i][2].document_id, candidates[i][3].start),
        )
        bm25_rank = {idx: rank + 1 for rank, idx in enumerate(bm25_order)}
        emb_rank = {idx: rank + 1 for rank, idx in enumerate(emb_order)}

        rows = []
        for idx, (bm25, emb, d, p, m) in enumerate(candidates):
            rrf_b = (rrf_k / (rrf_k + bm25_rank[idx])) if bm25 > 0 else 0.0
            rrf_e = (rrf_k / (rrf_k + emb_rank[idx])) if emb > 0 else 0.0
            rrf_score = 0.5 * (rrf_b + rrf_e)
            norm_b = bm25 / max_bm25 if bm25 > 0 else 0.0
            linear_score = alpha * norm_b + (1.0 - alpha) * emb
            hybrid_score = 0.5 * rrf_score + 0.5 * linear_score
            rows.append((hybrid_score, bm25, emb, d, p, m))
        return sorted(rows, key=lambda r: (-r[0], -r[1], r[3].document_id, r[4].start))

    def ranked(self, keywords, accented=(), mode="bm25"):
        return [
            (score, d, p, m)
            for score, _, _, d, p, m in self.ranked_detailed(keywords, accented=accented, mode=mode)
        ]
