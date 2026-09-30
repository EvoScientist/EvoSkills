"""Tests for .github/scripts/validate_mcp.py.

Run from the repository root (needs pytest and pyyaml):
    pytest tests/ci -q
"""

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / ".github" / "scripts" / "validate_mcp.py"

STDIO = """\
name: my-server
label: "My Server  (does things)"
description: "Does things"
tags: [web-search]
transport: stdio
command: npx
args: ["-y", "@org/server"]
"""

HTTP = """\
name: my-server
label: "My Server  (does things)"
description: "Does things"
tags: [web-search]
transport: streamable_http
url: "https://mcp.example.com/mcp"
headers:
  Authorization: "Bearer ${MY_TOKEN}"
env_key: MY_TOKEN
env_hint: "export MY_TOKEN=..."
env_optional: true
"""


def run(tmp_path: Path, content: str, filename: str = "my-server.yaml"):
    (tmp_path / "mcp").mkdir(exist_ok=True)
    (tmp_path / "mcp" / filename).write_text(content, encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(SCRIPT)], cwd=tmp_path, capture_output=True, text=True
    )
    return proc.returncode, proc.stdout + proc.stderr


def test_valid_stdio_server_passes(tmp_path):
    code, out = run(tmp_path, STDIO)
    assert code == 0, out


def test_valid_http_server_passes(tmp_path):
    code, out = run(tmp_path, HTTP)
    assert code == 0, out


def test_name_different_from_filename_is_an_error(tmp_path):
    code, out = run(tmp_path, STDIO, filename="other.yaml")
    assert code == 1
    assert "must match the filename" in out


def test_missing_required_field_is_an_error(tmp_path):
    code, out = run(tmp_path, STDIO.replace('label: "My Server  (does things)"\n', ""))
    assert code == 1
    assert "Missing required field 'label'" in out


def test_unknown_transport_is_an_error(tmp_path):
    code, out = run(tmp_path, STDIO.replace("transport: stdio", "transport: sse"))
    assert code == 1
    assert "transport" in out and "sse" in out


def test_stdio_without_command_is_an_error(tmp_path):
    code, out = run(tmp_path, STDIO.replace("command: npx\n", ""))
    assert code == 1
    assert "stdio" in out and "'command'" in out


def test_http_without_url_is_an_error(tmp_path):
    code, out = run(tmp_path, HTTP.replace('url: "https://mcp.example.com/mcp"\n', ""))
    assert code == 1
    assert "'url'" in out


def test_empty_tags_is_an_error(tmp_path):
    code, out = run(tmp_path, STDIO.replace("tags: [web-search]", "tags: []"))
    assert code == 1
    assert "tags" in out


def test_misspelled_field_is_an_error(tmp_path):
    code, out = run(tmp_path, HTTP.replace("env_hint:", "env_hints:"))
    assert code == 1
    assert "Unknown field 'env_hints'" in out


def test_wrong_type_for_args_is_an_error(tmp_path):
    code, out = run(tmp_path, STDIO.replace('args: ["-y", "@org/server"]', "args: -y"))
    assert code == 1
    assert "'args' must be a list" in out


def test_invalid_yaml_is_an_error(tmp_path):
    code, out = run(tmp_path, "name: [unclosed\n")
    assert code == 1
    assert "Invalid YAML" in out


def test_one_bad_file_does_not_hide_a_good_one(tmp_path):
    run(tmp_path, STDIO.replace("name: my-server", "name: good"), filename="good.yaml")
    code, out = run(tmp_path, STDIO.replace("command: npx\n", ""))
    assert code == 1
    assert "✅ good" in out


def test_uppercase_name_is_an_error(tmp_path):
    code, out = run(
        tmp_path,
        STDIO.replace("name: my-server", "name: MyServer"),
        filename="MyServer.yaml",
    )
    assert code == 1
    assert "lowercase" in out


def test_command_on_an_http_server_is_an_error(tmp_path):
    code, out = run(tmp_path, HTTP + "command: npx\n")
    assert code == 1
    assert "'command'" in out and "stdio" in out


def test_url_on_a_stdio_server_is_an_error(tmp_path):
    code, out = run(tmp_path, STDIO + 'url: "https://mcp.example.com/mcp"\n')
    assert code == 1
    assert "'url'" in out and "http" in out
