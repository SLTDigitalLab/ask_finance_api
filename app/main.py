from fastapi.responses import RedirectResponse
from fastapi import FastAPI
from dotenv import dotenv_values
from typing import Dict
from apscheduler.schedulers.background import BackgroundScheduler
from prometheus_fastapi_instrumentator import Instrumentator
from fastapi.middleware.cors import CORSMiddleware

from api.v1.chat.base import router as multi_agent_router
from api.v1.chat.document_agent import router as document_router

app = FastAPI(title="ASK Finance Agent")
Instrumentator().instrument(app).expose(app)


app.include_router(multi_agent_router, prefix="/api/v1")
app.include_router(document_router, prefix="/api/v1")

config = dotenv_values(".env")

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)