"""
Script to list available modules and their contents in the project packages.
"""

import os
import importlib
import inspect
from pathlib import Path
from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def list_package_contents(package_dir: str) -> Dict[str, List[str]]:
    """List all Python modules in a package directory."""
    contents = {}
    package_path = Path('src') / package_dir
    
    if not package_path.is_dir():
        return contents
        
    for file in package_path.glob('*.py'):
        if file.name == '__init__.py':
            continue
            
        module_name = file.stem
        contents[module_name] = []
        
        with open(file, 'r', encoding='utf-8') as f:
            try:
                module_content = f.read()
                # Look for class definitions
                for line in module_content.split('\n'):
                    if line.startswith('class '):
                        class_name = line.split('class ')[1].split('(')[0].split(':')[0].strip()
                        contents[module_name].append(f"Class: {class_name}")
            except Exception as e:
                logger.error(f"Error reading {file}: {str(e)}")
                
    return contents

def main():
    """Main function to list package contents."""
    packages = [
        "proxy_services",
        "sn_fb",
        "sn_ig",
        "sn_tt",
        "sn_utils",
        "sn_yt"
    ]
    
    for package in packages:
        logger.info(f"\n=== {package} ===")
        contents = list_package_contents(package)
        
        if contents:
            for module, items in sorted(contents.items()):
                logger.info(f"\nModule: {module}")
                for item in sorted(items):
                    logger.info(f"  {item}")
        else:
            logger.info("No Python modules found")

if __name__ == "__main__":
    main() 