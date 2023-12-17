import socket
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix, precision_score, recall_score, f1_score, accuracy_score
from sklearn.svm import SVC
from datetime import datetime
import numpy as np
import psycopg2

"""
managerConnection

Description:
    Class in charge of the connection part of Python with both Azure and Unity

Input:
    ip: (string) IP on which Unity is located
    portSend: (int) Unity port for send
    portRecibe: (int) Unity port for listening
    (host, dbname, user, password, sslmode): (string) Configuring for the database in Azure
"""
class managerConnection:
    def __init__(self, ip, portSend, portRecibe, host, dbname, user, password, sslmode):

        # managerConnection con unity envio
        self.unityEnvio = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.unityEnvio.connect((ip, portSend))
        print("managerConnection Unity send")

        # managerConnection con unity recibo
        self.unityRecibo = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.unityRecibo.bind((ip, portRecibe))
        print("managerConnection Unity reception")

        
        # managerConnection con azure
        self.conn = psycopg2.connect("host={0} user={1} dbname={2} password={3} sslmode={4}".format(host, user, dbname, password, sslmode))
        self.cursor = self.conn.cursor()
        print("managerConnection azure")
        

    """
    unityRequest

    Description:
        Class Method for Sending Messages (Strings) to Unity
        
    Input:
        message: (string) message that you want to send
    """
    def unityRequest(self, message):
        self.unityEnvio.send(message.encode('utf-8'))

    """
    UnityReception

    Description:
        Class Method for Receive Messages (Strings) to Unity
    Return:
        (string) message that you recibe
    """
    def UnityReception(self):
        self.unityRecibo.listen(1)
        self.client_socket, self.addr = self.unityRecibo.accept()
        return self.client_socket.recv(1024).decode('utf-8')
    
    """
    dataBaseInsertGas

    Description:
        Class Method to insert the gas data into the Azure table
    
    Input:
        datos: Data that you want to insert
    """
    def dataBaseInsertGas(self, datos):
        self.cursor.execute('''INSERT INTO gas (id,time, NitrogenSensor, OxygenSensor, NitrousGasSensor, CarbonMonoxideSensor, CarbonAnidideSensor, 
            SulphurousAnidideSensor, FiredampGasSensor, HydrosulphurSensor) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''', datos.split(","))
        self.conn.commit()
    
    """
    dataBaseInsertDust

    Description:
        Class Method to insert the dust data into the Azure table

    Input:
        datos: Data that you want to insert
    """
    def dataBaseInsertDust(self, datos):
        self.cursor.execute('''INSERT INTO dust (id,time,concentration) values (%s,%s,%s)''', datos.split(","))
        self.conn.commit()
    
    """
    kpiUpdate

    Description:
        Class Method to update the kpi into the Azure table

    Input:
        datos: New data for send and update
    
    """
    def kpiUpdate(self, dato):
        self.cursor.execute(""" UPDATE kpi SET precision = %s, recall = %s, f1_score = %s, accuracy = %s, matrix = %s WHERE type = %s""", dato)
        self.conn.commit()

    """
    earthInsert

    Description:
        Class Method to insert the eartquake data into the Azure table

    Input:
        datos: Data that you want to insert
    """
    def earthInsert(self, dato):
        query = "INSERT INTO EARTH (time, label) VALUES (%s, %s) RETURNING id;"
        self.cursor.execute(query, dato)
        self.conn.commit()


"""
modelsPredictionGasDust

Description:
    Class for the Detection of Gas and Dust Anomalies

Input:
    csvGas: dataset of gas to train the model
    csvGasResult: dataset of the tarjets gas to train the model
    csvDust: dataset of dust to train the model
    csvDustResult: dataset of the tarjets dust to train the model
"""
class modelsPredictionGasDust:
    def __init__(self, csvGas, csvGasResult, csvDust, csvDustResult):
        # Gas and pre-processing data
        df = pd.read_csv(csvGas, header=None, names=["id", "Hour", "Nitrogen" , "Oxygen" , "NitrousGas", 
                                                "CarbonMonoxide", "CarbonAnidide", "SulphurousAnidide", 
                                                "FiredampGas", "Hydrosulphur"], parse_dates=[1], 
                                                infer_datetime_format=True)
        df_anomalia = pd.read_csv(csvGasResult, header=None, names=['id', 'anomalia'])
        df_merged = pd.merge(df, df_anomalia, on='id')

        # Gas Data Training
        train_data, self.test_dataGas = train_test_split(df_merged, test_size=0.3, random_state=42)
        self.modelGas = RandomForestClassifier(random_state=42)
        self.modelGas.fit(train_data[["Nitrogen" , "Oxygen" , "NitrousGas", 
                                                "CarbonMonoxide", "CarbonAnidide", "SulphurousAnidide", 
                                                "FiredampGas", "Hydrosulphur"]], train_data['anomalia'])
        
        # Gas data validation
        self.test_Gas = self.modelGas.predict(self.test_dataGas[["Nitrogen" , "Oxygen" , "NitrousGas", 
                                                "CarbonMonoxide", "CarbonAnidide", "SulphurousAnidide", 
                                                "FiredampGas", "Hydrosulphur"]])

        # Powder & Pre-Processed Data
        df = pd.read_csv(csvDust, header=None, names=['id', 'fecha', 'dato'], parse_dates=[1], infer_datetime_format=True)
        df_anomalia = pd.read_csv(csvDustResult, header=None, names=['id', 'anomalia'])
        df_merged = pd.merge(df, df_anomalia, on='id')

        # Powder Data Training
        train_data, self.test_dataDust = train_test_split(df_merged, test_size=0.1, random_state=42)
        self.modelDust = SVC(random_state=42)
        self.modelDust.fit(train_data[['dato']], train_data['anomalia'])

        # Dust Data Validation
        self.test_Dust = self.modelDust.predict(self.test_dataDust[['dato']])

    
    """
    predictionGas

    Description:
        Class Method to predict a new data os gas

    Input:
        dato: Data that you want to predict
        valor: Real result of the system. To get KPIs after the fact
    """
    def predictionGas(self, dato, valor):
        aux, aux2 = [], []
        for i in dato.split(","):
            try:
                aux += [float(i)]
            except:
                datetime_object = datetime.strptime(i, '%Y-%m-%d %H:%M:%S.%f')
                aux += [datetime_object.timestamp()]
        for i in valor.split(","):
            aux2 += [float(i)]
        datoAux = pd.DataFrame([aux], columns=["id", "Hour", "Nitrogen" , "Oxygen" , "NitrousGas", 
                                                "CarbonMonoxide", "CarbonAnidide", "SulphurousAnidide", 
                                                "FiredampGas", "Hydrosulphur"])
        valor = pd.DataFrame([aux2], columns=['id', 'anomalia'])
        dato = pd.merge(datoAux, valor, on='id')
        
        aux = self.modelGas.predict(dato[["Nitrogen" , "Oxygen" , "NitrousGas", 
                                                "CarbonMonoxide", "CarbonAnidide", "SulphurousAnidide", 
                                                "FiredampGas", "Hydrosulphur"]])
        
        self.test_Gas = np.append(self.test_Gas, aux)
        self.test_dataGas = pd.concat([self.test_dataGas, dato])
        return aux[0]
    
    """
    predictionDust

    Description:
        Class Method to predict a new data os dust

    Input:
        dato: Data that you want to predict
        valor: Real result of the system. To get KPIs after the fact
    """
    def predictionDust(self, dato, valor):
        aux, aux2 = [], []
        for i in dato.split(","):
            try:
                aux += [float(i)]
            except:
                datetime_object = datetime.strptime(i, '%Y-%m-%d %H:%M:%S.%f')
                aux += [datetime_object.timestamp()]
        for i in valor.split(","):
            aux2 += [float(i)]
        datoAux = pd.DataFrame([aux], columns=['id', 'fecha', 'dato'])
        valor = pd.DataFrame([aux2], columns=['id', 'anomalia'])
        dato = pd.merge(datoAux, valor, on='id')
        
        aux = self.modelDust.predict(dato[["dato"]])
        self.test_Dust = np.append(self.test_Dust, aux)
        self.test_dataDust = pd.concat([self.test_dataDust, dato])
        return aux[0]
    
    """
    kpiGas

    Description:
        Class Method to obtain the new percent of kpi of gas
    """
    def kpiGas(self):
        precision = precision_score(self.test_dataGas['anomalia'], self.test_Gas)
        recall = recall_score(self.test_dataGas['anomalia'], self.test_Gas)
        f1 = f1_score(self.test_dataGas['anomalia'], self.test_Gas)
        accuracy = accuracy_score(self.test_dataGas['anomalia'], self.test_Gas)
        conf_matrix = confusion_matrix(self.test_dataGas['anomalia'], self.test_Gas)

        return (precision, recall, f1, accuracy, str(conf_matrix), "gas")

    """
    kpiDust

    Description:
        Class Method to obtain the new percent of kpi of dust
    """
    def kpiDust(self):
        precision = precision_score(self.test_dataDust['anomalia'], self.test_Dust)
        recall = recall_score(self.test_dataDust['anomalia'], self.test_Dust)
        f1 = f1_score(self.test_dataDust['anomalia'], self.test_Dust)
        accuracy = accuracy_score(self.test_dataDust['anomalia'], self.test_Dust)
        conf_matrix = confusion_matrix(self.test_dataDust['anomalia'], self.test_Dust)

        return (precision, recall, f1, accuracy, str(conf_matrix), "dust")



