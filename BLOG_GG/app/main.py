from fastapi import FastAPI, Request, Depends, Query
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import app.models as models
from app.database import engine, get_db
from app.routers import auth, posts
from sqlalchemy.orm import Session
import time

app = FastAPI(title="GG-BLOG")

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
                print(f" Попытка {i + 1}/{max_retries}: Ждем подключения к БД...")
                time.sleep(3)
            else:
                print(f" Не удалось подключиться к БД: {e}")


app.include_router(auth.router)
app.include_router(posts.router)


@app.get("/", response_class=HTMLResponse)
async def home(
        request: Request,
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=50),
        db: Session = Depends(get_db)
):
    try:
        total_posts = db.query(models.Post).count()

        skip = (page - 1) * per_page
        total_pages = (total_posts + per_page - 1) // per_page

        posts = db.query(models.Post) \
            .order_by(models.Post.created_at.desc()) \
            .offset(skip) \
            .limit(per_page) \
            .all()

        user_count = db.query(models.User).count()
    except:
        total_posts = 0
        total_pages = 1
        posts = []
        user_count = 0

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "post_count": total_posts,
            "user_count": user_count,
            "posts": posts,
            "page": page,
            "total_pages": total_pages,
            "per_page": per_page
        }
    )

@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/search", response_class=HTMLResponse)
async def search_posts(
        request: Request,
        q: str = Query("", max_length=100),
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=50),
        db: Session = Depends(get_db)
):
    try:

        skip = (page - 1) * per_page
        posts = db.query(models.Post) \
            .filter(models.Post.title.ilike(f"%{q}%") |
                    models.Post.content.ilike(f"%{q}%")) \
            .order_by(models.Post.created_at.desc()) \
            .offset(skip) \
            .limit(per_page) \
            .all()

        total_results = db.query(models.Post) \
            .filter(models.Post.title.ilike(f"%{q}%") |
                    models.Post.content.ilike(f"%{q}%")) \
            .count()

        total_pages = (total_results + per_page - 1) // per_page
    except:
        posts = []
        total_results = 0
        total_pages = 1

    return templates.TemplateResponse(
        "search.html",
        {
            "request": request,
            "posts": posts,
            "query": q,
            "total_results": total_results,
            "page": page,
            "total_pages": total_pages,
            "per_page": per_page
        }
    )
