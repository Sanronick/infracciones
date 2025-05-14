import requests
from urllib.parse import quote_plus
import time


def usgi_geocode(direccion,pause=0.1):

    normalizador="http://servicios.usig.buenosaires.gob.ar/normalizar/"

    url=(
        f'{normalizador}'
        f'?direccion={quote_plus(direccion)}'
        f'&geocodificar=TRUE'
    )

    #print(f'Intentando {url}')

    try:
        resp=requests.get(url,timeout=5)
        resp.raise_for_status()
    

        #Parseo JSON
        data=resp.json()
        direcciones=data.get("direccionesNormalizadas",[])
        if direcciones:
            primera=direcciones[0]
            coords=primera.get("coordenadas",{})
            return{
                "direccion":direccion,
                "Direccion Normalizada":primera.get("direccion"),
                "lat":coords.get("y"),
                "lng":coords.get("x")
            }
        else:
            resultado={"direccion":direccion,
                "Direccion Normalizada":None,
                "lat":None,
                "lng":None}
    

    except requests.RequestException as e:
        resultado={
            "Direccion":direccion,
            "Direccion Normalizada":None,
            "lat":None,
            "lon":None
        }

    time.sleep(pause)
    return resultado

# df_geo=df_singeo.copy()
# resultados=[]

# #Progreso de Geocodificacion
# for direccion in tqdm(df_geo['direccion'],desc="Geocodificando"):
#     resultados.append(usgi_geocode(direccion,pause=0.2))

# #Paso a un dataframe
# df_resultados=pd.DataFrame(resultados)

# #uno por columna Direccion
# df_geo=df_geo.merge(df_resultados,on='direccion',how='left')

# #Renombro las columnas
# df_geo=df_geo.rename(columns={
#     'Direccion Normalizada':'Dir. Normalizada',
#     'lat':'Latitud',
#     'lng':'Longitud'
# })


# print(df_geo)