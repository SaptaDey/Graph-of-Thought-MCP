# ASR Graph of Thoughts (GoT) Model Context Protocol (MCP) Server

The Advanced Scientific Research (ASR) Graph of Thoughts (GoT) MCP server is a highly efficient implementation of the Model Context Protocol (MCP) that allows for sophisticated reasoning workflows using graph-based representations.

## Project Overview

This project implements a Model Context Protocol (MCP) server architecture that leverages a Graph of Thoughts approach to enhance AI reasoning capabilities. It can be connected to AI models or applications like Claude desktop app or API-based integrations.

## Project Structure

```
asr-got-mcp/
├── docker-compose.yml        # Docker Compose configuration for multi-container setup
├── Dockerfile                # Docker configuration for the backend
├── requirements.txt          # Python dependencies
├── src/                      # Source code
│   ├── server.py             # Main server implementation
│   ├── asr_got/              # Core ASR-GoT implementation
│   │   ├── core.py           # Core functionality
│   │   ├── stages/           # Processing stages
│   │   │   ├── stage_1_initialization.py
│   │   │   ├── stage_2_decomposition.py
│   │   │   ├── stage_3_hypothesis.py
│   │   │   ├── stage_4_evidence.py
│   │   │   ├── stage_5_pruning.py
│   │   │   ├── stage_6_subgraph.py
│   │   │   ├── stage_7_composition.py
│   │   │   └── stage_8_reflection.py
│   │   ├── utils/            # Utility functions
│   │   └── models/           # Data models
│   └── api/                  # API implementation
│       ├── routes.py         # API routes
│       └── schema.py         # API schemas
├── config/                   # Configuration files
└── tests/                    # Test suite
```

## Running the Project with Docker

This project provides a multi-container Docker setup for both the Python backend (FastAPI) and the static JavaScript client. The setup uses Docker Compose for orchestration.

### Project-Specific Docker Requirements
- **Python Version:** 3.13-slim (as specified in the backend Dockerfile)
- **System Dependencies:** `build-essential`, `curl` (installed in the backend image)
- **Non-root Users:** Both backend and client containers run as non-root users for security
- **Virtual Environment:** Python dependencies are installed in a virtual environment (`/app/.venv`)
- **Static Client:** Served via nginx (alpine) in a separate container

### Environment Variables
The backend service sets the following environment variables (see Dockerfile):
- `PYTHONUNBUFFERED=1`
- `MCP_SERVER_PORT=8082` (the FastAPI server port)
- `LOG_LEVEL=INFO`

> **Note:** If you need to override or add environment variables, you can uncomment and use the `env_file` option in `docker-compose.yml`.

### Exposed Ports
- **Backend (python-app):**
  - Host: `8082` → Container: `8082` (FastAPI server)
- **Client (js-client):**
  - Host: `80` → Container: `80` (nginx static server)

### Build and Run Instructions
1. **Build and start all services:**
   ```sh
   docker compose up --build
   ```
   This will build both the backend and client images and start the containers.

2. **Access the services:**
   - **Backend API:** http://localhost:8082
   - **Static Client:** http://localhost/

### Integration with AI Models

This MCP server can be integrated with:
- Claude desktop application
- API-based integrations with AI models
- Other MCP-compatible clients

## Development

To set up a development environment without Docker:

1. Clone this repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Run the server: `python src/server.py`

## License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.

---

_If you update dependencies, remember to rebuild the images with `docker compose build`._
