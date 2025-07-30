import os
import importlib.util
from typing import List, Optional

def get_python_scripts() -> List[str]:
    """Get list of Python scripts from the scripts directory."""
    scripts_dir = './scripts'
    return sorted([f for f in os.listdir(scripts_dir) if f.endswith('.py')])

def load_script(script_name: str) -> Optional[object]:
    """Load a Python script module dynamically."""
    script_path = os.path.join('./scripts', script_name)
    try:
        spec = importlib.util.spec_from_file_location(script_name[:-3], script_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        return None
    except Exception as e:
        print(f"Error loading {script_name}: {str(e)}")
        return None

def run_script(script_name: str) -> None:
    """Run a single script."""
    print(f"\nRunning {script_name}...")
    module = load_script(script_name)
    if module and hasattr(module, '__main__'):
        try:
            if hasattr(module, 'main'):
                module.main()
            elif hasattr(module, 'generate_readme'):  # Special case for readme-builder
                module.generate_readme()
            else:
                print(f"No runnable function found in {script_name}")
        except Exception as e:
            print(f"Error running {script_name}: {str(e)}")
    print(f"Finished {script_name}\n")

def main():
    """Main interactive script runner."""
    scripts = get_python_scripts()
    
    if not scripts:
        print("No Python scripts found in the scripts directory!")
        return

    while True:
        print("\nAvailable scripts:")
        for i, script in enumerate(scripts, 1):
            print(f"{i}. {script}")
        print("\nOptions:")
        print("* - Run all scripts")
        print("q - Quit")
        
        choice = input("\nEnter your choice (number, *, or q): ").strip().lower()
        
        if choice == 'q':
            break
        elif choice == '*':
            print("\nRunning all scripts...")
            for script in scripts:
                run_script(script)
            print("All scripts completed!")
        else:
            try:
                script_index = int(choice) - 1
                if 0 <= script_index < len(scripts):
                    run_script(scripts[script_index])
                else:
                    print("Invalid script number!")
            except ValueError:
                print("Invalid input! Please enter a number, *, or q")

if __name__ == '__main__':
    main()