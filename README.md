# Fullstack RBAC Application 🚀

A modern Fullstack Application featuring an Advanced Role-Based Access Control (RBAC) system mimicking Spatie (similar to Laravel). The platform comes with a secure Python/FastAPI backend using Oracle DB and a fully-typed Next.js 14 frontend, featuring a beautiful matrix-style GUI to assign permissions.

---

## 🏗️ Architecture

- **Backend Framework:** FastAPI (Python 3.10+)
- **Database:** Oracle Database Express Edition (XE) / oracledb
- **ORM:** SQLAlchemy 2.0
- **Authentication:** JWT via `python-jose` with `passlib` bcrypt hashing
- **Middleware:** `slowapi` Rate Limiting (200 req/minute), Trailing Audit Log for mutations
- **Frontend Framework:** Next.js 14 (App Router)
- **Styling:** TailwindCSS + Shadcn UI
- **State Management:** React Context API

---

## ⚙️ Features

1. **Robust Authentication**: Standard JWT login/registration flows.
2. **Spatie-like RBAC Dependency Checker**: FastAPI API endpoints are protected using a declarative dependency:
   ```python
   @router.delete("/users/{id}")
   def delete_user(db: Session = Depends(get_db), _ = Depends(require_permission("user.delete"))):
       pass
   ```
3. **Advanced Role-Permission GUI**: An interactive matrix interface built into the Next.js frontend where Administrators can toggle permissions attached to roles dynamically.
4. **Dynamic Next.js Sidebar**: Frontend Sidebar and Navigation links programmatically hide themselves if the authenticated User does not own the `permission.view` explicitly.
5. **Route Middleware Guards**: Next.js server-side route guarding redirecting unauthorized access.

---

## 🛠️ Installation & Setup (Local Environment)

### 1. Prerequisites
- Python 3.10+
- Node.js 18+ & npm
- An Oracle Database instance running locally on `localhost:1521` (Service name e.g., `freepdb1`).

### 2. Backend Setup
1. Navigate into the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Setup Environment Variables:
   Create a `.env` file in the `backend/` root:
   ```env
   ORACLE_USER=system
   ORACLE_PASSWORD=password
   ORACLE_DSN=localhost:1521/freepdb1
   SECRET_KEY=change_this_to_a_random_secure_string_in_production
   ```
5. Run the FastAPI Server:
   *(On start, SQLAlchemy will automatically detect the models and invoke `create_all()` to build the DB Schema).*
   ```bash
   uvicorn app.main:app --reload
   ```
6. Seed the Database:
   Run the seeder script to create a default `admin` user with the password `password123`.
   ```bash
   python seed.py
   ```

### 3. Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install NodeJS dependencies:
   ```bash
   npm install
   ```
3. Create an environment configuration:
   Optionally, create a `.env.local` to override the API target port if different from the default:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000/api
   ```
4. Run the Next.js Development Server:
   ```bash
   npm run dev
   ```

---

## 🚀 How to Use / Playbook

1. **Launch the DB & Server**: Ensure your Oracle instance, FastAPI, and Next.js layers are fully running.
2. **Access the Application**: Visit `http://localhost:3000`. You will be automatically redirected to the `/login` portal.
3. **Register/Login**: (Testing workflow via Swagger) You may need to create your first user via API at `http://localhost:8000/docs` (Swagger endpoint `POST /api/auth/register`).
4. **Login on GUI**: Open `http://localhost:3000`, login with the created credentials.
5. **Establish Master Data**:
   - Go to **Permissions**: Create nodes like `user.view`, `role.assign`, `worker.access`.
   - Go to **Roles**: Check the "Permissions Matrix" and assign the targeted Permissions to standard roles (like "Admin").
6. **Assign User Status**: Go to **Users**, toggle "Manage Roles", and grant your current profile the "Admin" status.
7. **Test Route Guards**: Create a fake user, sign in as them, and attempt to visit `http://localhost:3000/worker`. Next.js should successfully trigger a "Restricted Area" alert block because that user lacks the `worker.access` permission.
