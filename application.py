from flask_sslify import SSLify
from flask import Flask, make_response, request, redirect, render_template, url_for
from mariadb_client import mariadb_client
from differential_privacy_engine import differential_privacy_engine
from helper_functions import check_form_fields

app = Flask(__name__)
sslify = SSLify(app)

environment = "producion"

@app.route('/query', methods=['POST'])
def query():
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

    return make_response(f"Unknown query type.", 400)

@app.route('/table', methods=['POST'])
def get_schema():
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
        table=request.form['table'])

@app.route("/example", methods=['POST'])
def example():
    username = 'demonstration'
    password = 'demo'
    host = 'capstone-team-4-dev.cpbxzomz7uyl.us-east-2.rds.amazonaws.com'
    database = 'sys'
    port = 3306
    table = 'Arrests'

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
        columns=columns, username=username, password=password,
        host=host, database=database, port=port, table=table)

@app.route('/', methods=['GET'])
def index():
    return render_template("index.html")

if __name__ == '__main__':
    if environment == "production":
        app.run()
    else:
        app.run(ssl_context='adhoc', debug=True)