#!/usr/bin/env python3
"""
Unit and Integration Tests for agent-harness
Verifies language detection, zero-overwrite protection, template loading, and cross-IDE symlinks.
"""

import os
import sys
import unittest
import tempfile
import shutil

# Ensure bin/ is on sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BIN_DIR = os.path.join(SCRIPT_DIR, "..", "bin")
sys.path.insert(0, BIN_DIR)

import importlib.machinery
import importlib.util

# Load agent-harness module dynamically
loader = importlib.machinery.SourceFileLoader("agent_harness", os.path.join(BIN_DIR, "agent-harness"))
spec = importlib.util.spec_from_loader("agent_harness", loader)
ah = importlib.util.module_from_spec(spec)
loader.exec_module(ah)

class TestTestHarnessDetection(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_cargo_detection(self):
        with open(os.path.join(self.test_dir, "Cargo.toml"), "w") as f:
            f.write("[package]\nname = 'test'\n")
        res = ah.detect_test_harness(self.test_dir)
        self.assertIn("cargo test", res)
        self.assertIn("cargo clippy", res)

    def test_go_detection(self):
        with open(os.path.join(self.test_dir, "go.mod"), "w") as f:
            f.write("module test\n")
        res = ah.detect_test_harness(self.test_dir)
        self.assertIn("go test", res)
        self.assertIn("go vet", res)

    def test_node_detection(self):
        with open(os.path.join(self.test_dir, "package.json"), "w") as f:
            f.write('{"name": "test"}')
        res = ah.detect_test_harness(self.test_dir)
        self.assertIn("npm test", res)
        self.assertIn("tsc --noEmit", res)

    def test_python_detection(self):
        with open(os.path.join(self.test_dir, "pyproject.toml"), "w") as f:
            f.write("[tool.poetry]\nname = 'test'\n")
        res = ah.detect_test_harness(self.test_dir)
        self.assertIn("pytest", res)
        self.assertIn("ruff check", res)

    def test_monorepo_multi_stack_detection(self):
        with open(os.path.join(self.test_dir, "go.mod"), "w") as f:
            f.write("module monorepo\n")
        with open(os.path.join(self.test_dir, "package.json"), "w") as f:
            f.write('{"name": "frontend"}')
        res = ah.detect_test_harness(self.test_dir)
        self.assertIn("go test", res)
        self.assertIn("npm test", res)

    def test_bare_python_project_detection(self):
        # Tests a bare Python repo like agent-harness (no pyproject.toml, but has .py and tests/)
        tests_subdir = os.path.join(self.test_dir, "tests")
        os.makedirs(tests_subdir, exist_ok=True)
        with open(os.path.join(tests_subdir, "test_sample.py"), "w") as f:
            f.write("import unittest\n")
        with open(os.path.join(self.test_dir, "script.py"), "w") as f:
            f.write("print('hello')\n")
        
        res = ah.detect_test_harness(self.test_dir)
        self.assertIn("unittest", res)

class TestTemplateAndArchitectureParsing(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_template_loading(self):
        rules = ah.load_karpathy_rules()
        self.assertIn("先想再写", rules)
        self.assertIn("简单优先", rules)
        self.assertIn("手术式修改", rules)
        self.assertIn("目标驱动与自检验收", rules)

    def test_architecture_parsing_with_directory_fallback(self):
        # Create some dummy .rs and .py files
        with open(os.path.join(self.test_dir, "main.rs"), "w") as f:
            f.write("fn main() {}\n")
        with open(os.path.join(self.test_dir, "worker.py"), "w") as f:
            f.write("print('hello')\n")
        
        langs, entries = ah.parse_architecture(None, self.test_dir)
        self.assertTrue("Rust" in langs or "Python" in langs)
        self.assertIn("main.rs", entries)

    def test_extract_json_payload_with_noisy_logs(self):
        # Simulates CBM output with fake bracket in log message, valid JSON payload, and trailing log
        noisy_stdout = """level=info msg="allocator tuning {sqlite,tree_sitter}"
level=info msg="connecting to {host}:{port} invalid-json"
{"project": "Users-test-project", "nodes": 127, "edges": 255, "status": "ready"}
level=info msg="finished in 0.12s"
"""
        payload = ah.extract_json_payload(noisy_stdout)
        self.assertIsNotNone(payload)
        self.assertEqual(payload.get("project"), "Users-test-project")
        self.assertEqual(payload.get("nodes"), 127)

class TestInitExecutionAndSafety(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_zero_overwrite_protection(self):
        agents_path = os.path.join(self.test_dir, "AGENTS.md")
        secret_text = "# MY HAND-CRAFTED RULES - DO NOT OVERWRITE"
        with open(agents_path, "w", encoding="utf-8") as f:
            f.write(secret_text)

        # Run init
        ah.cmd_init(self.test_dir)

        # Verify content was untouched
        with open(agents_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertEqual(content, secret_text)

    def test_symlinks_creation(self):
        # Run init on clean directory
        ah.cmd_init(self.test_dir)

        # Verify AGENTS.md was created
        self.assertTrue(os.path.isfile(os.path.join(self.test_dir, "AGENTS.md")))

        # Verify compatibility symlinks (or copies) exist
        for alias in ["CLAUDE.md", "GEMINI.md", ".cursorrules"]:
            alias_path = os.path.join(self.test_dir, alias)
            self.assertTrue(os.path.exists(alias_path), f"Missing alias: {alias}")

    def test_gitignore_protection(self):
        git_ignore_path = os.path.join(self.test_dir, ".gitignore")
        with open(git_ignore_path, "w", encoding="utf-8") as f:
            f.write("node_modules/\n")

        ah.cmd_init(self.test_dir)

        with open(git_ignore_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn(".codebase-memory/", content)

    def test_safe_inject_mcp_with_corrupt_json(self):
        mcp_path = os.path.join(self.test_dir, "mcp.json")
        with open(mcp_path, "w", encoding="utf-8") as f:
            f.write("{ INVALID JSON ,,, ")

        ah.safe_inject_mcp(mcp_path, "TestIDE")

        # Verify .bak was created
        self.assertTrue(os.path.isfile(mcp_path + ".bak"))
        # Verify clean valid JSON was written
        import json
        with open(mcp_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertIn("codebase-memory-mcp", data["mcpServers"])

if __name__ == "__main__":
    unittest.main()
