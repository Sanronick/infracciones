from dotenv import load_dotenv
import os
from flask import Flask,render_template,jsonify,request,redirect,session,url_for
import requests
from datetime import datetime, timedelta, timezone
import ssl
from urllib.parse import urlencode
import pandas as pd
from io import BytesIO
from base64 import urlsafe_b64encode

load_dotenv()

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

def leer_excel():
    access_token=session.get("access_token")
    if not access_token:
        raise Exception("No se obtuvo el token de acceso")
    
    #excel_url="https://gcaba-my.sharepoint.com/:x:/g/personal/santiagorodriguez_buenosaires_gob_ar/EdC2aqQSphZMh9UE5WdR9dIBM0bPU1nJWGj1Gflgquwdkg?e=M3aPs8"
    #excel_url="https://gcaba-my.sharepoint.com/:x:/g/personal/santiagorodriguez_buenosaires_gob_ar/EdC2aqQSphZMh9UE5WdR9dIBy5js4b1nV8E2QRcVwuWwmw?e=8hkxJU"
    excel_url="https://gcaba-my.sharepoint.com/:x:/g/personal/santiagorodriguez_buenosaires_gob_ar/EY41IKk4yulEpKW1FDURQIYBlpO356-w73oBrvxXmi6OBA?e=1rKvbv"

    base64_url=urlsafe_b64encode(excel_url.encode("utf-8")).decode("utf-8").rstrip("=")
    share_id=f'u!{base64_url}'

    graph_url=f'https://graph.microsoft.com/v1.0/shares/{share_id}/driveItem/content'


    response=requests.get(
        graph_url,
        headers={"Authorization":f'Bearer {access_token}'}
    )

    if response.status_code!=200:
        raise Exception(f'Error al descargar el archivo: {response.status_code} - {response.text}')
    
    df=pd.read_excel(BytesIO(response.content),engine='openpyxl')
    return df




@app.route('/')
def index():
    return render_template('home.html',user=session.get("user"))

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
        return redirect(url_for("home"))
    
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
    if request.endpoint in ['home','login','getAToken','static']:
        return
    
    if 'user' not in session:
        return redirect('/login')
    
    if '_fresh' in session:
        if datetime.now(timezone.utc) > session['_fresh']:
            session.clear()
            return redirect('/login')
        


@app.route("/ver_planilla")
def ver_planilla():
    try:
        df=leer_excel()
        return df.head().to_html()
    
    except Exception as e:
        return f'<h3>Error: </h3><p>{str(e)}</p>',500
        

# @app.route("/manuales")
# def manuales():
#     access_token=session.get("access_token")
#     if not access_token:
#         return redirect("/login")
    
#     sharepoint_host="gcaba.sharepoint.com"
#     site_name="grupo_PlayasCAT"
#     site_info_url=(
#         f"https://graph.microsoft.com/v1.0/"
#         f"sites/{sharepoint_host}:/sites/{site_name}"
#     )

#     resp_site=requests.get(site_info_url,
#                            headers={"Authorization":f"Bearer {access_token}"})
    
#     if resp_site.status_code!=200:
#         return f"Error al obtener el site_id: {resp_site.status_code}, {resp_site.text}"
    
#     site_id=resp_site.json().get("id")


#     archivo_path="/Vehiculos en Playas CAT Online.xlsx"
#     file_url=(
#         f'https://graph.microsoft.com/v1.0/'
#         f'sites/{site_id}/drive/root:{archivo_path}:/content'
#     )


#     resp_file=requests.get(file_url,headers={"Authorization":f"Bearer {access_token}"})

#     if resp_file.status_code != 200:
#         return f"No se pudo descargar: {resp_file.status_code}<br>{resp_file.text}"
    

#     df=pd.read_excel(BytesIO(resp_file.content),engine='openpyxl')
#     return df.head().to_html()

            



        


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