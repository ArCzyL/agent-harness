#!/usr/bin/env python3
"""
Unit and Integration Tests for agent-harness
Verifies language detection, zero-overwrite protection, template loading, and cross-IDE alias files.
"""

import contextlib
import io
import json
import os
import subprocess
import sys
import unittest
import tempfile
import shutil
from unittest import mock

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


def write(base, rel, body, encoding="utf-8"):
    path = os.path.join(base, *rel.split("/"))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding=encoding) as f:
        f.write(body)
    return path


class FakeRun(object):
    """Stands in for ah.run_cmd: answers by git subcommand and records each call."""

    def __init__(self, replies):
        self.replies = replies
        self.calls = []

    def __call__(self, cmd, check=False):
        self.calls.append(list(cmd))
        code, out = next((reply for name, reply in self.replies.items() if name in cmd), (1, ""))
        return subprocess.CompletedProcess(cmd, code, out, "")


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

    def test_node_detection_without_scripts_leaves_room_for_real_commands(self):
        with open(os.path.join(self.test_dir, "package.json"), "w") as f:
            f.write('{"name": "test"}')
        res = ah.detect_test_harness(self.test_dir)
        self.assertIn("scripts.test", res)
        self.assertNotIn("npm test", res)
        self.assertNotIn("npx tsc", res)
        self.assertNotIn("npm run lint", res)

    def test_node_detection_uses_tsconfig_scripts_and_lockfile(self):
        with open(os.path.join(self.test_dir, "package.json"), "w") as f:
            f.write('{"scripts": {"test": "vitest", "lint": "eslint ."}}')
        with open(os.path.join(self.test_dir, "tsconfig.json"), "w") as f:
            f.write("{}\n")
        with open(os.path.join(self.test_dir, "pnpm-lock.yaml"), "w") as f:
            f.write("lockfileVersion: 9\n")
        res = ah.detect_test_harness(self.test_dir)
        self.assertIn("pnpm test", res)
        self.assertIn("npx tsc --noEmit", res)
        self.assertIn("pnpm run lint", res)

    def test_python_detection(self):
        with open(os.path.join(self.test_dir, "pyproject.toml"), "w") as f:
            f.write("[tool.poetry]\nname = 'test'\n")
        res = ah.detect_test_harness(self.test_dir)
        self.assertIn("unittest", res)
        self.assertNotIn("<入口文件>", res)
        self.assertNotIn("pytest", res)
        self.assertNotIn("ruff", res)

    def test_python_pytest_and_ruff_when_configured(self):
        with open(os.path.join(self.test_dir, "pyproject.toml"), "w") as f:
            f.write("[tool.pytest.ini_options]\n[tool.ruff]\nline-length = 100\n")
        res = ah.detect_test_harness(self.test_dir)
        self.assertIn("`pytest`", res)
        self.assertIn("ruff check", res)
        self.assertNotIn("unittest", res)
        self.assertNotIn("py_compile", res)

    def test_monorepo_multi_stack_detection(self):
        with open(os.path.join(self.test_dir, "go.mod"), "w") as f:
            f.write("module monorepo\n")
        with open(os.path.join(self.test_dir, "package.json"), "w") as f:
            f.write('{"name": "frontend"}')
        res = ah.detect_test_harness(self.test_dir)
        self.assertIn("go test", res)
        self.assertIn("scripts.test", res)
        self.assertNotIn("npm test", res)
        self.assertNotIn("npx tsc", res)

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

    def test_plain_assert_tests_run_with_pytest(self):
        # unittest discover reports "Ran 0 tests ... OK" for pytest-style tests, a false green
        write(self.test_dir, "pyproject.toml", "[project]\nname = 'x'\n")
        write(self.test_dir, "tests/test_a.py", "def test_x():\n    assert 1 == 2\n")
        res = ah.detect_test_harness(self.test_dir)
        self.assertIn("`pytest`", res)
        self.assertNotIn("unittest", res)

    def test_tests_conftest_means_pytest(self):
        write(self.test_dir, "pyproject.toml", "[project]\nname = 'x'\n")
        write(self.test_dir, "tests/conftest.py", "")
        write(self.test_dir, "tests/test_a.py", "import unittest\n")
        self.assertIn("`pytest`", ah.detect_test_harness(self.test_dir))

    def test_python_without_tests_dir_gets_guidance_instead_of_a_failing_command(self):
        write(self.test_dir, "pyproject.toml", "[project]\nname = 'x'\n")
        res = ah.detect_test_harness(self.test_dir)
        self.assertIn("测试写进 `tests/` 后执行", res)
        self.assertEqual(ah.harness_commands("### 本项目测试与校验命令：\n" + res), ["agent-harness check"])

    def test_bun_runs_the_package_test_script(self):
        # `bun test` starts Bun's built-in runner; `bun run test` runs scripts.test
        write(self.test_dir, "package.json", '{"scripts": {"test": "vitest run"}}')
        write(self.test_dir, "bun.lock", "")
        res = ah.detect_test_harness(self.test_dir)
        self.assertIn("`bun run test`", res)
        self.assertNotIn("`bun test`", res)

    def test_py_compile_names_the_python_entry_files(self):
        write(self.test_dir, "bin/tool", "#!/usr/bin/env python3\n")
        write(self.test_dir, "tests/test_a.py", "import unittest\n")
        res = ah.detect_test_harness(self.test_dir)
        self.assertIn("`python3 -m py_compile bin/tool`", res)
        self.assertNotIn("<入口文件>", res)

    def test_monorepo_subprojects_run_commands_in_their_directory(self):
        write(self.test_dir, "web/package.json", '{"scripts": {"test": "vitest"}}')
        write(self.test_dir, "web/pnpm-lock.yaml", "lockfileVersion: 9\n")
        write(self.test_dir, "services/api/go.mod", "module api\n")
        res = ah.detect_test_harness(self.test_dir)
        self.assertIn("`cd services/api && go build ./... && go test -v ./...`", res)
        self.assertIn("`cd web && pnpm test`", res)
        self.assertNotIn("请在此填入", res)

    def test_monorepo_scan_skips_dependency_test_and_example_dirs_and_stops_at_two_levels(self):
        write(self.test_dir, "node_modules/dep/package.json", "{}")
        write(self.test_dir, "examples/demo/package.json", "{}")
        write(self.test_dir, "tests/fixtures/go.mod", "module f\n")
        write(self.test_dir, "a/b/c/Cargo.toml", "[package]\n")
        self.assertIn("请在此填入", ah.detect_test_harness(self.test_dir))

    def test_root_manifest_covers_its_whole_stack(self):
        write(self.test_dir, "package.json", '{"scripts": {"test": "turbo test"}}')
        write(self.test_dir, "packages/ui/package.json", '{"scripts": {"test": "vitest"}}')
        res = ah.detect_test_harness(self.test_dir)
        self.assertIn("`npm test`", res)
        self.assertNotIn("packages/ui", res)

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
        
        langs, entries = ah.parse_architecture(self.test_dir)
        self.assertTrue("Rust" in langs or "Python" in langs)
        self.assertIn("main.rs", entries)

    def test_bin_script_entry_point_fallback(self):
        bin_dir = os.path.join(self.test_dir, "bin")
        os.makedirs(bin_dir)
        with open(os.path.join(bin_dir, "agent-harness"), "w") as f:
            f.write("#!/usr/bin/env python3\n")
        with open(os.path.join(bin_dir, "agent-harness.cmd"), "w") as f:
            f.write("@echo off\n")
        langs, entries = ah.parse_architecture(self.test_dir)
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
        langs, _ = ah.parse_architecture(self.test_dir)
        self.assertEqual(langs, "Go")

    def test_scan_skips_generated_dirs_and_counts_tsx_as_typescript(self):
        for sub in ["venv/lib", "dist", "build", ".next"]:
            os.makedirs(os.path.join(self.test_dir, sub))
        with open(os.path.join(self.test_dir, "venv", "lib", "a.py"), "w") as f:
            f.write("x = 1\n")
        with open(os.path.join(self.test_dir, "dist", "a.js"), "w") as f:
            f.write("exports.a = 1\n")
        with open(os.path.join(self.test_dir, "build", "a.go"), "w") as f:
            f.write("package a\n")
        with open(os.path.join(self.test_dir, ".next", "a.js"), "w") as f:
            f.write("x\n")
        with open(os.path.join(self.test_dir, "App.tsx"), "w") as f:
            f.write("export const A = 1\n")
        with open(os.path.join(self.test_dir, "page.vue"), "w") as f:
            f.write("<template></template>\n")
        langs, _entries = ah.parse_architecture(self.test_dir)
        self.assertEqual(set(part.strip() for part in langs.split(",")), {"TypeScript", "Vue"})

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

    @unittest.skipIf(sys.platform == "win32", "the fake engine is a POSIX shell script")
    def test_run_cbm_cli_unwraps_mcp_tool_result_envelope(self):
        # codebase-memory-mcp 0.10.x prints an MCP tool result; the payload lives in structuredContent
        fake_bin = os.path.join(self.test_dir, "fake-cbm")
        with open(fake_bin, "w") as f:
            f.write("#!/bin/sh\necho 'level=info msg=\"start {x}\"'\n")
            f.write("echo '{\"content\":[{\"type\":\"text\",\"text\":\"{}\"}],"
                    "\"structuredContent\":{\"project\":\"demo\",\"nodes\":33,\"edges\":38},\"isError\":false}'\n")
        os.chmod(fake_bin, 0o755)
        orig_bin = ah.CBM_BIN
        ah.CBM_BIN = fake_bin
        try:
            res = ah.run_cbm_cli("index_repository")
        finally:
            ah.CBM_BIN = orig_bin
        self.assertEqual(res, {"project": "demo", "nodes": 33, "edges": 38})

    @unittest.skipIf(sys.platform == "win32", "the fake engine is a POSIX shell script")
    def test_run_cbm_cli_sends_params_on_stdin(self):
        # Engine 0.11 deprecates raw JSON as a positional argument; piped stdin is the supported form
        fake_bin = os.path.join(self.test_dir, "fake-cbm")
        argv_file = os.path.join(self.test_dir, "argv.txt")
        stdin_file = os.path.join(self.test_dir, "stdin.json")
        with open(fake_bin, "w") as f:
            f.write(f"#!/bin/sh\necho \"$@\" > '{argv_file}'\ncat > '{stdin_file}'\n")
            f.write("echo '{\"content\":[],\"structuredContent\":{\"ok\":true},\"isError\":false}'\n")
        os.chmod(fake_bin, 0o755)
        orig_bin = ah.CBM_BIN
        ah.CBM_BIN = fake_bin
        try:
            res = ah.run_cbm_cli("index_repository", {"repo_path": "/tmp/demo"})
        finally:
            ah.CBM_BIN = orig_bin
        import json
        self.assertEqual(res, {"ok": True})
        with open(argv_file) as f:
            self.assertEqual(f.read().split(), ["cli", "--json", "index_repository"])
        with open(stdin_file) as f:
            self.assertEqual(json.load(f), {"repo_path": "/tmp/demo"})

    def test_status_requests_json_project_list(self):
        # Engine 0.11 prints a text table for list_projects unless format=json is requested
        import io
        import contextlib
        fake_bin = os.path.join(self.test_dir, "fake-cbm")
        open(fake_bin, "w").close()
        calls = []
        orig_bin, orig_run = ah.CBM_BIN, ah.run_cbm_cli
        ah.CBM_BIN = fake_bin
        ah.run_cbm_cli = lambda tool, params=None: calls.append((tool, params)) or {
            "projects": [{"name": "a", "root_path": "/a"}, {"name": "b", "root_path": "/b"}]}
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out):
                ah.cmd_status()
        finally:
            ah.CBM_BIN, ah.run_cbm_cli = orig_bin, orig_run
        self.assertEqual(calls, [("list_projects", {"format": "json"})])
        self.assertIn("Indexed Projects: 2", out.getvalue())

        ah.CBM_BIN = fake_bin
        ah.run_cbm_cli = lambda tool, params=None: {"content": [{"type": "text", "text": "projects: 2"}]}
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out):
                ah.cmd_status()
        finally:
            ah.CBM_BIN, ah.run_cbm_cli = orig_bin, orig_run
        self.assertNotIn("Indexed Projects: 0", out.getvalue())
        self.assertIn("⚠️", out.getvalue())

class TestInitExecutionAndSafety(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        # Stub run_cbm_cli so unit tests are isolated and never register temp test dirs into CBM daemon
        self.orig_run_cbm_cli = ah.run_cbm_cli
        ah.run_cbm_cli = lambda tool, params=None: {"project": "mock-test-project", "nodes": 0, "edges": 0}

    def tearDown(self):
        ah.run_cbm_cli = self.orig_run_cbm_cli
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_init_indexes_repo_path(self):
        calls = []
        ah.run_cbm_cli = lambda tool, params=None: calls.append((tool, params)) or {"project": "p", "nodes": 1, "edges": 0}
        ah.cmd_init(self.test_dir)
        self.assertEqual(calls[0], ("index_repository", {"repo_path": os.path.abspath(self.test_dir)}))

    def test_init_warns_loudly_on_unrecognized_engine_output(self):
        import io
        import contextlib
        fake_bin = os.path.join(self.test_dir, "fake-cbm")
        open(fake_bin, "w").close()
        orig_bin = ah.CBM_BIN
        ah.CBM_BIN = fake_bin
        ah.run_cbm_cli = lambda tool, params=None: {"some_future_shape": True}
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out):
                ah.cmd_init(self.test_dir)
        finally:
            ah.CBM_BIN = orig_bin
        self.assertIn("⚠️", out.getvalue())
        self.assertNotIn("Graph indexed: 0 nodes", out.getvalue())

    def test_zero_overwrite_protection(self):
        agents_path = os.path.join(self.test_dir, "AGENTS.md")
        secret_text = "# MY HAND-CRAFTED RULES - DO NOT OVERWRITE"
        with open(agents_path, "w", encoding="utf-8") as f:
            f.write(secret_text)

        # Run init
        ah.cmd_init(self.test_dir)

        with open(agents_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertTrue(content.startswith(secret_text))
        self.assertEqual(content.count(secret_text), 1)
        self.assertIn("agent-harness:auto:languages", content)
        self.assertIn("agent-harness:auto:harness", content)
        self.assertIn("先想再写", content)
        self.assertIn("文档与代码对齐", content)
        self.assertIn("search_graph", content)
        self.assertEqual(ah.alignment_issues(self.test_dir), [])

        ah.cmd_init(self.test_dir)
        with open(agents_path, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), content)

    def test_init_leaves_complete_agents_md_unchanged(self):
        ah.cmd_init(self.test_dir)
        agents_path = os.path.join(self.test_dir, "AGENTS.md")
        with open(agents_path, "r", encoding="utf-8") as f:
            first = f.read()
        ah.cmd_init(self.test_dir)
        with open(agents_path, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), first)

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

    @unittest.skipIf(sys.platform == "win32", "creating symlinks needs extra privileges on Windows")
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

    def test_safe_inject_mcp_treats_empty_file_as_new_config(self):
        # Antigravity ships ~/.gemini/config/mcp_config.json as a 0-byte file
        mcp_path = os.path.join(self.test_dir, "mcp_config.json")
        open(mcp_path, "w").close()

        ah.safe_inject_mcp(mcp_path, "Antigravity")

        self.assertFalse(os.path.exists(mcp_path + ".bak"))
        import json
        with open(mcp_path, "r", encoding="utf-8") as f:
            self.assertIn("codebase-memory-mcp", json.load(f)["mcpServers"])

    def test_excludesfile_appends_without_replacing_existing_path(self):
        target = os.path.join(self.test_dir, "excludes.txt")
        with open(target, "w", encoding="utf-8") as f:
            f.write("*.log\n")
        calls = []

        def fake_run(cmd, check=False):
            calls.append(list(cmd))
            class R(object):
                returncode = 0
                stdout = target + "\n"
                stderr = ""
            return R()

        orig = ah.run_cmd
        ah.run_cmd = fake_run
        try:
            ah.configure_global_git_excludes()
            ah.configure_global_git_excludes()
        finally:
            ah.run_cmd = orig
        with open(target, "r", encoding="utf-8") as f:
            body = f.read()
        self.assertIn("*.log", body)
        self.assertEqual(body.count(".codebase-memory/"), 1)
        self.assertEqual(body.count("*.graph.db*"), 1)
        self.assertFalse(any(cmd[1:4] == ["config", "--global", "core.excludesfile"] for cmd in calls))

    def test_excludesfile_is_created_only_when_unset(self):
        home = os.path.join(self.test_dir, "home")
        os.makedirs(home)
        calls = []

        def fake_run(cmd, check=False):
            calls.append(list(cmd))
            class R(object):
                stderr = ""
                stdout = ""
                returncode = 1 if "--get" in cmd else 0
            return R()

        orig_run = ah.run_cmd
        ah.run_cmd = fake_run
        try:
            # expanduser reads USERPROFILE on Windows and HOME elsewhere
            with mock.patch.dict(os.environ, {"HOME": home, "USERPROFILE": home}):
                ah.configure_global_git_excludes()
        finally:
            ah.run_cmd = orig_run
        with open(os.path.join(home, ".gitignore_global"), "r", encoding="utf-8") as f:
            self.assertIn(".codebase-memory/", f.read())
        self.assertTrue(any(
            cmd[:4] == ["git", "config", "--global", "core.excludesfile"] for cmd in calls
        ))

    def test_init_still_writes_agents_md_when_the_engine_cannot_run(self):
        engine_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, engine_dir, True)
        fake_bin = write(engine_dir, "fake-cbm", "not a program\n")
        with mock.patch.object(ah, "CBM_BIN", fake_bin), mock.patch.object(ah, "run_cbm_cli", self.orig_run_cbm_cli):
            ah.cmd_init(self.test_dir)
        self.assertTrue(os.path.isfile(os.path.join(self.test_dir, "AGENTS.md")))

    @unittest.skipIf(sys.platform == "win32", "the fake engine is a POSIX shell script")
    def test_engine_timeout_counts_as_no_result(self):
        engine_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, engine_dir, True)
        fake_bin = write(engine_dir, "fake-cbm", "#!/bin/sh\nexec sleep 5\n")
        os.chmod(fake_bin, 0o755)
        with mock.patch.object(ah, "CBM_BIN", fake_bin), mock.patch.object(ah, "CBM_TIMEOUT", 0.2):
            self.assertIsNone(self.orig_run_cbm_cli("index_repository"))


class TestDocAlignment(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.orig_run_cbm_cli = ah.run_cbm_cli
        self.orig_changed = ah.list_changed_files
        ah.run_cbm_cli = lambda tool, params=None: {"project": "mock-test-project", "nodes": 0, "edges": 0}

    def tearDown(self):
        ah.run_cbm_cli = self.orig_run_cbm_cli
        ah.list_changed_files = self.orig_changed
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

    def test_rules_are_written_affirmatively(self):
        # A negated rule ("never B") names B; after context compression an agent may keep B and lose the "never"
        negations = ["严禁", "禁止", "不要", "不得", "绝不", "坚决不", "切勿", "避免"]
        ah.cmd_init(self.test_dir)
        with open(os.path.join(self.test_dir, "AGENTS.md"), "r", encoding="utf-8") as f:
            generated = f.read()
        with open(os.path.join(SCRIPT_DIR, "..", "templates", "karpathy_rules.md"), "r", encoding="utf-8") as f:
            template = f.read()
        with open(os.path.join(SCRIPT_DIR, "..", "AGENTS.md"), "r", encoding="utf-8") as f:
            repo_rules = f.read()
        for name, text in [("generated", generated), ("template", template),
                           ("fallback", ah.DEFAULT_KARPATHY_RULES), ("repo AGENTS.md", repo_rules)]:
            found = [w for w in negations if w in text]
            self.assertEqual(found, [], name)
        for text in [generated, repo_rules]:
            self.assertIn("只写正确做法", text)
            self.assertIn("长期要求写进本文件", text)

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

    def test_check_passes_right_after_init_even_if_graph_disagrees(self):
        # The graph's notion of entry points differs from check's filesystem rules; init must follow check
        arch_text = ("languages: 1  (cols: language files)\n  TypeScript 2\n"
                     "entry_points: 1  (cols: qn file)\n  demo.src.api.users.getUser src/api/users.ts\n")
        ah.run_cbm_cli = lambda tool, params=None: (
            {"content": [{"type": "text", "text": arch_text}]} if tool == "get_architecture"
            else {"project": "demo", "nodes": 33, "edges": 38}
        )
        os.makedirs(os.path.join(self.test_dir, "src", "api"))
        os.makedirs(os.path.join(self.test_dir, "bin"))
        for rel, body in [("package.json", '{"name": "demo"}'), ("src/index.ts", "main();\n"),
                          ("src/api/users.ts", "export function getUser() {}\n"),
                          ("bin/cli.js", "#!/usr/bin/env node\n")]:
            with open(os.path.join(self.test_dir, rel), "w") as f:
                f.write(body)

        ah.cmd_init(self.test_dir)

        self.assertEqual(ah.alignment_issues(self.test_dir), [])

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


    def test_every_bin_entry_is_written_and_checked(self):
        bin_dir = os.path.join(self.test_dir, "bin")
        os.makedirs(bin_dir)
        names = ["tool-{0:02d}".format(i) for i in range(11)]
        for name in names:
            with open(os.path.join(bin_dir, name), "w") as f:
                f.write("#!/bin/sh\n")
        ah.cmd_init(self.test_dir)
        with open(os.path.join(self.test_dir, "AGENTS.md"), "r", encoding="utf-8") as f:
            text = f.read()
        for name in names:
            self.assertIn("bin/" + name, text)
        self.assertEqual(ah.alignment_issues(self.test_dir), [])

    def test_doc_drift_names_unchanged_docs_that_cite_the_path(self):
        os.makedirs(os.path.join(self.test_dir, "docs"))
        with open(os.path.join(self.test_dir, "docs", "ARCH.md"), "w", encoding="utf-8") as f:
            f.write("Flow lives in `bin/tool`.\n")
        ah.list_changed_files = lambda target: ["bin/tool"]
        issues = ah.doc_drift_issues(self.test_dir)
        self.assertTrue(any("docs/ARCH.md" in item and "仍引用它" in item for item in issues))

    def test_doc_drift_passes_when_citing_docs_change_together(self):
        os.makedirs(os.path.join(self.test_dir, "docs"))
        with open(os.path.join(self.test_dir, "docs", "ARCH.md"), "w", encoding="utf-8") as f:
            f.write("Flow lives in `bin/tool`.\n")
        ah.list_changed_files = lambda target: ["bin/tool", "docs/ARCH.md"]
        self.assertEqual(ah.doc_drift_issues(self.test_dir), [])

    def test_auto_entry_list_is_not_treated_as_an_explanation(self):
        with open(os.path.join(self.test_dir, "AGENTS.md"), "w", encoding="utf-8") as f:
            f.write("<!-- agent-harness:auto:entries -->\n- `bin/tool`\n<!-- /agent-harness:auto:entries -->\n")
        ah.list_changed_files = lambda target: ["bin/tool"]
        issues = ah.doc_drift_issues(self.test_dir)
        self.assertTrue(any("没有写这个路径" in item for item in issues))
        self.assertFalse(any("仍引用它" in item for item in issues))

    def test_test_only_edits_do_not_require_doc_updates(self):
        ah.list_changed_files = lambda target: ["tests/test_harness.py", "src/test/helper.py"]
        self.assertEqual(ah.doc_drift_issues(self.test_dir), [])

    def test_uncited_logic_change_passes_after_any_doc_update(self):
        ah.list_changed_files = lambda target: ["src/new.py"]
        issues = ah.doc_drift_issues(self.test_dir)
        self.assertTrue(any("src/new.py" in item for item in issues))
        ah.list_changed_files = lambda target: ["src/new.py", "README.md"]
        self.assertEqual(ah.doc_drift_issues(self.test_dir), [])

    def replace_in_agents(self, old, new):
        path = os.path.join(self.test_dir, "AGENTS.md")
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        self.assertIn(old, text)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text.replace(old, new))

    def test_check_accepts_the_real_command_in_place_of_the_placeholder(self):
        write(self.test_dir, "pom.xml", "<project/>\n")
        write(self.test_dir, "src/main/java/App.java", "class App {}\n")
        ah.cmd_init(self.test_dir)
        self.replace_in_agents("`# 请在此填入该技术栈的单元测试命令（如 pytest / go test / npm test）`", "`mvn test`")
        self.replace_in_agents("`# 请在此填入该技术栈的构建/语法检查命令`", "`mvn -q compile`")
        self.assertEqual(ah.alignment_issues(self.test_dir), [])

    def test_check_accepts_an_equivalent_test_runner(self):
        write(self.test_dir, "tests/test_a.py", "import unittest\n")
        ah.cmd_init(self.test_dir)
        self.replace_in_agents("`python3 -m unittest discover -s tests -v`", "`pytest -q`")
        self.assertEqual(ah.alignment_issues(self.test_dir), [])

    def test_check_requires_a_test_command_but_leaves_lint_to_the_developer(self):
        write(self.test_dir, "Cargo.toml", "[package]\nname = 'test'\n")
        ah.cmd_init(self.test_dir)
        self.replace_in_agents("`cargo clippy --all-targets -- -D warnings`", "`cargo fmt --check`")
        self.assertEqual(ah.alignment_issues(self.test_dir), [])
        self.replace_in_agents("`cargo check && cargo test`", "`cargo build`")
        self.assertTrue(any("Cargo.toml" in item for item in ah.alignment_issues(self.test_dir)))

    def test_check_passes_right_after_init_in_a_monorepo(self):
        write(self.test_dir, "web/package.json", '{"scripts": {"test": "vitest"}}')
        write(self.test_dir, "web/src/a.ts", "export {}\n")
        write(self.test_dir, "server/go.mod", "module x\n")
        write(self.test_dir, "server/main.go", "package main\n")
        ah.cmd_init(self.test_dir)
        self.assertEqual(ah.alignment_issues(self.test_dir), [])

    def test_doc_drift_survives_a_non_utf8_markdown_file(self):
        write(self.test_dir, "docs/legacy.md", "说明见 `src/a.py`", encoding="gbk")
        ah.list_changed_files = lambda target: ["src/a.py"]
        issues = ah.doc_drift_issues(self.test_dir)
        self.assertTrue(any("docs/legacy.md" in item for item in issues), issues)

    def test_download_urls_are_not_citations(self):
        write(self.test_dir, "README.md", "curl -fsSL https://example.com/main/install.sh | bash\n")
        ah.list_changed_files = lambda target: ["install.sh", "AGENTS.md"]
        self.assertEqual(ah.doc_drift_issues(self.test_dir), [])

    def test_colocated_test_files_do_not_require_doc_updates(self):
        ah.list_changed_files = lambda target: ["pkg/foo_test.go", "src/foo.test.ts", "src/foo.spec.ts",
                                                "src/__tests__/foo.ts", "app/test_foo.py"]
        self.assertEqual(ah.doc_drift_issues(self.test_dir), [])

    def test_changelog_and_adr_are_history_not_explanations(self):
        write(self.test_dir, "CHANGELOG.md", "- refactor `src/a.py`\n")
        write(self.test_dir, "docs/adr/0001-db.md", "We chose `src/a.py`.\n")
        ah.list_changed_files = lambda target: ["src/a.py", "README.md"]
        self.assertEqual(ah.doc_drift_issues(self.test_dir), [])
        ah.list_changed_files = lambda target: ["src/a.py", "CHANGELOG.md"]
        self.assertTrue(any("没有写这个路径" in item for item in ah.doc_drift_issues(self.test_dir)))

    def test_changed_files_keep_non_ascii_paths_and_both_sides_of_a_rename(self):
        fake = FakeRun({"rev-parse": (0, "\n"), "status": (0, "?? docs/架构.md\0 M src/tool.py\0R  new.py\0old.py\0")})
        with mock.patch.object(ah, "run_cmd", fake), mock.patch.dict(os.environ):
            os.environ.pop("GIT_INDEX_FILE", None)
            self.assertEqual(self.orig_changed(self.test_dir), ["docs/架构.md", "src/tool.py", "new.py", "old.py"])

    def test_changed_files_are_relative_to_the_target_subdirectory(self):
        fake = FakeRun({"rev-parse": (0, "packages/api/\n"), "status": (0, " M packages/api/src/app.py\0")})
        with mock.patch.object(ah, "run_cmd", fake), mock.patch.dict(os.environ):
            os.environ.pop("GIT_INDEX_FILE", None)
            self.assertEqual(self.orig_changed(self.test_dir), ["src/app.py"])
        status_call = [cmd for cmd in fake.calls if "status" in cmd][0]
        self.assertEqual(status_call[-2:], ["--", "."])

    def test_commit_hook_checks_only_staged_changes(self):
        # git exports GIT_INDEX_FILE to pre-commit; the commit holds the index, not the work tree
        fake = FakeRun({"rev-parse": (0, "\n"), "status": (0, "M  src/a.py\0 M docs/b.md\0?? c.py\0")})
        with mock.patch.object(ah, "run_cmd", fake), mock.patch.dict(os.environ, {"GIT_INDEX_FILE": ".git/index"}):
            self.assertEqual(self.orig_changed(self.test_dir), ["src/a.py"])


class TestCommandLine(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.test_dir, True)
        for name, value in [("run_cbm_cli", lambda tool, params=None: {"nodes": 0, "edges": 0}),
                            ("list_changed_files", lambda target: None)]:
            patcher = mock.patch.object(ah, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_cbm_init_alias_runs_init(self):
        with mock.patch.object(sys, "argv", ["/home/u/.local/bin/cbm-init", self.test_dir]), \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            ah.main()
        self.assertTrue(os.path.isfile(os.path.join(self.test_dir, "AGENTS.md")))

    def test_main_writes_utf8_when_the_console_code_page_lacks_emoji(self):
        # Windows pipes default to the ANSI code page (cp1252 / cp936), which has no ✅ or ❌
        raw = io.BytesIO()
        legacy = io.TextIOWrapper(raw, encoding="cp1252")
        with mock.patch.object(sys, "argv", ["agent-harness", "check", self.test_dir]), \
                mock.patch.object(sys, "stdout", legacy), \
                mock.patch.object(sys, "stderr", io.TextIOWrapper(io.BytesIO(), encoding="cp1252")):
            with self.assertRaises(SystemExit):
                ah.main()
            legacy.flush()
        self.assertIn("❌", raw.getvalue().decode("utf-8"))


class TestStopHooks(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.test_dir, True)
        patcher = mock.patch.object(ah, "run_cbm_cli", lambda tool, params=None: {"nodes": 0, "edges": 0})
        patcher.start()
        self.addCleanup(patcher.stop)

    def read_json(self, rel):
        with open(os.path.join(self.test_dir, *rel.split("/")), "r", encoding="utf-8") as f:
            return json.load(f)

    def test_init_installs_stop_hooks_for_cursor_claude_code_and_antigravity(self):
        ah.cmd_init(self.test_dir)
        cursor = self.read_json(".cursor/hooks.json")
        self.assertEqual(cursor["version"], 1)
        self.assertEqual(cursor["hooks"]["stop"][0]["command"], "agent-harness verify --hook")
        self.assertEqual(cursor["hooks"]["stop"][0]["loop_limit"], 3)
        claude = self.read_json(".claude/settings.json")
        self.assertEqual(claude["hooks"]["Stop"][0]["hooks"][0],
                         {"type": "command", "command": "agent-harness verify --hook", "timeout": ah.HOOK_TIMEOUT})
        antigravity = self.read_json(".agents/hooks.json")
        self.assertEqual(antigravity["agent-harness-verify"]["Stop"][0]["command"], "agent-harness verify --hook")

    def test_init_merges_into_existing_hook_config_once(self):
        write(self.test_dir, ".claude/settings.json", json.dumps({
            "permissions": {"allow": ["Bash(ls)"]},
            "hooks": {"Stop": [{"hooks": [{"type": "command", "command": "echo mine"}]}]}}))
        write(self.test_dir, ".cursor/hooks.json", json.dumps({"version": 1, "hooks": {"stop": [{"command": "echo mine"}]}}))
        ah.cmd_init(self.test_dir)
        ah.cmd_init(self.test_dir)
        claude = self.read_json(".claude/settings.json")
        self.assertEqual(claude["permissions"], {"allow": ["Bash(ls)"]})
        self.assertEqual([h["command"] for group in claude["hooks"]["Stop"] for h in group["hooks"]],
                         ["echo mine", "agent-harness verify --hook"])
        cursor = self.read_json(".cursor/hooks.json")
        self.assertEqual([h["command"] for h in cursor["hooks"]["stop"]], ["echo mine", "agent-harness verify --hook"])

    def test_init_backs_up_an_unparseable_hook_config(self):
        write(self.test_dir, ".cursor/hooks.json", "{ not json")
        ah.cmd_init(self.test_dir)
        with open(os.path.join(self.test_dir, ".cursor", "hooks.json.bak"), "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), "{ not json")
        self.assertEqual(self.read_json(".cursor/hooks.json")["hooks"]["stop"][0]["command"], "agent-harness verify --hook")


class TestVerify(unittest.TestCase):
    FAILING = "python3 -c \"print('FAIL: probe'); raise SystemExit(1)\""
    MARKER = "python3 -c \"open('ran.txt', 'w').close()\""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.test_dir, True)
        patcher = mock.patch.object(ah, "VERIFY_RETRY_FILE", os.path.join(self.test_dir, "retries.json"))
        patcher.start()
        self.addCleanup(patcher.stop)

    def agents(self, command):
        write(self.test_dir, "AGENTS.md",
              "# demo\n\n- **项目名称**：`demo`\n\n"
              "### 本项目测试与校验命令：\n"
              "<!-- agent-harness:auto:harness -->\n"
              "- **单元测试**：`{0}`\n"
              "- **测试验证**：`# 请在此填入该技术栈的单元测试命令`\n"
              "- **Node/TS**：已有 `package.json`。测试命令写进 `scripts.test` 后再执行。\n"
              "<!-- /agent-harness:auto:harness -->\n"
              "- **自动执行**：每轮回复结束时运行 `agent-harness verify`。\n\n"
              "### 文档与代码对齐\n- **示例**：`echo later`\n".format(command))

    def respond(self, event, dirty=True):
        fake = FakeRun({"status": (0, " M a.py\n" if dirty else "")})
        with mock.patch.object(ah, "run_cmd", fake):
            return ah.verify_hook_response(self.test_dir, event)

    def test_reads_only_command_lines_under_the_test_heading(self):
        self.agents("make test")
        with open(os.path.join(self.test_dir, "AGENTS.md"), "r", encoding="utf-8") as f:
            self.assertEqual(ah.harness_commands(f.read()), ["make test"])

    def test_failure_reply_matches_each_ide(self):
        self.agents(self.FAILING)
        cursor = self.respond({"hook_event_name": "stop", "status": "completed", "loop_count": 0})
        self.assertIn("FAIL: probe", cursor["followup_message"])
        claude = self.respond({"hook_event_name": "Stop", "session_id": "s", "stop_hook_active": False})
        self.assertEqual(claude["decision"], "block")
        self.assertIn("FAIL: probe", claude["reason"])
        antigravity = self.respond({"conversationId": "c", "terminationReason": "NO_TOOL_CALL"})
        self.assertEqual(antigravity["decision"], "continue")
        self.assertIn("FAIL: probe", antigravity["reason"])

    def test_commands_run_only_on_a_dirty_tree_after_a_normal_stop(self):
        self.agents(self.MARKER)
        marker = os.path.join(self.test_dir, "ran.txt")
        self.assertEqual(self.respond({"status": "completed"}, dirty=False), {})
        self.assertEqual(self.respond({"status": "aborted"}), {})
        self.assertFalse(os.path.exists(marker))
        self.assertEqual(self.respond({"status": "completed"}), {})
        self.assertTrue(os.path.exists(marker))

    def test_claude_code_stops_asking_after_three_rounds(self):
        self.agents(self.FAILING)
        event = {"hook_event_name": "Stop", "session_id": "s", "stop_hook_active": True}
        replies = [self.respond(event) for _ in range(4)]
        self.assertEqual([r.get("decision") for r in replies], ["block", "block", "block", None])

    def test_hook_mode_reads_the_event_from_stdin(self):
        self.agents(self.FAILING)
        hooks_dir = os.path.join(self.test_dir, ".agents")
        os.makedirs(hooks_dir)
        self.assertEqual(ah.find_project_root(hooks_dir), os.path.abspath(self.test_dir))
        out = io.StringIO()
        with mock.patch.object(ah, "run_cmd", FakeRun({"status": (0, " M a.py\n")})), \
                mock.patch.object(sys, "stdin", io.StringIO(json.dumps({"status": "completed"}))), \
                contextlib.redirect_stdout(out):
            ah.cmd_verify(["--hook", self.test_dir])
        self.assertIn("FAIL: probe", json.loads(out.getvalue())["followup_message"])

    def test_manual_run_exits_nonzero_on_failure(self):
        self.agents(self.FAILING)
        out = io.StringIO()
        with contextlib.redirect_stdout(out), self.assertRaises(SystemExit) as cm:
            ah.cmd_verify([self.test_dir])
        self.assertEqual(cm.exception.code, 1)
        self.assertIn("FAIL: probe", out.getvalue())


@unittest.skipIf(sys.platform == "win32", "runs a POSIX fake git and sh")
class TestAgentStopHook(unittest.TestCase):
    """Runs a copy of .githooks/agent-stop.py in a temp dir with a dirty fake git and always-failing checks."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        hooks_dir = os.path.join(self.test_dir, ".githooks")
        os.makedirs(hooks_dir)
        shutil.copy(os.path.join(SCRIPT_DIR, "..", ".githooks", "agent-stop.py"), hooks_dir)
        with open(os.path.join(hooks_dir, "pre-commit"), "w") as f:
            f.write("#!/bin/sh\necho 'FAIL: probe'\nexit 1\n")
        self.fake_bin = os.path.join(self.test_dir, "fake-bin")
        os.makedirs(self.fake_bin)
        fake_git = os.path.join(self.fake_bin, "git")
        with open(fake_git, "w") as f:
            f.write("#!/bin/sh\necho '?? dirty.txt'\n")
        os.chmod(fake_git, 0o755)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def run_hook(self, event):
        import json
        import subprocess
        res = subprocess.run(
            [sys.executable, os.path.join(self.test_dir, ".githooks", "agent-stop.py")],
            input=json.dumps(event), capture_output=True, text=True,
            env=dict(os.environ, TMPDIR=self.test_dir, PATH=self.fake_bin + os.pathsep + os.environ["PATH"]),
        )
        return json.loads(res.stdout)

    def test_antigravity_normal_stop_reasons_trigger_verification(self):
        # Docs show "model_stop"; real Antigravity runs send "NO_TOOL_CALL"
        for reason in ["model_stop", "NO_TOOL_CALL"]:
            out = self.run_hook({"conversationId": reason, "terminationReason": reason, "executionNum": 0})
            self.assertEqual(out.get("decision"), "continue", reason)
            self.assertIn("FAIL: probe", out.get("reason", ""))

    def test_antigravity_error_stop_is_left_alone(self):
        for event in [{"terminationReason": "error", "error": "boom"},
                      {"terminationReason": "max_steps_exceeded", "error": ""}]:
            event["conversationId"] = "c"
            self.assertEqual(self.run_hook(event), {}, event)


if __name__ == "__main__":
    unittest.main()
