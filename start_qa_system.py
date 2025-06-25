#!/usr/bin/env python3
"""
Startup script for the Development Portal Q&A System
This script starts both the FastAPI backend and Streamlit frontend
"""

import subprocess
import os
import sys
import time
import signal
import threading
from pathlib import Path

# Configuration
BACKEND_PORT = 8000
FRONTEND_PORT = 8501
BACKEND_DIR = "backend"
FRONTEND_DIR = "frontend"

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_colored(message, color=Colors.OKBLUE):
    """Print colored message to terminal"""
    print(f"{color}{message}{Colors.ENDC}")

def print_banner():
    """Print startup banner"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║              🤖 Development Portal Q&A System                ║
    ║                                                              ║
    ║  FastAPI Backend + Streamlit Frontend + Gemini AI          ║
    ║  Vector Search + RAG Pipeline                                ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print_colored(banner, Colors.HEADER)

def check_requirements():
    """Check if all required files and directories exist"""
    print_colored("🔍 Checking system requirements...", Colors.OKBLUE)
    
    # Check directories
    required_dirs = [BACKEND_DIR, FRONTEND_DIR]
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            print_colored(f"❌ Missing directory: {dir_name}", Colors.FAIL)
            return False
        print_colored(f"✅ Found directory: {dir_name}", Colors.OKGREEN)
    
    # Check backend files
    backend_files = [
        f"{BACKEND_DIR}/main.py",
        f"{BACKEND_DIR}/services/qa_pipeline.py",
        f"{BACKEND_DIR}/services/qa_processor.py",
        f"{BACKEND_DIR}/services/rag_pipeline.py"
    ]
    
    for file_path in backend_files:
        if not os.path.exists(file_path):
            print_colored(f"❌ Missing backend file: {file_path}", Colors.FAIL)
            return False
        print_colored(f"✅ Found backend file: {file_path}", Colors.OKGREEN)
    
    # Check frontend files
    frontend_files = [f"{FRONTEND_DIR}/app.py"]
    for file_path in frontend_files:
        if not os.path.exists(file_path):
            print_colored(f"❌ Missing frontend file: {file_path}", Colors.FAIL)
            return False
        print_colored(f"✅ Found frontend file: {file_path}", Colors.OKGREEN)
    
    return True

def check_environment():
    """Check environment variables"""
    print_colored("🔧 Checking environment variables...", Colors.OKBLUE)
    
    required_env_vars = ["PINECONE_API_KEY"]
    optional_env_vars = ["GOOGLE_API_KEY"]
    
    missing_required = []
    for var in required_env_vars:
        if not os.getenv(var):
            missing_required.append(var)
        else:
            print_colored(f"✅ Found required env var: {var}", Colors.OKGREEN)
    
    for var in optional_env_vars:
        if os.getenv(var):
            print_colored(f"✅ Found optional env var: {var}", Colors.OKGREEN)
        else:
            print_colored(f"⚠️  Missing optional env var: {var} (Gemini features will be disabled)", Colors.WARNING)
    
    if missing_required:
        print_colored(f"❌ Missing required environment variables: {', '.join(missing_required)}", Colors.FAIL)
        print_colored("Please set the required environment variables and try again.", Colors.FAIL)
        return False
    
    return True

def start_backend():
    """Start the FastAPI backend"""
    print_colored(f"🚀 Starting FastAPI backend on port {BACKEND_PORT}...", Colors.OKBLUE)
    
    try:
        # Change to backend directory
        backend_path = Path(BACKEND_DIR).resolve()
        
        # Start uvicorn server
        cmd = [
            sys.executable, "-m", "uvicorn",
            "main:app",
            "--host", "0.0.0.0",
            "--port", str(BACKEND_PORT),
            "--reload",
            "--log-level", "info"
        ]
        
        process = subprocess.Popen(
            cmd,
            cwd=backend_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        return process
        
    except Exception as e:
        print_colored(f"❌ Failed to start backend: {e}", Colors.FAIL)
        return None

def start_frontend():
    """Start the Streamlit frontend"""
    print_colored(f"🎨 Starting Streamlit frontend on port {FRONTEND_PORT}...", Colors.OKBLUE)
    
    try:
        # Change to frontend directory
        frontend_path = Path(FRONTEND_DIR).resolve()
        
        # Start streamlit
        cmd = [
            sys.executable, "-m", "streamlit",
            "run", "app.py",
            "--server.port", str(FRONTEND_PORT),
            "--server.address", "0.0.0.0",
            "--server.headless", "true"
        ]
        
        process = subprocess.Popen(
            cmd,
            cwd=frontend_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        return process
        
    except Exception as e:
        print_colored(f"❌ Failed to start frontend: {e}", Colors.FAIL)
        return None

def monitor_process(process, name, color=Colors.OKBLUE):
    """Monitor a process and print its output"""
    try:
        for line in iter(process.stdout.readline, ''):
            if line:
                print_colored(f"[{name}] {line.strip()}", color)
    except Exception as e:
        print_colored(f"❌ Error monitoring {name}: {e}", Colors.FAIL)

def main():
    """Main function to start the Q&A system"""
    print_banner()
    
    # Check requirements
    if not check_requirements():
        print_colored("❌ System requirements check failed. Please fix the issues and try again.", Colors.FAIL)
        sys.exit(1)
    
    # Check environment
    if not check_environment():
        print_colored("❌ Environment check failed. Please fix the issues and try again.", Colors.FAIL)
        sys.exit(1)
    
    print_colored("✅ All checks passed! Starting services...", Colors.OKGREEN)
    
    # Start processes
    backend_process = start_backend()
    if not backend_process:
        print_colored("❌ Failed to start backend. Exiting...", Colors.FAIL)
        sys.exit(1)
    
    # Give backend time to start
    print_colored("⏳ Waiting for backend to initialize...", Colors.OKBLUE)
    time.sleep(3)
    
    frontend_process = start_frontend()
    if not frontend_process:
        print_colored("❌ Failed to start frontend. Stopping backend...", Colors.FAIL)
        backend_process.terminate()
        sys.exit(1)
    
    # Print access information
    print_colored("\n" + "="*60, Colors.OKGREEN)
    print_colored("🎉 Q&A System is now running!", Colors.OKGREEN)
    print_colored(f"📡 Backend API: http://localhost:{BACKEND_PORT}", Colors.OKCYAN)
    print_colored(f"🌐 Frontend UI: http://localhost:{FRONTEND_PORT}", Colors.OKCYAN)
    print_colored(f"📚 API Docs: http://localhost:{BACKEND_PORT}/docs", Colors.OKCYAN)
    print_colored("="*60, Colors.OKGREEN)
    print_colored("\n💡 Tips:", Colors.WARNING)
    print_colored("- Use Ctrl+C to stop both services", Colors.WARNING)
    print_colored("- Visit the frontend URL to start chatting", Colors.WARNING)
    print_colored("- Check the API docs to see available endpoints", Colors.WARNING)
    print_colored("\n🔧 Make sure your environment variables are set:", Colors.WARNING)
    print_colored("- PINECONE_API_KEY (required)", Colors.WARNING)
    print_colored("- GOOGLE_API_KEY (optional, for Gemini)", Colors.WARNING)
    print_colored("\n")
    
    # Set up signal handlers
    def signal_handler(sig, frame):
        print_colored("\n🛑 Shutting down services...", Colors.WARNING)
        backend_process.terminate()
        frontend_process.terminate()
        print_colored("✅ Services stopped. Goodbye!", Colors.OKGREEN)
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start monitoring threads
    backend_thread = threading.Thread(
        target=monitor_process,
        args=(backend_process, "Backend", Colors.OKBLUE),
        daemon=True
    )
    
    frontend_thread = threading.Thread(
        target=monitor_process,
        args=(frontend_process, "Frontend", Colors.OKCYAN),
        daemon=True
    )
    
    backend_thread.start()
    frontend_thread.start()
    
    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
            
            # Check if processes are still running
            if backend_process.poll() is not None:
                print_colored("❌ Backend process stopped unexpectedly", Colors.FAIL)
                break
            
            if frontend_process.poll() is not None:
                print_colored("❌ Frontend process stopped unexpectedly", Colors.FAIL)
                break
                
    except KeyboardInterrupt:
        pass
    
    # Cleanup
    print_colored("\n🧹 Cleaning up...", Colors.WARNING)
    if backend_process.poll() is None:
        backend_process.terminate()
    if frontend_process.poll() is None:
        frontend_process.terminate()
    
    print_colored("✅ Cleanup complete. Goodbye!", Colors.OKGREEN)

if __name__ == "__main__":
    main() 