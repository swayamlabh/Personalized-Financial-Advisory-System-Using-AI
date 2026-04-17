#!/bin/bash
set -e

echo "1. Register/Login Org"
TOKEN=$(curl -s -X POST -H 'Content-Type: application/json' \
  -d '{"orgName": "RefactorTest", "password": "pass"}' \
  http://127.0.0.1:8000/api/org_login | python3 -c "import sys,json; print(json.load(sys.stdin).get('token',''))")

if [ -z "$TOKEN" ]; then
  TOKEN=$(curl -s -X POST -H 'Content-Type: application/json' \
    -d '{"orgName": "RefactorTest", "password": "pass"}' \
    http://127.0.0.1:8000/api/org_signup | python3 -c "import sys,json; print(json.load(sys.stdin).get('token',''))")
fi

echo "2. Check Dashboard Data before Input (Expected: None / Input Needed)"
curl -s http://127.0.0.1:8000/api/org/dashboard -H "Authorization: Bearer $TOKEN" | grep -o "No data provided yet" || echo "Data found?"

echo "3. Upload sample payload (Flexible columns)"
curl -s -X POST http://127.0.0.1:8000/api/org/input_manual \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "revenue": 50000,
    "total_cost": 30000,
    "growth_rate": 0.1,
    "profit": 20000,
    "industry": "Software"
  }'

echo "4. Check Dashboard Predict (Expected: Success with Global ML)"
curl -s http://127.0.0.1:8000/api/org/dashboard -H "Authorization: Bearer $TOKEN" | grep -o "predicted_health_score"

echo "5. Reset Analysis"
curl -s -X POST -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8000/api/org/reset_analysis

echo "6. Check Dashboard after Reset (Expected: None / Input Needed)"
curl -s http://127.0.0.1:8000/api/org/dashboard -H "Authorization: Bearer $TOKEN" | grep -o "No data provided yet"
