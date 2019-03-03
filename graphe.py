import numpy as np
from QuantLib import *

from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.ticker import LinearLocator, FormatStrFormatter
from callibriUtils import *

def afficheSurfaceVol(black_var_surface) :
    '''plot_years = np.arange(0, 2, 0.1)
    plot_strikes = np.arange(535, 750, 1)
    fig = plt.figure()
    ax = fig.gca(projection='3d')
    X, Y = np.meshgrid(plot_strikes, plot_years)
    Z = np.array([black_var_surface.blackVol(y, x)
                for xr, yr in zip(X, Y)
                    for x, y in zip(xr,yr) ]
                ).reshape(len(X), len(X[0]))

    surf = ax.plot_surface(X,Y,Z, rstride=1, cstride=1, cmap=cm.coolwarm,
                    linewidth=0.1)
    fig.colorbar(surf, shrink=0.5, aspect=5)'''


    fig = plt.figure()
    ax = fig.gca(projection='3d')

    # Make data.
    X = np.arange(0.1, 10, 0.1)
    Y = np.arange(1500, 5000, 10)
    X, Y = np.meshgrid(X, Y)

    Z = np.array([black_var_surface.blackVol(float(x),float(y))/100
                for xr, yr in zip(X, Y)
                    for x, y in zip(xr,yr) ]
                ).reshape(len(X), len(X[0]))




    # Plot the surface.
    surf = ax.plot_surface(X, Y, Z, cmap=cm.coolwarm,
                        linewidth=0, antialiased=False)

    # Customize the z axis.
    ax.set_zlim(0.1, 0.5)
    ax.zaxis.set_major_locator(LinearLocator(10))
    ax.zaxis.set_major_formatter(FormatStrFormatter('%.02f'))

    # Add a color bar which maps values to colors.
    fig.colorbar(surf, shrink=0.5, aspect=5)

    plt.show()


