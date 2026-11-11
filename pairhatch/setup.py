"""One-command offline setup. Never edits host settings or contacts a model."""
import argparse
import contextlib
import io
import json
import os
import shlex
from pathlib import Path
import sys
import tempfile
import time

from .engine import Broker, load_config
from .init_config import main as initialize
from .store import Store
from .hosts import HOSTS, write_bundles, config_text, toml_value


def private_write(path, text):
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w", encoding="utf-8") as stream:
        stream.write(text)


def check_mock(directory):
    """Use isolated disposable state, never a grant in the user's setup."""
    with tempfile.TemporaryDirectory(prefix="check-", dir=directory) as tmp:
        config_path = Path(tmp) / "mock" / "peers.json"
        with contextlib.redirect_stdout(io.StringIO()):
            if initialize(["--directory", str(config_path.parent)]) != 0:
                raise RuntimeError("Could not create isolated check")
        config, peers = load_config(config_path)
        store = Store(config["database"])
        try:
            a = Broker(store, peers, "peer-a")
            b = Broker(store, peers, "peer-b")
            store.create_grant("setup-check", ["peer-a", "peer-b"], "Synthetic offline check", time.time()+60, 2, 1)
            question = a.ask("setup-check", "peer-b", "What is 2 plus 2?", "setup-check", "question")
            answer = b.reply("setup-check", "question", "4", True, "answer")
            status = a.inspect("setup-check")
            if question["state"] != "accepted" or answer["state"] != "accepted" or status["consultation"]["state"] != "completed":
                raise RuntimeError("Offline roundtrip failed")
        finally:
            store.close()


def setup(directory, hosts=None):
    hosts = tuple(HOSTS) if hosts is None else tuple(dict.fromkeys(hosts))
    if not hosts or any(host not in HOSTS for host in hosts):
        raise ValueError("Choose supported host bundles: " + ", ".join(HOSTS))
    # Hosts expand ${...} in command/args. Refuse ambiguous paths before creating state.
    if any("${" in str(path) for path in (directory, Path(__file__).resolve(), sys.executable)):
        raise ValueError("Host configuration interpolation is unsupported in setup/runtime paths")
    with contextlib.redirect_stdout(io.StringIO()):
        if initialize(["--directory", str(directory)]) != 0:
            return 1
    check_mock(directory)
    # The persistent state contains peer enrollment only, never a demo grant.
    config, peers = load_config(directory / "peers.json")
    store = Store(config["database"])
    try:
        store.bind_peers(peers)
    finally:
        store.close()
    package_root = str(Path(__file__).resolve().parent.parent)
    launcher = directory / "launch.py"
    private_write(launcher, "import sys\nsys.path.insert(0, " + repr(package_root) + ")\nfrom pairhatch.__main__ import main\nraise SystemExit(main())\n")
    servers = {}
    for actor in ("peer-a", "peer-b"):
        args = [str(launcher), "--config", str(directory / "peers.json"), "--actor", actor, "serve"]
        servers[actor] = {"command": sys.executable, "args": args}
        private_write(directory / (actor + ".claude.json"), json.dumps(
            {"mcpServers": {"pairhatch": {"command": sys.executable, "args": args}}}, indent=2) + "\n")
        private_write(directory / (actor + ".codex.toml"),
            config_text("codex", servers[actor]))
    write_bundles(directory, servers, hosts, private_write)
    claude_command = shlex.join(["claude", "--strict-mcp-config", "--mcp-config", str(directory / "peer-b.claude.json")])
    codex_args = [str(launcher), "--config", str(directory / "peers.json"), "--actor", "peer-a", "serve"]
    codex_command = shlex.join(["codex", "-c", "mcp_servers.pairhatch.command=" + toml_value(sys.executable),
                                "-c", "mcp_servers.pairhatch.args=" + toml_value(codex_args)])
    private_write(directory / "README.txt",
        "Pairhatch offline setup\n\n"
        "No model was contacted. No host settings were changed. No active grants exist.\n"
        "The disposable synthetic check state was removed.\n\n"
        "Host snippets are examples, not installed registrations. Review before use.\n"
        "hosts/ contains per-host, per-actor bundles with BOTH usage skill and MCP tooling.\n"
        "Read host-bundles.json for paths, and each bundle README.txt for activation/removal.\n"
        "Claude/Codex/Cursor bundles target project scope; generic needs client-specific translation.\n"
        "Do not copy a whole config over existing settings. No automatic agent wake-up exists.\n"
        "Use one actor per host. A mock peer does not deliver to another model.\n"
        "Keep the Python environment and Pairhatch source/install at their current paths.\n"
        "Review-only temporary Claude Code command (actor peer-b):\n" + claude_command + "\n\n"
        "Review-only per-invocation Codex command (actor peer-a):\n" + codex_command + "\n\n"
        "These commands launch real hosts; review provider/logging and tool permissions first.\n"
        "Persistent registration needs separate informed permission.\n"
        "Never weaken host approval policies to make a test pass.\n"
        "Repository references:\n"
        "https://github.com/JeffOtano/pairhatch/blob/main/INSTALL.md\n"
        "https://github.com/JeffOtano/pairhatch/blob/main/docs/HOST_VALIDATION.md\n"
        "Each host bundle README includes an operator-only finite-grant example.\n")
    print("Offline broker check passed. No model contacted; host connection not yet verified.")
    print("Setup directory:", directory)
    print("Created private config, empty broker state, launcher and review-only host snippets.")
    print("Zero active grants. No host settings, credentials, daemons or shell profiles changed.")
    print("Next: read", directory / "README.txt")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", default=str(Path.home() / "pairhatch-demo"),
                        help="New private directory (default: ~/pairhatch-demo); never overwritten")
    parser.add_argument("--host", action="append", choices=tuple(HOSTS),
                        help="Generate only this host bundle (repeatable; default: all). Never installs.")
    args = parser.parse_args(argv)
    if sys.version_info < (3, 10):
        parser.error("Pairhatch requires Python 3.10 or newer")
    if os.name != "posix":
        parser.error("Pairhatch requires Linux or macOS")
    directory = Path(args.directory).expanduser().absolute()
    try:
        return setup(directory, args.host)
    except (OSError, ValueError, RuntimeError) as exc:
        print("pairhatch-setup: " + str(exc) + ". Inspect any partial setup; choose a fresh directory to retry.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
