"""Build an ASTRA Toán pack with reviewed probability examples and keep the base snapshot."""

import argparse
import hashlib
import json
from pathlib import Path

from exam_baseline.config import DEFAULT_RAG_CORPUS_REF
from rag_workflow.profile_pack import export_release_pack, load_profile_release

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "rag_workflow" / "probability_supplement.json"
REVIEW = ROOT / "rag_workflow" / "probability_supplement_review.json"


def digest(data: bytes) -> str:
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def write_json(path: Path, value) -> None:
    path.write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def build(output: Path, ref: str) -> dict:
    if output.exists() and any(output.iterdir()):
        raise ValueError("Choose a new or empty directory for the generated pack.")
    src = DATA.read_bytes()
    samples = json.loads(src)
    receipt = json.loads(REVIEW.read_bytes())
    if digest(src) != receipt["source_sha256"]:
        raise ValueError("The review receipt belongs to a different version of the examples.")
    votes = {row["id"]: row for row in receipt["reviews"]}
    if len(votes) != len(samples) or len(receipt["reviews"]) != len(samples):
        raise ValueError("The review must cover each example exactly once.")

    base = load_profile_release(ref=ref, repo=ROOT)
    known_refs = {
        observation["ref"]
        for pack in base["topic_packs_by_id"].values()
        for observation in pack["construction_observations"]
    }
    augmented = {}
    for sample in samples:
        vote = votes[sample["id"]]
        if vote["answer"] != sample["answer"] or vote["level"] != sample["level"]:
            raise ValueError(f"Independent review disagreed for {sample['id']}.")
        if not set(sample["support_refs"]) <= known_refs:
            raise ValueError(f"Missing supporting corpus metadata for {sample['id']}.")
        augmented.setdefault(sample["pack"], []).append(
            {
                "target": {
                    "id": sample["id"],
                    "part": sample["part"],
                    "level": sample["level"],
                    "topic": sample["topic"],
                    "qtype": "mcq" if sample["part"] == "P1" else "short_answer",
                    "support_refs": sample["support_refs"],
                },
                "sample": {
                    "id": sample["id"],
                    "stem": sample["stem"],
                    "options": sample["options"],
                    "answers": [sample["answer"]],
                    "solution": sample["solution"],
                    "level_reason": sample["level_reason"],
                    "variation_guidance": sample["variation"],
                },
                "origin": "synthetic_not_corpus_evidence",
                "model": "Codex",
                "review_model": receipt["model"],
                "key_agreement": True,
                "level_agreement": True,
                "status": "model_checks_passed_pending_teacher_review",
            }
        )

    export_release_pack(output, ref=ref, repo=ROOT)
    profile = output / "corpus/profiles/toan"
    index = profile / "profile.bundle.json"
    bundle = json.loads(index.read_bytes())
    for entry in bundle["topic_packs"]:
        path = profile / entry["path"]
        additions = augmented.pop(path.stem, None)
        if additions:
            topic = json.loads(path.read_bytes())
            topic.setdefault("examples", []).extend(additions)
            write_json(path, topic)
            entry["sha256"] = digest(path.read_bytes())
    if augmented:
        raise ValueError(f"Unknown topic packs: {sorted(augmented)}")
    write_json(index, bundle)

    release = load_profile_release(pack_dir=output, force_rebuild=True)
    manifest_path = output / "manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    manifest["release_fingerprint"] = release["release_fingerprint"]
    manifest["bundle_sha256"] = release["release_info"]["bundle_sha256"]
    manifest["supplement_example_ids"] = [sample["id"] for sample in samples]
    manifest["supplement_review_sha256"] = digest(REVIEW.read_bytes())
    manifest["files_sha256"] = {
        name: digest((output / name).read_bytes()) for name in manifest["files_sha256"]
    }
    write_json(manifest_path, manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--ref", default=DEFAULT_RAG_CORPUS_REF)
    args = parser.parse_args()
    manifest = build(args.output, args.ref)
    print(f"Built {len(manifest['supplement_example_ids'])} examples in {args.output}")
    print(f"Release fingerprint: {manifest['release_fingerprint']}")


if __name__ == "__main__":
    main()
