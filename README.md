<div align="center">

# 💪 PowerFit — Gym Management System

**A modern, full-stack gym management web app built with Python Flask + Supabase.**  
Manage members, payments, attendance, trainers, and more — all from one clean dashboard.

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.x-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)](https://supabase.com)
[![License](https://img.shields.io/badge/License-MIT-FF6B00?style=for-the-badge)](LICENSE)

[🚀 Live Demo](#) · [🐛 Report Bug](https://github.com/panneldhruvesh2007/gym-management-system/issues) · [✨ Request Feature](https://github.com/panneldhruvesh2007/gym-management-system/issues)

</div>

---

## 📸 Screenshots

| Admin Dashboard | Member Portal |
|:-:|:-:|
| ![Dashboard](screenshots/dashboard.png) | ![Member](screenshots/member-portal.png) |

| Payments & Invoices | Reports |
|:-:|:-:|
| ![Payments](screenshots/payments.png) | ![Reports](screenshots/reports.png) |

> 📁 Add your screenshots to a `/screenshots` folder in the project root.

---

## ✨ Features

### 🔐 Authentication & Security
- Secure admin and member login with role-based access control
- Passwords hashed with Werkzeug `pbkdf2:sha256`
- CSRF protection on every form via Flask-WTF
- Rate limiting — 5 login attempts/min, 100 API requests/min per IP
- Input sanitization with Bleach (XSS prevention)
- Security headers via Flask-Talisman (CSP, X-Frame-Options)
- HTTP-only session cookies with SameSite protection
- Session auto-expires after 1 hour
- Activity logging to `app.log`

### 👥 Member Management
- Add, edit, view, delete members with full profile
- Auto-generate unique member IDs (`GYM001`, `GYM002`...)
- Member photo upload (PNG, JPG, JPEG, GIF, WEBP — max 5MB)
- Track membership status (active / expired)
- Auto-calculate expiry date from plan duration
- Search by name, phone, ID, or email
- Filter by status and plan
- Paginated member list

### 💳 Payments & Invoices
- Record payments (Cash / UPI / Card)
- Auto-generate invoice numbers (`INV-2025-001`)
- View and print clean invoices
- Edit and delete payment records
- Revenue breakdown by payment mode

### 📅 Attendance
- Daily attendance marking per member
- Calendar view with streak counter
- Monthly attendance stats

### 🏋️ Trainer Management
- Add and manage trainers with photo upload
- Assign trainers to members
- Specialization, experience, bio, salary fields

### 📋 Membership Plans
- Create unlimited plans with duration and pricing
- Plans linked to member signup and payments

### 📊 Dashboard & Reports
- Live stats — members, revenue, active/expired counts
- Monthly revenue chart (last 6 months)
- Member growth chart
- Payment mode breakdown chart
- Expiring memberships alert (next 7 days)

### 📣 Announcements & Communication
- Post gym-wide announcements with priority levels
- Per-member read tracking with unread badge
- Two-way complaints system with status control
- Direct messaging between admin and members

### ⚙️ Settings
- Gym name, logo, address, phone, email
- Dark / light theme toggle
- Currency setting

### 👤 Member Portal
- Personal dashboard — plan info, trainer, days left
- Attendance calendar with streak counter
- Invoice history with validity dates
- Submit and track complaints
- Contact gym or trainer
- Update profile and change password

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+ → [python.org/downloads](https://python.org/downloads)
- Free Supabase account → [supabase.com](https://supabase.com)

### 1. Clone the repository

```bash
git clone https://github.com/panneldhruvesh2007/gym-management-system.git
cd gym-management-system
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up Supabase database

1. Go to [supabase.com](https://supabase.com) → create a new project
2. Open **SQL Editor** → **New Query**
3. Copy the contents of `supabase_schema.sql` → paste → click **Run**
4. All tables are created ✅

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-service-role-key
SECRET_KEY=any-long-random-string-here
```

> Find your keys in Supabase → **Project Settings** → **API**

### 5. Run the app

```bash
python app.py
```

Open **http://127.0.0.1:5000** in your browser 🎉

---

## � Default Login

| Role | Username / ID | Password |
|------|--------------|----------|
| Admin | `admin` | `admin123` |
| Member | `GYM001` or email | Last 4 digits of phone |

> ⚠️ Change the admin password immediately after first login via Settings.

---

## 📁 Project Structure

```
gym-management-system/
│
├── app.py                  # All routes, decorators, security setup
├── config.py               # App configuration (dev/prod)
├── supabase_client.py      # Supabase client initialisation
├── supabase_schema.sql     # Full database schema — run this first
├── requirements.txt        # Python dependencies
├── .env                    # Secrets — never commit this
├── .gitignore
│
├── static/
│   ├── css/
│   │   ├── main.css        # Admin panel styles
│   │   ├── member.css      # Member portal styles
│   │   └── style.css
│   ├── js/
│   │   ├── main.js         # Core JS (sidebar, modals, charts)
│   │   └── app.js
│   └── uploads/
│       ├── members/        # Member photos
│       └── trainers/       # Trainer photos
│
└── templates/              # Jinja2 HTML templates
    ├── base.html           # Admin base layout
    ├── member_base.html    # Member base layout
    ├── index.html          # Landing page
    ├── login.html
    ├── dashboard.html
    ├── members.html
    ├── add_member.html
    ├── view_member.html
    ├── trainers.html
    ├── plans.html
    ├── payments.html
    ├── reports.html
    ├── settings.html
    ├── admin_attendance.html
    ├── admin_complaints.html
    ├── admin_messages.html
    ├── admin_announcements.html
    ├── invoice.html
    ├── edit_payment.html
    ├── member_dashboard.html
    ├── member_profile.html
    ├── member_attendance.html
    ├── member_invoices.html
    ├── member_complaints.html
    ├── member_contact.html
    └── member_announcements.html
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.13 |
| Framework | Flask |
| Database | Supabase (PostgreSQL) |
| Frontend | HTML5, CSS3, JavaScript, Jinja2 |
| Auth | Session-based + Werkzeug password hashing |
| Security | Flask-WTF · Flask-Talisman · Flask-Limiter · Bleach |
| Charts | Chart.js |
| Icons | Font Awesome 6 |

---

## 🔒 Security Overview

| Feature | Implementation |
|---------|---------------|
| Password hashing | Werkzeug `pbkdf2:sha256` |
| CSRF protection | Flask-WTF on all forms |
| Rate limiting | 5 login/min · 100 API/min per IP |
| XSS prevention | Bleach input sanitization |
| Security headers | Flask-Talisman (CSP, X-Frame-Options) |
| Session security | HTTP-only · SameSite=Lax · 1hr expiry |
| API protection | Session-required decorator on all API routes |
| Logging | All auth events logged to `app.log` |

---

## 🌐 API Endpoints

| Method | Endpoint | Access |
|--------|----------|--------|
| `GET` | `/api/plans` | Public |
| `GET` | `/api/trainers` | Authenticated |
| `GET` | `/api/members` | Admin only |
| `GET` | `/api/member/<id>` | Own data only |
| `GET` | `/api/plan/<id>` | Authenticated |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch — `git checkout -b feature/amazing-feature`
3. Commit your changes — `git commit -m 'Add amazing feature'`
4. Push to the branch — `git push origin feature/amazing-feature`
5. Open a Pull Request

---

## 📞 Support

- 🐛 [Open an issue](https://github.com/panneldhruvesh2007/gym-management-system/issues)
- 📧 Email: your@email.com

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

<div align="center">
  Made with ❤️ by <a href="https://github.com/panneldhruvesh2007">Dhruvesh Pannel</a>
</div>
