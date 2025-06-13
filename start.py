#!/usr/bin/env python3
"""
Startup script for Railway deployment
Handles PORT environment variable properly
"""
import os
import uvicorn

if __name__ == "__main__":
    # Get port from environment variable, default to 8000
    port = int(os.getenv("PORT", 8000))
    
    print(f"🚀 Starting Eindr Email Capture API on port {port}")
    
    # Run the application
    uvicorn.run(
        "app.main_postgresql:app",
        host="0.0.0.0",
        port=port,
        reload=False  # Disable reload in production
    ) 