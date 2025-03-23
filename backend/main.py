from fastapi import FastAPI
from routers import cases

app = FastAPI(
    title="MarketSec",
    description="MarketSec is an open-source project that lets you crossban scammers."
)

app.include_router(cases.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
