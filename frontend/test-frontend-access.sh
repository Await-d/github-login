#\!/bin/bash
echo "Testing frontend file access..."

# Test if index.html exists and show content
echo "=== Frontend index.html content ==="
cat frontend/build/index.html

echo -e "\n=== Frontend static files ==="
ls -la frontend/build/static/

echo -e "\n=== Testing backend with frontend serving ==="
cd backend
source ../venv/bin/activate 
python app/main.py &
sleep 3

echo -e "\n=== Testing API health ==="
curl -s http://localhost:8000/api/health

echo -e "\n=== Testing frontend serving ==="
curl -s http://localhost:8000/  < /dev/null |  head -5

kill %1 2>/dev/null
