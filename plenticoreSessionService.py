import base64
import hashlib
import hmac
import json
import os
import random
import requests
import string
import sys
# pip3 install pycryptodomex
from Cryptodome.Cipher import AES


# Based on https://stackoverflow.com/questions/59053539/api-call-portation-from-java-to-python-kostal-plenticore-inverter
# generates Session token that can be used to authenticate all futher request to the inverters api

def get_session_key(passwd, base_url):
    USER_TYPE = "user"
    AUTH_START = "/auth/start"
    AUTH_FINISH = "/auth/finish"
    AUTH_CREATE_SESSION = "/auth/create_session"
    ME = "/auth/me"

    def randomString(stringLength):
        letters = string.ascii_letters
        return ''.join(random.choice(letters) for i in range(stringLength))

    u = randomString(12)
    u = base64.b64encode(u.encode('utf-8')).decode('utf-8')

    step1 = {
        "username": USER_TYPE,
        "nonce": u
    }
    step1 = json.dumps(step1)

    url = base_url + AUTH_START
    headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
    response = requests.post(url, data=step1, headers=headers)
    response = json.loads(response.text)
    i = response['nonce']
    e = response['transactionId']
    o = response['rounds']
    a = response['salt']
    bitSalt = base64.b64decode(a)

    def getPBKDF2Hash(password, bytedSalt, rounds):
        return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), bytedSalt, rounds)

    r = getPBKDF2Hash(passwd, bitSalt, o)
    s = hmac.new(r, "Client Key".encode('utf-8'), hashlib.sha256).digest()
    c = hmac.new(r, "Server Key".encode('utf-8'), hashlib.sha256).digest()
    _ = hashlib.sha256(s).digest()
    d = "n=user,r=" + u + ",r=" + i + ",s=" + a + ",i=" + str(o) + ",c=biws,r=" + i
    g = hmac.new(_, d.encode('utf-8'), hashlib.sha256).digest()
    p = hmac.new(c, d.encode('utf-8'), hashlib.sha256).digest()
    f = bytes(a ^ b for (a, b) in zip(s, g))
    proof = base64.b64encode(f).decode('utf-8')

    step2 = {
        "transactionId": e,
        "proof": proof
    }
    step2 = json.dumps(step2)

    url = base_url + AUTH_FINISH
    headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
    response = requests.post(url, data=step2, headers=headers)
    response = json.loads(response.text)
    token = response['token']
    signature = response['signature']

    y = hmac.new(_, "Session Key".encode('utf-8'), hashlib.sha256)
    y.update(d.encode('utf-8'))
    y.update(s)
    P = y.digest()
    protocol_key = P
    t = os.urandom(16)

    e2 = AES.new(protocol_key, AES.MODE_GCM, t)
    e2, authtag = e2.encrypt_and_digest(token.encode('utf-8'))

    step3 = {
        "transactionId": e,
        "iv": base64.b64encode(t).decode('utf-8'),
        "tag": base64.b64encode(authtag).decode("utf-8"),
        "payload": base64.b64encode(e2).decode('utf-8')
    }
    step3 = json.dumps(step3)

    headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
    url = base_url + AUTH_CREATE_SESSION
    response = requests.post(url, data=step3, headers=headers)
    response = json.loads(response.text)
    sessionId = response['sessionId']

    # create a new header with the new Session-ID for all further requests
    headers = {'Content-type': 'application/json', 'Accept': 'application/json',
               'authorization': "Session " + sessionId}
    url = base_url + ME
    response = requests.get(url=url, headers=headers)
    response = json.loads(response.text)
    authOK = response['authenticated']
    if not authOK:
        print("authorization NOT OK")
        sys.exit()

    url = base_url + "/info/version"
    response = requests.get(url=url, headers=headers)
    response = json.loads(response.text)
    swversion = response['sw_version']
    apiversion = response['api_version']
    hostname = response['hostname']
    name = response['name']
    print("Connected to the inverter " + name + "/" + hostname + " with SW-Version " + swversion + " and API-Version " + apiversion)
    return sessionId, swversion, apiversion

