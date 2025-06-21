# Smart Debugger Usage Guide

## Two Essential Patterns

### Pattern 1: Debug Source Code with Inline Commands
Debug any Python file by setting a breakpoint and using an inline command:

```bash
# Quick debug with inline command
echo "print(f'Variable value: {my_variable}')" | pydebug-stdin --quiet src/modules/target.py 150

# Debug triggered by specific test
echo "print(f'Function args: {locals()}')" | pydebug-stdin --quiet src/modules/processor.py 75 -- tests/test_integration.py::TestClass::test_method -v
```

### Pattern 2: Debug with File Parameter (-f)
Create reusable debug scripts and reference them with `-f`:

```bash
# Create debug script
cat > /tmp/debug.py << 'EOF'
import json
print("=== Debug Info ===")
print(f"Variables: {[k for k in locals().keys() if not k.startswith('_')]}")
if 'data' in locals():
    print(f"Data: {json.dumps(data, indent=2)[:200]}...")
EOF

# Use the debug script file. First write the file then run. You place breakpoint in the file you want, then you run the test the calls that file. It's best to run from tests so you isolate the code. 
pydebug-stdin --quiet -f scratch/debug.py src/modules/condense.py 150 -- tests/test_smart_content/test_integration_pipeline.py::TestSmartContentIntegrationPipeline::test_complete_pipeline_with_real_llm -v
```

## Key Points

- **Inline commands**: Use `echo "command" |` for quick debugging
- **File parameter**: Use `-f debug_file.py` for complex or reusable debug scripts  
- **Specific tests**: Add `-- test_path::test_name -v` to run only the test that triggers your breakpoint
- **Always use `--quiet`**: Reduces noise and focuses on your debug output
- **Standalone mode**: Add `--mode standalone` when debugging non-test Python scripts