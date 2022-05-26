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

    result = get_table_schema(request.form['username'], 
        request.form['password'], 
        request.form['host'],
        request.form['database'],
        request.form['table'],
        int(request.form['port']))

    return json.dumps(result)

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