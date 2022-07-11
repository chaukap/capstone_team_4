"""
CORE ANONYMOUS FUNCTIONS
    - ANON_COUNT
    - ANON_SUM
    - ANON_AVG
6.6.22
"""

import numpy as np
from scipy.stats import laplace
import matplotlib.pyplot as plt
import pandas as pd

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
    x +=  np.random.laplace(0, 2/epsilon, 1)[0]
    return x

def laplaceMechanismClamped(x, epsilon, u, l):
    
    c = abs(u - l)
    noise = np.random.laplace(0, 2*c/epsilon, 1)[0]
    print(noise)
    if noise >= u :
        noise = u
    else :
        if noise <= l:
            noise = l
    return x + noise

def ANON_COUNT(col, epsilon):
    """
    Computes the count of the membership in a column 
    adds noise to the count, Laplacian noise sensitivity = 1
            
    """
    trueCount = np.shape(col)[0]
    noisyCount = laplaceMechanism(trueCount, epsilon)
    return noisyCount

def ANON_SUM(col, epsilon, u, l):
    """
    Computes the sum of a column 
    adds noise to the sum, here using Laplace 
    eventually want to pass a function additional noise options
    returns noisy sum, sensitivity = u -l, to generalize sensitivity 
    parameter needs to be added
            
    """
    trueSum = np.sum(col)
    noisySum = laplaceMechanismClamped(trueSum, epsilon, u,l)
    return round(noisySum, 2)
    
def ANON_AVG(col, epsilon, u, l):
    """
    Computes the sum of a column 
    adds noise to the sum, here using Laplace 
    eventually want to pass a function additional noise options
    returns noisy sum, sensitivity = u -l 
            
    """
    s = ANON_SUM(col, epsilon, u, l)
    c = ANON_COUNT(col, epsilon)
    if c <= 1:
        return (np.max(col) - np.min(col))/2
    else:
        return round(s/c,2)


def score(col, option):
    # Counts the number of occurances of "option" in a column of a dataframe
    # Divides the numver of occurances by 1000
    return col.value_counts()[option]/1000
   
def exponential(col, R, u, sensitivity, epsilon):
    # For a given column of data, col,
    # calculate the score for each unique element of the column
    # R is the set of unique values in col
    # u is the "score" function chosen

    scores = [u(col, r) for r in R]
    
    # Calculate the probability for each element, based on its score
    probabilities = [np.exp(epsilon * score / (2 * sensitivity)) for score in scores]
    
    # Normalize the probabilties so they sum to 1
    probabilities = probabilities / np.linalg.norm(probabilities, ord=1)
    print(probabilities)
    #print(probabilities)
    # Choose an element from all unique elements based on the probabilities
    return np.random.choice(R, 1, p=probabilities)[0]

#__________________________________________________________
# Test Laplace
    
k = 10       
epsilon = 1.0
col = np.random.randint(100, size=(k))
u = np.max(col)
l = np.min(col)
trueSum = round(np.sum(col),2)       
noisySum = ANON_SUM(col, epsilon, u, l)
print(noisySum, trueSum, noisySum - trueSum)
noisyAvg = ANON_AVG(col, epsilon,u, l)
print(noisyAvg)

fig, ax = plt.subplots(1, 1)
x = np.linspace(laplace.ppf(0.01), laplace.ppf(0.99), 100)
ax.plot(x, laplace.pdf(x),'r-', lw=5, alpha=0.6, label='laplace pdf')
rv = laplace()
ax.plot(x, rv.pdf(x), 'k-', lw=2, label='frozen pdf')
r = laplace.rvs(size=100000)
ax.hist(r, density=True, histtype='stepfilled', alpha=0.5)
ax.legend(loc='best', frameon=False)
plt.show()

#_______________________________________________________________
# Test Exponential

adult = {'Marital Status': ['Never Married', 'Never Married','Married', 'Married',
                            'Married','Divorced','Married','Widowed','Divorced','Married',
                            'Never Married', 'Divorced', 'Married', 'Widowed', 'Married']}
adult = pd.DataFrame(adult)

# Generate all unique elements in the chosen column
options = adult['Marital Status'].unique()

# Observe the fixed scores (frequencies) 
score(adult['Marital Status'], 'Never Married')
score(adult['Marital Status'], 'Divorced')
score(adult['Marital Status'], 'Married')
score(adult['Marital Status'], 'Widowed')

# test exponential mechanism by choosing col, unique values, score function,
#  sensitivity = 1, episilon  = 1, random choice of 200 options?
r = [exponential(adult['Marital Status'], options, score, 1, 1) for i in range(200)]
pd.Series(r).value_counts()

print(pd.Series(r).value_counts())

#k = 10 
      
epsilon = .5
col = [10,13,14,12,18,14,18,17,16,12,48]
u = np.max(col)
l = np.min(col)
trueSum = round(np.sum(col),2)       
noisySum = ANON_SUM(col, epsilon, u, l)
print(noisySum, trueSum, noisySum - trueSum)
noisyAvg = ANON_AVG(col, epsilon,u, l)
print(noisyAvg, u, l)

# test exponential mechanism by choosing col, unique values, score function,

r = [exponential(adult['Marital Status'], options, score, 1, 10) for i in range(200)]
pd.Series(r).value_counts()
