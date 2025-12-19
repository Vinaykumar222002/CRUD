# BLOG Application 

A full-stack user management system built with **FastAPI** and **PostgreSQL**, featuring secure authentication, a responsive frontend, bulk CSV upload, searchable user listings, and dynamic PDF profile generation. Designed for trainers and admins to efficiently manage user data with clear visual feedback and polished workflows.

---

## 🚀 Features

* 🔐 **Authentication & Authorization**
  Secure authentication implemented using a dedicated `auth.py` module with protected routes and role-based access for admin/trainer workflows.

* ✅ **User Registration Form**
  Responsive HTML/CSS form with fields for name, email, age, city, gender, skills, profile image upload, and resume upload.

* 📥 **Bulk CSV Upload**
  Upload multiple users using tab-separated `.csv` or `.tsv` files. Newly added users are visually highlighted in the user listing for easy identification.

* 🔍 **Search & Pagination**
  Search users by name or email with paginated results to efficiently manage large datasets.

* 📄 **PDF Profile Generation**
  Dynamically generates downloadable user profile PDFs by:

  * Merging uploaded resume and profile image
  * Showing fallback messages when files are missing
  * Maintaining clean and consistent formatting

* 🧾 **Admin Dashboard**
  Clean, mobile-responsive admin interface with clear feedback messages and intuitive navigation for day-to-day user management.

---

## 🛠️ Tech Stack

* **Backend:** FastAPI, PostgreSQL, Psycopg2
* **Authentication:** Custom authentication module (`auth.py`)
* **PDF Handling:** ReportLab, PyPDF2
* **Frontend:** HTML, CSS (Flexbox & Grid)
* **Utilities:** CSV parsing, file handling, PDF merging, image fallback logic

---

## 📂 Folder Structure

```
├── backend/
│   ├── main.py
│   ├── auth.py
│   ├── templates/
│   ├── static/
│   │   ├── images/
│   │   └── downloads/
├── users.csv
├── README.md
```

---

## 📸 Screenshots

* Login page with authentication flow
  <img width="1913" height="912" alt="image" src="https://github.com/user-attachments/assets/ec6b0e0b-d384-444f-9a2e-78e888f5caed" />
* User registration form with image and resume upload
  <img width="1901" height="913" alt="image" src="https://github.com/user-attachments/assets/bc06bc08-d48f-4875-97c0-bd22e57b54be" />
* Highlighted users after bulk upload
  <img width="1906" height="896" alt="image" src="https://github.com/user-attachments/assets/e8137b5a-6efe-49f0-86bd-614ec16c4a19" />
  <img width="1887" height="912" alt="image" src="https://github.com/user-attachments/assets/4a668b5e-56a8-4747-8fd7-9cfcff275e6f" />

* Users in Table and list format with sorting, pagination, filter, edit, delete, download
  <img width="1892" height="922" alt="image" src="https://github.com/user-attachments/assets/93527e69-ef14-4b40-9856-ff1f69223ad6" />
  <img width="1897" height="915" alt="image" src="https://github.com/user-attachments/assets/7fc5f8fe-5670-4970-b812-d7b98edf3b20" />
* Generated PDF profile with fallback image and resume message
  <img width="1880" height="879" alt="image" src="https://github.com/user-attachments/assets/dda0ed15-4c5b-4010-adc8-16704b634ca5" />
  <img width="1812" height="860" alt="image" src="https://github.com/user-attachments/assets/8b53666e-936c-4859-8ee9-a8e832820e31" />


---

## 🧪 How to Run

1. Clone the repository
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```
3. Start the FastAPI server:

   ```bash
   uvicorn main:app --reload
   ```
4. Open your browser and navigate to:

   ```
   http://localhost:8000
   ```
<img width="1457" height="179" alt="image" src="https://github.com/user-attachments/assets/c3d94f4f-befe-443a-9777-53a684155abf" />

---
