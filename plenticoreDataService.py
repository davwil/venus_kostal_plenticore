import requests
import time
lastTime = 0
lastEnergy = 0
calcEnergy = 0

def get_data(baseUrl, sessionId):
    global lastTime
    global lastEnergy
    global calcEnergy

    headers = {'Content-type': 'application/json', 'Accept': 'application/json',
               'authorization': "Session " + sessionId}
    url = baseUrl + "/processdata/devices:local:ac"

    response = requests.get(url=url, headers=headers)
    processdata = response.json()[0]['processdata']

    def getProcessDataValue(id):
        return next(x['value'] for x in processdata if x['id'] == id)

    data = {}

    data['VA'] = round(getProcessDataValue('L1_U'), 1)
    data['PA'] = round(getProcessDataValue('L1_P'), 1)
    data['IA'] = round(getProcessDataValue('L1_I'), 1)
    data['VB'] = round(getProcessDataValue('L2_U'), 1)
    data['PB'] = round(getProcessDataValue('L2_P'), 1)
    data['IB'] = round(getProcessDataValue('L2_I'), 1)
    data['VC'] = round(getProcessDataValue('L3_U'), 1)
    data['PC'] = round(getProcessDataValue('L3_P'), 1)
    data['IC'] = round(getProcessDataValue('L3_I'), 1)
    data['PT'] = data['PA'] + data['PB'] + data['PC']
    data['IN0'] = round(data['IA'] + data['IB'] + data['IC'], 1)

    url = baseUrl + "/processdata/scb:statistic:EnergyFlow/Statistic:Yield:Total"
    response = requests.get(url=url, headers=headers)
    energy = response.json()[0]['processdata'][0]['value']
    currentTime = time.time()

    # Unfortunately the total energy is only updated every 5 min. This is used by the Victron VRM Portal
    # to calculate the energy consumption.
    # If the portal has no regular updates, the energy consumption is higher than normal.
    # To avoid it, we need a actual energy. So we need to calculate the delta by our own.

    # If a new value is retrieved, use this value and reset the delta calculation.
    if energy != lastEnergy:
        print("Calculated Energy: {} Energy: {}".format(calcEnergy, energy))
        lastEnergy = energy
        calcEnergy = energy
        lastTime = currentTime
    else: # Calculate the delta
        # The formula is E = P * t
        deltaTime = currentTime-lastTime # time since last delta calculation
        delta = data['PT'] * deltaTime / 3600 # P is given in Watt and delta time should be hour, so divide it by 3600 (60min * 60s = 1h)
        calcEnergy += delta # add the new delta to the total energy
        print("Calculated Energy: {} Energy: {} Last Energy {}.".format(calcEnergy, energy, lastEnergy))

    data['EFAT'] = round(calcEnergy / 1000, 3)

    # assume we always run ;)
    data['STATUS'] = 'running'
    lastTime = currentTime # record the last time for the next iteration

    return data
