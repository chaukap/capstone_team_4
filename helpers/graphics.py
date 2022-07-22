import plotly.graph_objects as go
import numpy as np
import pandas as pd
import scipy.stats as st

def epsilon_slider(data, u, l):
    # Get true values from random
    data=pd.DataFrame(data)
    df = data.sample(n = 1)
    true_value = (df.iloc[: , -1]).values[0]
    u , l = int(u), int(l)
    ad_value = max(abs(u),abs(l))
    if ad_value == true_value:
        ad_value += 1
    else: 
        ad_value = ad_value

    wo_tv_df = data.copy(deep=False).drop(data.index[df.index[0]])
    
    epsilons=np.arange(0.1, 4.1, 0.1)
    graph_range=np.arange(float(true_value - (true_value*5)), float(true_value + (true_value*5)))
    ad_graph_range=np.arange(float(ad_value - (ad_value*5)), float(ad_value + (ad_value*5)))
    confidence_intervals = st.t.interval(0.95, len(graph_range)-1, loc=float(true_value), scale=st.sem(graph_range))

    #calculate sensitivity
    sens = max(abs(l- wo_tv_df.iloc[: , -1].mean()), abs(u - wo_tv_df.iloc[: , -1].mean()))
    ad_sens = max(abs(l- data.iloc[: , -1].mean()), abs(u - data.iloc[: , -1].mean()))
    
    # Create figure
    # Add traces, one for each slider step
    trace_list1 =[]
    trace_list2 =[]
    for epsilon in np.arange(0.1, 4.1, 0.1):
        trace_list1.append(go.Scatter(
            visible=False,
            line=dict(color="#6505cc", width=6),
            name='Ex. True Value',
            x=graph_range,
            y=np.exp(-abs(graph_range-float(true_value))/(sens/float(epsilon)))/(2.*(sens/float(epsilon)))))
        trace_list2.append(go.Scatter(
            visible=False,
            line=dict(color="red", width=6),
            name='Worst-Case Value',
            x=ad_graph_range,
            y=np.exp(-abs(ad_graph_range-float(ad_value))/(ad_sens/float(epsilon)))/(2.*(ad_sens/float(epsilon)))))

    fig = go.Figure(data=trace_list1+trace_list2)
    fig.data[0].visible = True

    
    # Create and add slider
    steps = []
    for i in range(len(epsilons)):
        step = dict(
            method="update",
            label=""+str(round(epsilons[i],2)),
            args=[{"visible": [False] * len(np.arange(0.1, 4.1, 0.1))},
                {"title": "Epsilon: " + str(round(epsilons[i], 2))}],  # layout attribute
        )
        step["args"][0]["visible"][i] = True  # Toggle i'th trace to "visible"
        steps.append(step)

    sliders = [dict(
        active=0,
        currentvalue={"visible": False},
        pad={"t": 20},
        steps=steps
    )]

    fig.add_vline(true_value, name="True Value")
    fig.add_vrect(x0=confidence_intervals[0], x1=confidence_intervals[1], line_width=0, fillcolor="green", opacity=0.2)

    fig.update_layout(
        sliders=sliders
    )
    fig.update_layout(
        title='Epsilon: 0.1',
        xaxis_visible=False,
        yaxis=dict(
            title= dict(
                text='Probability Density',
                font=dict(
                    family='Montserrat, sans-serif'
                )
            ),
            titlefont_size=20,
            tickfont_size=14,
        )
    )

    return fig

def exponential_epsilon_slider(probabilities: pd.DataFrame) -> go.Figure:
    fig = go.Figure()

    probabilities.groupby("Epsilon").apply(
        lambda r: fig.add_trace(
                go.Bar(x=[q[0] for q in r.Value], y=r.Probability,visible=False, 
                    marker=dict(
                        color = [f"rgb({str((1-t) * 101)}, {str((1-t) * 5)}, {str((1-t) * 204)})" for t in r.Probability]
                    ),
                    hovertext = r.apply(lambda t: f"{t.Value[0]}: {round(t.Probability*100, 2)}%", axis=1),
                    hoverinfo = "text"
                )
            )
    )
    fig.data[0].visible = True

    epsilons = probabilities.Epsilon.unique()

    # Create and add slider
    steps = []
    for i in range(len(fig.data)):
        step = dict(
            method="update",
            args=[{"visible": [False] * len(fig.data)},
                {"title": "Epsilon: " + str(round(epsilons[i], 2))}],  # layout attribute
            label=round(epsilons[i],1)
        )
        step["args"][0]["visible"][i] = True  # Toggle i'th trace to "visible"
        steps.append(step)

    sliders = [dict(
        active=0,
        currentvalue={"visible": False},
        pad={"t": 20},
        steps=steps
    )]

    fig.update_layout(
        sliders=sliders
    )
    fig.update_layout(
        title='Epsilon: 0.1',
        xaxis_tickfont_size=14,
        yaxis=dict(
            title= dict(
                text='Probability',
                font=dict(
                    family='Montserrat, sans-serif'
                )
            ),
            titlefont_size=20,
            tickfont_size=14,
        )
    )
    return fig