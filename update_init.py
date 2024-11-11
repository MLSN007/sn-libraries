import os
from pathlib import Path
from typing import Dict, List, Set, Tuple

def find_python_files(directory: Path) -> Dict[Path, List[Tuple[str, str]]]:
    """
    Find all Python files and their classes in the given directory and subdirectories.
    
    Args:
        directory (Path): Root directory to search from
        
    Returns:
        Dict[Path, List[Tuple[str, str]]]: Dictionary mapping directories to (class_name, file_path) tuples
    """
    modules: Dict[Path, List[Tuple[str, str]]] = {}
    
    for path in directory.rglob("*.py"):
        if path.name == "__init__.py":
            continue
            
        dir_path = path.parent
        if dir_path not in modules:
            modules[dir_path] = []
            
        # Convert file name to class name (e.g., proxy_manager.py -> ProxyManager)
        class_name = "".join(word.capitalize() for word in path.stem.split("_"))
        # Store relative path from src
        rel_path = path.relative_to(directory)
        modules[dir_path].append((class_name, rel_path))
    
    return modules

def create_init_content(directory: Path, root_dir: Path, all_modules: Dict[Path, List[Tuple[str, str]]]) -> str:
    """
    Create content for __init__.py file.
    
    Args:
        directory (Path): Directory to create __init__.py for
        root_dir (Path): Root directory of the project
        all_modules (Dict[Path, List[Tuple[str, str]]]): Dictionary of all modules
        
    Returns:
        str: Content for __init__.py file
    """
    imports = []
    classes = set()
    
    # Handle current directory modules
    if directory in all_modules:
        for class_name, _ in all_modules[directory]:
            module_name = "".join(word.lower() for word in class_name.split("_"))
            imports.append(f"from .{module_name} import {class_name}")
            classes.add(class_name)
    
    # Handle subdirectories
    for subdir in directory.iterdir():
        if subdir.is_dir() and not subdir.name.startswith("__"):
            subdir_init = subdir / "__init__.py"
            if subdir_init.exists():
                imports.append(f"from .{subdir.name} import *")
                # Read __all__ from subdir's __init__.py to get exposed classes
                with open(subdir_init) as f:
                    content = f.read()
                    if "__all__" in content:
                        exec(content, globals())
                        classes.update(globals().get("__all__", []))
    
    # Create the __init__.py content
    content = "\n".join(imports)
    content += "\n\n__all__ = [\n"
    content += "".join(f'    "{class_name}",\n' for class_name in sorted(classes))
    content += "]\n"
    
    return content

def create_root_init_content(root_dir: Path, all_modules: Dict[Path, List[Tuple[str, str]]]) -> str:
    """
    Create content for root __init__.py that re-exports everything.
    
    Args:
        root_dir (Path): Root directory of the project
        all_modules (Dict[Path, List[Tuple[str, str]]]): Dictionary of all modules
        
    Returns:
        str: Content for root __init__.py
    """
    imports = []
    classes = set()
    
    for directory, module_list in all_modules.items():
        for class_name, rel_path in module_list:
            module_path = rel_path.with_suffix("")
            module_path_str = str(module_path).replace(os.sep, ".")
            imports.append(f"from .{module_path_str} import {class_name}")
            classes.add(class_name)
    
    content = "\n".join(sorted(imports))
    content += "\n\n__all__ = [\n"
    content += "".join(f'    "{class_name}",\n' for class_name in sorted(classes))
    content += "]\n"
    
    return content

def update_init_files(root_dir: str) -> None:
    """
    Update all __init__.py files in the project.
    
    Args:
        root_dir (str): Root directory of the project
    """
    root_path = Path(root_dir)
    all_modules = find_python_files(root_path)
    
    # First create/update the root __init__.py
    root_init = root_path / "__init__.py"
    root_content = create_root_init_content(root_path, all_modules)
    with open(root_init, "w") as f:
        f.write(root_content)
    print(f"Updated {root_init}")
    
    # Process other directories from deepest to shallowest
    dirs = sorted([d for d in root_path.rglob("*") if d.is_dir()], 
                 key=lambda x: len(x.parts),
                 reverse=True)
    
    for directory in dirs:
        if directory.name.startswith("__"):
            continue
            
        init_file = directory / "__init__.py"
        content = create_init_content(directory, root_path, all_modules)
        
        with open(init_file, "w") as f:
            f.write(content)
        print(f"Updated {init_file}")

if __name__ == "__main__":
    update_init_files("src")