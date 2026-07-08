import uvicorn
import os

if __name__ == "__main__":
    is_prod = os.getenv("RENDER") == "true"  # Render sets this automatically

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=not is_prod,  # reload only in local dev
        workers=2 if is_prod else 1,  # 2 workers in prod, 1 in dev
    )
