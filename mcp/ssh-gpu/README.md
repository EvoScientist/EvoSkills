# Remote SSH GPU Execution with MCP

> **WARNING: Full Unsupervised Remote Access**
>
> Configuring an SSH MCP server gives the AI agent **full, unsupervised access to the remote machine**.
> Every command the agent generates — including destructive ones — will execute on that machine without
> human approval. Only connect to machines you fully control and accept this risk explicitly.

This guide explains how to configure [EvoScientist](https://github.com/EvoScientist/EvoScientist) for remote GPU experiment execution using the [`mcp-server-ssh`](https://www.npmjs.com/package/mcp-server-ssh) MCP server.

## Overview

EvoScientist leverages MCP infrastructure to enable remote GPU execution. By configuring an SSH MCP server, your `code-agent` and `debug-agent` gain access to tools for remote operations:

| Tool | Description |
|------|-------------|
| `ssh_connect` | Open a persistent SSH connection (returns a `connectionId`) |
| `ssh_exec` | Execute a command on the remote server |
| `sftp_write` | Upload files to the remote server |
| `sftp_read` | Download files from the remote server |
| `sftp_ls` | List remote directory contents |
| `ssh_disconnect` | Close a connection |

**Typical flow:**

1. Agent calls `ssh_connect` with host and credentials → gets a `connectionId`
2. Uses `connectionId` for all subsequent operations (`ssh_exec`, `sftp_*`)
3. Connection stays open until `ssh_disconnect` or 30 min idle timeout

## Prerequisites

1. **Node.js 18+**: Required to run the MCP server via `npx`

2. **SSH Key Authentication**: Set up SSH key-based authentication to your remote GPU server

3. **Remote Environment**: Ensure your remote server has:
   - CUDA drivers installed
   - Required Python packages (or conda environment)
   - Sufficient disk space for experiments

## Configuration

### Step 1: Create MCP Configuration

Create or edit `~/.config/evoscientist/mcp.yaml`:

```yaml
ssh-gpu:
  transport: stdio
  command: npx
  args: ["-y", "mcp-server-ssh@1.0.2"]
  env:
    # Optional defaults — credentials can also be provided per-connection
    SSH_MCP_DEFAULT_USERNAME: "your-username"
    SSH_MCP_DEFAULT_KEY: "~/.ssh/id_ed25519"
  expose_to: [code-agent, debug-agent]
```

See [`mcp-ssh-gpu.yaml.example`](./mcp-ssh-gpu.yaml.example) for a fully commented template with multi-cluster examples.

### Step 2: Activate Configuration

Start an EvoScientist session. The SSH MCP server will be loaded automatically from `~/.config/evoscientist/mcp.yaml`.

You can also use `/mcp add` to add a server interactively, and `/mcp check <name>` to validate config and run a live connection test.

## Usage

### Remote Experiment Execution

When SSH MCP tools are available, the `code-agent` will:

1. **Connect to the remote server**:
   ```
   ssh_connect(host: "gpu-server.example.com", username: "user", privateKeyPath: "~/.ssh/id_ed25519")
   → returns connectionId
   ```

2. **Check GPU status**:
   ```
   ssh_exec(connectionId: "...", command: "nvidia-smi")
   ```

3. **Upload experiment code**:
   ```
   sftp_write(connectionId: "...", remotePath: "/home/user/experiment/train.py", content: "...")
   ```

4. **Execute GPU-dependent commands**:
   ```
   ssh_exec(connectionId: "...", command: "cd /home/user/experiment && python train.py")
   ```

5. **Handle long-running jobs** (non-interactive):
   ```
   ssh_exec(connectionId: "...", command: "screen -dmS experiment python train.py")
   ssh_exec(connectionId: "...", command: "screen -ls")  # check status
   ssh_exec(connectionId: "...", command: "tail -n 50 /home/user/experiment/output.log")
   ```

6. **Retrieve results**:
   ```
   sftp_read(connectionId: "...", remotePath: "/home/user/experiment/results.json")
   ```

> **Important:** All commands via `ssh_exec` must be **non-interactive**. Do not run commands that prompt for user input (e.g., `vim`, `passwd`, `apt upgrade` without `-y`).

### Remote Debugging

The `debug-agent` will use SSH tools to:

1. Reproduce failures on the remote server
2. Check remote environment (`nvidia-smi`, `python --version`, `pip list`)
3. Retrieve remote logs for analysis

## Troubleshooting

### SSH Connection Fails

1. Verify SSH key has proper permissions:
   ```bash
   chmod 600 ~/.ssh/id_ed25519
   ssh-add ~/.ssh/id_ed25519
   ```

2. Test manual SSH connection:
   ```bash
   ssh your-username@your-gpu-server.example.com
   ```

### SSH MCP Tools Not Available

1. Check `mcp.yaml` configuration
2. Verify `expose_to` includes `code-agent` and/or `debug-agent`
3. Reload agent session: `/new` or restart CLI

### Remote Commands Hang

Commands must be non-interactive. Use non-interactive alternatives:

```
# Start a detached screen session
ssh_exec "screen -dmS train python train.py"

# Check running sessions (non-interactive)
ssh_exec "screen -ls"

# Check output logs
ssh_exec "tail -n 100 /path/to/training.log"
```

## Security Considerations

> **Full unsupervised access**: The agent can execute any command on the remote machine without
> asking for confirmation. Treat this as equivalent to giving the agent an interactive shell.

- **SSH Keys**: Never commit SSH private keys to repositories
- **Credentials**: The `mcp-server-ssh` package supports per-connection credentials via `ssh_connect` — prefer this over env var defaults for sensitive environments
- **Network**: Consider using VPN or bastion hosts for production deployments
- **Least privilege**: Use a dedicated user with restricted permissions on the remote server
- **Host verification**: Pre-populate `~/.ssh/known_hosts` with verified host keys

## Backward Compatibility

When no SSH MCP server is configured:
- Agents execute experiments locally as before
- No changes to existing behavior
- No new dependencies required

## Further Reading

- [`mcp-server-ssh` on npm](https://www.npmjs.com/package/mcp-server-ssh)
- [MCP Documentation](https://modelcontextprotocol.io/)
- [MCP Server Directory](https://github.com/modelcontextprotocol/servers)
