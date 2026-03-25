<p align="center">
  <img src="screenshots/banner.png" alt="PowerFit Banner" width="100%">
</p>

<h1 align="center">💪 PowerFit — Gym Management System</h1>

<p align="center">
  A modern, full-stack gym management web app built with Python Flask + Supabase.<br>
  Manage members, payments, attendance, trainers, and more — all from one clean dashboard.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.13-blue?style=flat-square">
  <img src="https://img.shields.io/badge/Flask-3.x-green?style=flat-square">
  <img src="https://img.shields.io/badge/Supabase-PostgreSQL-orange?style=flat-square">
  <img src="https://img.shields.io/badge/License-MIT-purple?style=flat-square">
</p>

---

## 📸 Screenshots

> Add your screenshots inside a `/screenshots` folder in the project root.

| Admin Dashboard | Members |
|----------------|---------|
| ![Dashboard](screenshots/dashboard.png) | ![Members](screenshots/members.png) |

| Payments | Member Portal |
|----------|--------------|
| ![Payments](screenshots/payments.png) | ![Portal](screenshots/member-portal.png) |

---

## ✨ Features

- **Member Management** — add, edit, delete members with photo upload and auto ID generation
- **Payments & Invoices** — record payments, generate invoices, track revenue
- **Attendance Tracking** — daily attendance, calendar view, streak counter
- **Trainer Management** — assign trainers to members, manage profiles
- **Membership Plans** — create plans with duration and pricing
- **Dashboard** — live stats, revenue charts, member growth, expiry alerts
- **Reports** — monthly revenue, member growth, payment mode breakdown
- **Announcements** — post gym-wide announcements with read tracking
- **Complaints & Messages** — two-way communication between admin and members
- **Member Portal** — members view their own dashboard, invoices, attendance
- **Settings** — gym name, logo, theme, currency
- **Security** — CSRF protection, rate limiting, password hashing, XSS prevention

---

## 🚀 Installation

### Requirements
- Python 3.10 or higher → https://python.org/downloads
- A free Supabase account → https://supabase.com

---

### Step 1 — Get the project

```bash
git clone https://github.com/yourusername/gym-management-system.git
cd gym-management-system
```

Or download the ZIP and extract it.

---

### Step 2 — Install dependencies

```bash
pip install -r requirements.txt
```

---

### Step 3 — Set up Supabase

1. Go to https://supabase.com and create a free project
2. Click **SQL Editor** in the left sidebar
3. Click **New Query**
4. Open `supabase_schema.sql` from this project, copy everything, paste it in, click **Run**
5. All tables are now created

---

### Step 4 — Add your environment variables

Create a file called `.env` in the project root folder and add:

```
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-service-role-key
SECRET_KEY=any-long-random-string
```

Find your keys in Supabase → **Project Settings** → **API**

---

### Step 5 — Run the app

```bash
python app.py
```

Open your browser at **http://127.0.0.1:5000**

---

## 🔑 Default Login

| Role | Username | Password |
|------|----------|----------|
| Admin | `admin` | `admin123` |
| Member | `GYM001` or email | last 4 digits of phone |

> Change the admin password immediately after first login.

---

## 📁 Project Structure

```
gym-management-system/
├── app.py                  # All routes and logic
├── config.py               # App configuration
├── supabase_client.py      # Database connection
├── supabase_schema.sql     # Run this in Supabase to create tables
├── requirements.txt        # Python packages
├── .env                    # Your secret keys (never share this)
├── static/
│   ├── css/                # Stylesheets
│   ├── js/                 # JavaScript
│   └── uploads/            # Member and trainer photos
└── templates/              # HTML pages
```

---

## 🛠️ Tech Stack

| | |
|-|-|
| Backend | Python 3.13 + Flask |
| Database | Supabase (PostgreSQL) |
| Frontend | HTML, CSS, JavaScript, Jinja2 |
| Security | Flask-WTF, Flask-Talisman, Flask-Limiter, Bleach |

---

## 📞 Support

- Open an issue on GitHub
- Email: your@email.com

---

## 📄 License

MIT — free to use, modify, and sell to clients.
