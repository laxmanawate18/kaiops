#!/bin/bash

# Session Testing Script for KaiOPS
# Tests various session scenarios to identify issues

set -e

API_URL="http://kaiops-sre.searceinc.net"
APP_NAME="sre_agent"

echo "=================================================="
echo "KaiOPS Session Testing Suite"
echo "=================================================="
echo ""

# Helper function to create a session
create_session() {
    local user_id=$1
    local session_id=$2
    echo "[$(date '+%H:%M:%S')] Creating session: $session_id for user: $user_id..."
    curl -s -X POST "${API_URL}/apps/${APP_NAME}/users/${user_id}/sessions/${session_id}" \
        -H "Content-Type: application/json" \
        -d '{"state": {}}' > /dev/null
    echo "  Session created"
}

# Helper function to test /run endpoint
test_run() {
    local user_id=$1
    local session_id=$2
    local message=$3
    echo "[$(date '+%H:%M:%S')] Testing /run with session: $session_id"
    response=$(curl -s -X POST "${API_URL}/run" \
        -H "Content-Type: application/json" \
        -d "{\"appName\": \"${APP_NAME}\", \"userId\": \"${user_id}\", \"sessionId\": \"${session_id}\", \"newMessage\": {\"role\": \"user\", \"parts\": [{\"text\": \"${message}\"}]}}")
    
    # Check if it contains an error
    if echo "$response" | grep -q "Session not found"; then
        echo "  ❌ FAILED - Session not found error"
        return 1
    elif echo "$response" | grep -q "detail"; then
        echo "  ❌ FAILED - Error response: $(echo "$response" | head -c 100)"
        return 1
    elif echo "$response" | grep -q "modelVersion"; then
        echo "  ✅ SUCCESS - Got response from model"
        return 0
    else
        echo "  ⚠️  UNKNOWN - Got response: $(echo "$response" | head -c 100)"
        return 0
    fi
}

echo ""
echo "========== SCENARIO 1: Single Session, Multiple Messages =========="
echo "Testing if one session can handle 3 consecutive messages..."
SESSION1="test-session-1-$(date +%s)"
USER1="test-user-1"

create_session "$USER1" "$SESSION1"
sleep 1

echo ""
echo "Message 1/3:"
test_run "$USER1" "$SESSION1" "hello" || true
sleep 2

echo ""
echo "Message 2/3:"
test_run "$USER1" "$SESSION1" "how are you" || true
sleep 2

echo ""
echo "Message 3/3:"
test_run "$USER1" "$SESSION1" "what is your name" || true

echo ""
echo ""
echo "========== SCENARIO 2: Multiple Concurrent Sessions =========="
echo "Testing if multiple sessions can work simultaneously..."
SESSION2="test-session-2-$(date +%s)"
SESSION3="test-session-3-$(date +%s)"
USER2="test-user-2"
USER3="test-user-3"

create_session "$USER2" "$SESSION2"
create_session "$USER3" "$SESSION3"
sleep 1

echo ""
echo "Sending messages from both sessions..."
echo "User 2 message:"
test_run "$USER2" "$SESSION2" "message from user 2" || true

echo ""
echo "User 3 message:"
test_run "$USER3" "$SESSION3" "message from user 3" || true

echo ""
echo "User 2 second message:"
test_run "$USER2" "$SESSION2" "another message from user 2" || true

echo ""
echo ""
echo "========== SCENARIO 3: Load Balancing Test =========="
echo "Testing if session works across multiple pods..."
SESSION4="persist-session-$(date +%s)"
USER4="persist-user"

create_session "$USER4" "$SESSION4"
sleep 1

echo ""
echo "Message 1 (Pod 1):"
test_run "$USER4" "$SESSION4" "first message" || true
sleep 1

echo ""
echo "Message 2 (May go to different pod):"
test_run "$USER4" "$SESSION4" "second message" || true
sleep 1

echo ""
echo "Message 3 (May go to different pod):"
test_run "$USER4" "$SESSION4" "third message" || true

echo ""
echo ""
echo "========== SCENARIO 4: Rapid Fire Messages =========="
echo "Testing rapid consecutive messages (0.5 second interval)..."
SESSION5="rapid-session-$(date +%s)"
USER5="rapid-user"

create_session "$USER5" "$SESSION5"
sleep 1

echo ""
for i in {1..3}; do
    echo "Rapid message $i/3:"
    test_run "$USER5" "$SESSION5" "rapid msg $i" || true
    sleep 0.5
done

echo ""
echo ""
echo "========== SCENARIO 5: Invalid Session Error Handling =========="
echo "Testing what happens with non-existent session..."
FAKE_SESSION="fake-session-$(date +%s)"
USER6="test-user-6"

echo ""
echo "Attempting to send message with non-existent session:"
test_run "$USER6" "$FAKE_SESSION" "test message" || true

echo ""
echo ""
echo "=================================================="
echo "Testing Complete"
echo "=================================================="
