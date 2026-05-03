# How to Run the Frontend

The frontend for the **Tender Evaluation RAG system** is served directly by the backend FastAPI server. The HTML, CSS, and JavaScript files are located in the `static/` directory and are mounted to the root (`/`) route of the server.

Follow these steps to run and access the frontend:

## Prerequisites

Ensure you have your Python virtual environment set up and the necessary dependencies installed.

## 1. Start the Server

Open your terminal or command prompt, navigate to the `Ragbased-chat--system` directory, and run the FastAPI server using Uvicorn:

```bash
# If using Windows (Powershell/Command Prompt):
.\venv\Scripts\uvicorn app:app --reload --port 8000

# If using macOS/Linux:
./venv/bin/uvicorn app:app --reload --port 8000
```

> **Note:** The `--reload` flag allows the server to automatically restart when it detects any code changes, which is highly useful during development.

## 2. Access the Frontend

Once the server is running, you should see output similar to this:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

Open your preferred web browser and navigate to:
[http://127.0.0.1:8000](http://127.0.0.1:8000) or [http://localhost:8000](http://localhost:8000)

## How it works
- The `app.py` script contains a route that mounts the `static` directory: 
  `app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")`
- When you visit the root URL (`/`), FastAPI automatically serves `index.html` from the `static` folder.
- The `index.html` page uses `app.js` to communicate with the `/api/sections` and `/api/evaluate/{section_id}` backend endpoints.

## Stopping the Server
To stop the application, return to your terminal and press `CTRL+C`.
