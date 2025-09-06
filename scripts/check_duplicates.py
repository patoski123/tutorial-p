# scripts/check_duplicates.py
import ast
import sys
from pathlib import Path

class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def extract_step_definitions(file_path):
    with open(file_path) as f:
        tree = ast.parse(f.read())
    
    steps = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call):
                    if hasattr(decorator.func, 'id') and decorator.func.id in ['given', 'when', 'then']:
                        if decorator.args:
                            arg = decorator.args[0]
                            if isinstance(arg, ast.Constant):
                                pattern = arg.value
                                pattern_type = "string"
                            elif isinstance(arg, ast.Call):
                                if hasattr(arg.func, 'attr') and arg.func.attr == 'parse':
                                    if arg.args and isinstance(arg.args[0], ast.Constant):
                                        pattern = arg.args[0].value
                                        pattern_type = "parse"
                                    else:
                                        pattern = "<complex_parse>"
                                        pattern_type = "parse"
                                else:
                                    pattern = "<function_call>"
                                    pattern_type = "other"
                            else:
                                pattern = "<unknown>"
                                pattern_type = "other"
                            
                            steps.append((decorator.func.id, pattern_type, pattern, node.lineno, node.name))
    return steps

def find_duplicates():
    steps_dir = Path("step_definitions")
    all_steps = {}
    duplicates_found = False
    
    for py_file in steps_dir.rglob("*_steps.py"):
        try:
            steps = extract_step_definitions(py_file)
            for step_type, pattern_type, pattern, lineno, func_name in steps:
                key = (step_type, pattern_type, pattern)
                if key in all_steps:
                    if not duplicates_found:
                        print(f"{Colors.RED}{Colors.BOLD}🚨 DUPLICATE BDD STEP DEFINITIONS DETECTED 🚨{Colors.END}")
                        print()
                        duplicates_found = True
                    
                    print(f"{Colors.RED}DUPLICATE: {step_type.upper()} {pattern_type}:'{pattern}'{Colors.END}")
                    print(f"  {Colors.YELLOW}First:{Colors.END}  {all_steps[key][0]}:{all_steps[key][1]} in {Colors.BLUE}{all_steps[key][2]}(){Colors.END}")
                    print(f"  {Colors.YELLOW}Second:{Colors.END} {py_file}:{lineno} in {Colors.BLUE}{func_name}(){Colors.END}")
                    print()
                else:
                    all_steps[key] = (py_file, lineno, func_name)
        except Exception as e:
            print(f"{Colors.RED}Error processing {py_file}: {e}{Colors.END}")
    
    if duplicates_found:
        print(f"{Colors.RED}{Colors.BOLD}❌ BUILD BLOCKED: Fix duplicate step definitions before pushing{Colors.END}")
        return 1
    else:
        print(f"{Colors.GREEN}✅ No duplicate step definitions found{Colors.END}")
        return 0

if __name__ == "__main__":
    sys.exit(find_duplicates())