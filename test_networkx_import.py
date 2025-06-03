import sys
import subprocess

def test_networkx_import():
    """Test if networkx can be imported without Unicode errors."""
    print("Testing networkx import...")
    
    try:
        # Try to import networkx and print a simple ASCII message
        result = subprocess.run(
            [sys.executable, "-c", "import networkx; print('[OK] Networkx module imported successfully')"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("Success! The import worked without errors:")
            print(result.stdout.strip())
            return True
        else:
            print("Failed to import networkx:")
            print(result.stderr.strip())
            return False
            
    except Exception as e:
        print(f"Error during test: {e}")
        return False

if __name__ == "__main__":
    print("Verifying the fix for the UnicodeEncodeError issue...")
    success = test_networkx_import()
    
    if success:
        print("\nThe fix was successful! No UnicodeEncodeError occurred.")
    else:
        print("\nThe fix may not have resolved the issue. Please check the error messages above.")