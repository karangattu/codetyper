#!/bin/bash
agent-browser close 2>/dev/null || true
agent-browser record start browser_demo.webm

say "Opening the Data Dashboard." &
agent-browser --headed open http://127.0.0.1:8000
sleep 2

say "Let's toggle the label display on our toolbar." &
agent-browser --headed click "#toggle_label"
sleep 2

say "Adding Grid option to the toolbar view modes." &
agent-browser --headed click "#add_option"
sleep 2

say "Let's change our view selection to the Chart." &
agent-browser --headed click "#change_selection"
sleep 2

say "Selecting the newly added Grid option." &
agent-browser --headed select "#view_mode" "Grid"
sleep 3

agent-browser record stop
agent-browser close
