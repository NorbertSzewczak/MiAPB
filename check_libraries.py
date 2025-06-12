import sys
import os
import importlib
import pkg_resources

def check_libraries():
    print("Python path:")
    for path in sys.path:
        print(f"  {path}")
    
    print("\nInstalled packages:")
    installed_packages = pkg_resources.working_set
    for package in sorted(installed_packages, key=lambda p: p.key):
        print(f"  {package.key} {package.version} - {package.location}")
    
    print("\nTrying to locate bpmn-python:")
    try:
        import bpmn_python
        print(f"  bpmn_python found at: {bpmn_python.__file__}")
        print(f"  Package path: {os.path.dirname(os.path.dirname(bpmn_python.__file__))}")
    except ImportError:
        print("  bpmn_python package not found")
    
    # Check for any module with 'bpmn' in the name
    print("\nSearching for any modules with 'bpmn' in the name:")
    bpmn_modules = []
    for path in sys.path:
        if os.path.isdir(path):
            for item in os.listdir(path):
                if 'bpmn' in item.lower():
                    full_path = os.path.join(path, item)
                    bpmn_modules.append(full_path)
    
    if bpmn_modules:
        for module in bpmn_modules:
            print(f"  Found: {module}")
    else:
        print("  No modules with 'bpmn' in the name found")

if __name__ == "__main__":
    check_libraries()