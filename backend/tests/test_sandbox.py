import pytest
from app.services.code_sandbox import CodeSandboxService

def test_sandbox_normal_execution():
    code = """
def factorial(n):
    return 1 if n <= 1 else n * factorial(n - 1)

print("Factorial 5:", factorial(5))
"""
    res = CodeSandboxService.execute_python_code(code, timeout_seconds=3)
    assert res["success"] is True
    assert "Factorial 5: 120" in res["stdout"]
    assert res["error_type"] is None

def test_sandbox_network_egress_blocked():
    code = """
import urllib.request
urllib.request.urlopen("https://google.com")
"""
    res = CodeSandboxService.execute_python_code(code, timeout_seconds=3)
    assert res["success"] is False
    assert res["error_type"] == "network_violation"
    assert "Network egress is strictly forbidden" in res["stderr"] or "Network access is disabled" in res["stderr"]

def test_sandbox_infinite_loop_timeout():
    code = """
while True:
    pass
"""
    res = CodeSandboxService.execute_python_code(code, timeout_seconds=2)
    assert res["success"] is False
    assert res["error_type"] == "timeout"
    assert "timed out after 2 seconds" in res["output"]

def test_sandbox_fork_bomb_blocked():
    code = """
import os
for _ in range(10):
    os.fork()
"""
    res = CodeSandboxService.execute_python_code(code, timeout_seconds=3)
    assert res["success"] is False
    assert res["error_type"] == "fork_bomb_prevented"
    assert "fork bomb prevented" in res["stderr"]

def test_sandbox_syntax_error():
    code = """
def broken_syntax(
"""
    res = CodeSandboxService.execute_python_code(code, timeout_seconds=3)
    assert res["success"] is False
    assert res["error_type"] == "syntax_error"

def test_sandbox_scratch_directory_isolation():
    code = """
import os
print("CWD:", os.path.basename(os.getcwd()))
with open("test.txt", "w") as f:
    f.write("hello")
print("File written:", os.path.exists("test.txt"))
"""
    res = CodeSandboxService.execute_python_code(code, timeout_seconds=3)
    assert res["success"] is True
    assert "File written: True" in res["stdout"]
