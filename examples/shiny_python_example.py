---
language: python
output_file: app.py
typing_speed: 0.01
execute_blocks: true
format_output: true
---

## Imports | execute=true, pause_after=1.0
from faicons import icon_svg
from shiny import App, render, ui
import pandas as pd
import matplotlib.pyplot as plt

## Data | execute=true, pause_after=1.0
df = pd.DataFrame({
    "Category": ["A", "A", "B", "B", "C", "C"],
    "X": [1, 2, 3, 4, 5, 6],
    "Y": [10, 15, 7, 12, 18, 22]
})

## UI Layout | execute=true, pause_after=1.0
app_ui = ui.page_fluid(
    ui.card(
        ui.card_header(
            "Graph Filter Dashboard",
            ui.toolbar(
                ui.toolbar_input_select(
                    id="filter_type",
                    label="Filter Category",
                    choices=["All", "A", "B", "C"],
                    icon=icon_svg("filter"),
                ),
                align="right",
            ),
        ),
        ui.card_body(
            ui.output_plot("category_plot"),
        ),
        full_screen=True,
    ),
    {"class": "vh-100 d-flex justify-content-center align-items-center px-4"},
)

## Server Logic | execute=true, pause_after=1.0
def server(input, output, session):
    @render.plot
    def category_plot():
        selected = input.filter_type()
        if selected == "All":
            filtered_df = df
        else:
            filtered_df = df[df["Category"] == selected]
        
        fig, ax = plt.subplots(figsize=(6, 4))
        colors = filtered_df["Category"].map({"A": "#e06666", "B": "#6fa8dc", "C": "#8fce00"})
        ax.scatter(filtered_df["X"], filtered_df["Y"], c=colors, s=150, edgecolors="black", linewidths=1.5)
        ax.set_xlim(0, 7)
        ax.set_ylim(5, 25)
        ax.set_title(f"Scatter Plot: {selected}", fontsize=14, pad=15)
        ax.grid(True, linestyle="--", alpha=0.5)
        return fig

## Run App | execute=true, pause_after=1.0
app = App(app_ui, server)
