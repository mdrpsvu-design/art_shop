import shutil
import os
from fastapi import FastAPI, Request, Depends, Form, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from database import create_db_and_tables, get_session
from models import Item
import secrets
from fastapi import HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

app = FastAPI()

security = HTTPBasic()

# Придумайте логин и пароль для мамы
ADMIN_USERNAME = "Olga"
ADMIN_PASSWORD = "Gosha"  # Замените на сложный пароль!

# Функция-охранник: проверяет логин и пароль
def get_current_admin(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, ADMIN_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
    
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# Создаем папку для картинок, если нет
os.makedirs("static/images", exist_ok=True)

# Подключаем статику (CSS, картинки)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Подключаем шаблоны
templates = Jinja2Templates(directory="templates")

# При запуске создаем базу данных
@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# --- СТРАНИЦЫ ДЛЯ ПОСЕТИТЕЛЕЙ ---

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/catalog", response_class=HTMLResponse)
async def read_catalog(request: Request, session: Session = Depends(get_session)):
    items = session.exec(select(Item)).all()
    return templates.TemplateResponse("catalog.html", {"request": request, "items": items})

# --- АДМИНКА (ДЛЯ МАМЫ) ---

@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(
    request: Request, 
    session: Session = Depends(get_session),
    auth: str = Depends(get_current_admin)  # <--- ЗАМОК ЗДЕСЬ
):
    items = session.exec(select(Item)).all()
    return templates.TemplateResponse("admin.html", {"request": request, "items": items})

@app.post("/admin/add")
async def add_item(
    title: str = Form(...),
    description: str = Form(...),
    price: int = Form(...),
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    auth: str = Depends(get_current_admin)  # <--- ЗАМОК ЗДЕСЬ
):
    file_location = f"static/images/{file.filename}"
    with open(file_location, "wb+") as file_object:
        shutil.copyfileobj(file.file, file_object)

    new_item = Item(title=title, description=description, price=price, image_url=file_location)
    session.add(new_item)
    session.commit()
    
    return RedirectResponse(url="/admin", status_code=303)

@app.post("/admin/delete/{item_id}")
async def delete_item(
    item_id: int, 
    session: Session = Depends(get_session),
    auth: str = Depends(get_current_admin)  # <--- ЗАМОК ЗДЕСЬ
):
    item = session.get(Item, item_id)
    if item:
        session.delete(item)
        session.commit()
    return RedirectResponse(url="/admin", status_code=303)
