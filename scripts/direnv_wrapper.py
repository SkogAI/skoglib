import subprocess


def run_command(command, cwd=None, env=None):
    """Run a shell command and return (stdout, stderr, returncode)."""
    result = subprocess.run(
        command, shell=True, cwd=cwd, env=env, capture_output=True, text=True
    )
    return result.stdout, result.stderr, result.returncode


def direnv(command="status", cwd=None):
    """Simple wrapper for direnv commands."""
    cmd = f"direnv {command}"
    return run_command(cmd, cwd=cwd)
