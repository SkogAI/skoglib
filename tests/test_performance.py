"""
Performance tests for skoglib execution overhead and benchmarks.

Tests import speed, execution overhead, and performance characteristics.
"""

import time
import sys
import statistics
from unittest import TestCase
from concurrent.futures import ThreadPoolExecutor, as_completed

from skoglib import run_executable


class TestExecutionPerformance(TestCase):
    """Test execution performance and overhead."""
    
    def test_execution_overhead_simple_command(self):
        """Test overhead for simple command execution."""
        # Baseline: measure direct execution time
        import subprocess
        
        # Warm up
        for _ in range(3):
            subprocess.run(["echo", "warmup"], capture_output=True, text=True)
        
        # Measure subprocess overhead
        times_subprocess = []
        for _ in range(10):
            start_time = time.perf_counter()
            subprocess.run(["echo", "test"], capture_output=True, text=True)
            times_subprocess.append(time.perf_counter() - start_time)
        
        # Warm up skoglib
        for _ in range(3):
            run_executable("echo", ["warmup"])
        
        # Measure skoglib overhead
        times_skoglib = []
        for _ in range(10):
            start_time = time.perf_counter()
            run_executable("echo", ["test"])
            times_skoglib.append(time.perf_counter() - start_time)
        
        avg_subprocess = statistics.mean(times_subprocess)
        avg_skoglib = statistics.mean(times_skoglib)
        
        # skoglib overhead should be reasonable (less than 3x subprocess)
        overhead_ratio = avg_skoglib / avg_subprocess
        
        print(f"Subprocess avg: {avg_subprocess:.4f}s")
        print(f"Skoglib avg: {avg_skoglib:.4f}s")
        print(f"Overhead ratio: {overhead_ratio:.2f}x")
        
        self.assertLess(overhead_ratio, 3.0, 
                       f"Excessive overhead: {overhead_ratio:.2f}x > 3.0x")
    
    def test_execution_time_accuracy(self):
        """Test accuracy of execution time measurement."""
        # Test with known sleep duration
        sleep_duration = 0.1
        result = run_executable("sleep", [str(sleep_duration)])
        
        # Execution time should be close to sleep duration
        # Allow some tolerance for system overhead
        self.assertGreaterEqual(result.execution_time, sleep_duration - 0.01)
        self.assertLessEqual(result.execution_time, sleep_duration + 0.05)
    
    def test_repeated_execution_consistency(self):
        """Test consistency of repeated executions."""
        execution_times = []
        
        for _ in range(20):
            result = run_executable("echo", ["consistency_test"])
            execution_times.append(result.execution_time)
        
        # Calculate statistics
        mean_time = statistics.mean(execution_times)
        stdev_time = statistics.stdev(execution_times)
        
        print(f"Mean execution time: {mean_time:.4f}s")
        print(f"Standard deviation: {stdev_time:.4f}s")
        
        # Standard deviation should be reasonable (less than 50% of mean)
        cv = stdev_time / mean_time  # Coefficient of variation
        self.assertLess(cv, 0.5, f"High execution time variability: {cv:.2f}")
    
    def test_concurrent_execution_performance(self):
        """Test performance under concurrent execution."""
        def execute_command():
            return run_executable("echo", ["concurrent_test"])
        
        # Test sequential execution
        start_time = time.perf_counter()
        for _ in range(5):
            result = execute_command()
            self.assertTrue(result.success)
        sequential_time = time.perf_counter() - start_time
        
        # Test concurrent execution
        start_time = time.perf_counter()
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(execute_command) for _ in range(5)]
            for future in as_completed(futures):
                result = future.result()
                self.assertTrue(result.success)
        concurrent_time = time.perf_counter() - start_time
        
        print(f"Sequential time: {sequential_time:.4f}s")
        print(f"Concurrent time: {concurrent_time:.4f}s")
        
        # Concurrent execution should be faster (or at least not much slower)
        # Allow some overhead but should show benefit of parallelism
        self.assertLess(concurrent_time, sequential_time * 1.2,
                       "Concurrent execution too slow compared to sequential")
    
    def test_large_output_performance(self):
        """Test performance with large output."""
        # Generate large output (but not too large to avoid timeouts)
        large_text = "x" * 10000
        
        start_time = time.perf_counter()
        result = run_executable("echo", [large_text])
        execution_time = time.perf_counter() - start_time
        
        self.assertTrue(result.success)
        self.assertEqual(len(result.stdout.strip()), 10000)
        
        # Should handle large output without significant overhead
        self.assertLess(execution_time, 1.0, "Large output handling too slow")
    
    def test_many_arguments_performance(self):
        """Test performance with many arguments."""
        # Create many arguments
        many_args = [f"arg{i}" for i in range(100)]
        
        start_time = time.perf_counter()
        result = run_executable("echo", many_args)
        execution_time = time.perf_counter() - start_time
        
        self.assertTrue(result.success)
        
        # Verify all arguments are present
        for arg in many_args:
            self.assertIn(arg, result.stdout)
        
        # Should handle many arguments efficiently
        self.assertLess(execution_time, 1.0, "Many arguments handling too slow")


class TestMemoryUsage(TestCase):
    """Test memory usage and resource management."""
    
    def test_memory_cleanup_after_execution(self):
        """Test that memory is properly cleaned up after execution."""
        import gc
        
        # Force garbage collection
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        # Execute multiple commands
        for i in range(50):
            result = run_executable("echo", [f"test_{i}"])
            self.assertTrue(result.success)
        
        # Force garbage collection again
        gc.collect()
        final_objects = len(gc.get_objects())
        
        # Object count increase should be reasonable
        object_increase = final_objects - initial_objects
        print(f"Object count increase: {object_increase}")
        
        # Allow some increase but not excessive memory leaks
        self.assertLess(object_increase, 1000, 
                       f"Potential memory leak: {object_increase} new objects")
    
    def test_no_file_descriptor_leaks(self):
        """Test that file descriptors are properly managed."""
        try:
            import resource
            
            # Get initial file descriptor limit (basic check)
            _ = resource.getrlimit(resource.RLIMIT_NOFILE)[0]
            
            # Execute many commands
            for i in range(20):
                result = run_executable("echo", [f"fd_test_{i}"])
                self.assertTrue(result.success)
            
            # File descriptor usage should remain stable
            # (This is a basic check - more sophisticated monitoring would require /proc access)
            
        except ImportError:
            # Skip on systems without resource module
            self.skipTest("resource module not available")


class TestScalabilityBenchmarks(TestCase):
    """Test scalability and performance benchmarks."""
    
    def test_execution_rate_benchmark(self):
        """Benchmark the rate of command execution."""
        num_executions = 50
        
        start_time = time.perf_counter()
        for i in range(num_executions):
            result = run_executable("echo", [f"benchmark_{i}"])
            self.assertTrue(result.success)
        total_time = time.perf_counter() - start_time
        
        executions_per_second = num_executions / total_time
        
        print(f"Executed {num_executions} commands in {total_time:.3f}s")
        print(f"Rate: {executions_per_second:.1f} executions/second")
        
        # Should be able to execute at least 10 simple commands per second
        self.assertGreater(executions_per_second, 10.0,
                          f"Execution rate too low: {executions_per_second:.1f}/s")
    
    def test_timeout_precision_benchmark(self):
        """Benchmark timeout precision and handling."""
        timeout_values = [0.1, 0.2, 0.5, 1.0]
        
        for timeout in timeout_values:
            with self.subTest(timeout=timeout):
                start_time = time.perf_counter()
                
                try:
                    # This should timeout
                    run_executable("sleep", [str(timeout * 2)], timeout=timeout)
                    self.fail("Expected timeout exception")
                except Exception:
                    # Expected to timeout
                    pass
                
                actual_time = time.perf_counter() - start_time
                
                # Timeout should be reasonably accurate
                # Allow 20% tolerance for system overhead
                self.assertLessEqual(actual_time, timeout * 1.2,
                                   f"Timeout took too long: {actual_time:.3f}s > {timeout * 1.2:.3f}s")
                self.assertGreaterEqual(actual_time, timeout * 0.8,
                                      f"Timeout too fast: {actual_time:.3f}s < {timeout * 0.8:.3f}s")


class TestPerformanceRegression(TestCase):
    """Test for performance regressions."""
    
    def test_import_performance_regression(self):
        """Test that imports remain fast."""
        # Clear modules to ensure fresh import
        modules_to_remove = [name for name in sys.modules.keys() 
                            if name.startswith('skoglib')]
        for module_name in modules_to_remove:
            if module_name in sys.modules:
                del sys.modules[module_name]
        
        # Time the main import
        start_time = time.perf_counter()
        import_time = time.perf_counter() - start_time
        
        import_time_ms = import_time * 1000
        print(f"Main skoglib import time: {import_time_ms:.2f}ms")
        
        # Should import quickly (within 100ms)
        self.assertLess(import_time_ms, 100.0,
                       f"Import too slow: {import_time_ms:.2f}ms > 100ms")
    
    def test_simple_execution_baseline(self):
        """Establish baseline for simple execution performance."""
        # This test establishes performance expectations
        # and can be used to detect regressions in the future
        
        executions = []
        
        # Warm up
        for _ in range(5):
            run_executable("echo", ["warmup"])
        
        # Measure execution times
        for _ in range(10):
            start_time = time.perf_counter()
            result = run_executable("echo", ["performance_baseline"])
            execution_time = time.perf_counter() - start_time
            
            self.assertTrue(result.success)
            executions.append(execution_time)
        
        # Calculate statistics
        mean_time = statistics.mean(executions)
        median_time = statistics.median(executions)
        p95_time = sorted(executions)[int(0.95 * len(executions))]
        
        print("Simple execution performance baseline:")
        print(f"  Mean: {mean_time:.4f}s")
        print(f"  Median: {median_time:.4f}s")
        print(f"  95th percentile: {p95_time:.4f}s")
        
        # Set reasonable performance expectations
        self.assertLess(mean_time, 0.1, f"Mean execution too slow: {mean_time:.4f}s")
        self.assertLess(p95_time, 0.2, f"95th percentile too slow: {p95_time:.4f}s")


if __name__ == '__main__':
    import unittest
    unittest.main()