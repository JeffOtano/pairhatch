"""Review-only host bundles. No host discovery, installation or config mutation."""
import json
import shlex
from pathlib import Path

HOSTS = {
    "claude": (".mcp.json", ".claude/skills/pairhatch/SKILL.md"),
    "codex": (".codex/config.toml", ".agents/skills/pairhatch/SKILL.md"),
    "cursor": (".cursor/mcp.json", ".cursor/skills/pairhatch/SKILL.md"),
    "generic": ("stdio-server.json", "skills/pairhatch/SKILL.md"),
}


def toml_value(value):
    """JSON basic strings are TOML-compatible after escaping DEL as well."""
    return json.dumps(value, ensure_ascii=False).replace("\x7f", "\\u007f")


def config_text(host, server):
    if host == "codex":
        return ("[mcp_servers.pairhatch]\ncommand = " +
                toml_value(server["command"]) + "\nargs = " +
                toml_value(server["args"]) + "\n")
    if host == "generic":
        # Descriptor, not a purported universal host configuration format.
        payload = {"transport": "stdio", **server}
    else:
        payload = {"mcpServers": {"pairhatch": {"type": "stdio", **server}}}
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def write_bundles(directory, servers, hosts, write):
    """Create inert artifacts under a NEW private setup, never an existing project."""
    skill = (Path(__file__).parent / "resources/peer-skill.md").read_text(encoding="utf-8")
    entries = []
    for host in hosts:
        config_path, skill_path = HOSTS[host]
        for actor, server in servers.items():
            root = directory / "hosts" / host / actor
            for relative, content in ((config_path, config_text(host, server)), (skill_path, skill)):
                target = root / relative
                # Parents are all inside our freshly created setup directory.
                missing = []
                parent = target.parent
                while not parent.exists():
                    missing.append(parent)
                    parent = parent.parent
                for parent in reversed(missing):
                    parent.mkdir(mode=0o700)
                write(target, content)
            entry = {"host": host, "actor": actor,
                     "bundle": str(root.relative_to(directory)),
                     "config_path": config_path, "skill_path": skill_path,
                     "installed": False, "host_validated": False,
                     "automatic_wakeup": False}
            entries.append(entry)
            generic_note = ("This is a generic stdio descriptor, NOT an installable host config.\n"
                            "Translate it using your client's documented MCP schema; skill discovery varies.\n"
                            if host == "generic" else "")
            grant_command = shlex.join([
                server["command"], server["args"][0], "--config", str(directory / "peers.json"),
                "grant", "--id", "approved-synthetic-check", "--participants", "peer-a", "peer-b",
                "--topic", "Synthetic question and answer only", "--minutes", "10",
                "--max-messages", "2", "--max-consultations", "1", "--confirm", "ALLOW peer-a peer-b",
            ])
            write(root / "README.txt",
                  f"Pairhatch {host} bundle for {actor} (review only)\n\n" + generic_note +
                  "No host settings were changed. No grants or native wake-up were enabled.\n"
                  "These paths describe a proposed PROJECT install, not a global install.\n"
                  f"MCP configuration: {config_path}\nSkill: {skill_path}\n\n"
                  "To activate, first obtain permission for the named project and continuing tool access.\n"
                  "Inspect the command/args and skill. Merge ONLY the pairhatch server entry into the\n"
                  "project config, preserving all existing fields/servers/comments. If an entry or skill\n"
                  "already exists, stop and compare; never overwrite silently. Copy only this skill\n"
                  "folder into the approved project's skill path. Do not duplicate it in other paths.\n"
                  "Do not commit generated paths or broker state to a shared repository.\n"
                  "Use one actor per host session. All bundles use the SAME local broker; they are\n"
                  "alternatives, not separate broker instances. Keep source/install/Python paths stable.\n"
                  "Restart/reload as your host requires, keep trust and tool approvals enabled, then\n"
                  "verify the skill and five tools are discovered. Test read-only peer_inbox first.\n"
                  "A zero-grant setup must refuse ask_peer. Only then plan a separately approved\n"
                  "synthetic two-host exchange with a finite grant. No live host has been validated\n"
                  "by generating this bundle. Remote/cloud hosts cannot use these local paths unless\n"
                  "the runtime and broker are accessible in their own execution environment.\n\n"
                  "Operator-only example, AFTER separate approval of peer-a/peer-b, synthetic content,\n"
                  "10-minute expiry and TWO total messages (one question + one final reply):\n" +
                  grant_command + "\n"
                  "This command creates a grant; it is not run by setup. Do not run it on skill load.\n"
                  "Use grant_id approved-synthetic-check, a fresh consultation_id and fresh message IDs.\n"
                  "If that grant ID exists or delivery is uncertain, inspect state, never recreate/retry.\n\n"
                  "Private repository references (repository access required):\n"
                  "https://github.com/JeffOtano/pairhatch/blob/main/INSTALL.md\n"
                  "https://github.com/JeffOtano/pairhatch/blob/main/docs/HOST_VALIDATION.md\n"
                  "https://github.com/JeffOtano/pairhatch/blob/main/docs/RETENTION.md\n\n"
                  "Removal: stop hosts; remove ONLY the pairhatch entry and this skill from the\n"
                  "approved project. Retain unrelated settings. Review broker data separately.\n")
    write(directory / "host-bundles.json", json.dumps({
        "schema_version": 1, "status": "generated-not-installed", "bundles": entries,
    }, indent=2) + "\n")
