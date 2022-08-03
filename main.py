from flask_sslify import SSLify
from flask import Flask, make_response, request, redirect, render_template, url_for
from mariadb_client import mariadb_client
from differential_privacy_engine import differential_privacy_engine
from helpers.helper_functions import check_form_fields
from database_repository import database_repository
import json
from functools import wraps
from helpers.graphics import epsilon_slider, exponential_epsilon_slider

from google.oauth2 import id_token
from google.auth.transport import requests
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

def authenticate(func):
    @wraps(func)
    def inner(*args, **kws):
        jwt = request.cookies.get("gauth")
        if jwt == None:
            return redirect("/", 302)
        try:
            repo = database_repository()
            idinfo = id_token.verify_oauth2_token(jwt, requests.Request(), GOOGLE_CLIENT_ID)
            userid = idinfo['sub']
            user = repo.get_user(userid)
            if user == None:
                return make_response(redirect("/", 302))
        except ValueError:
            response = make_response(redirect("/", 302))
            response.set_cookie("gauth", '', expires=0)
            return response
        
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
            repo = database_repository()
            idinfo = id_token.verify_oauth2_token(jwt, requests.Request(), GOOGLE_CLIENT_ID)
            userid = idinfo['sub']
            user = repo.get_user(userid)
            if user == None:
                return func(None, *args, **kws)
        except:
            response = make_response(redirect("/", 302))
            response.set_cookie("gauth", '', expires=0)
            return response
        
        return func(user, *args, **kws)
    return inner  

@app.route('/query', methods=['POST'])
@authenticate
def query(user):
    success, missing_field = check_form_fields([
        'database_id', 'query_type', 'epsilon', 'statistic'
    ], request.form)

    if not success:
        return make_response(f"{missing_field} not specified", 400)

    repo = database_repository()
    database = repo.get_database(int(request.form['database_id']))
    if database == None or database.user_id != user.id:
        return make_response("Database not found", 404)

    if request.form['query_type'] == 'laplace_sum':
        success, missing_field = check_form_fields([
            'upper_bound', 'lower_bound'
        ], request.form)

        if not success:
            return make_response(f"{missing_field} not specified", 400)

    id = repo.insert_database_query(
        database_id=database.id,
        statistic=request.form['statistic'],
        query_type=request.form['query_type'],
        grouping_column=request.form['grouping_column'] if 'grouping_column' in request.form.keys() else "",
        epsilon=request.form['epsilon'],
        upper_bound=request.form['upper_bound'] if 'upper_bound' in request.form.keys() else 0,
        lower_bound=request.form['lower_bound'] if 'lower_bound' in request.form.keys() else 0
        )

    if 'dummy_values' in request.form.keys():
        if(request.form['dummy_values'].split(',')[0] != ""):
            for value in request.form['dummy_values'].split(','):
                repo.insert_dummy_value(id, value)
            
    return redirect(f"/queries?database_id={database.id}", 302)

@app.route('/product_roadmap', methods=['GET'])
@identify
def product_roadmap(user):
    return render_template('roadmap.html', user=user)

@app.route('/query', methods=['DELETE'])
@authenticate
def delete_query(user):
    query_id = request.args.get("query_id")
    if query_id == None:
        return make_response("No database specified", 404)

    repo = database_repository()
    query = repo.get_database_query(query_id)
    database = repo.get_database(query.database_id)
    if database == None or database.user_id != user.id:
        return make_response("Database not found", 404)
    
    try:
        repo.delete_database_query(query_id)
        return make_response("Success", 200)
    except:
        return make_response("Error", 500)

@app.route('/query/result', methods=['GET'])
@authenticate
def download_results(user):
    query_id = request.args.get("query_id")
    if query_id == None:
        return make_response("No query specified", 404)

    repo = database_repository()
    query = repo.get_database_query(query_id)
    if query == None:
        return make_response("Query not found", 404)

    database = repo.get_database(query.database_id)
    if database == None:
        return make_response("Query not found", 404)
    elif database.user_id != user.id:
        if user.epsilon < query.epsilon:
            return redirect("/epsilon/purchase")
        repo.update_user_epsilon(user.google_id, user.epsilon - query.epsilon)

    dp_engine = differential_privacy_engine(database.username, 
        database.password, 
        database.host,
        database.database,
        int(database.port))

    if query.query_type == 'laplace_count':
        values, values_ndp  = dp_engine.count(
            database.table,
            query.statistic,
            query.epsilon,
            grouping_column = query.grouping_column)
        response = make_response(values.to_csv())
        response.headers['Content-Disposition'] = "attachment; filename=results.csv"
        return response

    if query.query_type == 'laplace_sum':
        values, values_ndp  = dp_engine.sum(
            table=database.table,
            sum_column=query.statistic,
            epsilon=query.epsilon,
            lower_bound=query.lower_bound,
            upper_bound=query.upper_bound,
            grouping_column = query.grouping_column)
        response = make_response(values.to_csv())
        response.headers['Content-Disposition'] = "attachment; filename=results.csv"
        return response
    
    if query.query_type == 'laplace_average':
        noisy_result, result  = dp_engine.average(
            table=database.table,
            average_column=query.statistic,
            epsilon=query.epsilon,
            lower_bound=query.lower_bound,
            upper_bound=query.upper_bound,
            grouping_column = query.grouping_column)
        response = make_response(noisy_result.to_csv())
        response.headers['Content-Disposition'] = "attachment; filename=results.csv"
        return response

    if query.query_type.startswith("exponential"):
        scoring_function = None
        dummy_values = pd.Series([n.dummy_value for n in repo.get_dummy_values(query.id)])
        if query.query_type == 'exponential_max':
            scoring_function = lambda c, u: 1 + int(
                np.where(
                    np.sort([float(q) for q in c.unique()]) == float(u)
                    )[0]
                )
        elif query.query_type == 'exponential_min':
            scoring_function = lambda c, u:  1 + int(
                np.where(
                    np.sort([float(q) for q in c.unique()])[::-1] == float(u)
                    )[0]
                )
        elif query.query_type == 'exponential_most_common':
            scoring_function = lambda c, u: sum(u == c)
        elif query.query_type == 'exponential_least_common':
            scoring_function = lambda c, u: sum(u != c)
        else:
            return make_response("Unknown query type", 400)
        
        noisy_result, _ = dp_engine.exponential(
            database.table, 
            query.statistic, 
            scoring_function,
            query.epsilon,
            sensitivity = 1,
            dummy_values=dummy_values
            )

        response = make_response(noisy_result.to_csv())
        response.headers['Content-Disposition'] = "attachment; filename=results.csv"
        return response

    return make_response("Unknown query type", 400)

@app.route('/queries', methods=['GET'])
@authenticate
def get_queries(user):
    database_id = request.args.get("database_id")
    if database_id == None:
        return make_response("No database specified", 404)

    repo = database_repository()
    database = repo.get_database(database_id)
    if database == None or database.user_id != user.id:
        return make_response("Database not found", 404)

    queries = repo.get_database_queries(database.id)

    return render_template("queries.html", 
        database=database,
        queries=queries, 
        user = user)

@app.route('/query/laplace/epsilon', methods=['POST'])
@authenticate
def select_laplace_epsilon(user):
    success, missing_field = check_form_fields([
        'database_id', 'query_type',
        'grouping_column', 'statistic'
    ], request.form)

    if not success:
        return make_response(f"{missing_field} not specified", 400)

    repo = database_repository()
    database = repo.get_database(int(request.form['database_id']))
    if database == None or database.user_id != user.id:
        return make_response("Database not found", 404)
    
    dp_engine = differential_privacy_engine(database.username, 
        database.password, 
        database.host,
        database.database,
        int(database.port))
    
    if request.form['query_type'] == 'laplace_count':
        noisy_result, result  = dp_engine.count(
            table=database.table,
            count_column=request.form['statistic'],
            epsilon=0.5,
            grouping_column=request.form['grouping_column'])
            

        fig = epsilon_slider(result, 1, 0)
        fig.update_layout(width=1300, height=500)
        
        return render_template("laplace_epsilon_selection.html", 
            values=result, plot=fig.to_html(full_html=False, include_plotlyjs='cdn'), 
            database_id=database.id,
            grouping_column=request.form['grouping_column'],
            statistic=request.form['statistic'],
            query_type=request.form['query_type'],
            user = user)

    elif request.form['query_type'] == 'laplace_sum':
        noisy_result, result  = dp_engine.sum(
            table=database.table,
            sum_column=request.form['statistic'],
            epsilon=0.5,
            lower_bound=float(request.form['lower_bound']),
            upper_bound=float(request.form['upper_bound']),
            grouping_column=request.form['grouping_column'])
            
        fig = epsilon_slider(result, float(request.form['upper_bound']), float(request.form['lower_bound']))
        fig.update_layout(width=1300, height=500)

        return render_template("laplace_epsilon_selection.html", 
            values=result, plot=fig.to_html(full_html=False, include_plotlyjs='cdn'), 
            database_id=database.id,
            grouping_column=request.form['grouping_column'],
            statistic=request.form['statistic'],
            query_type=request.form['query_type'],
            user = user)

    elif request.form['query_type'] == 'laplace_average':
        noisy_result, result  = dp_engine.average(
            table=database.table,
            average_column=request.form['statistic'],
            epsilon=0.5,
            lower_bound=float(request.form['lower_bound']),
            upper_bound=float(request.form['upper_bound']),
            grouping_column=request.form['grouping_column'])
        
        fig = epsilon_slider(result, float(request.form['upper_bound']), float(request.form['lower_bound']))
        fig.update_layout(width=1300, height=500)
        
        return render_template("laplace_epsilon_selection.html", 
            values=result, plot=fig.to_html(full_html=False, include_plotlyjs='cdn'), 
            database_id=database.id,
            grouping_column=request.form['grouping_column'],
            statistic=request.form['statistic'],
            query_type=request.form['query_type'],
            user = user)

    return make_response("Unknown query type", 400)

@app.route('/query/exponential/epsilon', methods=['POST'])
@authenticate
def select_exponential_epsilon(user):
    success, missing_field = check_form_fields([
        'database_id', 'query_type', 'statistic'
    ], request.form)

    if not success:
        return make_response(f"{missing_field} not specified", 400)

    repo = database_repository()
    database = repo.get_database(int(request.form['database_id']))
    if database == None or database.user_id != user.id:
        return make_response("Database not found", 404)
    
    dp_engine = differential_privacy_engine(database.username, 
        database.password, 
        database.host,
        database.database,
        int(database.port))

    scoring_function = None
    upper_bound = 0
    lower_bound = 0
    if request.form['query_type'] == 'exponential_max':
        scoring_function = lambda c, u: 1 + int(
            np.where(
                np.sort([float(q) for q in c.unique()]) == float(u)
                )[0]
            )
        upper_bound = float(request.form['upper_bound'])
        lower_bound = float(request.form['lower_bound'])
    elif request.form['query_type'] == 'exponential_min':
        scoring_function = lambda c, u: 1 + int(
            np.where(
                np.sort([float(q) for q in c.unique()])[::-1] == float(u)
                )[0]
            )
        upper_bound = float(request.form['upper_bound'])
        lower_bound = float(request.form['lower_bound'])
    elif request.form['query_type'] == 'exponential_most_common':
        scoring_function = lambda c, u: sum(u == c)
    elif request.form['query_type'] == 'exponential_least_common':
        scoring_function = lambda c, u: sum(u != c)
    else:
        return(make_response("Unknown query type", 404))

    dummy_values = request.form['dummy_values'].split(',')
    print(dummy_values)
    if dummy_values[0] != "":
        dummy_values = pd.Series(dummy_values)
    else:
        dummy_values = None

    distributions = dp_engine.exponential_options(
        database.table, 
        request.form['statistic'],
        scoring_function=scoring_function,
        epsilons=np.arange(0.1, 6.1, 0.1),
        sensitivity = 1,
        dummy_values = dummy_values
        )

    fig = exponential_epsilon_slider(distributions)
    fig = fig.update_layout(width=1000, height=500)

    return render_template("exponential_epsilon_selection.html", 
        plot=fig.to_html(full_html=False, include_plotlyjs='cdn'), 
        database_id=database.id,
        statistic=request.form['statistic'],
        query_type=request.form['query_type'],
        upper_bound=upper_bound,
        lower_bound=lower_bound,
        dummy_values=request.form['dummy_values'],
        user = user)


@app.route('/query/exponential/dummy_values', methods=['POST'])
@authenticate
def select_exponential_dummy_values(user):
    success, missing_field = check_form_fields([
        'database_id', 'query_type', 'statistic'
    ], request.form)

    if not success:
        return make_response(f"{missing_field} not specified", 400)

    repo = database_repository()
    database = repo.get_database(int(request.form['database_id']))
    if database == None or database.user_id != user.id:
        return make_response("Database not found", 404)

    dp_engine = differential_privacy_engine(database.username, 
        database.password, 
        database.host,
        database.database,
        int(database.port))

    unique_values = dp_engine.unique_values(
        database.table, 
        request.form['statistic'])

    upper_bound = 0
    lower_bound = 0
    if request.form['query_type'] == 'exponential_max':
        upper_bound = float(request.form['upper_bound'])
        lower_bound = float(request.form['lower_bound'])
    elif request.form['query_type'] == 'exponential_min':
        upper_bound = float(request.form['upper_bound'])
        lower_bound = float(request.form['lower_bound'])

    return render_template("exponential_dummy_values.html",
        database_id=database.id,
        unique_values=unique_values,
        statistic=request.form['statistic'],
        query_type=request.form['query_type'],
        upper_bound=upper_bound,
        lower_bound=lower_bound,
        user = user)
  
@app.route('/databases/add', methods=['POST'])
@authenticate
def post_database(user):
    success, missing_field = check_form_fields([
        'database', 'username', 'password', 'port',
        'table', 'host', 'display_name', 'description'
    ], request.form)

    if not success:
        return make_response(f"{missing_field} not specified", 400)

    repo = database_repository()
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

    return redirect("/home", 302)

@app.route("/databases/add", methods=['GET'])
@authenticate
def add_database(user):
    return render_template("add_database.html", user = user)

@app.route("/query/mechanism")
@authenticate
def select_mechanism(user):
    database_id = request.args.get("database_id")
    if database_id == None:
        return make_response("No database specified", 404)

    repo = database_repository()
    database = repo.get_database(database_id)
    if database == None or database.user_id != user.id:
        return make_response("Database not found", 404)

    return render_template(
        "mechanism_selection.html", 
        user = user,
        database_id=database_id)

@app.route("/query/laplace", methods=["GET"])
@authenticate
def laplace_query(user):
    database_id = request.args.get("database_id")
    if database_id == None:
        return make_response("No database specified", 404)

    repo = database_repository()
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

    return render_template("laplace_query.html",
        columns=columns,
        database_id=database_id,
        user = user)

@app.route("/learn", methods=["GET"])
def learn():
    return render_template( "education_basic.html")

@app.route("/learn/differential_privacy", methods=["GET"])
def learn_differential_privacy():
    return render_template( "education_differential_privacy.html")

@app.route("/learn/epsilon_selection", methods=["GET"])
def learn_epsilon_selection():
    return render_template( "education_epsilon_selection.html")

@app.route("/learn/sensitivity", methods=["GET"])
def learn_sensitivity():
    return render_template("education_sensitivity.html")

@app.route("/learn/probablistic_attacks", methods=["GET"])
def learn_probablistic_attacks():
    return render_template("education_probablistic_attack.html")

@app.route("/learn/coming_soon", methods=["GET"])
def learn_coming_soon():
    return render_template("education_coming_soon.html")

@app.route("/query/exponential", methods=["GET"])
@authenticate
def exponential_query(user):
    database_id = request.args.get("database_id")
    if database_id == None:
        return make_response("No database specified", 404)

    repo = database_repository()
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

    return render_template("exponential_query.html",
        columns=columns,
        database_id=database_id,
        user = user)

@app.route("/search", methods=["GET"])
@authenticate
def search(user):
    return render_template("search.html", user = user)

@app.route("/epsilon/purchase", methods=["GET"])
@authenticate
def purchase_epsilon(user):
    return render_template(
        "buy_epsilon.html", 
        user = user, 
        epsilon=user.epsilon)

@app.route("/epsilon/buy", methods=["POST"])
@authenticate
def buy_epsilon(user):
    repo = database_repository() 
    repo.update_user_epsilon(user.google_id, user.epsilon + float(request.form['epsilon'])) 
    user = repo.get_user_by_email(user.email)

    return redirect(url_for("search"))

@app.route("/lookup", methods=["GET"])
@authenticate
def lookup(user):
    query = request.args.get("query")
    if query == None:
        query = ""

    repo = database_repository()
    queries = repo.lookup_queries(query, exclude_user = user.google_id)
    print(queries)
    results = [
        {
        "id": q[0].id,
        "database_id": q[0].database_id,
        "database_name": q[1],
        "query_type": q[0].query_type,
        "statistic": q[0].statistic,
        "grouping_column": q[0].grouping_column,
        "description" : q[0].to_string(),
        "epsilon" : q[0].epsilon
        } for q in queries
    ]
    return json.dumps(results) 

@app.route('/', methods=['GET'])
@identify
def index(user):
    if user == None:
        return render_template("index.html")
    
    repo = database_repository()
    databases = repo.get_user_databases(user.id)
    return render_template("index.html", user = user, databases=databases)

@app.route('/home', methods=['GET'])
@identify
def home(user):
    if user == None:
        return render_template("home.html")
    
    repo = database_repository()
    databases = repo.get_user_databases(user.id)
    return render_template("home.html", user = user, databases=databases)

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
        repo = database_repository()
        idinfo = id_token.verify_oauth2_token(data['credential'], requests.Request(), GOOGLE_CLIENT_ID)
        userid = idinfo['sub']
        user = repo.get_user(userid)
        if user == None:
            repo.insert_user(userid, idinfo['email'])
            user = repo.get_user(userid)
            repo.insert_database(
                user.id,
                "sys",
                "capstone-team-4-dev.cpbxzomz7uyl.us-east-2.rds.amazonaws.com",
                "admin",
                "testpassword",
                "BaldingBears",
                3306,
                "Balding Bears",
                "An example database to get started!"
            )

        response = make_response(redirect("/", 302))
        response.set_cookie("gauth", data['credential'])
        return response
    except ValueError:
        return redirect("/", code=302)

@app.route("/logout")
def logout():
    response = make_response(redirect("/", 302))
    response.set_cookie("gauth", '', expires=0)
    return response

if __name__ == '__main__':
    if ENVIRONMENT == "production":
        app.run()
    else:
        app.run(ssl_context='adhoc', debug=True)
