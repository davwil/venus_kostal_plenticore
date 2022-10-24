import requests


def get_data(baseUrl, sessionId):
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
    data['EFAT'] = round(response.json()[0]['processdata'][0]['value'] / 1000, 3)

    # assume we always run ;)
    data['STATUS'] = 'running'

    return data
