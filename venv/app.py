from conexion import ConectorDB
from flask import Flask,render_template,jsonify,request
import pandas as pd
from plotly import express as px
import json
import textwrap
import requests


def ajuste(text,width=40):
    return '<br>'.join(textwrap.wrap(text,width))


app=Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/infracciones',methods=['GET','POST'])
def infracciones():

    if request.method=='GET':
    
        with ConectorDB() as cursor:

            cursor.execute(
            '''
            SELECT EXTRACT(YEAR FROM ai.FECH) AS AÑO, COUNT(*) AS CANTIDAD
            FROM AGENTES.ACTA_INFRACCION ai
            WHERE ai.DEPENDENCIA_FK IN (58,59,61)
            GROUP BY EXTRACT(YEAR FROM ai.FECH)'''
            )

            data=cursor.fetchall()
        
            column_names=[column[0] for column in cursor.description]

            columnas=['AÑO','CANTIDAD']


            #Grafico 1
            infracciones_año=pd.DataFrame(data=data,columns=columnas)


            infracciones_año=infracciones_año.sort_values(by='AÑO')
            infracciones_año['AÑO']=infracciones_año['AÑO'].astype(str)
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

            if 'json' in request.args:
                return jsonify({'grafico1':graf1_json})
            else:
                return render_template('infracciones.html',grafico1=graf1_json)


    else:
        data_request=request.get_json()
        fecha1=data_request.get('fecha1')
        fecha2=data_request.get('fecha2')

        with ConectorDB() as cursor:
            cursor.execute(
            '''
            SELECT EXTRACT(YEAR FROM ai.FECH) AS AÑO, COUNT(*) AS CANTIDAD
            FROM AGENTES.ACTA_INFRACCION ai
            WHERE ai.DEPENDENCIA_FK IN (58,59,61)
            GROUP BY EXTRACT(YEAR FROM ai.FECH)'''
            )
            data=cursor.fetchall()
        
            column_names=[column[0] for column in cursor.description]

            columnas=['AÑO','CANTIDAD']


            #Grafico 1
            infracciones_año=pd.DataFrame(data=data,columns=columnas)


            infracciones_año=infracciones_año.sort_values(by='AÑO')
            infracciones_año['AÑO']=infracciones_año['AÑO'].astype(str)
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



            #Infracciones por Tipo de Vehiculo
            cursor.execute(
                '''
                    SELECT 
                    NVL(tv.NOMB, 'NO ESPECIFICADO') AS TIPO_VEHICULO,
                    COUNT(*) AS CANTIDAD
                FROM AGENTES.ACTA_INFRACCION ai
                LEFT JOIN AGENTES.ACTA_INFRACCION_VEHICULO aiv ON aiv.ACTA_INFRACCION_FK = ai.ID
                LEFT JOIN AGENTES.TIPO_VEHICULOS tv ON aiv.TIPO_VEHICULO_FK = tv.ID
                WHERE to_date(ai.FECH)>=to_date(:fecha1,'YYYY-MM-DD') AND TO_date(ai.FECH)<=to_date(:fecha2,'YYYY-MM-DD')
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

            graf2.update_layout(showlegend=False)

            graf2.update_traces(
                textinfo='percent+label',
                textposition='inside',
                marker=dict(line=dict(color='#FFFFFF',width=1)),
                hovertemplate="<b>%{label}</b><br>Cantidad: %{value}<br>Porcentaje: %{percent}"
            )
            graf2_json=graf2.to_json()


            #Por tipo de infraccion
            cursor.execute(
                '''
            SELECT
    ti.DES AS TIPO_INFRACCION,
    COUNT(*) AS CANTIDAD
    FROM (
    SELECT TRIM(REGEXP_SUBSTR(ai.COD_INFRACCIONES, '[^,]+', 1, 1)) AS ID
    FROM AGENTES.ACTA_INFRACCION ai
    WHERE ai.FECH BETWEEN TO_DATE(:fecha1, 'YYYY-MM-DD') AND TO_DATE(:fecha2, 'YYYY-MM-DD')
    AND ai.DEPENDENCIA_FK IN (58,59,61)
    UNION ALL
    SELECT TRIM(REGEXP_SUBSTR(ai.COD_INFRACCIONES, '[^,]+', 1, 2)) AS ID
    FROM AGENTES.ACTA_INFRACCION ai
    WHERE ai.FECH BETWEEN TO_DATE(:fecha1, 'YYYY-MM-DD') AND TO_DATE(:fecha2, 'YYYY-MM-DD')
    AND ai.DEPENDENCIA_FK IN (58,59,61)
    UNION ALL
    SELECT TRIM(REGEXP_SUBSTR(ai.COD_INFRACCIONES, '[^,]+', 1, 3)) AS ID
    FROM AGENTES.ACTA_INFRACCION ai
    WHERE ai.FECH BETWEEN TO_DATE(:fecha1, 'YYYY-MM-DD') AND TO_DATE(:fecha2, 'YYYY-MM-DD')
    AND ai.DEPENDENCIA_FK IN (58,59,61)
    UNION ALL
    SELECT TRIM(REGEXP_SUBSTR(ai.COD_INFRACCIONES, '[^,]+', 1, 4)) AS ID
    FROM AGENTES.ACTA_INFRACCION ai
    WHERE ai.FECH BETWEEN TO_DATE(:fecha1, 'YYYY-MM-DD') AND TO_DATE(:fecha2, 'YYYY-MM-DD')
    AND ai.DEPENDENCIA_FK IN (58,59,61)
    ) infrac
    JOIN AGENTES.TIPO_INFRACCIONES ti ON ti.ID = infrac.ID
    GROUP BY ti.DES
    ORDER BY CANTIDAD DESC

            
        ''',fecha1=fecha1,fecha2=fecha2
            )

            datos_tipoinfraccion=cursor.fetchall()

            columas_tipoinfraccion=['TIPO_INFRACCION','CANTIDAD']
            df_tipoinfraccion=pd.DataFrame(data=datos_tipoinfraccion,columns=columas_tipoinfraccion)
            df_tipoinfraccion['TIPO_INFRACCION']=df_tipoinfraccion['TIPO_INFRACCION'].apply(lambda x: ajuste(x,40))


            #Grafico 3 por tipo de infraccion
            graf3=px.bar(
                data_frame=df_tipoinfraccion,
                x='CANTIDAD',
                y='TIPO_INFRACCION',
                orientation='h',
                color='TIPO_INFRACCION',
                title='Tipos de Infraccion',
                hover_data={
                    'TIPO_INFRACCION':True,
                    'CANTIDAD':True
                }
            )

            graf3.update_layout(
                showlegend=False,
                height=100*len(df_tipoinfraccion),
                margin=dict(l=300,r=50,t=80,b=50),
                yaxis=dict(automargin=False),
                title=dict(
                text='Tipos de Infraccion',
                x=0.5,
                xanchor='center',
                font=dict(size=20)
            ))

            graf3.update_traces(
                hovertemplate="<b>%{y}</b><br>Cantidad: %{x}<extra></extra>"
            )

            graf3_json=graf3.to_json()




            return jsonify({
                'grafico1':graf1_json,
                'grafico2':graf2_json,
                'grafico3':graf3_json,
                'data':[list(row) for row in data],
                'columnas':columnas
            })
        return render_template('infracciones.html',grafico1=graf1_json)
    


# @app.route('/geo_data',methods=['POST'])
# def geo_data():

#     data_request=request.get_json()
#     fecha1=data_request.get('fecha1')
#     fecha2=data_request.get('fecha2')
#     tipos_filtro=data_request.get('tipos')

#     with ConectorDB() as cursor:

#         sql='''
#             SELECT
#                 ai.SLAT,
#                 ai.SLNG,
#                 ti.DES
#             FROM
#                 AGENTES.ACTA_INFRACCION ai
#             INNER JOIN AGENTES.ACTA_INFRACCION_INFRACCION aii ON
#                 ai.id = aii.ID
#             INNER JOIN AGENTES.TIPO_INFRACCIONES ti ON
#                 aii.TIPO_INFRACCIONES_FK = ti.ID
#             WHERE to_date(ai.fech) between to_date(:fecha1,'YYYY-MM-DD') and to_date(:fecha2,'YYYY-MM-DD')
#             and ai.dependencia_fk in ( 58,
#                                         59,
#                                         61 )
#             and ai.slat is not null
#             and ai.slng is not null
#             and ai.SLAT <>'0'
#             and ai.SLNG <>'0'
#             '''
    
    
#         if tipos_filtro:
#             tipos_named={f'tipo{i}':tipo for i, tipo in enumerate(tipos_filtro)}
#             sql+=f" AND ti.DES IN ({','.join(f':{k}' for k in tipos_named)})"
#             params={'fecha1':fecha1,'fecha2':fecha2,**tipos_named}
        
#         else:
#             params={'fecha1':fecha1,'fecha2':fecha2}

#         cursor.execute(sql,params)

#         geo=cursor.fetchall()

#         df_geo=pd.DataFrame(geo,columns=['lat','lon','tipo_infraccion'])
#         tipos_infraccion=sorted(df_geo['tipo_infraccion'].unique().tolist())



#         #Cargo el GeoJson
#         geojson="https://cdn.buenosaires.gob.ar/datosabiertos/datasets/ministerio-de-educacion/comunas/comunas.geojson"
#         datos_geo=requests.get(geojson).json()

#         #Creo el mapa

#         mapa=px.scatter_mapbox(
#             df_geo,
#             lat='lat',
#             lon='lon',
#             color='tipo_infraccion',
#             zoom=1,
#             height=600,
#             title="Infracciones por Comunas"
#         )

#         #Agrego la capa por comunas
#         mapa.update_layout(
#             mapbox=dict(
#                 style="open-street-map",
#                 layers=[
#                     dict(
#                         sourcetype="geojson",
#                         source=datos_geo,
#                         type="line",
#                         color="black",
#                         line=dict(width=2)
#                     )
#                 ],
#                 center={"lat":-34.60,"lon":-58.38},
#                 zoom=11
#             ),
#             margin={"r":0,"t":40,"l":0,"b":0},
#             title=dict(x=0.5),
#             showlegend=False
#         )

#         return jsonify({'mapa':mapa.to_json(),'tipos':tipos_infraccion})

# @app.route('/geo',methods=['GET'])
# def geo():
#     return render_template('Geolocalizacion.html')



@app.route('/geo',methods=['GET','POST'])
def geo():
    if request.method=='GET':
        #Fechas por defecto
        fecha1='2025-01-01'
        fecha2='2025-12-31'
        tipos_filtro=None

    else:
        data_request=request.get_json()
        fecha1=data_request.get('fecha1')
        fecha2=data_request.get('fecha2')
        tipos_filtro=data_request.get('tipos')

    with ConectorDB() as cursor:

        sql='''
            SELECT
                ai.SLAT,
                ai.SLNG,
                ti.DES
            FROM
                AGENTES.ACTA_INFRACCION ai
            INNER JOIN AGENTES.ACTA_INFRACCION_INFRACCION aii ON
                ai.id = aii.ID
            INNER JOIN AGENTES.TIPO_INFRACCIONES ti ON
                aii.TIPO_INFRACCIONES_FK = ti.ID
            WHERE to_date(ai.fech) between to_date(:fecha1,'YYYY-MM-DD') and to_date(:fecha2,'YYYY-MM-DD')
            and ai.dependencia_fk in ( 58,
                                        59,
                                        61 )
            and ai.slat is not null
            and ai.slng is not null
            and ai.SLAT <>'0'
            and ai.SLNG <>'0'
            '''
        
        if tipos_filtro:
            tipos_named={f'tipo{i}':tipo for i, tipo in enumerate(tipos_filtro)}
            sql+=f" AND ti.DES IN ({','.join(f':{k}' for k in tipos_named)})"
            params={'fecha1':fecha1,'fecha2':fecha2,**tipos_named}
        
        else:
            params={'fecha1':fecha1,'fecha2':fecha2}

        cursor.execute(sql,params)
        # cursor.execute(
        #     '''
        #     SELECT
        #         ai.SLAT,
        #         ai.SLNG,
        #         ti.DES
        #     FROM
        #         AGENTES.ACTA_INFRACCION ai
        #     INNER JOIN AGENTES.ACTA_INFRACCION_INFRACCION aii ON
        #         ai.id = aii.ID
        #     INNER JOIN AGENTES.TIPO_INFRACCIONES ti ON
        #         aii.TIPO_INFRACCIONES_FK = ti.ID
        #     WHERE to_date(ai.fech) between to_date(:fecha1,'YYYY-MM-DD') and to_date(:fecha2,'YYYY-MM-DD')
        #     and ai.dependencia_fk in ( 58,
        #                                 59,
        #                                 61 )
        #     and ai.slat is not null
        #     and ai.slng is not null
        #     and ai.SLAT <>'0'
        #     and ai.SLNG <>'0'
        #     ''',fecha1=fecha1,fecha2=fecha2
        # )

        geo=cursor.fetchall()

        df_geo=pd.DataFrame(geo,columns=['lat','lon','tipo_infraccion'])
        tipos_infraccion=sorted(df_geo['tipo_infraccion'].unique().tolist())

        # df_geo_all=pd.DataFrame(geo,columns=['lat','lon','tipo_infraccion'])

        # #Lista de Tipos de infraccion
        # full_tipos=sorted(df_geo_all['tipo_infraccion'].unique().tolist())

        # #Si el usuario aplico el filtro, se filtra el dataframe
        # if tipos_filtro:
        #     df_geo=df_geo_all[df_geo_all['tipo_infraccion'].isin(tipos_filtro)]
        # else:
        #     df_geo=df_geo_all.copy()



        #Cargo el GeoJson
        geojson="https://cdn.buenosaires.gob.ar/datosabiertos/datasets/ministerio-de-educacion/comunas/comunas.geojson"
        datos_geo=requests.get(geojson).json()

        #Creo el mapa

        mapa=px.scatter_mapbox(
            df_geo,
            lat='lat',
            lon='lon',
            color='tipo_infraccion',
            zoom=1,
            height=600,
            title="Infracciones por Comunas"
        )

        #Agrego la capa por comunas
        mapa.update_layout(
            mapbox=dict(
                style="open-street-map",
                layers=[
                    dict(
                        sourcetype="geojson",
                        source=datos_geo,
                        type="line",
                        color="black",
                        line=dict(width=2)
                    )
                ],
                center={"lat":-34.60,"lon":-58.38},
                zoom=11
            ),
            margin={"r":0,"t":40,"l":0,"b":0},
            title=dict(x=0.5),
            showlegend=False
        )

        map_json=mapa.to_json()

        if request.method=='POST':
            return jsonify({'mapa':map_json})
            #return jsonify({'mapa':map_json,'tipos':full_tipos})
        else:
            return render_template('Geolocalizacion.html',mapa=map_json,tipos=tipos_infraccion)
            #return render_template('Geolocalizacion.html',mapa=map_json,tipos=full_tipos)



        


if __name__=='__main__':
    app.run(debug=True)


            


            

        


