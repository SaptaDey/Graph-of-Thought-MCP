#!/usr/bin/env python
import os
import sys
import time
import subprocess
import requests
import logging
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("asr-got-launcher")

def check_asr_got_running() -> bool:
    """Check if ASR-GoT server is running."""
    try:
        response = requests.get("http://localhost:8082/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def start_docker_containers(project_dir: str) -> Optional[subprocess.Popen]:
    """Start ASR-GoT Docker containers."""
    try:
        # Change to project directory
        os.chdir(project_dir)
        
        # Check if containers are already running
        if check_asr_got_running():
            logger.info("ASR-GoT server is already running")
            return None
        
        # Start containers in detached mode
        logger.info("Starting ASR-GoT Docker containers...")
        process = subprocess.Popen(
            ["docker-compose", "up", "--detach"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for containers to start
        max_attempts = 10
        attempts = 0
        while attempts < max_attempts:
            logger.info(f"Waiting for ASR-GoT server to start (attempt {attempts+1}/{max_attempts})...")
            time.sleep(3)  # Wait 3 seconds between checks
            if check_asr_got_running():
                logger.info("ASR-GoT server is now running!")
                return process
            attempts += 1
        
        logger.error("Failed to start ASR-GoT server in time")
        return process
    except Exception as e:
        logger.error(f"Error starting Docker containers: {str(e)}")
        return None

def main():
    """Main function to run ASR-GoT with MCP bridge."""
    # Get the project directory from the script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    
    # Start ASR-GoT containers
    container_process = start_docker_containers(project_dir)
    
    try:
        # Start MCP server (this will block until terminated)
        mcp_server_path = os.path.join(script_dir, "mcp_server.py")
        logger.info(f"Starting MCP server: {mcp_server_path}")
        
        # Ensure the script is executable
        if sys.platform != "win32":
            os.chmod(mcp_server_path, 0o755)
        
        mcp_process = subprocess.Popen(
            [sys.executable, mcp_server_path],
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr
        )
        
        # Wait for MCP server to exit
        mcp_process.wait()
    except KeyboardInterrupt:
        logger.info("Terminating ASR-GoT MCP integration")
    finally:
        # Stop Docker containers if we started them
        if container_process is not None:
            logger.info("Stopping ASR-GoT Docker containers...")
            try:
                subprocess.run(
                    ["docker-compose", "down"],
                    cwd=project_dir,
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                logger.info("ASR-GoT Docker containers stopped")
            except Exception as e:
                logger.error(f"Error stopping Docker containers: {str(e)}")

if __name__ == "__main__":
    main()