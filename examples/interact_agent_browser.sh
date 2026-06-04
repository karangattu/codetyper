#!/bin/bash
agent-browser close 2>/dev/null || true
agent-browser record start browser_demo.webm

agent-browser --headed open http://127.0.0.1:8000
sleep 2

agent-browser --headed select "#filter_type" "A"
sleep 2

agent-browser --headed select "#filter_type" "B"
sleep 2

agent-browser --headed select "#filter_type" "C"
sleep 2

agent-browser --headed select "#filter_type" "All"
sleep 2

agent-browser record stop
agent-browser close
