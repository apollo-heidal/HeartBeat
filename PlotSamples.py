from matplotlib import pyplot
import numpy as np

times = []
vals = []

with open('samples.csv') as file:
    for n in file:
        try:
            t, v = n.split(",")
            times.append(int(t))
            vals.append(int(v))
        except ValueError as e:
            print(e)
        #val = int(n.split(",")[-1])
        # if abs(val) > 1500:
        #     continue
        # samples.append(val)

x = np.array(times)
y = np.array(vals)
# x = np.linspace(0, 100, num=len(y))

pyplot.plot(x, y, '-o', markersize=2,linewidth=1)
pyplot.show()

