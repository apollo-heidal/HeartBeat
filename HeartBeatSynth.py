import numpy as np
from numpy import pi as PI
import wave
from matplotlib import pyplot

SAMPLE_RATE = 44100

def genericRescale(inputArray, outputMin, outputMax):
        '''
        Generic scaling function that maps inputArry to the range (outputMin, outputMax)
        Dimension is set to 0 for 1-D array. Specify dimension to scale.
        '''
        inputMax = np.amax(inputArray)
        inputMin = np.amin(inputArray)
        ###          input range->displacement  scale input to (0,1)    scale to output displacement  offset to true output range
        return (((inputArray - inputMin) / (inputMax - inputMin)) * (outputMax - outputMin)) + outputMin


def getHRSamples():
    times, values = [], [] #init sample lists
    with open('samples.csv', 'r') as samplesFile:
        for l in samplesFile:
            if l == '':
                continue #skip last/empty row
            t, v = l.split(',') #timestamp, value(uV)
            times.append(int(t))
            values.append(int(v))
    return np.array(times), np.array(values)


def uVtoFx():
    '''
    Maps uV readings from H10 to frequency space (25Hz, 5000Hz)
    Measurements happen about every 17ms, but the sample rate
    of the .wav file is 44100Hz so interpolation between samples is necessary.
    '''
    times, uVvalues = getHRSamples()
    assert(times.shape == uVvalues.shape)
    fxValues = genericRescale(uVvalues, 25, 1600) #25Hz min, 12800Hz max (because readings start high then drop)
    # print(np.min(fxValues), np.max(fxValues))
    # print(fxValues.shape)
    # print(fxValues)
    n_samples = times.shape[0]
    # print(len(times))

    audioSamples = np.array([]) #empty array to be appended

    for s in range(1, n_samples): #start at 1 to avoid out of bounds
        time_span = (times[s] - times[s-1]) / 1000000000 # converted to seconds
        ###                     convert to seconds      seconds / (samples / second) = samples
        n_interp_points = int(time_span * SAMPLE_RATE)
        # print(time_span)
        # print(n_interp_points)
        radians = 2*PI * fxValues[s-1] * (time_span)
        fx = np.sin(np.linspace(0, radians, num=n_interp_points))
        # print(scaled_fx)
        audioSamples = np.append(audioSamples, fx)
        # print(s)
    
    # print(audioSamples.shape)

    return audioSamples


def writeFile(data):
    with wave.open('HeartBeat.wav', 'wb') as wavFile:
        wavFile.setparams( (1, 2, SAMPLE_RATE, 0, 'NONE', None) ) # (nchannels, sample_width=2B, framerate, nframe, ...)
        scaled_data = genericRescale(data, 0, 2**16 - 1)
        # print(np.min(scaled_data), np.max(scaled_data))
        wavFile.writeframes(np.short(scaled_data))


def plotAudioData(data):
    t_axis = np.linspace(0, len(data) / SAMPLE_RATE, num=len(data))
    pyplot.plot(t_axis, data)
    pyplot.show()


if __name__ == "__main__":
    data = uVtoFx()
    writeFile(data)
    # plotAudioData(data)
