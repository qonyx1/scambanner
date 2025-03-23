from fastapi import FastAPI
import uvicorn
from routers import cases, checks
import logger
from utilities import SystemConfig
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

if __name__ == "__main__":
    logger.ok("Beginning FastAPI server..", debug=True)
    logger.ok("FastAPI server now serving at 127.0.0.1:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level=0)
