from msilib.schema import ReserveCost
from flask_sslify import SSLify
from flask import Flask, make_response, request, redirect, render_template, url_for
from mariadb_client import mariadb_client
from differential_privacy_engine import differential_privacy_engine
from helper_functions import check_form_fields
from database_repository import database_repository
import json
from functools import wraps

from google.oauth2 import id_token
from google.auth.transport import requests

app = Flask(__name__)
sslify = SSLify(app)
repo = database_repository()

f = open("keys.json")
keys = json.load(f)
f.close()
GOOGLE_CLIENT_ID = keys["google_oauth"]["client_id"]
ENVIRONMENT = keys["environment"]

def authenticate(func):
    @wraps(func)
    def inner(*args, **kws):
        jwt = request.cookies.get("gauth")
        if jwt == None:
            return redirect("/", 302)
        try:
            idinfo = id_token.verify_oauth2_token(jwt, requests.Request(), GOOGLE_CLIENT_ID)
            userid = idinfo['sub']
            user = repo.get_user(userid)
            if user == None:
                return make_response(redirect("/", 302))
        except ValueError:
            return redirect("https://www.youtube.com/watch?v=ZzWqfJFxC0w", code=302)
        
        return func(idinfo['email'], *args, **kws)
    return inner

def identify(func):
    @wraps(func)
    def inner(*args, **kws):
        jwt = request.cookies.get("gauth")
        if jwt == None:
            return func(None, *args, **kws)
        try:
            idinfo = id_token.verify_oauth2_token(jwt, requests.Request(), GOOGLE_CLIENT_ID)
            userid = idinfo['sub']
            user = repo.get_user(userid)
            if user == None:
                return func(None, *args, **kws)
        except ValueError:
            return redirect("https://www.youtube.com/watch?v=ZzWqfJFxC0w", code=302)
        
        return func(idinfo['email'], *args, **kws)
    return inner  

@app.route('/query', methods=['POST'])
@authenticate
def query(user_email):
    success, missing_field = check_form_fields([
        'database', 'username', 'password', 'port',
        'table', 'host', 'query_type', 'epsilon',
        'identifier', 'grouping', 'statistic'
    ], request.form)

    if not success:
        return make_response(f"{missing_field} not specified", 400)
    
    dp_engine = differential_privacy_engine(request.form['username'], 
        request.form['password'], 
        request.form['host'],
        request.form['database'],
        int(request.form['port']))
    
    if request.form['query_type'] == 'laplace_count':
        values = dp_engine.count(
            request.form['table'],
            request.form['identifier'],
            request.form['grouping'],
            request.form['statistic'],
            int(request.form['epsilon']))
        response = make_response(values.to_csv())
        response.headers['Content-Disposition'] = "attachment; filename=results.csv"
        return response

@app.route('/table', methods=['POST'])
@authenticate
def get_schema(user_email):
    """Get the schema for a database table.
        Form Fields (Required)
        ----------
        username : str,
        password : str,
        host : str,
        database : str,
        table : str
        port : str"""

    success, missing_field = check_form_fields([
        'database', 'username', 'password', 'port',
        'table', 'host'
    ], request.form)

    if not success:
        return make_response(f"{missing_field} not specified", 400)

    client = mariadb_client(request.form['username'], 
        request.form['password'], 
        request.form['host'],
        request.form['database'],
        int(request.form['port']))
    result = client.get_table_schema(request.form['table'])

    columns = []
    for res in result:
        columns.append(dict(name=res[0], type=res[1]))

    return render_template("query.html",
        columns=columns, 
        username=request.form['username'], 
        password=request.form['password'],
        host=request.form['host'],
        database=request.form['database'],
        port=request.form['port'],
        table=request.form['table'],
        user_email = user_email)

@app.route('/', methods=['GET'])
@identify
def index(user_email):
    if user_email != None:
        return render_template("index.html", user_email = user_email)
    return render_template("index.html")

@app.route("/login", methods=['POST'])
def login():
    csrf_token_cookie = request.cookies.get('g_csrf_token')
    data = request.get_data(as_text=True)
    data = data.replace('=', '":"').replace('&', '",\n"')
    data = '{\n"' + data + '"\n}'
    data = json.loads(data)

    csrf_token_body = data['g_csrf_token']

    if csrf_token_cookie != csrf_token_body:
        return redirect("https://www.youtube.com/watch?v=ZzWqfJFxC0w", code=302)

    try:
        idinfo = id_token.verify_oauth2_token(data['credential'], requests.Request(), GOOGLE_CLIENT_ID)
        userid = idinfo['sub']
        user = repo.get_user(userid)
        if user == None:
            repo.insert_user(userid, idinfo['email'])

        response = make_response(redirect("/", 302))
        response.set_cookie("gauth", data['credential'])
        return response
    except ValueError:
        return redirect("https://www.youtube.com/watch?v=ZzWqfJFxC0w", code=302)

if __name__ == '__main__':
    if ENVIRONMENT == "production":
        app.run()
    else:
        app.run(ssl_context='adhoc', debug=True)