"""FastAPI entry point for the initiative dashboard prototype.
Provides a minimal placeholder page so the server can start and be
accessed by the test suite.
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def root():
    return "<html><head><title>Initiative Dashboard</title></head><body><h1>Initiative Dashboard Prototype</h1><p>Placeholder page – implementation coming soon.</p></body></html>"
