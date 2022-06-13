from ast import arg
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
import plotly.graph_objects as go
from plotly.figure_factory import create_distplot
import plotly.figure_factory as ff
import plotly
import json
import pandas as pd
import numpy as np

app = Flask(__name__)
sslify = SSLify(app)

f = open("keys.json")
keys = json.load(f)
f.close()
GOOGLE_CLIENT_ID = keys["google_oauth"]["client_id"]
ENVIRONMENT = keys["environment"]

repo = database_repository()

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
        
        return func(user, *args, **kws)
    return inner

def identify(func):
    @wraps(func)
    def inner(*args, **kws):
        jwt = request.cookies.get("gauth")
        if jwt == None:
            print("jwt not found")
            return func(None, *args, **kws)
        try:
            idinfo = id_token.verify_oauth2_token(jwt, requests.Request(), GOOGLE_CLIENT_ID)
            userid = idinfo['sub']
            user = repo.get_user(userid)
            if user == None:
                return func(None, *args, **kws)
        except:
            response = make_response(redirect("/", 302))
            print("deleting cookie")
            response.set_cookie("gauth", '', expires=0)
            return response
        
        return func(user, *args, **kws)
    return inner  

@app.route('/query', methods=['POST'])
@authenticate
def query(user):
    success, missing_field = check_form_fields([
        'database', 'username', 'password', 'port',
        'table', 'host', 'query_type', 'epsilon',
        'grouping', 'statistic'
    ], request.form)

    if not success:
        return make_response(f"{missing_field} not specified", 400)
    
    dp_engine = differential_privacy_engine(request.form['username'], 
        request.form['password'], 
        request.form['host'],
        request.form['database'],
        int(request.form['port']))
    
    if request.form['query_type'] == 'laplace_count':
        values, values_ndp  = dp_engine.count(
            request.form['table'],
            request.form['statistic'],
            int(request.form['epsilon']),
            grouping_column = request.form['grouping'])
        response = make_response(values.to_csv())
        response.headers['Content-Disposition'] = "attachment; filename=results.csv"
        #return response
        #visualization
        variables =[values["count"], values_ndp["count"]]
        labels = ["Original","DP"]
        fig = ff.create_distplot(variables, labels, show_hist=False, show_rug=False)
        fig.update_layout(width=1000, height=500)
        plot_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

        return render_template("results.html", 
            values=values, plot_json=plot_json, 
            user_email=user.email)

    elif request.form['query_type'] == 'laplace_sum':
        values = dp_engine.sum(
            request.form['table'],
            request.form['statistic'],
            int(request.form['epsilon']),
            20,
            40,
            grouping_column = request.form['grouping'])
        response = make_response(values.to_csv())
        response.headers['Content-Disposition'] = "attachment; filename=results.csv"
        return response
  
@app.route('/databases/add', methods=['POST'])
@authenticate
def post_database(user):
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
        'table', 'host', 'display_name', 'description'
    ], request.form)

    if not success:
        return make_response(f"{missing_field} not specified", 400)

    repo.insert_database(
        user.id, 
        request.form['database'],
        request.form['host'], 
        request.form['username'],
        request.form['password'],
        request.form['table'],
        int(request.form['port']),
        request.form['display_name'],
        request.form['description']
        )

    return redirect("/", 302)

@app.route("/databases/add", methods=['GET'])
@authenticate
def add_database(user):
    return render_template("add_database.html", user_email = user.email)

@app.route("/query/create")
@authenticate
def create_query(user):
    database_id = request.args.get("database_id")
    if database_id == None:
        return make_response("No database specified", 404)

    database = repo.get_database(database_id)
    if database == None or database.user_id != user.id:
        return make_response("Database not found", 404)
    
    client = mariadb_client(database.username, 
        database.password, 
        database.host,
        database.database,
        database.port)
    result = client.get_table_schema(database.table)

    columns = []
    for res in result:
        columns.append(dict(name=res[0], type=res[1]))

    return render_template("query.html",
        columns=columns,
        username=database.username,
        password=database.password,
        host=database.host,
        database=database.database,
        port=database.port,
        table=database.table,
        user_email = user.email)

@app.route('/', methods=['GET'])
@identify
def index(user):
    if user == None:
        return render_template("home.html")
    
    databases = repo.get_user_databases(user.id)
    return render_template("home.html", user_email = user.email, databases=databases)

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