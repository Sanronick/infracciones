from conexion import ConectorDB
from flask import Flask,render_template,jsonify,request,redirect,session,url_for
import pandas as pd
from plotly import express as px
import json
import textwrap
import requests
import geopandas as gpd
import os
from urllib.parse import urlencode
from dotenv import load_dotenv
import ssl
from datetime import timedelta, datetime, timezone

load_dotenv()



def ajuste(text,width=40):
    return '<br>'.join(textwrap.wrap(text,width))

def puntos(numero):
    return "{:,}".format(numero).replace(",",".")


app=Flask(__name__)
app.secret_key=os.urandom(24)

TENANT_ID=os.getenv("TENANT_ID")
CLIENT_ID=os.getenv("CLIENT_ID")
CLIENT_SECRET=os.getenv("CLIENT_SECRET")
REDIRECT_URI=os.getenv("REDIRECT_URI")
SECRET_KEY=os.getenv("SECRET_KEY")
app.config['PERMANENT_SESSION_LIFETIME']=timedelta(
    minutes=int(os.getenv("PERMANENT_SESSION_LIFETIME",30))
)
app.config["SESSION_COOKIE_SECURE"]=True
app.config["SESSION_COOKIE_HTTPONLY"]=True
app.config["SESSION_COOKIE_SAMESITE"]="Lax"


AUTHORITY=f'https://login.microsoftonline.com/{TENANT_ID}'
AUTH_URL=f'{AUTHORITY}/oauth2/v2.0/authorize'
TOKEN_URL=f'{AUTHORITY}/oauth2/v2.0/token'
SCOPE='openid profile email'

@app.route('/')
def index():
    return render_template('index.html',user=session.get("user"))

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

            valores_con_formato=[puntos(valor) for valor in infracciones_año['CANTIDAD']]


            graf1=px.bar(
                data_frame=infracciones_año,
                x='AÑO',
                y='CANTIDAD',
                title='INFRACCIONES POR AÑO',
                text_auto=True,
                text=valores_con_formato,
                height=1000
            )

            graf1.update_layout(
                xaxis_title='AÑO',
                yaxis_title='CANTIDAD DE INFRACCIONES',
                yaxis=dict(
                    tickformat=',.0f',
                ),
                uniformtext_minsize=8,
                uniformtext_mode='hide'
            )

            graf1.update_traces(
                texttemplate='%{text}',
                textposition='outside'
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
                height=max(100,100*len(df_tipoinfraccion)),
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

        try:

            sql='''
                SELECT
                    ai.SLAT,
                    ai.SLNG,
                    ai.COD_INFRACCIONES,
                    (SELECT ti.DES FROM AGENTES.TIPO_INFRACCIONES ti WHERE ti.ID = TRIM(REGEXP_SUBSTR(ai.COD_INFRACCIONES, '[^,]+', 1, 1))) AS "Descripcion Infraccion 1",
            (SELECT ti.DES FROM AGENTES.TIPO_INFRACCIONES ti WHERE ti.ID = TRIM(REGEXP_SUBSTR(ai.COD_INFRACCIONES, '[^,]+', 1, 2))) AS "Descripcion Infraccion 2",
            (SELECT ti.DES FROM AGENTES.TIPO_INFRACCIONES ti WHERE ti.ID = TRIM(REGEXP_SUBSTR(ai.COD_INFRACCIONES, '[^,]+', 1, 3))) AS "Descripcion Infraccion 3",
            (SELECT ti.DES FROM AGENTES.TIPO_INFRACCIONES ti WHERE ti.ID = TRIM(REGEXP_SUBSTR(ai.COD_INFRACCIONES, '[^,]+', 1, 4))) AS "Descripcion Infraccion 4"
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
            
            params={
                'fecha1':fecha1,
                'fecha2':fecha2
            }
            cursor.execute(sql,params)
            rows=cursor.fetchall()

        except Exception as e:
            return jsonify({'Error al obtener los datos: ',str(e)}),500    


        #Dataframe de la base de datos con la lat y long
        df_geo=pd.DataFrame(rows,columns=['lat','lon','cod_infracciones','desc1','desc2','desc3','desc4'])

        df_long=(
            df_geo.melt(
                id_vars=['lat','lon'],
                value_vars=['desc1','desc2','desc3','desc4'],
                var_name='desc_num',
                value_name='tipo_infraccion'
            ).dropna(subset=['tipo_infraccion'])
        )

        #Filtro por Tipos
        if tipos_filtro:
            df_long=df_long[df_long['tipo_infraccion'].isin(tipos_filtro)]


        tipos_infraccion=sorted(df_long['tipo_infraccion'].unique().tolist())


        #Cargo el GeoJson de las comunas
        geojson_comunas='https://cdn.buenosaires.gob.ar/datosabiertos/datasets/ministerio-de-educacion/comunas/comunas.geojson'

        datos_geo=requests.get(geojson_comunas).json()

        #Uno los datos de la BB.DD con el geojson
        gdf_pts=gpd.GeoDataFrame(
            df_long,
            geometry=gpd.points_from_xy(df_long['lon'],df_long['lat']),
            crs="EPSG:4326"
        )

        gdf_comunas=gpd.read_file(geojson_comunas).to_crs(gdf_pts.crs)
        infracciones_comunas=gpd.sjoin(
            gdf_pts,
            gdf_comunas[['comuna','geometry']],
            how='inner',
            predicate='within'
        )

        #Cuento por comuna
        cnts=infracciones_comunas['comuna'].value_counts().to_dict()
        for feat in datos_geo['features']:
            nom=feat['properties']['comuna']
            feat['properties']['cantidad_infracciones']=cnts.get(nom,0)


        #Genero el mapa
        mapa=px.scatter_mapbox(
            df_long,
            lat='lat',
            lon='lon',
            color='tipo_infraccion',
            zoom=11,
            height=900,
            title='Infracciones por Comunas'
        )

        mapa.update_layout(
            mapbox=dict(
                style="open-street-map",
                layers=[{
                    'sourcetype':"geojson",
                    'source':datos_geo,
                    'type':"line",
                    'color':"black",
                    'line':{'width':2}
                }],
                center={'lat':-34.60,'lon':-58.38},
                zoom=11
            ),
            margin={'r':0,'t':40,'l':0,'b':0},
            title={'x':0.5},
            showlegend=False
        )

        map_json=mapa.to_json()


        #Tabla infracciones por comunas
        tabla_comunas=[
            {'comuna':k,'cantidad':v}
            for k, v in cnts.items()
        ]

        tabla_comunas.sort(
            key=lambda x:int(x['comuna'])
            if str(x['comuna']).isdigit()
            else x['comuna']
        )

        #Devuelvo el JSON o renderizo la plantilla
        payload={
            'mapa':map_json,
            'tipos':tipos_infraccion,
            'tabla_comunas':tabla_comunas
        }

        if request.method=='POST':
            return jsonify(payload)
        
        return render_template('Geolocalizacion.html',**payload)


@app.route("/login")
def login():
    
    params={
        "client_id":CLIENT_ID,
        "response_type":"code",
        "redirect_uri":REDIRECT_URI,
        "response_mode":"query",
        "scope":SCOPE,
        "state":os.urandom(8).hex()
    }

    login_url=f'{AUTH_URL}?{urlencode(params)}'
    return redirect(login_url)


@app.route("/getAToken")
def getAToken():
    code=request.args.get("code")

    if not code:
        return "Error: no se recibió el codigo de autorizacion",400
    
    if session.get("auth_code")==code:
        return redirect(url_for("index"))
    
    session["auth_code"] = code


    
    token_data={
        "client_id":CLIENT_ID,
        "scope":SCOPE,
        "code":code,
        "redirect_uri":REDIRECT_URI,
        "grant_type":"authorization_code",
        "client_secret":CLIENT_SECRET
    }

    response=requests.post(TOKEN_URL,data=token_data)
    if response.status_code != 200:
        session.pop("auth_code",None)
        return f'Error al obtener el token: {response.text}',400
    
    tokens=response.json()
    session.permanent=True
    session['_fresh']=datetime.now(timezone.utc) + timedelta(minutes=30)
    session['access_token']=tokens["access_token"]
    session['refresh_token']=tokens.get("refresh_token")


    #datos del usuario
    user_info=requests.get(
        "https://graph.microsoft.com/v1.0/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"}
    ).json()

    session["user"]=user_info
    return redirect(url_for("index"))


@app.route("/logout")
def logout():
    session.clear()

    logout_url=(
        f'https://login.microsoftonline.com/{TENANT_ID}'
        '/oauth2/v2.0/logout'
        f'?post_logout_redirect_uri={url_for('index',_external=True)}'
    )
    return redirect(logout_url)


@app.route("/refresh",methods=["POST"])
def refresh():
    if 'refresh_token' not in session:
        return redirect("/login")
    
    #verifico el tiempo minimo entre refrescos(5 minutos)
    last_refresh=session.get('last_refresh')
    if last_refresh and (datetime.now() - last_refresh) < timedelta(minutes=5):

        data={
        "client_id":CLIENT_ID,
        "scope":SCOPE,
        "refresh_token":session['refresh_token'],
        "grant_type":"refresh_token",
        "client_secret":CLIENT_SECRET
    }


    resp=requests.post(TOKEN_URL,data=data)

    if resp.status_code != 200:
        session.clear()
        return redirect("/login")
    
    tokens=resp.json()
    session["access_token"]=tokens["access_token"]
    session["refresh_token"]=tokens.get("refresh_token",session['refresh_token'])
    session['last_refresh']=datetime.now()
    session['_fresh']=datetime.now() + timedelta(minutes=30)

    return jsonify({"status":"token refreshed"})


#Verifico session
@app.before_request
def check_session():
    if request.endpoint in ['index','login','getAToken','static']:
        return
    
    if 'user' not in session:
        return redirect('/login')
    
    if '_fresh' in session:
        if datetime.now(timezone.utc) > session['_fresh']:
            session.clear()
            return redirect('/login')
            



        


if __name__=='__main__':
    context=ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    basedir=os.path.abspath(os.path.dirname(__file__))
    cert_file=os.path.join(basedir,'cert.pem')
    key_file=os.path.join(basedir,'key.pem')

    context.load_cert_chain(certfile=cert_file,keyfile=key_file)
   
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=True,
        ssl_context=context
    )


            


            

        


