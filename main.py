"""Entry point. Each Railway service runs its own block, chosen by the service name."""
import os
import sys

from bot.main import main as bot
from collector.main import main as collector
from web.main import main as web
from worker.main import main as worker

BLOCKS = {"web": web, "collector": collector, "worker": worker, "bot": bot}

if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("RAILWAY_SERVICE_NAME", "")
    if name not in BLOCKS:
        sys.exit(f"unknown block '{name}', expected one of: {', '.join(BLOCKS)}")
    BLOCKS[name]()
