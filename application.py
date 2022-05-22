from flask_sslify import SSLify
from flask import Flask, make_response, request, redirect, render_template, url_for

application = Flask(__name__)
sslify = SSLify(application)

environment = "production"
  
@application.route('/')
def define_clusters():
    if 'name' in request.args:
        return render_template("index.html", name=request.values["name"])
    else:
        return render_template("index.html")

if __name__ == '__main__':
    if environment == "production":
        application.run()
    else:
        application.run(ssl_context='adhoc', debug=True)