import sys
from pathlib import Path
from types import ModuleType

def check_module_names(module_path: Path, prefix: str = "") -> None:
    """Check for duplicate names across modules."""
    if module_path.is_file() and module_path.suffix == '.py':
        module_name = f"{prefix}{module_path.stem}"
        try:
            if module_name != "__init__":
                print(f"\nChecking {module_path}...")
                with open(module_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Look for class definitions
                    class_lines = [line.strip() for line in content.split('\n') 
                                 if line.strip().startswith('class ')]
                    if class_lines:
                        print("Found classes:")
                        for line in class_lines:
                            print(f"  {line}")
        except Exception as e:
            print(f"Error reading {module_path}: {e}")
    
    elif module_path.is_dir():
        if module_path.name == '__pycache__':
            return
        new_prefix = f"{prefix}{module_path.name}." if prefix else f"{module_path.name}."
        for child in module_path.iterdir():
            check_module_names(child, new_prefix)

# Start checking from src directory
src_path = Path(__file__).parent.parent / 'src'
print(f"Checking for class definitions in {src_path}")
check_module_names(src_path) 