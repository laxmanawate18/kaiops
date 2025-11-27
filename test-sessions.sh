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
    echo "Creating session: $session_id for user: $user_id..."
    curl -s -X POST "${API_URL}/apps/${APP_NAME}/users/${user_id}/sessions/${session_id}" \
        -H "Content-Type: application/json" \
        -d '{"state": {}}' | jq '.id'
}

# Helper function to test /run endpoint
test_run() {
    local user_id=$1
    local session_id=$2
    local message=$3
    echo "Testing /run with session: $session_id, message: $message"
    response=$(curl -s -X POST "${API_URL}/run" \
        -H "Content-Type: application/json" \
        -d "{\"appName\": \"${APP_NAME}\", \"userId\": \"${user_id}\", \"sessionId\": \"${session_id}\", \"newMessage\": {\"role\": \"user\", \"parts\": [{\"text\": \"${message}\"}]}}")
    
    if echo "$response" | jq -e '.[] | select(.id)' > /dev/null 2>&1; then
        echo "✅ SUCCESS - Got response with ID"
        echo "$response" | jq '.[0] | {id, finishReason, author}'
        return 0
    elif echo "$response" | jq -e '.detail' > /dev/null 2>&1; then
        error=$(echo "$response" | jq -r '.detail')
        echo "❌ FAILED - Error: $error"
        return 1
    else
        echo "❌ FAILED - Unexpected response:"
        echo "$response" | jq '.'
        return 1
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
echo "========== SCENARIO 3: Session Reuse After Pod Restart =========="
echo "Testing session persistence..."
SESSION4="persistent-session-$(date +%s)"
USER4="persistent-user"

create_session "$USER4" "$SESSION4"
sleep 1

echo ""
echo "First message before pod check:"
test_run "$USER4" "$SESSION4" "first message" || true
sleep 2

echo ""
echo "Checking which backend pod handled the request..."
CURRENT_POD=$(kubectl get pods -n kaiops -l app=kaiops-backend -o jsonpath='{.items[0].metadata.name}')
echo "Current backend pod: $CURRENT_POD"

echo ""
echo "Second message (may go to different pod due to load balancing):"
test_run "$USER4" "$SESSION4" "second message after load balance" || true

echo ""
echo ""
echo "========== SCENARIO 4: Rapid Fire Messages =========="
echo "Testing rapid consecutive messages..."
SESSION5="rapid-session-$(date +%s)"
USER5="rapid-user"

create_session "$USER5" "$SESSION5"
sleep 1

echo ""
for i in {1..3}; do
    echo "Rapid message $i/3:"
    test_run "$USER5" "$SESSION5" "rapid message $i" || true
    sleep 0.5
done

echo ""
echo ""
echo "========== SCENARIO 5: Non-existent Session Error Handling =========="
echo "Testing what happens with invalid session..."
FAKE_SESSION="fake-session-that-does-not-exist"
USER6="test-user-6"

echo ""
echo "Attempting to send message with non-existent session:"
test_run "$USER6" "$FAKE_SESSION" "test message" || true

echo ""
echo ""
echo "=================================================="
echo "Testing Complete"
echo "=================================================="
