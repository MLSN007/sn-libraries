"""
Script to automatically update __init__.py files across the project.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
import ast

def get_class_names(file_path: Path) -> List[str]:
    """Extract only class names from a Python file using AST."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            tree = ast.parse(file.read())
            
        return [node.name for node in ast.walk(tree) 
                if isinstance(node, ast.ClassDef)]
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return []

def get_python_files(directory: Path) -> List[Tuple[str, List[str]]]:
    """Get all Python files in a directory and extract their class names."""
    python_files = []
    
    for file in directory.glob("*.py"):
        if file.name == "__init__.py":
            continue
            
        class_names = get_class_names(file)
        if class_names:
            python_files.append((file.name, class_names))
            
    return python_files

def generate_init_content(package_name: str, files: List[Tuple[str, List[str]]]) -> str:
    """Generate content for __init__.py file."""
    imports = []
    all_exports = []
    
    # First, collect all class names to be exported
    for file_name, class_names in sorted(files):
        for class_name in sorted(class_names):
            all_exports.append(class_name)
    
    # Then create the __all__ list first
    content = f'"""\n{package_name} package.\n"""\n\n'
    content += "__all__ = [\n"
    content += ",\n".join(f'    "{name}"' for name in sorted(all_exports))
    content += "\n]\n\n"
    
    # Finally add the imports
    for file_name, class_names in sorted(files):
        module_name = file_name[:-3]  # Remove .py extension
        for class_name in sorted(class_names):
            imports.append(f"from .{module_name} import {class_name}")
    
    content += "\n".join(imports)
    content += "\n"
    
    return content

def main():
    """Main function to update all __init__.py files."""
    root_dir = Path(__file__).parent
    src_dir = root_dir / "src"
    
    for package_dir in src_dir.iterdir():
        if not package_dir.is_dir() or package_dir.name.startswith("__"):
            continue
            
        files = get_python_files(package_dir)
        
        content = generate_init_content(package_dir.name, files) if files else \
                 f'"""\n{package_dir.name} package.\n"""\n\n__all__ = []\n'
        
        init_file = package_dir / "__init__.py"
        with open(init_file, "w", encoding="utf-8") as f:
            f.write(content)
            
    print("Successfully updated all __init__.py files")

if __name__ == "__main__":
    main()