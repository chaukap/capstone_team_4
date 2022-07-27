import plotly.graph_objects as go
import numpy as np
import pandas as pd
import scipy.stats as st

def epsilon_slider(data, u, l):
    data=pd.DataFrame(data)
    df = data.sample(n = 1)
    true_value = float((df.iloc[: , -1]).values[0])
    sens = abs(max(u,-l))
    if -l > u:
        ad_value = float(true_value) - float(sens)
    else:
        ad_value = float(true_value) + float(sens)
    epsilons=np.arange(0.1, 4.1, 0.1)
    graph_range=np.arange(float(true_value - abs(true_value*5)), float(true_value + abs(true_value*5)))
        
    # Create figure
    # Add traces, one for each slider step
    trace_list1, trace_list2 =[],[] # True Value
    trace_list3, trace_list4 =[],[] # Hypothetical Value
    for epsilon in np.arange(0.1, 4.1, 0.1):
        b = float(sens)/float(epsilon)
        true_val_y=np.exp(-abs(graph_range-float(true_value))/(b))/(2.*(b)) # True value Y range
        ad_val_y=np.exp(-abs(graph_range-float(ad_value))/(b))/(2.*(b))     # Hypothetical value Y range
        # confidence interval
        true_val_a = np.array(true_val_y)
        ad_val_a = np.array(ad_val_y)
        true_val_x1 = np.percentile(true_val_a, 75)
        true_val_x2 = np.percentile(true_val_a, 25)
        ad_val_x1 = np.percentile(ad_val_a, 75)
        ad_val_x2 = np.percentile(ad_val_a, 25)

        y_max = max(true_val_y)
        if  min(true_val_y)< min(ad_val_y):
            y_min = min(true_val_y)
        else:
            y_min = min(ad_val_y)
        trace_list1.append(go.Scatter(
            visible=False,
            line=dict(color="#6505cc", width=6),
            name='True Value of Selected Group',
            x=graph_range,
            y=true_val_y
            ))
        trace_list2.append(go.Scatter(  # True Value Confidence Interval
            visible=False,
            name='True Value CI',
            line=dict(color="#9266c4", width=2),
            x=[None,true_val_x2,true_val_x2,true_val_x1,true_val_x1,true_val_x2], 
            y=[None,y_min,y_max,y_max,y_min,y_min], 
            fill="toself"
        ))
        trace_list3.append(go.Scatter(
            visible=False,
            line=dict(color="#e91919", width=6),
            name='Hypothetical Worst-Case Value',
            x=graph_range,
            y=ad_val_y
            ))
        trace_list4.append(go.Scatter(  # Hypothetical Value Confidence Interval
            visible=False,
            name='Hypothetical Worst-Case Value CI',
            line=dict(color="#e36666", width=2),
            x=[None,ad_val_x2,ad_val_x2,ad_val_x1,ad_val_x1,ad_val_x2], 
            y=[None,y_min,y_max,y_max,y_min,y_min], 
            fill="toself"
        ))
    trace_list1[0].visible = True          
    trace_list2[0].visible = True
    trace_list3[0].visible = True
    trace_list4[0].visible = True
    fig = go.Figure(data=trace_list4+trace_list2+trace_list3+trace_list1)

    
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
    #fig.add_vrect(x0=confidence_intervals[0], x1=confidence_intervals[1], line_width=0, fillcolor="green", opacity=0.2)

    fig.update_layout(
        sliders=sliders
    )
    fig.update_layout(
        title='Epsilon: 0.1',
        xaxis_visible=True,
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
                go.Bar(x=r.Value, y=r.Probability,visible=False, 
                    marker=dict(
                        color = [f"rgb({str((1-t) * 101)}, {str((1-t) * 5)}, {str((1-t) * 204)})" for t in r.Probability]
                    ),
                    hovertext = r.apply(lambda t: f"{t.Value}: {round(t.Probability*100, 2)}%", axis=1),
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