from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import mice, keyboards, mousepads, monitors, microphones, headphones

app = FastAPI(title="Peripheral DSS API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(mice.router)
app.include_router(keyboards.router)
app.include_router(mousepads.router)
app.include_router(monitors.router)
app.include_router(microphones.router)
app.include_router(headphones.router)

@app.get("/")
def root():
    return {"message": "Peripheral DSS API"}
