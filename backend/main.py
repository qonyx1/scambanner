from fastapi import FastAPI, HTTPException
import uvicorn
from routers import cases, checks
import logger
from utilities import SystemConfig
from datetime import timedelta, datetime
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os
import sys, logging

system_config = SystemConfig.system_config
app = FastAPI(
    title=system_config['discord']['bot_name'] or 'Scambanner',
    description=f"{system_config['discord']['bot_name'] or 'Scambanner'} is an open-source project..."
)

from limiter import limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(cases.router)
app.include_router(checks.router)

@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_exception_handler(request, exc: RateLimitExceeded):
    retry_after = datetime.utcnow() + timedelta(minutes=1)
    return JSONResponse(
        status_code=429,
        content={
            "message": "You have exceeded the rate limit. Please try again later.",
            "code": 1,
            "retry_after": retry_after.isoformat()
        },
        headers={"Retry-After": "60"}
    )

@app.get(path="/")
async def root():
    return {
        "code": 0,
        "body": f"{system_config['discord']['bot_name'] or 'Scambanner'} API is running."
    }

if __name__ == "__main__":     # Main starter

    logger.warn("Checking configuration", debug=True)
    if "https://" not in system_config['api']['url']:
        exit(logger.error("Invalid URL provided in configuration."))

    if system_config["api"]["port"] < 1024 and os.geteuid() != 0:
        logger.warn(f"Root permissions are required to bind to port {system_config['api']['port']}.")
        try:
            os.execvp("sudo", ["sudo", sys.executable] + sys.argv)
        except Exception as e:
            exit(logger.error(f"Failed to obtain root permissions: {e}"))

    logger.ok("Starting FastAPI server", debug=True)
    logger.ok(f"FastAPI server now serving at 127.0.0.1:{system_config['api']['port'] or 8000}")

    logging.getLogger('pymongo').setLevel(logging.ERROR)

    if system_config["general"]["debug_mode"] != True:
        logging.getLogger("fastapi").setLevel(logging.CRITICAL + 9) # remove all fastapi logging, set to ERROR if wanted

    uvicorn.run(app, host="0.0.0.0", port=system_config["api"]["port"] or 8000, log_level=999999999999)
