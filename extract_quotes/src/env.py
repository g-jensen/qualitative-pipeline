import os

def in_production():
    return os.environ.get("RUN_MODE") == "production"
