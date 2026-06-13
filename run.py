"""Run Jempol Turbo locally."""

from __future__ import annotations

import uvicorn
from app import config

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=config.HTTP_HOST, port=config.HTTP_PORT, reload=False)
