#!/bin/bash
# Quick test script to verify UI and API are working

echo "=== RFID Operations System Status Check ==="
echo ""

# Check UI Server
echo "1. UI Server (Port 3000):"
if curl -k -s https://localhost:3000 | grep -q "root"; then
    echo "   ✅ UI is responding"
else
    echo "   ❌ UI is NOT responding"
fi

# Check API Server
echo ""
echo "2. API Server (Port 8444):"
if curl -s http://localhost:8444/docs | grep -q "swagger"; then
    echo "   ✅ API docs are accessible"
else
    echo "   ❌ API is NOT responding"
fi

# Check Contract Endpoint
echo ""
echo "3. Contracts Endpoint:"
response=$(curl -s http://localhost:8444/api/v1/contracts/open)
if [ "$response" = "[]" ] || echo "$response" | grep -q "contract"; then
    echo "   ✅ Contract endpoint working (returned: $response)"
else
    echo "   ❌ Contract endpoint error"
fi

# Check for JavaScript errors
echo ""
echo "4. JavaScript Modules:"
if curl -k -s https://localhost:3000/src/App.jsx | grep -q "import"; then
    echo "   ✅ React modules loading"
else
    echo "   ❌ Module loading issues"
fi

echo ""
echo "=== Access URLs ==="
echo "UI:  https://localhost:3000"
echo "API: http://localhost:8444/docs"
echo ""
echo "Note: Accept the self-signed certificate warning in your browser"