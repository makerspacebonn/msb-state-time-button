# =============================================================================
# LOGGING MODULE
# =============================================================================
# Simple logging for MicroPython
# Levels: 0=DEBUG, 1=INFO, 2=WARN, 3=ERROR

LOG_LEVEL = 1  # Default level, can be changed by importing module
LOG_LEVELS = {0: "DEBUG", 1: "INFO", 2: "WARN", 3: "ERROR"}


def set_level(level):
    """Set the global log level (0=DEBUG, 1=INFO, 2=WARN, 3=ERROR)"""
    global LOG_LEVEL
    LOG_LEVEL = level


def log(level, component, message):
    """Log a message if level >= LOG_LEVEL"""
    if level >= LOG_LEVEL:
        level_name = LOG_LEVELS.get(level, "INFO")
        print(f"[{level_name}] [{component}] {message}")


def debug(component, message):
    """Log a DEBUG message"""
    log(0, component, message)


def info(component, message):
    """Log an INFO message"""
    log(1, component, message)


def warn(component, message):
    """Log a WARN message"""
    log(2, component, message)


def error(component, message):
    """Log an ERROR message"""
    log(3, component, message)
