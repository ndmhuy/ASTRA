"""Prepared local server. Only explicit user actions may trigger inference."""

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    parser.add_argument("--port", type=int, default=8001)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("Invalid port")
    env_file = args.env_file.absolute()
    os.chdir(ROOT)
    import uvicorn

    from exam_baseline.api.app import configure_logging, create_app
    from exam_baseline.connection import SharedConnection

    configure_logging()
    app = create_app(
        workspace_dir=ROOT / "astra-frontend/dist", connection=SharedConnection(env_file)
    )
    uvicorn.run(app, host="127.0.0.1", port=args.port, proxy_headers=False)


if __name__ == "__main__":
    main()
