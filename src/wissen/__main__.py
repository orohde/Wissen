"""Run with ``python -m wissen``."""

import logging
import os

import uvicorn

from .app import create_app


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    uvicorn.run(
        create_app(),
        host=os.environ.get("WISSEN_HOST", "0.0.0.0"),
        port=int(os.environ.get("WISSEN_PORT", "8000")),
        proxy_headers=True,
        forwarded_allow_ips="*",
    )


if __name__ == "__main__":
    main()
