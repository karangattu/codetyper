#!/bin/bash
agent-browser close 2>/dev/null || true
agent-browser record start browser_demo.webm

agent-browser --headed open http://127.0.0.1:8000
sleep 2

agent-browser --headed eval '$(".js-range-slider").data("ionRangeSlider").update({from: 55});'

sleep 3
agent-browser record stop
agent-browser close
