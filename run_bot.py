"""Entry point for the Telegram bot."""
import asyncio
import logging
import sys
import os

# Ensure /code is in path (Docker workdir)
sys.path.insert(0, "/code")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.telegram.tg_bot import main

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    asyncio.run(main())
