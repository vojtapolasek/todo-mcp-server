"""
Entry point when running the package as a module
"""
import asyncio
import sys

from .server import main

if __name__ == "__main__":
    asyncio.run(main())
