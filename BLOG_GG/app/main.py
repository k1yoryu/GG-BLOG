import time
from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import app.models as models
from app.database import engine, get_db
from sqlalchemy.orm import Session

app = FastAPI(title="Mini Blog")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")

@app.on_event("startup")
def startup():
    max_retries = 5
    for i in range(max_retries):
        try:
            models.Base.metadata.create_all(bind=engine)
            print("Таблицы созданы успешно")
            break
        except Exception as e:
            if i < max_retries - 1:
                print(f"⏳ Попытка {i + 1}/{max_retries}: Ждем подключения к БД...")
                time.sleep(3)
            else:
                print(f"Не удалось подключиться к БД: {e}")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    try:
        post_count = db.query(models.Post).count()
        user_count = db.query(models.User).count()
    except:
        post_count = 0
        user_count = 0

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "post_count": post_count,
            "user_count": user_count
        }
    )


@app.get("/health")
async def health_check():
    return {"status": "ok"}