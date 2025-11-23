from fastapi import FastAPI
from .routers import auth, events, tickets, scan, admin

app = FastAPI(title='TD-LOG Backend')

app.include_router(auth.router)
app.include_router(events.router)
app.include_router(tickets.router)
app.include_router(scan.router)
app.include_router(admin.router)
