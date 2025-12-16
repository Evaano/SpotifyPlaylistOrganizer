import subprocess
import time
import sys
import os
import signal

def run_app():
    # Paths
    root_dir = os.getcwd()
    backend_dir = os.path.join(root_dir, 'backend')
    frontend_dir = os.path.join(root_dir, 'frontend')

    print("🚀 Starting Spotify Sorter App...")

    # Start Backend
    print("   [1/2] Starting Backend (FastAPI)...")
    backend_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--reload", "--port", "8000"],
        cwd=backend_dir,
        shell=True
    )

    # Start Frontend
    print("   [2/2] Starting Frontend (React/Vite)...")
    frontend_process = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=frontend_dir,
        shell=True
    )

    print("\n✅ Both servers are running!")
    print("   - Backend: http://127.0.0.1:8000")
    print("   - Frontend: http://127.0.0.1:5173\n")
    print("Press Ctrl+C to stop both servers.")

    try:
        while True:
            time.sleep(1)
            # Check if processes are still alive
            if backend_process.poll() is not None:
                print("Backend stopped unexpectedly.")
                frontend_process.terminate()
                break
            if frontend_process.poll() is not None:
                print("Frontend stopped unexpectedly.")
                backend_process.terminate()
                break
    except KeyboardInterrupt:
        print("\n🛑 Stopping servers...")
        # On Windows, terminate might not kill the tree, but for dev it works reasonably well
        # Using taskkill /F /T /PID could be more aggressive if needed
        backend_process.terminate()
        frontend_process.terminate()
        print("Done.")

if __name__ == "__main__":
    run_app()
