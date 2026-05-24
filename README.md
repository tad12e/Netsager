# 🇪🇹 EthioCompare - Smart Price Comparison Engine

EthioCompare is a modern, high-performance web platform designed to aggregate, scrape, and compare product listings from popular online marketplaces in Ethiopia (such as Jiji, Shega, and local retail stores). It ranks listings and evaluates sellers to help users make smart shopping decisions.

---

## 📂 Project Architecture

```text
ethiocompare/
│
├── backend/                   # Django REST Framework backend
│   ├── config/                # Main settings, URLs, WSGI, and ASGI
│   ├── apps/                  # Modular backend applications
│   │   ├── users/             # Authentication, user roles, profile management
│   │   ├── products/          # Product and category catalog models
│   │   ├── sellers/           # Seller profiles, verification scoring, and reviews
│   │   ├── listings/          # Scraped marketplace listing indexer
│   │   ├── scraper/           # Scraper engine (Jiji, Shega, etc.)
│   │   ├── search/            # Search index, ranking, and filtration rules
│   │   └── alerts/            # Price tracking and email/SMS alerts system
│   ├── requirements.txt       # Python dependencies list
│   └── manage.py              # Django administrative utility
│
├── frontend/                  # React.js SPA (Vite Dev Server)
│   ├── src/
│   │   ├── pages/             # Pages (Home, Search, Product Details, Profiles)
│   │   ├── components/        # Reusable components (SearchBar, SellerCard, RankBadge)
│   │   ├── api/               # API clients (Axios connection to Django REST)
│   │   └── store/             # Global contexts (Authentication state, UI settings)
│   ├── package.json           # Frontend Node dependencies and build scripts
│   └── vite.config.js         # Vite configuration settings
│
└── README.md                  # System overview and developer instructions
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
Make sure you have **WSL** (Windows Subsystem for Linux), **Python 3.12+**, and **Node.js 18+** installed.

---

### 2. Backend Setup (WSL)

1. Open your terminal inside the project directory and activate the virtual environment:
   ```bash
   source .venv/bin/activate
   ```
2. Navigate to the backend folder:
   ```bash
   cd backend
   ```
3. Run the migrations to initialize your SQLite database:
   ```bash
   python manage.py migrate
   ```
4. Start the Django development server:
   ```bash
   python manage.py runserver
   ```
   The backend will be available at `http://127.0.0.1:8000/`.

---

### 3. Frontend Setup (React + Vite)

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install the frontend dependencies:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
   The interactive premium web app will run locally at `http://localhost:3000/`.

---

## 🛠️ Key Technologies Used
- **Backend**: Python, Django REST Framework, BeautifulSoup4, Requests
- **Frontend**: React, Lucide Icons, Vite
- **Styling**: Modern Vanilla CSS Custom Theme (featuring Glassmorphic cards, HSL tailored palettes, and elegant animations)
