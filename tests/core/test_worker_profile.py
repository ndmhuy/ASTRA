"""Local startup/configuration only: no model requests and no exam jobs."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from exam_baseline import worker_profile as profile
from scripts import run_app


def tokens():
    return dict(zip(profile.TOKEN_NAMES, ("a" * 64, "b" * 64), strict=True))


def test_shared_profile_survives_checkout_changes_without_provider_keys(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "user"))
    monkeypatch.delenv("ASTRA_WORKER_PROFILE", raising=False)
    target = profile.user_profile()
    profile.save_profile(target, {**tokens(), "EXAM_API_KEY": "never-copy-provider-key"})
    for checkout in (tmp_path / "branch-a", tmp_path / "branch-b"):
        monkeypatch.setattr(profile, "ROOT", checkout)
        assert profile.resolve_profile(".env.mas-worker") == target
    assert profile.read_tokens([target]) == tokens()
    assert "never-copy-provider-key" not in target.read_text()
    assert profile.DEFAULTS["EXAM_MODEL"] == "gemini-3.1-flash-lite"
    with pytest.raises(FileExistsError):
        profile.save_profile(target, tokens())


def test_import_whitelists_only_caller_fields_and_errors_never_echo_secrets(tmp_path):
    source = tmp_path / "provided.env"
    source.write_text("EXAM_API_KEY=private-provider\nASTRA_AGENT_WORKER_CALLER_TOKEN=" + "a" * 64)
    assert profile.read_tokens([source]) == {profile.TOKEN_NAMES[0]: "a" * 64}
    source.write_text("ASTRA_MAS_CALLER_TOKEN=private-invalid-value")
    with pytest.raises(ValueError) as error:
        profile.read_tokens([source])
    assert "private-invalid-value" not in str(error.value)


def test_explicit_profile_and_legacy_files_are_preserved(tmp_path, monkeypatch):
    monkeypatch.setattr(profile, "ROOT", tmp_path)
    monkeypatch.delenv("ASTRA_WORKER_PROFILE", raising=False)
    legacy = tmp_path / ".env.agent-worker"
    legacy.write_text("do-not-overwrite")
    assert profile.resolve_profile(legacy.name) == legacy
    explicit = tmp_path / "different.env"
    assert profile.resolve_profile(legacy.name, explicit) == explicit
    with pytest.raises(ValueError):
        profile.save_profile(legacy, tokens(), replace=True)
    assert legacy.read_text() == "do-not-overwrite"


def test_cache_fingerprint_detects_source_change_and_credentials_stay_out_of_argv(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(run_app, "ROOT", tmp_path)
    source = tmp_path / "source.ts"
    source.write_text("version-one")
    first = run_app.fingerprint([source])
    source.write_text("version-two")
    assert run_app.fingerprint([source]) != first
    command = run_app.launch_command(Path(sys.executable), tmp_path / "private.env", 8001)
    assert "--profile" in command and all(
        value not in " ".join(command) for value in tokens().values()
    )


def test_check_mode_is_read_only_and_never_starts_or_installs(tmp_path, monkeypatch, capsys):
    target = tmp_path / "absent.env"
    monkeypatch.setattr(sys, "argv", ["run_app.py", "--check", "--profile", str(target)])
    monkeypatch.setattr(run_app, "prepare", lambda: pytest.fail("check must not install"))
    monkeypatch.setattr(subprocess, "call", lambda *a, **kw: pytest.fail("must not start app"))
    assert run_app.main() == 0
    output = json.loads(capsys.readouterr().out)
    assert output["inferenceRequests"] == 0 and not target.exists()


def test_single_branch_clone_fetches_missing_pinned_corpus_without_switching(monkeypatch):
    calls = []
    monkeypatch.delenv("EXAM_RAG_PACK_DIR", raising=False)
    monkeypatch.setenv("EXAM_RAG_CORPUS_REF", "c" * 40)
    monkeypatch.setattr(run_app.shutil, "which", lambda _: "git")

    def run(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, 1 if "rev-parse" in command else 0)

    monkeypatch.setattr(run_app.subprocess, "run", run)
    run_app.prepare_corpus(Path(sys.executable))
    assert calls[-1] == ["git", "fetch", "--no-tags", "--", "origin", "c" * 40]
    assert not any(operation in call for call in calls for operation in ("switch", "merge"))


def test_fresh_clone_starts_with_shared_access_without_prompt_or_local_profile(
    tmp_path, monkeypatch
):
    checkout = tmp_path / "checkout"
    shared = checkout / "config/team-worker-access.env"
    shared.parent.mkdir(parents=True)
    shared.write_text("\n".join(f"{key}={value}" for key, value in tokens().items()))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "new-user"))
    monkeypatch.setattr(profile, "ROOT", checkout)
    monkeypatch.setattr(run_app, "ROOT", checkout)
    monkeypatch.setattr(sys, "argv", ["run_app.py", "--no-browser"])
    monkeypatch.setattr(run_app, "prepare", lambda: Path(sys.executable))
    monkeypatch.setattr(
        run_app.getpass, "getpass", lambda *a: pytest.fail("fresh clone must not prompt")
    )
    monkeypatch.setattr(
        run_app, "save_profile", lambda *a, **kw: pytest.fail("must not rewrite shared access")
    )

    class UnusedPort:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def connect_ex(self, address):
            return 1

    monkeypatch.setattr(run_app.socket, "socket", UnusedPort)

    def launch(command, *, cwd, env):
        assert env["ASTRA_WORKER_PROFILE"] == str(shared)
        assert all(env[key] == value for key, value in tokens().items())
        assert all(value not in " ".join(command) for value in tokens().values())
        return 0

    monkeypatch.setattr(run_app.subprocess, "call", launch)
    assert run_app.main() == 0
    assert not profile.user_profile().exists()
    assert profile.read_tokens([shared]) == tokens()


def test_existing_private_profile_still_overrides_shared_access(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "user"))
    monkeypatch.setattr(profile, "ROOT", tmp_path / "checkout")
    profile.save_profile(profile.user_profile(), tokens())
    assert profile.startup_profile() == profile.user_profile()
