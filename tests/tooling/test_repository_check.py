import hashlib
import importlib.util
import subprocess

from tests.paths import ROOT


def load_checker():
    path = ROOT / "scripts" / "check_repository.py"
    spec = importlib.util.spec_from_file_location("repository_check", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_ignore_rules_and_scan_do_not_expose_a_local_key(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / ".gitignore").write_text(".env\nruns/\n", encoding="utf-8")
    secret = "AQ." + "X" * 48
    (tmp_path / ".env").write_text(f"EXAM_API_KEY={secret}\n", encoding="utf-8")
    (tmp_path / "safe.py").write_text("print('ok')\n", encoding="utf-8")
    checker = load_checker()
    assert checker.check_repository(tmp_path) == []
    (tmp_path / "leaked.txt").write_text(secret, encoding="utf-8")
    issues = checker.check_repository(tmp_path)
    assert issues == ["Possible credential: leaked.txt"]
    assert secret not in str(issues)


def test_force_added_secret_is_detected_even_if_ignored(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / ".gitignore").write_text(".env\n", encoding="utf-8")
    (tmp_path / ".env").write_text("EXAM_API_KEY=local-dummy-value-only\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp_path), "add", "-f", ".env"], check=True)
    issues = load_checker().check_repository(tmp_path)
    assert "Local/private artifact: .env" in issues
    assert "Possible credential: .env" in issues


def test_staged_secret_cannot_be_hidden_by_cleaning_working_copy(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    path = tmp_path / "source.txt"
    path.write_text("AQ." + "X" * 48, encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp_path), "add", "source.txt"], check=True)
    path.write_text("clean working copy", encoding="utf-8")
    assert load_checker().check_repository(tmp_path) == ["Possible credential: source.txt"]


def test_accepts_only_exact_bytes_of_the_approved_mas_runtime(tmp_path, monkeypatch):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    checker = load_checker()
    payload = b"synthetic bytecode containing a BLA decoy sk-" + b"X" * 40
    runtime = tmp_path / "src" / "astra_mas"
    runtime.mkdir(parents=True)
    names = tuple(checker.MAS_RUNTIME_SHA256)
    for name in names:
        (runtime / name).write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()
    monkeypatch.setattr(checker, "MAS_RUNTIME_SHA256", dict.fromkeys(names, digest))
    git = ["git", "-C", str(tmp_path)]
    subprocess.run([*git, "add", "."], check=True)
    assert checker.check_repository(tmp_path) == []

    target = runtime / "runtime.pyc"
    target.write_bytes(b"modified")
    subprocess.run([*git, "add", str(target)], check=True)
    target.write_bytes(payload)
    assert checker.check_repository(tmp_path) == [
        "Invalid MAS release payload: src/astra_mas/runtime.pyc"
    ]
