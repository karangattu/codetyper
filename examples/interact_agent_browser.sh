#!/bin/bash
agent-browser close 2>/dev/null || true
agent-browser record start browser_demo.webm

say "Opening the Shiny application in the browser." &
agent-browser --headed open http://127.0.0.1:8000
sleep 2

say "Let's update the histogram slider to fifty-five to view the updated distribution." &
agent-browser --headed eval '$(".js-range-slider").data("ionRangeSlider").update({from: 55});'

sleep 3
say "The application has successfully updated. Let's complete the recording." &
agent-browser record stop
agent-browser close
