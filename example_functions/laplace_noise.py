import pandas as pd
import numpy as np

def laplaceMechanism(x, epsilon):
    """Add Laplace noise to query result.
    random.laplace parameters:
    loc: The position, µ, of the distribution peak. Default is 0.
    scale: λ, the exponential decay. Default is 1. Must be non-negative.
    size: Output shape.
    ----------
    Example:
    SELECT Age, Charge, COUNT(Charge) as c
    FROM Arrests
    GROUP BY Age, Charge
    ----------
    data["COUNT(Charge)"] = data["COUNT(Charge)"].apply(laplaceMechanism, args=(2,))
    """
    x +=  np.random.laplace(0, 1.0/epsilon, 1)[0]
    return x