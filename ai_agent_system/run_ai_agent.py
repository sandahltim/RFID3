#!/usr/bin/env python3
"""
AI Agent Server Entry Point
Minnesota Equipment Rental Business Intelligence System
"""

import sys
import os
import logging
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point"""
    
    try:
        # Import and run the FastAPI app
        from app.main import run_server
        
        logger.info("Minnesota Equipment Rental AI Agent - Starting...")
        logger.info("RTX 4070 GPU-Accelerated Business Intelligence System")
        logger.info("=" * 60)
        
        run_server()
        
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Failed to start server: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()