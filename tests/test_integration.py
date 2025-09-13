"""
Integration tests for skoglib with real executables.

Tests end-to-end workflows with actual system tools and mock executables.
"""

import os
import tempfile
import time
from pathlib import Path
from unittest import TestCase

from skoglib import run_executable, ExecutableNotFoundError, ExecutionError


class TestRealExecutableIntegration(TestCase):
    """Test integration with real system executables."""
    
    def test_echo_integration(self):
        """Test integration with echo command."""
        result = run_executable("echo", ["Integration test message"])
        
        self.assertTrue(result.success)
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Integration test message", result.stdout)
        self.assertEqual(result.stderr, "")
        self.assertGreater(result.execution_time, 0)
    
    def test_ls_integration(self):
        """Test integration with ls command."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create test files
            test_file = Path(tmp_dir) / "test_file.txt"
            test_file.write_text("test content")
            
            result = run_executable("ls", ["-la"], cwd=tmp_dir)
            
            self.assertTrue(result.success)
            self.assertIn("test_file.txt", result.stdout)
            self.assertEqual(result.cwd, tmp_dir)
    
    def test_cat_integration(self):
        """Test integration with cat command."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
            test_content = "Hello, integration test!\nLine 2\nLine 3"
            tmp.write(test_content)
            tmp_path = tmp.name
        
        try:
            result = run_executable("cat", [tmp_path])
            
            self.assertTrue(result.success)
            self.assertEqual(result.stdout.strip(), test_content)
        finally:
            os.unlink(tmp_path)
    
    def test_grep_integration(self):
        """Test integration with grep command."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
            content = "line 1\nthis is a test line\nline 3\nanother test"
            tmp.write(content)
            tmp_path = tmp.name
        
        try:
            result = run_executable("grep", ["test", tmp_path])
            
            self.assertTrue(result.success)
            self.assertIn("this is a test line", result.stdout)
            self.assertIn("another test", result.stdout)
            self.assertNotIn("line 1", result.stdout)
            self.assertNotIn("line 3", result.stdout)
        finally:
            os.unlink(tmp_path)
    
    def test_wc_integration(self):
        """Test integration with wc (word count) command."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
            content = "word1 word2\nword3 word4\nword5"
            tmp.write(content)
            tmp_path = tmp.name
        
        try:
            result = run_executable("wc", ["-w", tmp_path])
            
            self.assertTrue(result.success)
            # Should count 5 words
            self.assertIn("5", result.stdout)
        finally:
            os.unlink(tmp_path)
    
    def test_find_integration(self):
        """Test integration with find command."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create nested directory structure
            sub_dir = Path(tmp_dir) / "subdir"
            sub_dir.mkdir()
            
            test_file = sub_dir / "test.txt"
            test_file.write_text("test")
            
            result = run_executable("find", [tmp_dir, "-name", "*.txt"], cwd=tmp_dir)
            
            self.assertTrue(result.success)
            self.assertIn("test.txt", result.stdout)


class TestMockExecutableIntegration(TestCase):
    """Test integration with mock executables for consistent testing."""
    
    def setUp(self):
        """Set up mock executables for testing."""
        self.tmp_dir = tempfile.mkdtemp()
        self.mock_executables = {}
        
        # Create mock successful tool
        self._create_mock_executable("mock_success", """#!/bin/bash
echo "Mock tool executed successfully"
echo "Args: $@"
exit 0
""")
        
        # Create mock failing tool
        self._create_mock_executable("mock_fail", """#!/bin/bash
echo "Mock tool failed" >&2
exit 1
""")
        
        # Create mock timeout tool
        self._create_mock_executable("mock_timeout", """#!/bin/bash
echo "Starting long operation..."
sleep 10
echo "Done"
""")
        
        # Create mock environment tool
        self._create_mock_executable("mock_env", """#!/bin/bash
echo "TEST_VAR=$TEST_VAR"
echo "USER=$USER"
""")
    
    def tearDown(self):
        """Clean up mock executables."""
        import shutil
        shutil.rmtree(self.tmp_dir)
    
    def _create_mock_executable(self, name, script_content):
        """Create a mock executable script."""
        script_path = Path(self.tmp_dir) / name
        script_path.write_text(script_content)
        script_path.chmod(0o755)
        self.mock_executables[name] = str(script_path)
    
    def test_mock_successful_execution(self):
        """Test execution with mock successful tool."""
        result = run_executable(
            self.mock_executables["mock_success"], 
            ["arg1", "arg2", "arg3"]
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Mock tool executed successfully", result.stdout)
        self.assertIn("Args: arg1 arg2 arg3", result.stdout)
    
    def test_mock_failing_execution(self):
        """Test execution with mock failing tool."""
        with self.assertRaises(ExecutionError) as cm:
            run_executable(self.mock_executables["mock_fail"])
        
        exception = cm.exception
        self.assertEqual(exception.exit_code, 1)
        self.assertIn("Mock tool failed", exception.stderr)
    
    def test_mock_failing_execution_no_check(self):
        """Test execution with mock failing tool without checking exit code."""
        result = run_executable(
            self.mock_executables["mock_fail"], 
            check_exit_code=False
        )
        
        self.assertFalse(result.success)
        self.assertEqual(result.exit_code, 1)
        self.assertIn("Mock tool failed", result.stderr)
    
    def test_mock_timeout_execution(self):
        """Test timeout handling with mock tool."""
        with self.assertRaises(ExecutionError) as cm:
            run_executable(
                self.mock_executables["mock_timeout"], 
                timeout=1.0
            )
        
        exception = cm.exception
        self.assertEqual(exception.exit_code, -1)  # Timeout indicator
        self.assertGreater(exception.execution_time, 0.9)
    
    def test_mock_environment_execution(self):
        """Test environment variable passing with mock tool."""
        env_vars = {"TEST_VAR": "integration_test_value"}
        result = run_executable(
            self.mock_executables["mock_env"], 
            env_vars=env_vars
        )
        
        self.assertTrue(result.success)
        self.assertIn("TEST_VAR=integration_test_value", result.stdout)
        self.assertIn("USER=", result.stdout)  # Should have USER from system


class TestEndToEndWorkflows(TestCase):
    """Test complete end-to-end workflows."""
    
    def test_file_processing_workflow(self):
        """Test a complete file processing workflow."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Step 1: Create a test file
            input_file = Path(tmp_dir) / "input.txt"
            input_content = "apple\nbanana\ncherry\napple\ndate\nbanana"
            input_file.write_text(input_content)
            
            # Step 2: Sort the file
            sorted_file = Path(tmp_dir) / "sorted.txt"
            result1 = run_executable("sort", [str(input_file)], cwd=tmp_dir)
            self.assertTrue(result1.success)
            sorted_file.write_text(result1.stdout)
            
            # Step 3: Get unique lines
            unique_file = Path(tmp_dir) / "unique.txt"
            result2 = run_executable("uniq", [str(sorted_file)], cwd=tmp_dir)
            self.assertTrue(result2.success)
            unique_file.write_text(result2.stdout)
            
            # Step 4: Count lines
            result3 = run_executable("wc", ["-l", str(unique_file)], cwd=tmp_dir)
            self.assertTrue(result3.success)
            
            # Verify workflow results
            self.assertIn("apple", result2.stdout)
            self.assertIn("banana", result2.stdout)
            self.assertIn("cherry", result2.stdout)
            self.assertIn("date", result2.stdout)
            
            # Should have 4 unique lines
            line_count = int(result3.stdout.strip().split()[0])
            self.assertEqual(line_count, 4)
    
    def test_git_like_workflow(self):
        """Test a git-like workflow with multiple commands."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Initialize directory structure
            result1 = run_executable("mkdir", ["-p", "project"], cwd=tmp_dir)
            self.assertTrue(result1.success)
            
            project_dir = Path(tmp_dir) / "project"
            
            # Create files
            readme = project_dir / "README.md"
            readme.write_text("# Test Project\n\nThis is a test.")
            
            code_file = project_dir / "main.py"
            code_file.write_text("print('Hello, World!')")
            
            # List files
            result2 = run_executable("ls", ["-la"], cwd=str(project_dir))
            self.assertTrue(result2.success)
            self.assertIn("README.md", result2.stdout)
            self.assertIn("main.py", result2.stdout)
            
            # Check file contents
            result3 = run_executable("cat", ["README.md"], cwd=str(project_dir))
            self.assertTrue(result3.success)
            self.assertIn("Test Project", result3.stdout)
    
    def test_pipeline_simulation(self):
        """Test simulating a pipeline of commands."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create test data
            data_file = Path(tmp_dir) / "data.txt"
            data_content = "\n".join([
                "user1,25,engineer",
                "user2,30,designer", 
                "user3,35,engineer",
                "user4,28,manager",
                "user5,32,engineer"
            ])
            data_file.write_text(data_content)
            
            # Step 1: Extract engineers only
            result1 = run_executable("grep", ["engineer", str(data_file)], cwd=tmp_dir)
            self.assertTrue(result1.success)
            
            engineers_data = result1.stdout.strip()
            self.assertIn("user1", engineers_data)
            self.assertIn("user3", engineers_data)
            self.assertIn("user5", engineers_data)
            self.assertNotIn("user2", engineers_data)
            self.assertNotIn("user4", engineers_data)
            
            # Step 2: Count engineers
            engineer_lines = engineers_data.split('\n')
            self.assertEqual(len(engineer_lines), 3)


class TestCrossEnvironmentCompatibility(TestCase):
    """Test compatibility across different environments."""
    
    def test_shell_independence(self):
        """Test that execution works regardless of shell."""
        # Test basic commands that should work in any environment
        commands_to_test = [
            (["echo", ["test"]], "test"),
            (["pwd", []], "/"),  # Should contain a path separator
        ]
        
        for (cmd, args), expected in commands_to_test:
            with self.subTest(command=cmd):
                result = run_executable(cmd, args)
                self.assertTrue(result.success)
                self.assertIn(expected, result.stdout)
    
    def test_path_handling(self):
        """Test proper path handling across systems."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create file with known name
            test_file = Path(tmp_dir) / "path_test.txt"
            test_file.write_text("path test")
            
            # Test relative and absolute path access
            result1 = run_executable("cat", [str(test_file)])
            self.assertTrue(result1.success)
            self.assertIn("path test", result1.stdout)
            
            # Test with working directory
            result2 = run_executable("cat", ["path_test.txt"], cwd=tmp_dir)
            self.assertTrue(result2.success)
            self.assertIn("path test", result2.stdout)
    
    def test_environment_isolation(self):
        """Test that environment variables are properly isolated."""
        # Test without custom environment
        result1 = run_executable("printenv", ["PATH"])
        self.assertTrue(result1.success)
        original_path = result1.stdout.strip()
        
        # Test with custom environment (should inherit system PATH plus custom vars)
        custom_env = {"CUSTOM_VAR": "test_value"}
        result2 = run_executable("printenv", ["CUSTOM_VAR"], env_vars=custom_env)
        self.assertTrue(result2.success)
        self.assertIn("test_value", result2.stdout)
        
        # Verify PATH is still available (inheritance works)
        result3 = run_executable("printenv", ["PATH"], env_vars=custom_env)
        self.assertTrue(result3.success)
        self.assertEqual(result3.stdout.strip(), original_path)


if __name__ == '__main__':
    import unittest
    unittest.main()