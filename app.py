import flask
from jumbo import jumbo

app = flask.Flask(__name__)
app.register_blueprint(jumbo)

app.config["DEBUG"] = True

@app.route("/")
def hello():
    return "Hello World!"

app.run()

if __name__ == "__main__":
    app.run()
