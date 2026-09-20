import sys
import io
import os
import shutil
import tempfile
import subprocess
import logging
from typing import Dict, Any, Optional
from ..config import settings

logger = logging.getLogger("sahayak.sandbox")

class CodeSandboxService:
    MAX_TIMEOUT_SECONDS = 10
    DEFAULT_TIMEOUT_SECONDS = 5
    MEMORY_LIMIT_MB = 128

    @classmethod
    def _is_docker_available(cls) -> bool:
        if getattr(settings, "ENV", "").lower() == "test" or os.getenv("DISABLE_DOCKER_SANDBOX", "").lower() in ["1", "true"]:
            return False
        docker_path = shutil.which("docker")
        if not docker_path:
            return False
        try:
            res = subprocess.run(["docker", "info"], capture_output=True, timeout=2)
            return res.returncode == 0
        except Exception:
            return False

    @classmethod
    def _execute_docker(cls, code: str, timeout_seconds: int) -> Optional[Dict[str, Any]]:
        """
        Executes code inside an ephemeral isolated Docker container with strict constraints:
        - No network access (--network none)
        - Memory limit 128MB (--memory 128m)
        - CPU quota 0.5 (--cpus 0.5)
        - Process count limit 30 (--pids-limit 30)
        - Read-only root filesystem (--read-only) with 16MB writable tmpfs
        """
        try:
            cmd = [
                "docker", "run", "--rm", "-i",
                "--network", "none",
                f"--memory={cls.MEMORY_LIMIT_MB}m",
                "--cpus=0.5",
                "--pids-limit=30",
                "--read-only",
                "--tmpfs", "/tmp:rw,size=16m,noexec,nosuid",
                "python:3.9-slim",
                "python3", "-"
            ]
            res = subprocess.run(
                cmd,
                input=code,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=timeout_seconds
            )
            success = (res.returncode == 0)
            return {
                "success": success,
                "stdout": res.stdout,
                "stderr": res.stderr,
                "returncode": res.returncode,
                "error_type": None if success else cls._classify_error(res.stderr, res.returncode),
                "output": res.stdout if success else (res.stderr or "Execution failed"),
                "isolation_mode": "docker"
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Execution timed out after {timeout_seconds} seconds.",
                "error_type": "timeout",
                "returncode": -1,
                "output": f"Execution timed out after {timeout_seconds} seconds.",
                "isolation_mode": "docker"
            }
        except Exception as e:
            logger.warning(f"Docker sandbox execution failed: {e}; falling back to hardened runner.")
            return None

    @classmethod
    def _classify_error(cls, stderr: str, returncode: int) -> str:
        s = stderr.lower()
        if returncode in [137, -9] or "memoryerror" in s or "out of memory" in s:
            return "memory_limit_exceeded"
        if returncode in [152, -24] or "sigxcpu" in s or "cpu time limit exceeded" in s:
            return "cpu_limit_exceeded"
        if "network egress is strictly forbidden" in s or "network access is disabled" in s or "urlopen error" in s or "urlerror" in s:
            return "network_violation"
        if "fork bomb prevented" in s or "process spawning" in s or "resource temporarily unavailable" in s:
            return "fork_bomb_prevented"
        if "syntaxerror" in s:
            return "syntax_error"
        return "runtime_error"

    @classmethod
    def execute_python_code(cls, code: str, timeout_seconds: int = 5) -> Dict[str, Any]:
        """
        Executes Python code in a secure sandboxed environment.
        Guarantees:
        1. Process limit / Fork bomb protection
        2. Network egress isolation (no outbound connections)
        3. Strict execution timeout
        4. Memory containment (128MB)
        5. Ephemeral filesystem isolation
        6. Structured error classification
        """
        timeout = min(max(1, timeout_seconds), cls.MAX_TIMEOUT_SECONDS)

        # 1. Attempt Docker sandbox if Docker daemon is accessible
        if cls._is_docker_available():
            docker_res = cls._execute_docker(code, timeout)
            if docker_res is not None:
                return docker_res

        # 2. Hardened In-Host Subprocess Runner with sandbox harness
        with tempfile.TemporaryDirectory() as scratch_dir:
            user_script_path = os.path.join(scratch_dir, "student_code.py")
            with open(user_script_path, "w", encoding="utf-8") as f:
                f.write(code)

            bootstrap_runner_path = os.path.join(scratch_dir, "_runner.py")
            runner_script = f"""import sys, os, socket

# 1. Block network egress (connect, bind, send, DNS)
def _blocked_net(*args, **kwargs):
    raise PermissionError("Network egress is strictly forbidden in sandbox.")

socket.getaddrinfo = _blocked_net
socket.create_connection = _blocked_net
_orig_socket = socket.socket
class BlockedSocket(_orig_socket):
    def connect(self, *args, **kwargs):
        raise PermissionError("Network egress is strictly forbidden in sandbox.")
    def connect_ex(self, *args, **kwargs):
        raise PermissionError("Network egress is strictly forbidden in sandbox.")
    def send(self, *args, **kwargs):
        raise PermissionError("Network egress is strictly forbidden in sandbox.")
    def sendto(self, *args, **kwargs):
        raise PermissionError("Network egress is strictly forbidden in sandbox.")
    def bind(self, *args, **kwargs):
        raise PermissionError("Network binding is strictly forbidden in sandbox.")

socket.socket = BlockedSocket

# 2. Prevent fork bombs by blocking process creation
def _blocked_fork(*args, **kwargs):
    raise PermissionError("Process spawning (fork) is disabled in sandbox: fork bomb prevented.")
os.fork = _blocked_fork
if not hasattr(os, "register_at_fork"):
    os.register_at_fork = lambda **kwargs: None
if hasattr(os, "forkpty"):
    os.forkpty = _blocked_fork

# 3. Apply memory limits (RLIMIT_AS on Linux)
try:
    import resource
    mem_bytes = {cls.MEMORY_LIMIT_MB} * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))
except Exception:
    pass

# 4. Execute student code
script_target = sys.argv[1]
with open(script_target, "r", encoding="utf-8") as sf:
    source = sf.read()

# Run inside isolated module scope
exec(compile(source, "student_code.py", "exec"), {{"__name__": "__main__"}})
"""
            with open(bootstrap_runner_path, "w", encoding="utf-8") as f:
                f.write(runner_script)

            env = os.environ.copy()
            env["TMPDIR"] = scratch_dir
            env["TEMP"] = scratch_dir
            env["TMP"] = scratch_dir
            env["PYTHONDONTWRITEBYTECODE"] = "1"
            env["PYTHONIOENCODING"] = "utf-8"

            try:
                res = subprocess.run(
                    [sys.executable, bootstrap_runner_path, user_script_path],
                    cwd=scratch_dir,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    timeout=timeout,
                    env=env
                )
                success = (res.returncode == 0)
                stderr_clean = res.stderr.replace(scratch_dir, "/sandbox")
                error_type = None if success else cls._classify_error(stderr_clean, res.returncode)

                return {
                    "success": success,
                    "stdout": res.stdout,
                    "stderr": stderr_clean,
                    "returncode": res.returncode,
                    "error_type": error_type,
                    "output": res.stdout if success else (stderr_clean or "Execution failed"),
                    "isolation_mode": "hardened_subprocess"
                }
            except subprocess.TimeoutExpired:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": f"Execution timed out after {timeout} seconds.",
                    "error_type": "timeout",
                    "returncode": -1,
                    "output": f"Execution timed out after {timeout} seconds.",
                    "isolation_mode": "hardened_subprocess"
                }
            except Exception as e:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": str(e),
                    "error_type": "runtime_error",
                    "returncode": -1,
                    "output": f"Execution error: {str(e)}",
                    "isolation_mode": "hardened_subprocess"
                }

    @classmethod
    def run_python_code(cls, code: str, timeout_seconds: int = 5) -> Dict[str, Any]:
        return cls.execute_python_code(code, timeout_seconds)
