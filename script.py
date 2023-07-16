import subprocess
import re
import time


def getWattageRange():
    getWattageRange = ["sudo", "nvidia-smi", "-q", "-d", "POWER"]
    result = subprocess.run(
        getWattageRange, capture_output=True, encoding="utf-8"
    ).stdout
    minPattern = "Min Power Limit\s+:\s+(\d+)"
    maxPattern = "Max Power Limit\s+:\s+(\d+)"
    min = int(re.search(minPattern, result).group(1))
    max = int(re.search(maxPattern, result).group(1))
    return [min, max]


wattageRange = getWattageRange()
fanRange = [30, 100]

fanCurve = [[40, fanRange[0]], [50, 50], [60, 70], [65, fanRange[1]]]
wattageCurve = [
    [70, wattageRange[1]],
    [75, 220],
    [76, 200],
    [77, 170],
    [78, wattageRange[0]],
]


def resetFan():
    resetFan = ["sudo", "nvidia-settings", "-a", "GPUFanControlState=0"]
    subprocess.run(resetFan, capture_output=True)


def resetWattage():
    resetWattage = ["sudo", "nvidia-smi", "-pl", "270"]
    subprocess.run(resetWattage, capture_output=True)


def getTemperature():
    pattern = "GPU Current Temp\s+:\s+(\d+)"
    getTemperature = ["sudo", "nvidia-smi", "-q", "-d", "TEMPERATURE"]
    result = subprocess.run(
        getTemperature, capture_output=True, encoding="utf-8"
    ).stdout
    return int(re.search(pattern, result).group(1))


def getFanSpeed():
    pattern = "Fan Speed\s+:\s+(\d+)"
    getFanTarget = ["sudo", "nvidia-smi", "-q"]
    result = subprocess.run(getFanTarget, capture_output=True, encoding="utf-8").stdout
    return int(re.search(pattern, result).group(1))


def getMaxWattage():
    pattern = "Requested Power Limit\s+:\s+(\d+)"
    getMaxWattage = ["sudo", "nvidia-smi", "-q", "-d", "POWER"]
    result = subprocess.run(getMaxWattage, capture_output=True, encoding="utf-8").stdout
    return int(re.search(pattern, result).group(1))


def setFan(speed):
    if speed > fanRange[1] or speed < fanRange[0]:
        return False
    setFan = ["sudo", "nvidia-settings", "-a", f"GPUTargetFanSpeed={str(speed)}"]
    subprocess.run(setFan, capture_output=True, encoding="utf-8").stdout
    return True


def setWattage(wattage):
    if wattage > wattageRange[1] or wattage < wattageRange[0]:
        return False
    setMaxWattage = ["sudo", "nvidia-smi", "-pl", str(wattage)]
    subprocess.run(setMaxWattage, capture_output=True, encoding="utf-8").stdout
    return True


def calculateFanSpeed(currentTemperature, fanCurve):
    for point in fanCurve:
        if currentTemperature <= point[0]:
            newFanSpeed = int(point[1] * currentTemperature / point[0])
            if newFanSpeed < fanRange[0]:
                newFanSpeed = fanRange[0]
            setFan(newFanSpeed)
            return True
    setFan(fanCurve[len(fanCurve) - 1][1])


def calculateWattage(currentTemperature, wattageCurve):
    for point in wattageCurve:
        if currentTemperature <= point[0]:
            # Calculate the slope of the line using point 2 and point 1
            slope = (wattageCurve[1][1] - wattageCurve[0][1]) / (
                wattageCurve[1][0] - wattageCurve[0][0]
            )

            # Calculate the y-intercept (b) using point 1
            intercept = wattageCurve[0][1] - slope * wattageCurve[0][0]

            # Use the equation of the line to calculate the new wattage
            newWattage = int(slope * currentTemperature + intercept)
            # if newWattage < wattageCurve[1][1]:
            #     newWattage = wattageCurve[1][1]
            if currentTemperature < wattageCurve[0][0]:
                newWattage = wattageCurve[0][1]

            setWattage(newWattage)

            return True
    setWattage(wattageCurve[1][1])


try:
    while True:
        currentTemperature = getTemperature()
        calculateFanSpeed(currentTemperature, fanCurve)
        if currentTemperature < wattageCurve[0][0]:
            resetWattage()
        else:
            calculateWattage(currentTemperature, wattageCurve)
        time.sleep(1)
finally:
    resetFan()
    resetWattage()
