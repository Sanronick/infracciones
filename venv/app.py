from conexion import ConectorDB
from flask import Flask,render_template,jsonify,request
import pandas as pdpip
from plotly import express as px
import json


app=Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/infracciones',methods=['GET','POST'])
def infracciones():
    
    if request.method=='POST':
        data_request=request.get_json()
        fecha1=data_request.get('fecha1')
        fecha2=data_request.get('fecha2')
    
        
        with ConectorDB() as cursor:
            cursor.execute(
                '''
                    SELECT EXTRACT(YEAR FROM FECH) AS AÑO, COUNT(*) AS CANTIDAD
                    FROM AGENTES.ACTA_INFRACCION
                    WHERE FECH BETWEEN TO_DATE(:fecha1, 'YYYY-MM-DD') AND TO_DATE(:fecha2, 'YYYY-MM-DD')
                    AND DEPENDENCIA_FK IN (58,59,61)
                    GROUP BY EXTRACT(YEAR FROM FECH)
                ''',fecha1=fecha1,fecha2=fecha2
            )

            data=cursor.fetchall()
            
            column_names=[column[0] for column in cursor.description]

            columnas=['AÑO','CANTIDAD']


            # infracciones_data=ProcesosInfracciones(data=data,columnas=columnas)

            #Grafico 1
            infracciones_año=pd.DataFrame(data=data,columns=columnas)
            graf1=px.bar(
                data_frame=infracciones_año,
                x='AÑO',
                y='CANTIDAD',
                title='INFRACCIONES POR AÑO'
            )

            graf1.update_layout(
                xaxis_title='AÑO',
                yaxis_title='CANTIDAD DE INFRACCIONES'
            )
            graf1_json=graf1.to_json()

            #Infracciones por Tipo
            cursor.execute(
                '''
                    SELECT 
                                        NVL(tv.NOMB, 'NO ESPECIFICADO') AS TIPO_VEHICULO,
                                        COUNT(*) AS CANTIDAD
                                    FROM AGENTES.ACTA_INFRACCION ai
                                    LEFT JOIN AGENTES.ACTA_INFRACCION_VEHICULO aiv ON aiv.ACTA_INFRACCION_FK = ai.ID
                                    LEFT JOIN AGENTES.TIPO_VEHICULOS tv ON aiv.TIPO_VEHICULO_FK = tv.ID
                                    WHERE ai.FECH BETWEEN TO_DATE(:fecha1, 'YYYY-MM-DD') AND TO_DATE(:fecha2, 'YYYY-MM-DD')
                                    AND ai.DEPENDENCIA_FK IN (58,59,61)
                                    GROUP BY tv.NOMB
                                    ORDER BY CANTIDAD DESC
                    ''',fecha1=fecha1,fecha2=fecha2
            )

            data_vehiculos=cursor.fetchall()
            columas_vehiculos=['TIPO_VEHICULO','CANTIDAD']
            df_vehiculos=pd.DataFrame(data_vehiculos,columns=columas_vehiculos)


            #Grafico por tipo de vehiculo
            graf2=px.pie(
                data_frame=df_vehiculos,
                names='TIPO_VEHICULO',
                values='CANTIDAD',
                title='Infracciones por Tipo de Vehiculo'
            )

            graf2.update_traces(
                textinfo='percent+label',
                textposition='inside',
                marker=dict(line=dict(color='#FFFFFF',width=1)),
                hovertemplate="<b>%{label}</b><br>Cantidad: %{value}<br>Porcentaje: %{percent}"
            )
            graf2_json=graf2.to_json()

            return jsonify({
                'grafico1':graf1_json,
                'grafico2':graf2_json,
                'data':[list(row) for row in data],
                'columnas':columnas
            })
    return render_template('infracciones.html')

if __name__=='__main__':
    app.run(debug=True)


            


            

        


