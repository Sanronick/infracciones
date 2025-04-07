from conexion import ConectorDB
from flask import Flask,render_template,jsonify,request
import pandas as pd
from process import ProcesosInfracciones
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
                    SELECT
                        ai.id,
                        ai.NUAC,
                        ai.FECH,
                        ci.DES,
                        ai.MODA,
                        ai.COD_INFRACCIONES,
                        aiv.NDOM || ' ' || aiv.CDOM,
                        aii.APEL || ' ' || aii.NOMB || ' (' || aii.NDOC || ')',
                        c.APEL || ' ' || c.NOMB,
                        ai.ESTADO_FIRMA,
                        aii.NACTZ,
                        s.NOMB,
                        aii.DOSAJE ,
                        aii.NRO_TICKET_ALCOHOLEMIA ,
                        tv.NOMB,
                        CASE
                            WHEN aii.vret=1 THEN 'SI'
                            WHEN aii.vret=0 THEN 'NO'
                        END,
                        p.NOMB,
                        ai.CALL,
                        ai.ALTU,
                        ai.CPIZ,
                        ai.CPDE,
                        ai.REFE,
                        ai.SLAT,
                        ai.SLNG,
                        CASE 
                            WHEN aii.dret=1 THEN 'SI'
                            WHEN aii.dret=0 THEN 'NO'
                        END,
                        (SELECT ti.DES FROM AGENTES.TIPO_INFRACCIONES ti WHERE ti.ID = TRIM(REGEXP_SUBSTR(ai.COD_INFRACCIONES, '[^,]+', 1, 1))),
                                (SELECT ti.DES FROM AGENTES.TIPO_INFRACCIONES ti WHERE ti.ID = TRIM(REGEXP_SUBSTR(ai.COD_INFRACCIONES, '[^,]+', 1, 2))),
                                (SELECT ti.DES FROM AGENTES.TIPO_INFRACCIONES ti WHERE ti.ID = TRIM(REGEXP_SUBSTR(ai.COD_INFRACCIONES, '[^,]+', 1, 3))),
                                (SELECT ti.DES FROM AGENTES.TIPO_INFRACCIONES ti WHERE ti.ID = TRIM(REGEXP_SUBSTR(ai.COD_INFRACCIONES, '[^,]+', 1, 4)))
                    FROM
                        AGENTES.ACTA_INFRACCION ai
                    INNER JOIN AGENTES.ACTA_INFRACCION_IMPUTADO aii ON
                        aii.ACTA_INFRACCION_FK = ai.ID
                    LEFT JOIN AGENTES.ACTA_INFRACCION_VEHICULO aiv ON
                        aiv.ACTA_INFRACCION_FK = ai.ID
                    LEFT JOIN AGENTES.SEXOS s ON
                        aii.SEXO_FK = s.ID
                    LEFT JOIN AGENTES.CUENTAS c ON
                        ai.CUENTA_FK = c.ID
                    LEFT JOIN AGENTES.TIPO_VEHICULOS tv ON
                        aiv.TIPO_VEHICULO_FK = tv.ID
                    LEFT JOIN AGENTES.TIPO_INFRACCION_VEHICULO tiv ON
                        tv.ID = tiv.TIPO_VEHICULO_FK
                    LEFT JOIN AGENTES.CLASE_INFRACCION ci ON
                        tiv.CLASE_INFRACCION_FK = ci.ID
                    LEFT JOIN AGENTES.PLAYAS p ON
                        aiv.PLAYAS_FK =p.ID 
                    WHERE
                        TO_DATE(ai.FECH)>=TO_DATE(:fecha1,'YYYY-MM-DD')
                        AND TO_DATE(ai.FECH)<=TO_DATE(:fecha2,'YYYY-MM-DD')
                        AND ai.DEPENDENCIA_FK IN (58, 59, 61)
                            '''
            ,fecha1=fecha1,fecha2=fecha2)

            data=cursor.fetchall()
            
            column_names=[column[0] for column in cursor.description]

            columnas=['ID','ACTA','FECHA','TIPO DE INFRACCION','MODALIDAD','CODIGOS DE INFRACCION','DOMINIO','IMPUTADO','AGENTE','ESTADO DE FIRMA','ACTA Z','GENERO','DOSAJE','TICKET ALCOHOLEMIA','TIPO DE VEHICULO','VEHICULO RETENIDO','PLAYA ASIGNADA','CALLE','ALTURA','ENTRE CALLE 1','ENTRE CALLE 2','REFERENCIA','LATITUD','LONGITUD','LICENCIA RETENIDA','DESCRIPCION INFRACCION 1','DESCRIPCION INFRACCION 2','DESCRIPCION INFRACCION 3','DESCRIPCION INFRACCION 4']


            infracciones_data=ProcesosInfracciones(data=data,columnas=columnas)

            #Grafico 1
            infracciones_año=infracciones_data.infracciones_años()
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

            
            
            return jsonify({'grafico1':graf1_json,'data':[list(row) for row in data],'columnas':columnas})
    return render_template('infracciones.html')

if __name__=='__main__':
    app.run(debug=True)


            


            

        


