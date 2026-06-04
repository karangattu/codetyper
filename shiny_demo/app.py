from shiny import App, render, ui
import matplotlib.pyplot as plt
import numpy as np

app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.input_slider("n", "Number of bins", 10, 100, 30),
        ui.input_select("color", "Histogram Color", {
            "steelblue": "Steel Blue",
            "darkorange": "Dark Orange",
            "seagreen": "Sea Green",
            "crimson": "Crimson"
        }, selected="steelblue"),
        bg="#f8f9fa",
    ),
    ui.card(
        ui.card_header("Random Distribution Histogram"),
        ui.output_plot("dist_plot"),
    ),
    title="Shiny for Python - Interactive Demo",
)

def server(input, output, session):
    @render.plot
    def dist_plot():
        np.random.seed(42)
        x = 100 + 15 * np.random.randn(500)
        
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.hist(x, input.n(), density=True, color=input.color(), edgecolor="white", alpha=0.85)
        ax.set_title("Normal Distribution Sample", fontsize=14, pad=15)
        ax.set_xlabel("Value")
        ax.set_ylabel("Probability Density")
        ax.grid(True, linestyle="--", alpha=0.5)
        
        fig.tight_layout()
        return fig

app = App(app_ui, server)
