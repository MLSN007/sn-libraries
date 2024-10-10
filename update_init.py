import os
import re

def update_init_files(root_dir):
    for dirpath, dirnames, filenames in os.walk(root_dir):
        if '__init__.py' in filenames:
            update_init_file(dirpath)

def update_init_file(package_dir):
    modules = []
    for filename in os.listdir(package_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            module_name = filename[:-3]
            class_name = ''.join(word.capitalize() for word in module_name.split('_'))
            modules.append((module_name, class_name))

    init_content = []
    for module, class_name in modules:
        init_content.append(f"from .{module} import {class_name}")

    init_content.append("\n__all__ = [")
    for _, class_name in modules:
        init_content.append(f"    \"{class_name}\",")
    init_content.append("]")

    init_file_path = os.path.join(package_dir, '__init__.py')
    with open(init_file_path, 'w') as f:
        f.write('\n'.join(init_content))

    print(f"Updated {init_file_path}")

# Usage
update_init_files('src')
