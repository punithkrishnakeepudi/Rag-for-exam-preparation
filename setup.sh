#!/usr/bin/env bash
set -e

echo "==> StudyLens setup"

# Backend
echo ""
echo "[1/3] Installing backend dependencies..."
cd backend
if [ ! -f ".env" ]; then
  cp ../.env.example .env
  echo "      Created backend/.env from .env.example — edit it if needed"
fi
pip install -r requirements.txt -q
cd ..

# Frontend
echo ""
echo "[2/3] Installing frontend dependencies..."
cd frontend
npm install --silent
cd ..

echo ""
echo "[3/3] Done!"
echo ""
echo "Start the app:"
echo ""
echo "  Terminal 1 (backend):"
echo "    cd backend && PYTHONPATH=src uvicorn studylens.main:app --reload"
echo ""
echo "  Terminal 2 (frontend):"
echo "    cd frontend && npm run dev"
echo ""
echo "Then open http://localhost:5173"
