#!/usr/bin/env python3
"""
Setup script for ASR-GoT MCP Server integration with Claude Desktop.

This script helps configure the ASR-GoT MCP Server for use with Claude Desktop
by copying the configuration to the appropriate location and setting up
the necessary dependencies.
"""

import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


def get_claude_config_path():
    """Get the Claude Desktop configuration path for the current platform."""
    system = platform.system()

    if system == "Darwin":  # macOS
        return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    elif system == "Windows":
        return Path.home() / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json"
    elif system == "Linux":
        return Path.home() / ".config" / "Claude" / "claude_desktop_config.json"
    else:
        raise RuntimeError(f"Unsupported platform: {system}")


def install_dependencies():
    """Install required Python dependencies."""
    print("Setting up Python environment and installing dependencies...")

    current_dir = Path(__file__).parent.absolute()
    venv_dir = current_dir / "venv"

    try:
        # Create virtual environment if it doesn't exist
        if not venv_dir.exists():
            print("Creating virtual environment...")
            subprocess.check_call([sys.executable, "-m", "venv", str(venv_dir)])

        # Determine the correct python executable in the venv
        if platform.system() == "Windows":
            python_exe = venv_dir / "Scripts" / "python.exe"
            pip_exe = venv_dir / "Scripts" / "pip.exe"
        else:
            python_exe = venv_dir / "bin" / "python"
            pip_exe = venv_dir / "bin" / "pip"

        # Install dependencies in the virtual environment
        print("Installing dependencies in virtual environment...")
        subprocess.check_call([str(pip_exe), "install", "-r", "requirements.txt"])
        print("✓ Dependencies installed successfully")

        return True, str(python_exe)

    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install dependencies: {e}")
        return False, None


def setup_claude_config(python_exe=None):
    """Setup Claude Desktop configuration."""
    print("Setting up Claude Desktop configuration...")

    # Get the current directory (where this script is located)
    current_dir = Path(__file__).parent.absolute()

    # Use virtual environment python if available, otherwise system python
    if python_exe is None:
        venv_dir = current_dir / "venv"
        if venv_dir.exists():
            if platform.system() == "Windows":
                python_exe = str(venv_dir / "Scripts" / "python.exe")
            else:
                python_exe = str(venv_dir / "bin" / "python")
        else:
            python_exe = "python"

    # Create the MCP server configuration
    config = {
        "mcpServers": {
            "asr-got": {
                "command": python_exe,
                "args": [str(current_dir / "mcp-wrapper" / "mcp_server.py")],
                "cwd": str(current_dir),
                "env": {
                    "PYTHONPATH": str(current_dir / "src"),
                    "LOG_LEVEL": "INFO"
                }
            }
        }
    }

    # Get Claude config path
    claude_config_path = get_claude_config_path()

    # Create directory if it doesn't exist
    claude_config_path.parent.mkdir(parents=True, exist_ok=True)

    # Read existing config if it exists
    existing_config = {}
    if claude_config_path.exists():
        try:
            with open(claude_config_path, 'r') as f:
                existing_config = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            existing_config = {}

    # Merge configurations
    if "mcpServers" not in existing_config:
        existing_config["mcpServers"] = {}

    existing_config["mcpServers"]["asr-got"] = config["mcpServers"]["asr-got"]

    # Write the updated configuration
    try:
        with open(claude_config_path, 'w') as f:
            json.dump(existing_config, f, indent=2)
        print(f"✓ Configuration written to: {claude_config_path}")
        return True
    except Exception as e:
        print(f"✗ Failed to write configuration: {e}")
        return False


def test_mcp_server(python_exe=None):
    """Test if the MCP server can be started."""
    print("Testing MCP server...")
    try:
        current_dir = Path(__file__).parent.absolute()
        env = os.environ.copy()
        env["PYTHONPATH"] = str(current_dir / "src")

        # Use virtual environment python if available
        if python_exe is None:
            venv_dir = current_dir / "venv"
            if venv_dir.exists():
                if platform.system() == "Windows":
                    python_exe = str(venv_dir / "Scripts" / "python.exe")
                else:
                    python_exe = str(venv_dir / "bin" / "python")
            else:
                python_exe = sys.executable

        # Try to import the required modules
        result = subprocess.run(
            [python_exe, "-c", "from asr_got.core import ASRGoTProcessor; print('✓ ASR-GoT modules imported successfully')"],
            cwd=current_dir,
            env=env,
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            print(result.stdout.strip())
            return True
        else:
            print(f"✗ Failed to import ASR-GoT modules: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print("✗ Test timed out")
        return False
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def main():
    """Main setup function."""
    print("🧠 ASR-GoT MCP Server Setup for Claude Desktop")
    print("=" * 50)

    # Check if we're in the right directory
    if not Path("mcp-wrapper/mcp_server.py").exists():
        print("✗ Error: This script must be run from the ASR-GoT project root directory")
        print("  Make sure you're in the directory containing 'mcp-wrapper/mcp_server.py'")
        sys.exit(1)

    success = True
    python_exe = None

    # Install dependencies
    deps_success, python_exe = install_dependencies()
    if not deps_success:
        success = False

    # Test MCP server
    if not test_mcp_server(python_exe):
        success = False

    # Setup Claude configuration
    if not setup_claude_config(python_exe):
        success = False

    print("\n" + "=" * 50)
    if success:
        print("✓ Setup completed successfully!")
        print("\nNext steps:")
        print("1. Restart Claude Desktop")
        print("2. The ASR-GoT tools should now be available in Claude Desktop")
        print("3. Try asking Claude to use the 'asr_got_query' tool")
        print("\nExample: 'Use the ASR-GoT tool to analyze this complex problem: [your question]'")
    else:
        print("✗ Setup completed with errors")
        print("Please check the error messages above and try again")
        sys.exit(1)


if __name__ == "__main__":
    main()
