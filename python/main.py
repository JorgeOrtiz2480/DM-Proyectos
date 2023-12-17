import models
import threading
import time
from datetime import datetime, timedelta
import random

# Constant
IP = '127.0.0.1'
PORTSEND = 12346
PORTRECIBE = 12345

HOST = "database-mine.postgres.database.azure.com"
DBNAME = "postgres"
USER = "user_admin"
PASSWORD = "contrasenia_1"
SSLMODE = "require"
URLAPI = "everyearthquake.p.rapidapi.com" # Earthquake request URL. In the scope of the demo 
                                          # it was not planned to reach these due to their 
                                          # improbability of occurring. However, for possible real 
                                          # versions, your knowledge is necessary

CSVGAS = "csv\\Gas.csv"
CSVGASRESULT = "csv\\GasAnomalies.csv"
CSVDUST = "csv\\Dust.csv"
CSVDUSTRESULT = "csv\\DustAnomalies.csv"

# Functions
"""
periodicity

Description:
    This function is responsible for simulating a stopwatch to produce functions periodically

Input:
    function: (function) It is the function that you want to perform on a regular basis
    timeInterval: (int) Is the time between function and function

"""
def periodicity(function, timeInterval):
    while True:
        function()
        time.sleep(timeInterval)

"""
gasDustRequest

Description:
    This function is responsible for requesting and obtaining dust and gas data. 
    Once obtained, assess whether it is an anomaly. If so, ventilation is activated
"""
def gasDustRequest():
    # Request gas
    managerConnection.unityRequest("sendGas")
    dato = managerConnection.UnityReception()
    print("Recibido Gas: " + str(dato) + "\n")
    managerConnection.unityRequest("sendGasR")
    datoR = managerConnection.UnityReception()

    # Gas data prediction 
    pGas = modelsPredictionGasDust.predictionGas(dato, datoR)
    managerConnection.dataBaseInsertGas(dato)
    dato = modelsPredictionGasDust.kpiGas()
    managerConnection.kpiUpdate(dato)

    # Request dust
    managerConnection.unityRequest("sendDust")
    dato = managerConnection.UnityReception()
    print("Recibido Dust: " + str(dato) + "\n")
    managerConnection.unityRequest("sendDustR")
    datoR = managerConnection.UnityReception()

    # Dust data prediction
    pDust = modelsPredictionGasDust.predictionDust(dato, datoR)
    managerConnection.dataBaseInsertDust(dato)
    dato = modelsPredictionGasDust.kpiDust()
    managerConnection.kpiUpdate(dato)

    # Ventilation
    if pGas == 1 or pDust == 1:
        managerConnection.unityRequest("gasActuator")
    else:
        managerConnection.unityRequest("stopGasActuator")

"""
earthRequest

Description:
    This function is responsible for emulating earthquakes. 
    Randomly generates an earthquake with a 2% chance. In case of 
    taking the system to a real source of earthquakes (for its implementation)
    you need the url that can be seen above to make the request for the data
"""
def earthRequest():
    current_time = datetime.now()
    random_time = current_time.replace(second=0, microsecond=0) + timedelta(minutes=5 * random.randint(0, 11))
    random_boolean = random.choice([True] * 2 + [False] * 98)
    managerConnection.earthInsert((random_time, random_boolean))
    if random_boolean:
        managerConnection.unityRequest("EarthquakeAlarm")
        time.sleep(10)
        managerConnection.unityRequest("startDay")



# Setup

# class generations
managerConnection = models.managerConnection(IP, PORTSEND, PORTRECIBE, HOST, DBNAME, USER, PASSWORD, SSLMODE)
modelsPredictionGasDust = models.modelsPredictionGasDust(CSVGAS, CSVGASRESULT, CSVDUST, CSVDUSTRESULT)

# start working unity humans
managerConnection.unityRequest("startDay")

# config timers
timerDustGas = threading.Thread(target=lambda: periodicity(gasDustRequest, 5))
timerTerremotos = threading.Thread(target=lambda: periodicity(earthRequest, 5))
timerDustGas.start()
timerTerremotos.start()
timerDustGas.join()
timerTerremotos.join()


