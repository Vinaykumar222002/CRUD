from fastapi import FastAPI, Request, Form, UploadFile, File,Depends
from fastapi.responses import HTMLResponse, RedirectResponse,FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from psycopg2.extras import RealDictCursor
from db import get_connection
from auth import router as auth_router,get_current_user

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from PyPDF2 import PdfMerger
import shutil, os
from reportlab.lib import colors
from reportlab.lib.units import inch
from typing import Optional

import csv
import io



app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth_router)

UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/", response_class=HTMLResponse)
def root():
    return RedirectResponse(url="/login", status_code=303)

# ---------------- HOME ----------------
@app.get("/home/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# ---------------- CREATE ----------------
@app.post("/add_user_form/") 
async def add_user_form(
    name: str = Form(...),
    email: str = Form(...),
    age: int = Form(...),
    city: str = Form(...),
    gender: str = Form(...),
    skills: Optional[list[str]] = Form(None),
    image: Optional[UploadFile] = File(None),
    pdf: Optional[UploadFile] = File(None)
):
    skills_str = ",".join(skills) if skills else ""
    image_path, pdf_path = None, None

    if image:
        image_path = os.path.join(UPLOAD_DIR, image.filename)
        with open(image_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

    if pdf:
        pdf_path = os.path.join(UPLOAD_DIR, pdf.filename)
        with open(pdf_path, "wb") as buffer:
            shutil.copyfileobj(pdf.file, buffer)

    conn = get_connection()
    cur = conn.cursor()

    # ✅ Check if user already exists by email
    cur.execute("SELECT id FROM users WHERE email = %s", (email,))
    existing_user = cur.fetchone()

    if existing_user:
        cur.close()
        conn.close()
        return RedirectResponse(url="/users_table/?msg=User already exists", status_code=303)

    # ✅ Insert new user


    cur.execute(
        "INSERT INTO users (name, email, age, city, gender, skills, image_path, pdf_path) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
        (name, email, age, city, gender, skills_str, image_path, pdf_path)
    )
    conn.commit()
    cur.close()
    conn.close()

    return RedirectResponse(url="/users_table/", status_code=303)

# ---------------- READ ----------------
@app.get("/users/", response_class=HTMLResponse)
def list_users(
    request: Request,
    q: str = "",
    page: int = 1,
    per_page: int = 12,
    new_ids: str = ""
):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    highlighted_ids = set(map(int, new_ids.split(","))) if new_ids else set()

    if highlighted_ids:
        # ✅ Only fetch the newly added users
        cur.execute("SELECT * FROM users WHERE id = ANY(%s)", (list(highlighted_ids),))
        users = cur.fetchall()
        total_users = len(users)
        total_pages = 1
    else:
        # ✅ Normal search + pagination
        base_query = "FROM users WHERE TRUE"
        params = []

        if q:
            base_query += """ AND (
                name ILIKE %s OR
                email ILIKE %s OR
                city ILIKE %s OR
                gender ILIKE %s OR
                skills ILIKE %s
            )"""
            search_term = f"%{q}%"
            params.extend([search_term] * 5)

        count_query = f"SELECT COUNT(*) {base_query}"
        cur.execute(count_query, params)
        total_users = cur.fetchone()["count"]
        total_pages = (total_users + per_page - 1) // per_page

        offset = (page - 1) * per_page
        data_query = f"SELECT * {base_query} ORDER BY id LIMIT %s OFFSET %s"
        cur.execute(data_query, params + [per_page, offset])
        users = cur.fetchall()

    cur.close()
    conn.close()

    return templates.TemplateResponse("users.html", {
        "request": request,
        "users": users,
        "q": q,
        "page": page,
        "total_pages": total_pages,
        "highlighted_ids": highlighted_ids
    })
# ---------------- EDIT FORM ----------------
@app.get("/edit_user/{user_id}", response_class=HTMLResponse)
def edit_user(request: Request, user_id: int):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return templates.TemplateResponse("edit_user.html", {"request": request, "user": user})

# ---------------- UPDATE FORM ----------------
@app.post("/update_user/{user_id}")
async def update_user(
    user_id: int,
    name: str = Form(...),
    email: str = Form(...),
    age: int = Form(...),
    city: str = Form(...),
    gender: str = Form(...),
    skills: Optional[list[str]] = Form(None),
    image: Optional[UploadFile] = File(None),
    pdf: Optional[UploadFile] = File(None)
):
    skills_str = ",".join(skills) if skills else ""

    image_path = None
    pdf_path = None

    if image and image.filename:
        image_path = os.path.join(UPLOAD_DIR, image.filename)
        with open(image_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

    if pdf and pdf.filename:
        pdf_path = os.path.join(UPLOAD_DIR, pdf.filename)
        with open(pdf_path, "wb") as buffer:
            shutil.copyfileobj(pdf.file, buffer)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """UPDATE users 
           SET name=%s, email=%s, age=%s, city=%s, gender=%s, skills=%s,
               image_path = COALESCE(%s, image_path),
               pdf_path = COALESCE(%s, pdf_path)
           WHERE id=%s""",
        (name, email, age, city, gender, skills_str, image_path, pdf_path, user_id)
    )
    conn.commit()
    cur.close()
    conn.close()

    return RedirectResponse(url="/users_table/", status_code=303)

# ---------------- DELETE ----------------
@app.get("/delete_user/{user_id}")
def delete_user(user_id: int):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("SELECT image_path, pdf_path FROM users WHERE id=%s", (user_id,))
    user_files = cur.fetchone()

    cur.execute("DELETE FROM users WHERE id=%s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()

    if user_files:
        if user_files.get("image_path") and os.path.exists(user_files["image_path"]):
            os.remove(user_files["image_path"])
        if user_files.get("pdf_path") and os.path.exists(user_files["pdf_path"]):
            os.remove(user_files["pdf_path"])

    return RedirectResponse(url="/users_table/", status_code=303)



@app.get("/users_table/", response_class=HTMLResponse)
def list_users(
    request: Request,
    q: str = "",
    page: int = 1,
    per_page: int =4,
    new_ids: str = ""
):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    highlighted_ids = set(map(int, new_ids.split(","))) if new_ids else set()
    new_users_count=len(highlighted_ids)
    if highlighted_ids:
        # ✅ Only fetch the newly added users
        cur.execute("SELECT * FROM users WHERE id = ANY(%s)", (list(highlighted_ids),))
        users = cur.fetchall()
        total_users = len(users)
        total_pages = 1
    else:
        # ✅ Normal search + pagination
        base_query = "FROM users WHERE TRUE"
        params = []

        if q:
            base_query += """ AND (
                name ILIKE %s OR
                email ILIKE %s OR
                city ILIKE %s OR
                gender ILIKE %s OR
                skills ILIKE %s
            )"""
            search_term = f"%{q}%"
            params.extend([search_term] * 5)

        count_query = f"SELECT COUNT(*) {base_query}"
        cur.execute(count_query, params)
        total_users = cur.fetchone()["count"]
        total_pages = (total_users + per_page - 1) // per_page

        offset = (page - 1) * per_page
        data_query = f"SELECT * {base_query} ORDER BY id LIMIT %s OFFSET %s"
        cur.execute(data_query, params + [per_page, offset])
        users = cur.fetchall()

    cur.close()
    conn.close()
    return templates.TemplateResponse("users_table.html", {
        "request": request,
        "users": users,
        "q": q,
        "page": page,
        "total_pages": total_pages,
        "highlighted_ids": highlighted_ids,
        "new_users_count": new_users_count
    })


# download file 

def generate_profile_pdf(user, profile_path, pdf_missing=False, image_missing=False):
    c = canvas.Canvas(profile_path, pagesize=letter)
    width, height = letter

    # Header
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width / 2, height - 50, "User Profile")

    # Logo (optional)
    logo_path = "static/images/logo.png"
    if os.path.exists(logo_path):
        c.drawImage(logo_path, width - 2 * inch, height - 1 * inch, width=1.5 * inch, height=0.5 * inch)

    # ✅ Profile Image (centered below header, larger size)
    image_path = user.get("image_path") or ""
    image_path = image_path.replace("\\", "/") if image_path else ""

    if image_path and os.path.exists(image_path):
        final_image = image_path
    elif os.path.exists("static/images/no image.jpg"):
        final_image = "static/images/no image.jpg"
    else:
        final_image = None

    image_width = 3.5 * inch
    image_height = 3.5 * inch
    image_x = (width - image_width) / 2
    image_y = height - 4.5 * inch

    if final_image:
        c.drawImage(final_image, image_x, image_y, width=image_width, height=image_height)
    else:
        c.setFont("Helvetica-Oblique", 12)
        c.setFillColor(colors.red)
        c.drawCentredString(width / 2, image_y + image_height / 2, ".......Image not uploaded.......")

    # Table-like layout
    c.setFont("Helvetica", 12)
    start_y = image_y - 0.75 * inch
    line_height = 20
    labels = ["Name", "Email", "Age", "City", "Gender", "Skills"]
    values = [
        user["name"],
        user["email"],
        str(user["age"]),
        user["city"],
        user["gender"],
        user["skills"]
    ]

    for i, (label, value) in enumerate(zip(labels, values)):
        y = start_y - i * line_height
        c.setFillColor(colors.grey)
        c.drawString(80, y, f"{label}:")
        c.setFillColor(colors.black)
        c.drawString(150, y, value)

    # ✅ Only show resume message if missing
    if pdf_missing:
        c.setFont("Helvetica-Oblique", 12)
        c.setFillColor(colors.red)
        c.drawString(220, y - line_height, ".......Resume not uploaded.......")

    c.save()

@app.get("/download_user_pdf/{user_id}")
def download_user_pdf(user_id: int):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if not user:
        return {"error": "User not found"}

    os.makedirs("static/downloads", exist_ok=True)
    profile_path = f"static/downloads/profile_{user_id}.pdf"
    final_path = f"static/downloads/user_{user_id}_full.pdf"

    # Resume path safe check
    resume_path = user.get("pdf_path") or ""
    resume_path = resume_path.replace("\\", "/") if resume_path else ""
    pdf_missing = not resume_path or not os.path.exists(resume_path)

    # Image path safe check
    image_path = user.get("image_path") or ""
    image_path = image_path.replace("\\", "/") if image_path else ""
    image_missing = not image_path or not os.path.exists(image_path)

    # Generate profile PDF
    generate_profile_pdf(user, profile_path, pdf_missing=pdf_missing, image_missing=image_missing)

    # Merge profile + resume if available
    merger = PdfMerger()
    merger.append(profile_path)
    if not pdf_missing:
        merger.append(resume_path)

    merger.write(final_path)
    merger.close()

    return FileResponse(final_path, media_type="application/pdf", filename=f"{user['name']}.pdf")


@app.get("/upload_users")
def upload_users_page(request: Request):
    return templates.TemplateResponse("upload_users.html", {"request": request})

@app.post("/upload_users_csv")
async def upload_users_csv(file: UploadFile = File(...)):
    contents = await file.read()
    decoded = contents.decode("utf-8")
    reader = csv.DictReader(io.StringIO(decoded))

    conn = get_connection()
    cur = conn.cursor()
    inserted_ids = []

    for row in reader:
        cur.execute("""
            INSERT INTO users (name, email, age, city, gender, skills)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            row["name"],
            row["email"],
            row["age"],
            row["city"],
            row["gender"],
            row["skills"]
        ))
        new_id = cur.fetchone()[0]
        inserted_ids.append(str(new_id))

    conn.commit()
    cur.close()
    conn.close()

    return RedirectResponse(url=f"/users_table/?new_ids={','.join(inserted_ids)}", status_code=303)
