from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "API is running"}

# Health check endpoint to wake up the server
@app.get("/status")
def status_check():
    return {"status": "200"}