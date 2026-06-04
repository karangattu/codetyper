---
language: python
output_file: shiny_demo_output.py
typing_speed: 0.01
execute_blocks: true
format_output: true
---

## Imports | execute=true, pause_after=1.0
from shiny import App, render, ui

## UI Layout | execute=true, pause_after=1.0
app_ui = ui.page_fluid(
    ui.input_slider("n", "N", 0, 100, 20),
    ui.output_text_verbatim("txt"),
)

## Server Function | execute=true, pause_after=1.0
def server(input, output, session):
    @render.text
    def txt():
        return f"n*2 is {input.n() * 2}"

## Run App | execute=true, pause_after=1.0
app = App(app_ui, server)
