from fastapi import FastAPI
from routers import customer, admin, support
import auth

app = FastAPI()

# Mount all feature routers onto the main application
app.include_router(auth.router)
app.include_router(customer.router)
app.include_router(admin.router)
app.include_router(support.router)
