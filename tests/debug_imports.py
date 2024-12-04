import sys
from pathlib import Path
print(f"Python path: {sys.path}")
print(f"Current directory: {Path.cwd()}")

try:
    from proxy_services.proxy_manager import SessionConfig
    print("Successfully imported SessionConfig")
except ImportError as e:
    print(f"Import error: {e}")
    
    # Try to list contents of the module
    import proxy_services.proxy_manager as pm
    print("\nAvailable names in proxy_manager:")
    print([name for name in dir(pm) if not name.startswith('_')]) 