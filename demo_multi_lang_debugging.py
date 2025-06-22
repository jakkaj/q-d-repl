#!/usr/bin/env python3
"""
Demo script showing how to use the multi-language Smart Debugger 
with real test repositories.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from smart_debugger.multi_language import (
    setup_multi_language_debugger, 
    debug_file, 
    list_supported_languages,
    list_available_languages,
    get_language_info
)


def demo_multi_language_capabilities():
    """Demonstrate multi-language debugger capabilities."""
    print("🔧 Multi-Language Smart Debugger Demo")
    print("=" * 50)
    
    # Setup debugger
    registry = setup_multi_language_debugger()
    
    # Show supported languages
    supported = list_supported_languages()
    available = list_available_languages()
    
    print(f"📋 Supported languages: {', '.join(supported)}")
    print(f"✅ Available languages: {', '.join(available)}")
    print()
    
    # Show language details
    for lang in supported:
        info = get_language_info(lang)
        status = "✅" if lang in available else "❌"
        print(f"{status} {lang}:")
        print(f"   Debugger: {info.get('debugger_type', 'Unknown')}")
        if 'adapter' in info:
            adapter = info['adapter']
            print(f"   Command: {adapter.get('command', ['N/A'])[0]}")
            print(f"   Transport: {adapter.get('transport', 'N/A')}")
        print()


def demo_python_debugging_scenarios():
    """Show Python debugging scenarios with test repository."""
    print("🐍 Python Debugging Scenarios")
    print("-" * 30)
    
    # Test repository paths
    python_repo = Path("tests/test-repos/python")
    
    if not python_repo.exists():
        print("❌ Python test repository not found. Please run from project root.")
        return
    
    scenarios = [
        {
            "name": "Pydantic Model Validation",
            "file": python_repo / "src" / "models.py",
            "line_hint": "Look for @validator decorator methods",
            "debug_expression": "print(f'Validating {cls.__name__}: {v}')",
            "description": "Debug Pydantic validation logic"
        },
        {
            "name": "Async Data Processing",
            "file": python_repo / "src" / "data_processor.py", 
            "line_hint": "Look for async def _process_batch method",
            "debug_expression": "print(f'Processing batch of {len(batch)} items')",
            "description": "Debug async batch processing"
        },
        {
            "name": "Unit Test Execution", 
            "file": python_repo / "tests" / "test_models.py",
            "line_hint": "Look for def test_ methods",
            "debug_expression": "print(f'Test data: {data_point.to_dict()}')",
            "description": "Debug unit test execution"
        },
        {
            "name": "Web Service Handler",
            "file": python_repo / "src" / "web_service.py",
            "line_hint": "Look for async def analyze_data method", 
            "debug_expression": "print(f'Analyzing request: {await request.json()}')",
            "description": "Debug async web service handlers"
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"{i}. {scenario['name']}")
        print(f"   File: {scenario['file']}")
        print(f"   Hint: {scenario['line_hint']}")
        print(f"   Expression: {scenario['debug_expression']}")
        print(f"   Description: {scenario['description']}")
        
        if scenario['file'].exists():
            print("   Status: ✅ File exists and ready for debugging")
        else:
            print("   Status: ❌ File not found")
        print()
    
    print("💡 Example Smart Debugger commands:")
    print("   # Debug Pydantic validation")
    print("   echo \"print(f'Validating value: {v}')\" > scratch/debug_validation.py")
    print("   pydebug-stdin --quiet -f scratch/debug_validation.py tests/test-repos/python/src/models.py 25 -- -v")
    print()
    print("   # Debug async processing")
    print("   echo \"print(f'Batch size: {len(batch)}')\" > scratch/debug_batch.py")
    print("   pydebug-stdin --quiet -f scratch/debug_batch.py tests/test-repos/python/src/data_processor.py 95 -- -v")
    print()


def demo_csharp_debugging_scenarios():
    """Show C# debugging scenarios with test repository."""
    print("🔷 C# Debugging Scenarios")
    print("-" * 25)
    
    # Test repository paths
    csharp_repo = Path("tests/test-repos/csharp")
    
    if not csharp_repo.exists():
        print("❌ C# test repository not found. Please run from project root.")
        return
    
    scenarios = [
        {
            "name": "Async Calculator Operations",
            "file": csharp_repo / "Services" / "CalculatorService.cs",
            "line_hint": "Look for async Task<CalculationResult> methods",
            "debug_expression": "Console.WriteLine($\"Calculating: {a} + {b}\")",
            "description": "Debug async calculator operations with semaphore"
        },
        {
            "name": "Error Handling Logic",
            "file": csharp_repo / "Services" / "CalculatorService.cs", 
            "line_hint": "Look for division by zero check",
            "debug_expression": "Console.WriteLine($\"Division check: {a} / {b}\")",
            "description": "Debug error handling for invalid operations"
        },
        {
            "name": "Unit Test Execution",
            "file": csharp_repo / "Tests" / "CalculatorServiceTests.cs",
            "line_hint": "Look for [Theory] test methods",
            "debug_expression": "Console.WriteLine($\"Testing with: {a}, {b}\")",
            "description": "Debug parameterized unit tests"
        },
        {
            "name": "Data Model Serialization",
            "file": csharp_repo / "Models" / "CalculationResult.cs",
            "line_hint": "Look for ToJson() method",
            "debug_expression": "Console.WriteLine($\"Serializing: {Operation} = {Value}\")",
            "description": "Debug JSON serialization of calculation results"
        },
        {
            "name": "Main Application Flow",
            "file": csharp_repo / "Program.cs",
            "line_hint": "Look for async demonstration methods",
            "debug_expression": "Console.WriteLine($\"Demo step: {add}\")",
            "description": "Debug main application demonstration flow"
        }
    ]
    
    # Check if netcoredbg is available
    registry = setup_multi_language_debugger()
    csharp_available = registry.has_debugger('csharp') and registry.is_environment_valid('csharp')
    
    print(f"C# Debugging Status: {'✅' if csharp_available else '❌'} netcoredbg available")
    if not csharp_available:
        print("Note: Install netcoredbg for C# debugging: apt install netcoredbg")
    print()
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"{i}. {scenario['name']}")
        print(f"   File: {scenario['file']}")
        print(f"   Hint: {scenario['line_hint']}")
        print(f"   Expression: {scenario['debug_expression']}")
        print(f"   Description: {scenario['description']}")
        
        if scenario['file'].exists():
            print("   Status: ✅ File exists and ready for debugging")
        else:
            print("   Status: ❌ File not found")
        print()
    
    print("💡 Example Smart Debugger commands (when netcoredbg available):")
    print("   # Debug async calculator")
    print("   smartdebug tests/test-repos/csharp/Services/CalculatorService.cs 45 \"result.Value\" --csharp")
    print()
    print("   # Debug unit tests")
    print("   smartdebug tests/test-repos/csharp/Tests/CalculatorServiceTests.cs 25 \"expected\" --csharp")
    print()
    print("   # Build project first:")
    print("   cd tests/test-repos/csharp && dotnet build")
    print()


def demo_language_detection():
    """Demonstrate automatic language detection."""
    print("🎯 Language Detection Demo")
    print("-" * 25)
    
    test_files = [
        "tests/test-repos/python/main.py",
        "tests/test-repos/python/src/models.py",
        "tests/test-repos/python/tests/test_models.py",
        "tests/test-repos/csharp/Program.cs",
        "tests/test-repos/csharp/Services/CalculatorService.cs",
        "tests/test-repos/csharp/Tests/CalculatorServiceTests.cs"
    ]
    
    registry = setup_multi_language_debugger()
    
    for file_path in test_files:
        if Path(file_path).exists():
            # Detect language
            from smart_debugger.core import LanguageDetector
            detector = LanguageDetector()
            
            try:
                language = detector.detect_language(file_path)
                debugger = registry.get_debugger(language)
                supports = debugger.supports_file(file_path)
                
                print(f"📄 {file_path}")
                print(f"   Detected: {language}")
                print(f"   Debugger: {type(debugger).__name__}")
                print(f"   Supports: {'✅' if supports else '❌'}")
                print()
                
            except Exception as e:
                print(f"📄 {file_path}")
                print(f"   Error: {e}")
                print()


def demo_debugging_workflow():
    """Show complete debugging workflow."""
    print("🔄 Complete Debugging Workflow")
    print("-" * 30)
    
    print("1. 🎯 Language Detection")
    print("   - Automatic detection by file extension")
    print("   - Content-based detection for unknown extensions")
    print("   - Shebang line detection")
    print()
    
    print("2. 🔧 Debugger Selection")
    print("   - Plugin registry selects appropriate debugger")
    print("   - Python: Uses sys.settrace (native)")
    print("   - C#/F#: Uses netcoredbg via DAP")
    print("   - JavaScript/TypeScript: Uses Node.js inspector via DAP")
    print("   - Other languages: Uses respective DAP adapters")
    print()
    
    print("3. 🎛️ Environment Validation")
    print("   - Check if required debugging tools are available")
    print("   - Provide helpful error messages if tools missing")
    print("   - Graceful degradation for unavailable languages")
    print()
    
    print("4. 🐛 Debugging Execution")
    print("   - Set breakpoint at specified line")
    print("   - Execute program until breakpoint hit")
    print("   - Evaluate expression in breakpoint context")
    print("   - Return result in standardized format")
    print()
    
    print("5. 📊 Result Processing")
    print("   - Standardized DebugResult with Pydantic validation")
    print("   - Success/failure status")
    print("   - Expression result and output")
    print("   - Error messages and metadata")
    print()


def main():
    """Run the complete multi-language debugging demo."""
    try:
        demo_multi_language_capabilities()
        print()
        
        demo_language_detection() 
        print()
        
        demo_python_debugging_scenarios()
        print()
        
        demo_csharp_debugging_scenarios()
        print()
        
        demo_debugging_workflow()
        print()
        
        print("🎉 Multi-Language Smart Debugger Demo Complete!")
        print("=" * 50)
        print("✅ Features Demonstrated:")
        print("   • Multi-language support (Python, C#, JavaScript, etc.)")
        print("   • Automatic language detection")
        print("   • Plugin architecture for extensibility")
        print("   • Standardized debugging interface")
        print("   • Real-world test repositories")
        print("   • Async/await debugging support")
        print("   • Unit test debugging")
        print("   • Environment validation")
        print("   • Error handling and resilience")
        print()
        print("📚 Test Repositories Available:")
        print("   • tests/test-repos/python/ - Async data processing service")
        print("   • tests/test-repos/csharp/ - Async calculator with unit tests")
        print()
        print("🚀 Ready for real-world debugging scenarios!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()