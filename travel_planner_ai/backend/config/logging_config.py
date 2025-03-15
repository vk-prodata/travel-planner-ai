import logging
from pathlib import Path
from datetime import datetime
import os
import sys

def setup_logging():
    # Create logs directory if it doesn't exist
    log_dir = Path(__file__).parent.parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # Get log level from environment or default to INFO
    log_level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_name, logging.INFO)
    
    # Create a formatter with more details
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create handlers
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    file_handler = logging.FileHandler(
        log_dir / f"travel_planner_{datetime.now().strftime('%Y%m%d')}.log",
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    
    # Create a separate debug log file
    debug_file_handler = logging.FileHandler(
        log_dir / f"travel_planner_debug_{datetime.now().strftime('%Y%m%d')}.log",
        encoding='utf-8'
    )
    debug_file_handler.setLevel(logging.DEBUG)
    debug_file_handler.setFormatter(formatter)

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        handlers=[console_handler, file_handler, debug_file_handler]
    )
    
    # Get the root logger and set its level
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Configure specific loggers
    app_logger = logging.getLogger("travel_planner_ai")
    app_logger.setLevel(logging.DEBUG)  # Always set app logger to DEBUG for detailed logs
    
    # Set OpenAI and httpx logging to WARNING level
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    # Log startup information
    app_logger.info(f"Logging initialized with level: {log_level_name}")
    app_logger.info(f"Log files will be stored in: {log_dir}")
    
    return app_logger 