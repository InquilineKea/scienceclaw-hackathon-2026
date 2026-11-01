"""Container entry point (no network, read-only root): verify wheel hashes, build an offline venv, run pmf.py."""
import hashlib
import json
import os
import subprocess
import sys
import venv
from pathlib import Path

ROOT = Path("/project")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    lock = json.loads((ROOT / "lock.json").read_text())
    for p in lock["packages"]:
        assert sha(Path("/wheels") / p["filename"]) == p["sha256"], p["name"]
    env = Path("/runtime/venv")
    venv.EnvBuilder(with_pip=False, system_site_packages=False, symlinks=True).create(env)
    subprocess.run([sys.executable, "-I", "-m", "pip", "--python", str(env / "bin/python"), "--isolated",
                    "--disable-pip-version-check", "install", "--no-index", "--no-deps", "--require-hashes",
                    "--no-cache-dir", "--find-links", "/wheels", "-r", str(ROOT / "requirements.txt")], check=True)
    args = sys.argv[1:] or ["--out", "/results"]
    os.execv(str(env / "bin/python"), [str(env / "bin/python"), "-I", str(ROOT / "pmf.py"), *args])


if __name__ == "__main__":
    main()
