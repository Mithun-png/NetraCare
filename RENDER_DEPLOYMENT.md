# Deploying NetraCare to Render

This repository is configured for zero-configuration, one-click deployment on [Render](https://render.com).

The deployment uses a **Unified Architecture**: Render builds the React frontend with Vite, installs FastAPI Python dependencies, seeds the clinic database, and serves the entire full-stack application on a single free Web Service with automatic SSL and zero CORS issues.

---

## Method 1: Instant Blueprint Deployment (Recommended)

Render Blueprints use the [`render.yaml`](./render.yaml) file in this repository to configure everything automatically.

1. **Push your code to GitHub:**
   Your changes are already synced to `https://github.com/Mithun-png/NetraCare`.
2. **Log into Render:**
   Go to [dashboard.render.com](https://dashboard.render.com) and sign in with your GitHub account.
3. **Create New Blueprint:**
   - Click the **New +** button in the top right.
   - Select **Blueprint**.
   - Connect your **`NetraCare`** GitHub repository.
4. **Deploy:**
   - Render will automatically parse `render.yaml`.
   - Click **Apply**.
   - Render will run `./render-build.sh` (installs dependencies, builds React, seeds database) and start the service with Uvicorn.
5. **Access Your App:**
   - Once the build says **Live**, click the assigned URL (e.g., `https://netracare.onrender.com`).

---

## Method 2: Manual Web Service Setup

If you prefer to configure the Web Service manually in the Render dashboard:

1. In Render Dashboard, click **New +** $\rightarrow$ **Web Service**.
2. Select your repository: `Mithun-png/NetraCare`.
3. Configure the following settings:
   - **Name:** `netracare`
   - **Language:** `Python`
   - **Branch:** `main`
   - **Region:** Any (e.g., *Oregon (US West)* or *Frankfurt (EU)*)
   - **Build Command:**
     ```bash
     ./render-build.sh
     ```
   - **Start Command:**
     ```bash
     python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
     ```
   - **Instance Type:** `Free`
4. Add the following **Environment Variables** in the *Environment* tab:
   | Key | Value | Notes |
   | :--- | :--- | :--- |
   | `PYTHON_VERSION` | `3.11.9` | Or any 3.10+ version |
   | `PYTHONPATH` | `backend` | Required so FastAPI finds `app` |
   | `APP_NAME` | `NetraCare AI Front Desk` | Optional |
   | `CLINIC_TIMEZONE` | `Asia/Kolkata` | Clinic timezone |
   | `SECRET_KEY` | *(Click Generate)* | Session security |
   | `GEMINI_API_KEY` | *(Your key if desired)* | Optional: runs offline if omitted |
   | `OPIK_API_KEY` | *(Your key if desired)* | Optional: observability |
5. Click **Deploy Web Service**.

---

## Health Check & Verification

Once deployed, Render monitors your service via:
- Health check path: `https://<your-app>.onrender.com/api/v1/health`
- Frontend UI: `https://<your-app>.onrender.com/`
- Interactive API Docs: `https://<your-app>.onrender.com/docs`
