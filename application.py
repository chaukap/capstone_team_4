from flask_sslify import SSLify
from flask import Flask, make_response, request, redirect, render_template, url_for
from mariadb_client import get_table_schema
import json

application = Flask(__name__)
sslify = SSLify(application)

environment = "producion"
  
@application.route('/table', methods=['POST'])
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

    if 'database' not in request.form.keys():
        return make_response("Database not specified", 400)
    if 'username' not in request.form.keys():
        return make_response("Username not specified", 400)
    if 'password' not in request.form.keys():
        return make_response("Password not specified", 400)
    if 'port' not in request.form.keys():
        return make_response("Port not specified", 400)
    if 'table' not in request.form.keys():
        return make_response("Table not specified", 400)
    if 'host' not in request.form.keys():
        return make_response("Host not specified", 400)

    result = get_table_schema(request.form['username'], 
        request.form['password'], 
        request.form['host'],
        request.form['database'],
        request.form['table'],
        int(request.form['port']))

    columns = []
    for res in result:
        columns.append(dict(name=res[0], type=res[1]))

    return render_template("query.html", columns=columns)

@application.route('/', methods=['GET'])
def index():
    if 'name' in request.args:
        return render_template("index.html", name=request.values["name"])
    else:
        return render_template("index.html")

if __name__ == '__main__':
    if environment == "production":
        application.run()
    else:
        application.run(ssl_context='adhoc', debug=True)