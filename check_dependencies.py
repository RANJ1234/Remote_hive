import subprocess
import sys

def check_dependencies():
    """Check if all dependencies are installed and compatible"""
    print("=== Checking dependencies ===")
    result = subprocess.run([sys.executable, "-m", "pip", "check"], 
                           capture_output=True, text=True)
    
    if result.returncode == 0:
        print("All dependencies are installed and compatible!")
        print(result.stdout)
        return True
    else:
        print("Issues found with dependencies:")
        print(result.stderr)
        print(result.stdout)
        return False

if __name__ == "__main__":
    check_dependencies()