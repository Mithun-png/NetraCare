#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "=================================================="
echo "==> NetraCare Render Build Started"
echo "=================================================="

# 1. Install Python dependencies
echo "==> Installing Python dependencies..."
python -m pip install --upgrade pip
pip install -r backend/requirements.txt

# 2. Build React Frontend SPA
echo "==> Installing Node dependencies & building frontend..."
npm --prefix frontend install
npm --prefix frontend run build

# 3. Initialize SQLite Database & Seed Data
echo "==> Initializing SQLite Database & foundational seed data..."
export PYTHONPATH="backend"
python -c "from app.db.session import init_db, SessionLocal; from app.db.seed import seed_db; init_db(); db = SessionLocal(); seed_db(db, load_stretch=False); db.close(); print('Database seeded successfully.')"

echo "=================================================="
echo "==> NetraCare Build Complete!"
echo "=================================================="
