import numpy as np


def kde_mode(kernel, values):
    height = kernel.pdf(values)
    print("height", height[np.argmax(height)])
    return values[np.argmax(height)]
