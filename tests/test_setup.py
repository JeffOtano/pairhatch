import contextlib
import io
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from pairhatch.setup import main

ROOT = Path(__file__).resolve().parents[1]


class SetupTests(unittest.TestCase):
    def test_setup_is_private_empty_and_launchable_outside_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve() / 'demo space "quoted"'
            with contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(main(["--directory", str(destination)]), 0)
            self.assertIn("No model contacted", output.getvalue())
            self.assertEqual(destination.stat().st_mode & 0o777, 0o700)
            self.assertEqual(list(destination.glob("check-*")), [])
            db = sqlite3.connect(destination / "broker.sqlite")
            try:
                for table in ("grants", "messages", "consultations"):
                    self.assertEqual(db.execute("SELECT count(*) FROM " + table).fetchone()[0], 0)
            finally:
                db.close()
            for name in ("peers.json", "launch.py", "peer-a.claude.json", "peer-b.codex.toml"):
                self.assertEqual((destination / name).stat().st_mode & 0o777, 0o600)
            config = json.loads((destination / "peer-a.claude.json").read_text())
            server = config["mcpServers"]["pairhatch"]
            request = {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
            result = subprocess.run([server["command"], *server["args"]],
                                    input=json.dumps(request)+"\n", cwd=tmp,
                                    capture_output=True, text=True, timeout=5)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(len(json.loads(result.stdout)["result"]["tools"]), 5)

    def test_existing_destination_is_not_modified(self):
        with tempfile.TemporaryDirectory() as tmp:
            marker = Path(tmp) / "keep"
            marker.write_text("user data")
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main(["--directory", tmp]), 1)
            self.assertEqual(list(Path(tmp).iterdir()), [marker])
            self.assertEqual(marker.read_text(), "user data")

    def test_no_home_settings_changed(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            (home / ".claude.json").write_text("existing")
            with patch("pairhatch.setup.Path.home", return_value=home), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main([]), 0)
            self.assertEqual((home / ".claude.json").read_text(), "existing")
            self.assertEqual({p.name for p in home.iterdir()}, {".claude.json", "pairhatch-demo"})

    def test_missing_parent_has_clear_error(self):
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stderr(io.StringIO()) as error:
            self.assertEqual(main(["--directory", str(Path(tmp)/"missing"/"demo")]), 1)
            self.assertIn("parent directory", error.getvalue())

    def test_manifests_are_instruction_only(self):
        for folder in (".claude-plugin", ".codex-plugin"):
            manifest = json.loads((ROOT / folder / "plugin.json").read_text())
            self.assertEqual(manifest["name"], "pairhatch")
            self.assertEqual(manifest["skills"], "./skills/")
            self.assertFalse({"hooks", "mcpServers", "mcp", "userConfig"} & manifest.keys())
        self.assertFalse((ROOT / ".mcp.json").exists())
        self.assertTrue((ROOT / "skills/pairhatch/SKILL.md").is_file())

    def test_unsupported_python_fails_before_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "not-created"
            with patch("pairhatch.setup.sys.version_info", (3, 9)), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                main(["--directory", str(dest)])
            self.assertEqual(error.exception.code, 2)
            self.assertFalse(dest.exists())

    def test_generated_toml_matches_json(self):
        try:
            import tomllib
        except ImportError:
            self.skipTest("stdlib TOML parser requires Python 3.11+")
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve() / 'demo quote " café'
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(["--directory", str(destination)]), 0)
            toml = tomllib.loads((destination / "peer-a.codex.toml").read_text())
            js = json.loads((destination / "peer-a.claude.json").read_text())
            self.assertEqual(toml["mcp_servers"]["pairhatch"], js["mcpServers"]["pairhatch"])

    def test_parent_symlink_resolves_database_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            real = root / "real"
            real.mkdir()
            link = root / "link"
            link.symlink_to(real, target_is_directory=True)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(["--directory", str(link / "demo")]), 0)
            config = json.loads((real / "demo/peers.json").read_text())
            self.assertEqual(config["database"], str(real / "demo/broker.sqlite"))
