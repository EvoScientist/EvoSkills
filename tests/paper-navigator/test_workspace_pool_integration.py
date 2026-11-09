"""Optional EvoScientist host regression, without model or network calls.

Tested with EvoScientist 0.4.1 and deepagents 0.7.34. The host's v0.4.1
requirement allows deepagents ~=0.7.32; dependency resolution is not an
exact reproduction of the issue reporter's (unavailable) lockfile.
"""

import json
from importlib.metadata import version
from types import SimpleNamespace

import pytest

pytest.importorskip("EvoScientist", reason="optional EvoScientist host integration")
pytest.importorskip("deepagents", reason="optional deepagents host integration")

host_backends = pytest.importorskip("EvoScientist.backends")
fs_middleware = pytest.importorskip("deepagents.middleware.filesystem")


def test_workspace_pool_execute_then_read_file(tmp_path):
    """A relative non-system pool survives real host middleware normalization."""
    if version("EvoScientist") != "0.4.1":
        pytest.skip("This regression targets EvoScientist 0.4.1")

    backend = host_backends.CustomSandboxBackend(
        root_dir=str(tmp_path), virtual_mode=True, inherit_env=False
    )
    middleware = fs_middleware.FilesystemMiddleware(
        backend=backend, tool_token_limit_before_evict=None
    )
    tools = {tool.name: tool for tool in middleware.tools}
    runtime = SimpleNamespace(tool_call_id="workspace-pool-integration")
    relative_path = "./paper-navigator/integration-run/pool.jsonl"
    record = {"paperId": "integration-sentinel", "title": "Host integration"}
    command = (
        "mkdir -p ./paper-navigator/integration-run && "
        f"printf '%s\\n' '{json.dumps(record)}' > {relative_path}"
    )
    # Invoke the actual tool functions. No mock, AST helper, model, credentials,
    # or network service is involved; runtime supplies only the tool-call ID.
    executed = tools["execute"].func(command=command, runtime=runtime)
    assert executed.artifact["exit_code"] == 0, executed.content
    assert json.loads((tmp_path / relative_path).read_text()) == record

    for path in (relative_path, relative_path[2:], "/" + relative_path[2:]):
        result = tools["read_file"].func(file_path=path, runtime=runtime)
        assert result.status == "success", (path, result.content)
        assert "integration-sentinel" in result.content
