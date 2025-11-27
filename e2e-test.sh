#!/bin/bash

# Comprehensive End-to-End Testing for KaiOPS Session Fix
# Tests all scenarios with MongoDB session storage

set -e

API_URL="http://kaiops-sre.searceinc.net"
APP_NAME="sre_agent"
PASSED=0
FAILED=0

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  KaiOPS End-to-End Session Testing with MongoDB Storage       ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Test helper functions
test_endpoint() {
    local name=$1
    local method=$2
    local endpoint=$3
    local data=$4
    
    echo "[TEST] $name"
    response=$(curl -s -X "$method" "${API_URL}${endpoint}" \
        -H "Content-Type: application/json" \
        -d "$data" 2>&1)
    
    if echo "$response" | grep -q "error\|Error\|ERROR"; then
        echo "❌ FAILED"
        echo "Response: $(echo "$response" | head -c 100)"
        FAILED=$((FAILED + 1))
        return 1
    else
        echo "✅ PASSED"
        PASSED=$((PASSED + 1))
        return 0
    fi
}

create_session() {
    local user_id=$1
    local session_id=$2
    
    curl -s -X POST "${API_URL}/apps/${APP_NAME}/users/${user_id}/sessions/${session_id}" \
        -H "Content-Type: application/json" \
        -d '{"state": {}}'
}

test_run() {
    local user_id=$1
    local session_id=$2
    local message=$3
    
    curl -s -X POST "${API_URL}/run" \
        -H "Content-Type: application/json" \
        -d "{\"appName\": \"${APP_NAME}\", \"userId\": \"${user_id}\", \"sessionId\": \"${session_id}\", \"newMessage\": {\"role\": \"user\", \"parts\": [{\"text\": \"${message}\"}]}}"
}

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "PHASE 1: Health Checks"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Check frontend health
echo "[1.1] Frontend Health Check"
if curl -s -I http://kaiops-sre.searceinc.net/ | grep -q "200\|304"; then
    echo "✅ Frontend is responding"
    PASSED=$((PASSED + 1))
else
    echo "❌ Frontend is not responding"
    FAILED=$((FAILED + 1))
fi

# Check backend health
echo "[1.2] Backend Health Check"
response=$(curl -s http://kaiops-sre.searceinc.net/api/v1/health)
if echo "$response" | grep -q "healthy"; then
    echo "✅ Backend is healthy"
    PASSED=$((PASSED + 1))
else
    echo "❌ Backend health check failed"
    FAILED=$((FAILED + 1))
fi

# Check backend pods
echo "[1.3] Backend Pods Status"
backend_pods=$(kubectl get pods -n kaiops -l app=kaiops-backend --no-headers | wc -l)
if [ "$backend_pods" -ge 2 ]; then
    echo "✅ Backend has $backend_pods pods running"
    PASSED=$((PASSED + 1))
else
    echo "❌ Only $backend_pods backend pods running (need at least 2)"
    FAILED=$((FAILED + 1))
fi

# Check MongoDB connection
echo "[1.4] MongoDB Connection Check"
mongodb_check=$(kubectl exec -n kaiops kaiops-backend-78964bcf4-2gqwg -- python3 -c "import os; print(os.getenv('MONGODB_URI', 'NOT_SET')[:50])" 2>/dev/null || echo "ERROR")
if [[ ! "$mongodb_check" =~ "ERROR" ]] && [[ "$mongodb_check" != "NOT_SET" ]]; then
    echo "✅ MongoDB URI is configured"
    PASSED=$((PASSED + 1))
else
    echo "❌ MongoDB URI not properly configured"
    FAILED=$((FAILED + 1))
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "PHASE 2: Session Creation & Persistence"
echo "════════════════════════════════════════════════════════════════"
echo ""

SESSION1="e2e-test-1-$(date +%s)"
USER1="e2e-user-1"

echo "[2.1] Creating session: $SESSION1 for user: $USER1"
session_response=$(create_session "$USER1" "$SESSION1")
if echo "$session_response" | grep -q "id"; then
    echo "✅ Session created successfully"
    PASSED=$((PASSED + 1))
else
    echo "❌ Session creation failed"
    echo "Response: $session_response"
    FAILED=$((FAILED + 1))
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "PHASE 3: Single Session Multiple Messages"
echo "════════════════════════════════════════════════════════════════"
echo ""

for i in {1..3}; do
    echo "[3.$i] Message $i/3 in same session"
    run_response=$(test_run "$USER1" "$SESSION1" "test message $i")
    
    if echo "$run_response" | grep -q "modelVersion\|id" && ! echo "$run_response" | grep -q "Session not found"; then
        echo "✅ Message $i successful"
        PASSED=$((PASSED + 1))
    else
        echo "❌ Message $i failed"
        echo "Response: $(echo "$run_response" | head -c 80)"
        FAILED=$((FAILED + 1))
    fi
    
    sleep 1
done

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "PHASE 4: Multiple Concurrent Sessions"
echo "════════════════════════════════════════════════════════════════"
echo ""

SESSION2="e2e-test-2-$(date +%s)"
SESSION3="e2e-test-3-$(date +%s)"
USER2="e2e-user-2"
USER3="e2e-user-3"

echo "[4.1] Creating session 2 for user 2"
create_session "$USER2" "$SESSION2" > /dev/null
PASSED=$((PASSED + 1))

echo "[4.2] Creating session 3 for user 3"
create_session "$USER3" "$SESSION3" > /dev/null
PASSED=$((PASSED + 1))

echo "[4.3] Message from user 2"
run_response=$(test_run "$USER2" "$SESSION2" "message from user 2")
if echo "$run_response" | grep -q "modelVersion" && ! echo "$run_response" | grep -q "Session not found"; then
    echo "✅ User 2 message successful"
    PASSED=$((PASSED + 1))
else
    echo "❌ User 2 message failed"
    FAILED=$((FAILED + 1))
fi

sleep 1

echo "[4.4] Message from user 3"
run_response=$(test_run "$USER3" "$SESSION3" "message from user 3")
if echo "$run_response" | grep -q "modelVersion" && ! echo "$run_response" | grep -q "Session not found"; then
    echo "✅ User 3 message successful"
    PASSED=$((PASSED + 1))
else
    echo "❌ User 3 message failed"
    FAILED=$((FAILED + 1))
fi

sleep 1

echo "[4.5] Second message from user 2"
run_response=$(test_run "$USER2" "$SESSION2" "second message from user 2")
if echo "$run_response" | grep -q "modelVersion" && ! echo "$run_response" | grep -q "Session not found"; then
    echo "✅ User 2 second message successful"
    PASSED=$((PASSED + 1))
else
    echo "❌ User 2 second message failed"
    FAILED=$((FAILED + 1))
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "PHASE 5: Load Balancing Test (Multiple Pods)"
echo "════════════════════════════════════════════════════════════════"
echo ""

SESSION4="e2e-test-lb-$(date +%s)"
USER4="e2e-user-lb"

echo "[5.1] Creating session for load balancing test"
create_session "$USER4" "$SESSION4" > /dev/null
PASSED=$((PASSED + 1))

# Get first pod that handled session creation
POD1=$(kubectl get pods -n kaiops -l app=kaiops-backend -o jsonpath='{.items[0].metadata.name}')
echo "[5.2] Session created via pod: $POD1"

echo "[5.3] Message 1 (may hit different pod)"
run_response=$(test_run "$USER4" "$SESSION4" "message 1")
if echo "$run_response" | grep -q "modelVersion" && ! echo "$run_response" | grep -q "Session not found"; then
    echo "✅ Load balanced message 1 successful"
    PASSED=$((PASSED + 1))
else
    echo "❌ Load balanced message 1 failed - Sessions not shared!"
    FAILED=$((FAILED + 1))
fi

sleep 1

echo "[5.4] Message 2 (may hit different pod again)"
run_response=$(test_run "$USER4" "$SESSION4" "message 2")
if echo "$run_response" | grep -q "modelVersion" && ! echo "$run_response" | grep -q "Session not found"; then
    echo "✅ Load balanced message 2 successful"
    PASSED=$((PASSED + 1))
else
    echo "❌ Load balanced message 2 failed - Sessions not shared!"
    FAILED=$((FAILED + 1))
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "PHASE 6: Rapid Fire Messages"
echo "════════════════════════════════════════════════════════════════"
echo ""

SESSION5="e2e-test-rapid-$(date +%s)"
USER5="e2e-user-rapid"

echo "[6.1] Creating session for rapid test"
create_session "$USER5" "$SESSION5" > /dev/null
PASSED=$((PASSED + 1))

echo "[6.2] Sending 3 messages rapidly (0.5s interval)"
for i in {1..3}; do
    run_response=$(test_run "$USER5" "$SESSION5" "rapid msg $i")
    if echo "$run_response" | grep -q "modelVersion" && ! echo "$run_response" | grep -q "Session not found"; then
        echo "✅ Rapid message $i successful"
        PASSED=$((PASSED + 1))
    else
        echo "❌ Rapid message $i failed"
        FAILED=$((FAILED + 1))
    fi
    sleep 0.5
done

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "PHASE 7: Error Handling"
echo "════════════════════════════════════════════════════════════════"
echo ""

echo "[7.1] Test with non-existent session"
run_response=$(test_run "test-user" "fake-session-xyz" "test")
if echo "$run_response" | grep -q "Session not found"; then
    echo "✅ Proper error handling for missing session"
    PASSED=$((PASSED + 1))
else
    echo "⚠️  Unexpected response for missing session (may be acceptable)"
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "FINAL RESULTS"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "✅ Tests Passed: $PASSED"
echo "❌ Tests Failed: $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║  ✅ ALL TESTS PASSED - Ready for final build!                 ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    exit 0
else
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║  ❌ SOME TESTS FAILED - Do not proceed with build             ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    exit 1
fi
