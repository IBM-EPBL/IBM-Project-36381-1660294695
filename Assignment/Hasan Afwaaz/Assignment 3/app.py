from flask import Flask,redirect,url_for,render_template,request

app = Flask(__name__)
app.secret_key="hdbcbhjbfjbj"

@app.route("/")
def home():
    return render_template('home.html')

@app.route("/branch/<id>")
def branch(id):
    return render_template('branch.html',id =id)

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=8080,debug=True)
