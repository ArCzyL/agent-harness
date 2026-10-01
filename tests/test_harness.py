#!/usr/bin/env python3
"""
Unit and Integration Tests for agent-harness
Verifies language detection, zero-overwrite protection, template loading, and cross-IDE alias files.
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
        self.assertIn("agent-harness check", res)

    def test_node_bin_script_is_not_python(self):
        with open(os.path.join(self.test_dir, "package.json"), "w") as f:
            f.write('{"name": "cli"}')
        os.makedirs(os.path.join(self.test_dir, "bin"))
        with open(os.path.join(self.test_dir, "bin", "cli.js"), "w") as f:
            f.write("#!/usr/bin/env node\n")
        self.assertFalse(ah.detect_stacks(self.test_dir)["python"])

    def test_python_shebang_bin_script_is_python(self):
        os.makedirs(os.path.join(self.test_dir, "bin"))
        with open(os.path.join(self.test_dir, "bin", "tool"), "w") as f:
            f.write("#!/usr/bin/env python3\n")
        self.assertTrue(ah.detect_stacks(self.test_dir)["python"])

    def test_harness_always_includes_doc_alignment_check(self):
        with open(os.path.join(self.test_dir, "Cargo.toml"), "w") as f:
            f.write("[package]\nname = 'test'\n")
        res = ah.detect_test_harness(self.test_dir)
        self.assertIn("agent-harness check", res)

class TestTemplateAndArchitectureParsing(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_template_loading(self):
        rules = ah.load_karpathy_rules()
        self.assertTrue(rules.startswith("## 2. "), "Rules section must be numbered 2 between sections 1 and 3")
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

    def test_bin_script_entry_point_fallback(self):
        bin_dir = os.path.join(self.test_dir, "bin")
        os.makedirs(bin_dir)
        with open(os.path.join(bin_dir, "agent-harness"), "w") as f:
            f.write("#!/usr/bin/env python3\n")
        with open(os.path.join(bin_dir, "agent-harness.cmd"), "w") as f:
            f.write("@echo off\n")
        langs, entries = ah.parse_architecture(None, self.test_dir)
        self.assertIn("bin/agent-harness", entries)
        self.assertNotIn("bin/agent-harness.cmd", entries)

    def test_directory_scan_excludes_by_exact_name_only(self):
        for sub in ["src/targets", "src/vendors", "node_modules/dep"]:
            os.makedirs(os.path.join(self.test_dir, sub))
        for sub in ["src/targets", "src/vendors"]:
            with open(os.path.join(self.test_dir, sub, "a.go"), "w") as f:
                f.write("package a\n")
        for i in range(5):
            with open(os.path.join(self.test_dir, "node_modules", "dep", "m{0}.js".format(i)), "w") as f:
                f.write("module.exports = {}\n")
        langs, _ = ah.parse_architecture(None, self.test_dir)
        self.assertEqual(langs, "Go")

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
        # Stub run_cbm_cli so unit tests are isolated and never register temp test dirs into CBM daemon
        self.orig_run_cbm_cli = ah.run_cbm_cli
        ah.run_cbm_cli = lambda args: {"project": "mock-test-project", "nodes": 0, "edges": 0}

    def tearDown(self):
        ah.run_cbm_cli = self.orig_run_cbm_cli
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

    def test_alias_files_import_agents_md(self):
        ah.cmd_init(self.test_dir)

        self.assertTrue(os.path.isfile(os.path.join(self.test_dir, "AGENTS.md")))
        # Import stubs instead of symlinks: tools that read several rule files (e.g. Cursor) load the rules once
        for alias in ["CLAUDE.md", "GEMINI.md"]:
            alias_path = os.path.join(self.test_dir, alias)
            self.assertFalse(os.path.islink(alias_path), f"{alias} should not be a symlink")
            with open(alias_path, "r", encoding="utf-8") as f:
                self.assertEqual(f.read().strip(), "@AGENTS.md")
        self.assertFalse(os.path.lexists(os.path.join(self.test_dir, ".cursorrules")))

    def test_init_migrates_legacy_symlinks_and_keeps_handwritten_alias(self):
        with open(os.path.join(self.test_dir, "AGENTS.md"), "w", encoding="utf-8") as f:
            f.write("# rules\n")
        os.symlink("AGENTS.md", os.path.join(self.test_dir, "CLAUDE.md"))
        os.symlink("AGENTS.md", os.path.join(self.test_dir, ".cursorrules"))
        with open(os.path.join(self.test_dir, "GEMINI.md"), "w", encoding="utf-8") as f:
            f.write("# my gemini notes\n")

        ah.cmd_init(self.test_dir)

        claude_path = os.path.join(self.test_dir, "CLAUDE.md")
        self.assertFalse(os.path.islink(claude_path))
        with open(claude_path, "r", encoding="utf-8") as f:
            self.assertEqual(f.read().strip(), "@AGENTS.md")
        self.assertFalse(os.path.lexists(os.path.join(self.test_dir, ".cursorrules")))
        with open(os.path.join(self.test_dir, "GEMINI.md"), "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), "# my gemini notes\n")

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


class TestDocAlignment(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.orig_run_cbm_cli = ah.run_cbm_cli
        ah.run_cbm_cli = lambda args: {"project": "mock-test-project", "nodes": 0, "edges": 0}

    def tearDown(self):
        ah.run_cbm_cli = self.orig_run_cbm_cli
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_init_embeds_auto_markers_and_doc_rule(self):
        ah.cmd_init(self.test_dir)
        with open(os.path.join(self.test_dir, "AGENTS.md"), "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("agent-harness:auto:languages", content)
        self.assertIn("agent-harness:auto:entries", content)
        self.assertIn("agent-harness:auto:harness", content)
        self.assertIn("文档与代码对齐", content)
        self.assertIn("agent-harness check", content)

    def test_init_graph_rule_degrades_when_tool_unavailable(self):
        ah.cmd_init(self.test_dir)
        with open(os.path.join(self.test_dir, "AGENTS.md"), "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("若工具不可用", content)
        self.assertNotIn("严禁直接全文盲目 grep", content)

    def test_check_language_needs_whole_word(self):
        with open(os.path.join(self.test_dir, "main.go"), "w") as f:
            f.write("package main\n")
        with open(os.path.join(self.test_dir, "AGENTS.md"), "w", encoding="utf-8") as f:
            f.write("Built with Google tools. `main.go`. Run go test ./...\n")
        issues = ah.alignment_issues(self.test_dir)
        self.assertTrue(any("Go 代码" in item for item in issues), issues)

    def test_check_missing_agents_md(self):
        issues = ah.alignment_issues(self.test_dir)
        self.assertTrue(any("AGENTS.md" in item for item in issues))

    def test_check_detects_language_and_harness_drift(self):
        with open(os.path.join(self.test_dir, "Cargo.toml"), "w") as f:
            f.write("[package]\nname = 'test'\n")
        with open(os.path.join(self.test_dir, "main.rs"), "w") as f:
            f.write("fn main() {}\n")
        ah.cmd_init(self.test_dir)
        self.assertEqual(ah.alignment_issues(self.test_dir), [])

        agents_path = os.path.join(self.test_dir, "AGENTS.md")
        with open(agents_path, "r", encoding="utf-8") as f:
            content = f.read().replace("Rust", "Nope").replace("cargo", "nope")
        with open(agents_path, "w", encoding="utf-8") as f:
            f.write(content)

        issues = ah.alignment_issues(self.test_dir)
        self.assertTrue(any("Rust" in item for item in issues))
        self.assertTrue(any("Cargo.toml" in item for item in issues))

    def test_sync_refreshes_marked_fields_and_preserves_custom_rules(self):
        with open(os.path.join(self.test_dir, "Cargo.toml"), "w") as f:
            f.write("[package]\nname = 'test'\n")
        ah.cmd_init(self.test_dir)

        agents_path = os.path.join(self.test_dir, "AGENTS.md")
        with open(agents_path, "a", encoding="utf-8") as f:
            f.write("\n- KEEPME-CUSTOM-RULE\n")

        with open(os.path.join(self.test_dir, "go.mod"), "w") as f:
            f.write("module test\n")
        ah.cmd_sync(self.test_dir)

        with open(agents_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("KEEPME-CUSTOM-RULE", content)
        self.assertIn("go test", content)
        self.assertIn("cargo test", content)
        self.assertEqual(ah.alignment_issues(self.test_dir), [])

    def test_sync_refuses_to_rewrite_unmarked_handwritten_docs(self):
        agents_path = os.path.join(self.test_dir, "AGENTS.md")
        secret = "# MY HAND-CRAFTED RULES - DO NOT OVERWRITE\n"
        with open(agents_path, "w", encoding="utf-8") as f:
            f.write(secret)

        with self.assertRaises(SystemExit) as cm:
            ah.cmd_sync(self.test_dir)
        self.assertEqual(cm.exception.code, 1)

        with open(agents_path, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), secret)


if __name__ == "__main__":
    unittest.main()
