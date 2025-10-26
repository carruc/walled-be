import asyncio
from typing import Dict

running_tasks: Dict[str, asyncio.Task] = {}
