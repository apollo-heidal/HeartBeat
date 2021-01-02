from matplotlib import pyplot
import numpy as np

samples = []
with open('src/samples.csv') as file:
    file.readline()
    for n in file:
        samples.append(int(n))
        #val = int(n.split(",")[-1])
        # if abs(val) > 1500:
        #     continue
        # samples.append(val)

y = np.array(samples)
x = np.linspace(0, 100, num=len(y))

pyplot.plot(x, y)
pyplot.show()

