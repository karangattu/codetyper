#!/bin/bash
agent-browser close 2>/dev/null || true
agent-browser record start browser_demo.webm

say "Opening the Graph Filter Dashboard." &
agent-browser --headed open http://127.0.0.1:8000
sleep 2

say "Filtering plot to show Category A data." &
agent-browser --headed select "#filter_type" "A"
sleep 2

say "Filtering plot to show Category B data." &
agent-browser --headed select "#filter_type" "B"
sleep 2

say "Filtering plot to show Category C data." &
agent-browser --headed select "#filter_type" "C"
sleep 2

say "Restoring the plot to display all categories." &
agent-browser --headed select "#filter_type" "All"
sleep 2

agent-browser record stop
agent-browser close
