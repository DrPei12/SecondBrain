#!/bin/bash
# SecondBrain Startup Script
# Starts frontend on port 3003, backend on port 8000

echo "🚀 Starting SecondBrain..."

# Start frontend in background
cd /mnt/d/Desktop/SecondBrain/frontend
echo "📦 Starting frontend on http://localhost:3003..."
npm run dev &
FRONTEND_PID=$!

# Start backend in background
cd /mnt/d/Desktop/SecondBrain/backend
echo "🔧 Starting backend on http://localhost:8000..."
source venv/bin/activate && uvicorn app.main:app --reload &
BACKEND_PID=$!

echo ""
echo "✅ SecondBrain is running:"
echo "   Frontend: http://localhost:3003"
echo "   Backend:  http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for any signal
trap \"kill $FRONTEND_PID $BACKEND_PID 2>/dev/null\" EXIT
wait
