#!/bin/bash
agent-browser close 2>/dev/null || true

agent-browser --headed open http://127.0.0.1:8000
agent-browser record start browser_demo.webm
sleep 2

agent-browser --headed select "#filter_type-select" "All"
sleep 2

agent-browser --headed select "#filter_type-select" "A"
sleep 2

agent-browser --headed select "#filter_type-select" "B"
sleep 2

agent-browser --headed select "#filter_type-select" "C"
sleep 2

agent-browser record stop
agent-browser close
