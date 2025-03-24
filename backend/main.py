from fastapi import FastAPI
import uvicorn
from routers import cases, checks
import logger
from utilities import SystemConfig
import os
import sys
system_config = SystemConfig.system_config

app = FastAPI(
    title=system_config["discord"]["bot_name"] or "Scambanner",
    description=f"{system_config["discord"]["bot_name"] or "Scambanner"} is an open-source project that lets you crossban scammers."
)

app.include_router(cases.router)
app.include_router(checks.router)

@app.get(path="/")
async def root():
    return {
        "code": 0,
        "body": f"{system_config["discord"]["bot_name"] or "Scambanner"} API is running."
    }

if __name__ == "__main__":     # Main starter

    logger.warn("Checking configuration", debug=True)
    if "https://" not in system_config["api"]["url"]:
        exit(logger.error("Invalid URL provided in configuration."))

    # Check for root permissions if needed
    if system_config["api"]["port"] < 1024 and os.geteuid() != 0:
        logger.warn(f"Root permissions are required to bind to port {system_config['api']['port']}.", debug=True)
        try:
            os.execvp("sudo", ["sudo", sys.executable] + sys.argv)
        except Exception as e:
            exit(logger.error(f"Failed to obtain root permissions: {e}"))

    logger.ok("Starting FastAPI server", debug=True)
    logger.ok(f"FastAPI server now serving at 127.0.0.1:{system_config['api']['port'] or 8000}")

    uvicorn.run(app, host="0.0.0.0", port=system_config["api"]["port"] or 8000, log_level=0)
