import plotly.graph_objects as go
import numpy as np
import pandas as pd

def epsilon_slider(data):
    # Get true values from random
    data = data.sample(n = 5)
    last_column = (data.iloc[: , -1]).values
    true_value1, true_value2, true_value3, true_value4, true_value5 = [last_column[i] for i in (0, 1, 2, 3, 4)]
    # Create figure
    fig = go.Figure()

    # Add traces, one for each slider step
    steps = []
    for epsilon in np.logspace(float(0.1), 5):
        fig.add_trace(
            go.Scatter(
                visible=False,
                line=dict(color="#00CED1", width=6),
                name="epsilon = " + str(epsilon),
                x=np.logspace(float(true_value1 - (true_value1/2)), float(true_value1 + (true_value1/2))),
                y=np.exp(-abs(np.logspace(float(true_value1 - (true_value1/2)), 
                float(true_value1 + (true_value1/2)))-true_value1)/(2.0/float(epsilon)))/(2.*(2.0/float(epsilon)))))

    # Make 10th trace visible
    fig.data[1].visible = True

    # Create and add slider
    steps = []
    for i in range(len(fig.data)):
        step = dict(
            method="update",
            args=[{"visible": [False] * len(fig.data)},
                {"title": "Slider switched to Epsilon: " + str(i)}],  # layout attribute
        )
        step["args"][0]["visible"][i] = True  # Toggle i'th trace to "visible"
        steps.append(step)

    sliders = [dict(
        active=1,
        currentvalue={"prefix": "Epsilon: "},
        pad={"t": 1},
        steps=steps
    )]

    fig.update_layout(
        sliders=sliders
    )
    fig.add_vline(true_value1)

    return fig

def exponential_epsilon_slider(probabilities: pd.DataFrame) -> go.Figure:
    fig = go.Figure()

    probabilities.groupby("Epsilon").apply(
        lambda r: fig.add_trace(
                go.Bar(x=[p[0] for p in r.Value], y=r.Probability, visible=False)
            )
    )
    fig.data[0].visible = True

    # Create and add slider
    steps = []
    for i in range(len(fig.data)):
        step = dict(
            method="update",
            args=[{"visible": [False] * len(fig.data)},
                {"title": "Slider switched to Epsilon: " + str(i)}],  # layout attribute
        )
        step["args"][0]["visible"][i] = True  # Toggle i'th trace to "visible"
        steps.append(step)

    sliders = [dict(
        active=0,
        currentvalue={"prefix": "Epsilon: "},
        pad={"t": 1},
        steps=steps
    )]

    fig.update_layout(
        sliders=sliders
    )

    return fig