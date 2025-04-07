import pandas as pd

class ProcesosInfracciones:

    def __init__(self,data,columnas):
        self.data=pd.DataFrame(data,columns=columnas)
        self.procesamiento()


    def procesamiento(self):
        self.data['FECHA']=pd.to_datetime(self.data['FECHA'])
        self.data['AÑO']=self.data['FECHA'].dt.year
        self.data['TIPO DE VEHICULO']=self.data['TIPO DE VEHICULO'].fillna('NO ESPECIFICADO')

    def infracciones_años(self):
        
        return self.data.groupby('AÑO').size().reset_index(name='CANTIDAD')
    

    def infracciones_tipo(self):

        return self.data['TIPO DE VEHICULO'].value_counts().reset_index()
        
