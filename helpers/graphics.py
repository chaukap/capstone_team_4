import plotly.graph_objects as go
import numpy as np

def epsilon_slider(df):
    # Get true values from random
    df = df.sample(n = 5)
    last_column = (df.iloc[: , -1]).values
    true_value1, true_value2, true_value3, true_value4, true_value5 = [last_column[i] for i in (0, 1, 2, 3, 4)]
    # Create figure
    print(df)

    # Add traces, one for each slider step
    start = float(true_value1 - (true_value1*2))
    stop = float(true_value1 + (true_value1*2))
    trace_list1 =[]
    for epsilon in np.arange(0.1, 4.1, 0.1):
        #fig.add_trace(
        trace_list1.append(go.Scatter(
            visible=False,
            line=dict(color="#00CED1", width=6),
            showlegend=True,
            name="epsilon = " + str(round(epsilon, 3)),
            x=np.arange(start, stop, 0.2),
            y=np.exp(-abs(np.arange(start, stop, 0.2)-true_value1)/(2.0/float(epsilon)))/(2.*(2.0/float(epsilon)))))

    fig = go.Figure(data=trace_list1)
    # Default
    fig.data[5].visible = True
    # Create and add slider
    steps = []
    for i in range(len(np.arange(0.1, 4.1, 0.1))):
        step = dict(
            method="restyle",
            args=[{"visible": [False] * len(np.arange(0.1, 4.1, 0.1))},
                {"title": "Slider switched to Epsilon: " + str(i)}],  # layout attribute
        )
        step["args"][0]["visible"][i] = True  # Toggle i'th trace to "visible"
        steps.append(step)

    sliders = [dict(
        active=1,
        currentvalue={"prefix": "Epsilon: "},
        pad={"t": 10},
        steps=steps
    )]

    fig.update_layout(
        sliders=sliders
    )
    fig.add_vline(true_value1)

    return fig