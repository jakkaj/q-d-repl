"""Test multi-language debugger with real test repositories."""

import pytest
import tempfile
import os
import subprocess
import sys
from pathlib import Path

from smart_debugger.multi_language import setup_multi_language_debugger, debug_file


class TestMultiLanguageWithRealRepos:
    """Test multi-language debugger with actual standardized test repositories."""
    
    @pytest.fixture
    def python_test_repo_path(self):
        """Get path to Python test repository."""
        repo_path = Path(__file__).parent / "test-repos" / "python"
        return str(repo_path.absolute())
    
    @pytest.fixture
    def csharp_test_repo_path(self):
        """Get path to C# test repository."""
        repo_path = Path(__file__).parent / "test-repos" / "csharp"
        return str(repo_path.absolute())
    
    def test_python_repo_structure_exists(self, python_test_repo_path):
        """Verify Python test repository structure exists."""
        repo_path = Path(python_test_repo_path)
        
        assert repo_path.exists(), f"Python test repo not found at {repo_path}"
        assert (repo_path / "main.py").exists()
        assert (repo_path / "src" / "models.py").exists()
        assert (repo_path / "src" / "data_processor.py").exists()
        assert (repo_path / "src" / "web_service.py").exists()
        assert (repo_path / "tests" / "test_models.py").exists()
        assert (repo_path / "tests" / "test_data_processor.py").exists()
        assert (repo_path / "requirements.txt").exists()
    
    def test_csharp_repo_structure_exists(self, csharp_test_repo_path):
        """Verify C# test repository structure exists."""
        repo_path = Path(csharp_test_repo_path)
        
        assert repo_path.exists(), f"C# test repo not found at {repo_path}"
        assert (repo_path / "Calculator.csproj").exists()
        assert (repo_path / "Program.cs").exists()
        assert (repo_path / "Models" / "CalculationResult.cs").exists()
        assert (repo_path / "Services" / "CalculatorService.cs").exists()
        assert (repo_path / "Services" / "ICalculatorService.cs").exists()
        assert (repo_path / "Tests" / "CalculatorServiceTests.cs").exists()
        assert (repo_path / "Tests" / "CalculationResultTests.cs").exists()
    
    def test_language_detection_for_test_repos(self, python_test_repo_path, csharp_test_repo_path):
        """Test language detection works correctly for test repository files."""
        registry = setup_multi_language_debugger()
        
        # Test Python files
        python_files = [
            f"{python_test_repo_path}/main.py",
            f"{python_test_repo_path}/src/models.py",
            f"{python_test_repo_path}/src/data_processor.py",
            f"{python_test_repo_path}/tests/test_models.py"
        ]
        
        for file_path in python_files:
            if Path(file_path).exists():
                debugger = registry.get_debugger('python')
                assert debugger.supports_file(file_path), f"Python debugger should support {file_path}"
        
        # Test C# files
        csharp_files = [
            f"{csharp_test_repo_path}/Program.cs",
            f"{csharp_test_repo_path}/Models/CalculationResult.cs",
            f"{csharp_test_repo_path}/Services/CalculatorService.cs",
            f"{csharp_test_repo_path}/Tests/CalculatorServiceTests.cs"
        ]
        
        for file_path in csharp_files:
            if Path(file_path).exists():
                if registry.has_debugger('csharp'):
                    debugger = registry.get_debugger('csharp')
                    assert debugger.supports_file(file_path), f"C# debugger should support {file_path}"
    
    def test_python_models_file_content_analysis(self, python_test_repo_path):
        """Test analyzing content of Python models file."""
        models_file = f"{python_test_repo_path}/src/models.py"
        
        if not Path(models_file).exists():
            pytest.skip("Python models file not found")
        
        # Read the file to verify it has expected content
        with open(models_file, 'r') as f:
            content = f.read()
        
        # Verify it contains expected classes and patterns
        assert "class DataPoint" in content
        assert "class AnalysisResult" in content
        assert "class ProcessingConfig" in content
        assert "from pydantic import" in content
        # Models file has Pydantic models (async patterns are in data_processor.py)
        assert "@validator" in content  # Has Pydantic validators
    
    def test_csharp_program_file_content_analysis(self, csharp_test_repo_path):
        """Test analyzing content of C# Program file."""
        program_file = f"{csharp_test_repo_path}/Program.cs"
        
        if not Path(program_file).exists():
            pytest.skip("C# Program file not found")
        
        # Read the file to verify it has expected content
        with open(program_file, 'r') as f:
            content = f.read()
        
        # Verify it contains expected patterns
        assert "async Task Main" in content
        assert "namespace Calculator" in content
        assert "class Program" in content
        assert "await " in content  # Has async/await patterns
        assert "try" in content and "catch" in content  # Has error handling
    
    @pytest.mark.asyncio
    async def test_python_file_debugging_simulation(self, python_test_repo_path):
        """Simulate debugging Python files from test repository."""
        models_file = f"{python_test_repo_path}/src/models.py"
        
        if not Path(models_file).exists():
            pytest.skip("Python models file not found")
        
        # Test debugging a DataPoint creation
        # We'll debug line where DataPoint class is defined
        with open(models_file, 'r') as f:
            lines = f.readlines()
        
        # Find line with DataPoint class definition
        datapoint_line = None
        for i, line in enumerate(lines, 1):
            if "class DataPoint" in line:
                datapoint_line = i
                break
        
        if datapoint_line:
            # Mock debugging - we can't actually run the code without dependencies
            # but we can verify our debugger would handle it correctly
            registry = setup_multi_language_debugger()
            python_debugger = registry.get_debugger('python')
            
            assert python_debugger.supports_file(models_file)
            assert python_debugger.get_language_name() == 'python'
            assert python_debugger.validate_environment()
    
    def test_csharp_file_debugging_simulation(self, csharp_test_repo_path):
        """Simulate debugging C# files from test repository."""
        calculator_file = f"{csharp_test_repo_path}/Services/CalculatorService.cs"
        
        if not Path(calculator_file).exists():
            pytest.skip("C# calculator file not found")
        
        # Test that our debugger recognizes the file
        registry = setup_multi_language_debugger()
        
        if registry.has_debugger('csharp'):
            csharp_debugger = registry.get_debugger('csharp')
            
            assert csharp_debugger.supports_file(calculator_file)
            assert csharp_debugger.get_language_name() == 'csharp'
            # Note: validate_environment might be False if netcoredbg isn't installed
    
    def test_python_test_file_debugging_points(self, python_test_repo_path):
        """Identify good debugging points in Python test files."""
        test_file = f"{python_test_repo_path}/tests/test_models.py"
        
        if not Path(test_file).exists():
            pytest.skip("Python test file not found")
        
        with open(test_file, 'r') as f:
            lines = f.readlines()
        
        # Find test methods that would be good for debugging
        test_methods = []
        for i, line in enumerate(lines, 1):
            if "def test_" in line and "async" not in line:
                test_methods.append((i, line.strip()))
        
        assert len(test_methods) > 0, "Should have test methods to debug"
        
        # Verify we have pytest patterns
        content = ''.join(lines)
        assert "import pytest" in content
        assert "@pytest." in content
        assert "assert " in content
    
    def test_csharp_test_file_debugging_points(self, csharp_test_repo_path):
        """Identify good debugging points in C# test files."""
        test_file = f"{csharp_test_repo_path}/Tests/CalculatorServiceTests.cs"
        
        if not Path(test_file).exists():
            pytest.skip("C# test file not found")
        
        with open(test_file, 'r') as f:
            lines = f.readlines()
        
        # Find test methods (look for [Fact] and [Theory] attributes)
        test_methods = []
        for i, line in enumerate(lines, 1):
            if "[Fact]" in line or "[Theory]" in line:
                test_methods.append((i, line.strip()))
        
        assert len(test_methods) > 0, "Should have test methods to debug"
        
        # Verify we have xUnit patterns
        content = ''.join(lines)
        assert "using Xunit" in content
        assert "[Fact]" in content or "[Theory]" in content
        assert ".Should()." in content  # FluentAssertions
    
    def test_debugging_realistic_scenarios(self, python_test_repo_path):
        """Test realistic debugging scenarios that developers would encounter."""
        
        # Scenario 1: Debugging a Pydantic model validation
        models_file = f"{python_test_repo_path}/src/models.py"
        if Path(models_file).exists():
            with open(models_file, 'r') as f:
                lines = f.readlines()
            
            # Find validator methods
            for i, line in enumerate(lines, 1):
                if "@validator" in line:
                    # This would be a good line to debug validation logic
                    debug_line = i + 1  # Usually the function definition is next
                    assert debug_line > 0
                    break
        
        # Scenario 2: Debugging async method execution
        processor_file = f"{python_test_repo_path}/src/data_processor.py"
        if Path(processor_file).exists():
            with open(processor_file, 'r') as f:
                content = f.read()
            
            # Should have async methods for debugging
            assert "async def " in content
            assert "await " in content
            assert "asyncio" in content
    
    def test_debugging_async_csharp_scenarios(self, csharp_test_repo_path):
        """Test debugging async C# scenarios."""
        service_file = f"{csharp_test_repo_path}/Services/CalculatorService.cs"
        
        if Path(service_file).exists():
            with open(service_file, 'r') as f:
                content = f.read()
            
            # Should have async patterns for debugging
            assert "async Task" in content
            assert "await " in content
            assert "Task.Delay" in content or "ConfigureAwait" in content
            assert "SemaphoreSlim" in content  # Concurrency control
    
    def test_integration_with_smart_debugger_commands(self, python_test_repo_path):
        """Test how these repos integrate with Smart Debugger commands."""
        
        # These are the commands that would be used with Smart Debugger:
        models_file = f"{python_test_repo_path}/src/models.py"
        
        if Path(models_file).exists():
            # Example debugging commands for different scenarios:
            debug_scenarios = [
                {
                    "file": models_file,
                    "description": "Debug DataPoint validation",
                    "expression": "print(f'Validating value: {v}')",
                    "context": "Inside @validator method"
                },
                {
                    "file": f"{python_test_repo_path}/src/data_processor.py",
                    "description": "Debug async batch processing",
                    "expression": "print(f'Processing batch of {len(batch)} items')",
                    "context": "Inside _process_batch method"
                },
                {
                    "file": f"{python_test_repo_path}/tests/test_models.py",
                    "description": "Debug test execution",
                    "expression": "print(f'Test data point: {data_point.to_dict()}')",
                    "context": "Inside test method"
                }
            ]
            
            # Verify these files exist and would be debuggable
            for scenario in debug_scenarios:
                if Path(scenario["file"]).exists():
                    registry = setup_multi_language_debugger()
                    debugger = registry.get_debugger('python')
                    assert debugger.supports_file(scenario["file"])
    
    def test_repo_complexity_metrics(self, python_test_repo_path, csharp_test_repo_path):
        """Verify test repositories are sufficiently complex for real testing."""
        
        # Check Python repo complexity
        python_stats = self._analyze_repo_complexity(python_test_repo_path, ['.py'])
        
        assert python_stats['total_files'] >= 6, "Should have multiple Python files"
        assert python_stats['total_lines'] >= 500, "Should have substantial code"
        assert python_stats['async_patterns'] >= 10, "Should have async/await patterns"
        assert python_stats['test_methods'] >= 20, "Should have comprehensive tests"
        
        # Check C# repo complexity  
        csharp_stats = self._analyze_repo_complexity(csharp_test_repo_path, ['.cs'])
        
        assert csharp_stats['total_files'] >= 6, "Should have multiple C# files"
        assert csharp_stats['total_lines'] >= 500, "Should have substantial code"
        assert csharp_stats['async_patterns'] >= 5, "Should have async/await patterns"
        assert csharp_stats['test_methods'] >= 15, "Should have comprehensive tests"
    
    def _analyze_repo_complexity(self, repo_path: str, extensions: list) -> dict:
        """Analyze repository complexity metrics."""
        repo = Path(repo_path)
        stats = {
            'total_files': 0,
            'total_lines': 0,
            'async_patterns': 0,
            'test_methods': 0,
            'classes': 0,
            'methods': 0
        }
        
        for ext in extensions:
            for file_path in repo.rglob(f'*{ext}'):
                if file_path.is_file():
                    stats['total_files'] += 1
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            lines = content.split('\n')
                            stats['total_lines'] += len(lines)
                            
                            # Count patterns
                            stats['async_patterns'] += content.count('async ') + content.count('await ')
                            
                            if ext == '.py':
                                stats['test_methods'] += content.count('def test_')
                                stats['classes'] += content.count('class ')
                                stats['methods'] += content.count('def ')
                            elif ext == '.cs':
                                stats['test_methods'] += content.count('[Fact]') + content.count('[Theory]')
                                stats['classes'] += content.count('class ')
                                stats['methods'] += content.count('public ') + content.count('private ')
                    
                    except UnicodeDecodeError:
                        continue  # Skip binary files
        
        return stats


# Debugging command examples for use with Smart Debugger:
# 
# Python examples:
# echo "print(f'DataPoint created: {data_point.id} = {data_point.value}')" > scratch/debug_datapoint.py
# pydebug-stdin --quiet -f scratch/debug_datapoint.py tests/test-repos/python/src/models.py 15 -- -v
#
# echo "print(f'Processing batch size: {len(batch)}')" > scratch/debug_batch.py  
# pydebug-stdin --quiet -f scratch/debug_batch.py tests/test-repos/python/src/data_processor.py 95 -- -v
#
# echo "print(f'Test validation error: {exc_info.value}')" > scratch/debug_test.py
# pydebug-stdin --quiet -f scratch/debug_test.py tests/test-repos/python/tests/test_models.py 45 -- -v
#
# C# examples (when netcoredbg is available):
# echo "Console.WriteLine($\"Calculator result: {result.Value}\")" > scratch/debug_calc.cs
# smartdebug tests/test-repos/csharp/Services/CalculatorService.cs 45 "result.Value" --csharp
#
# echo "Console.WriteLine($\"Test data: {data}\")" > scratch/debug_test.cs
# smartdebug tests/test-repos/csharp/Tests/CalculatorServiceTests.cs 25 "data" --csharp