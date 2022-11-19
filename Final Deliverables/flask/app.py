from crypt import methods
from re import RegexFlag
from clarifai_grpc.grpc.api import service_pb2, resources_pb2
from clarifai_grpc.grpc.api.status import status_code_pb2
from clarifai_grpc.channel.clarifai_channel import ClarifaiChannel
from clarifai_grpc.grpc.api import service_pb2_grpc
from flask import Flask, json, jsonify, render_template, url_for, request, redirect, session, flash
from turtle import st
from markupsafe import escape
import bcrypt
import requests
import dns.resolver
from bson import ObjectId
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content
import ibm_db
conn = ibm_db.connect("DATABASE=bludb;HOSTNAME=ba99a9e6-d59e-4883-8fc0-d6a8c9f7a08f.c1ogj3sd0tgtu0lqde00.databases.appdomain.cloud;PORT=31321;SECURITY=SSL;SSLServerCertificate=DigiCertGlobalRootCA (3).crt;UID=vbz29727;PWD=zgvT4AKDdg9I90uZ",'','')
session = {}

dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
dns.resolver.default_resolver.nameservers = ['8.8.8.8']


class MyEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super(MyEncoder, self).default(obj)

app = Flask(__name__)



@app.route('/')
def home():
  return render_template('home.html')

@app.route('/signup')
def signup():
  return render_template('sign up.html')

@app.route('/addrec',methods = ['POST', 'GET'])
def addrec():
  if request.method == 'POST':

    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']
    password = request.form['password']
    retypepassword = request.form['retypepassword']


    sql = "SELECT * FROM students WHERE name =?"
    stmt = ibm_db.prepare(conn, sql)
    ibm_db.bind_param(stmt,1,name)
    ibm_db.execute(stmt)
    account = ibm_db.fetch_assoc(stmt)

    if account:
      return render_template('admin.html', msg="You are already a member, please login using your details")
    else:
      insert_sql = "INSERT INTO students VALUES (?,?,?,?,?)"
      prep_stmt = ibm_db.prepare(conn, insert_sql)
      ibm_db.bind_param(prep_stmt, 1, name)
      ibm_db.bind_param(prep_stmt, 2, email)
      ibm_db.bind_param(prep_stmt, 3, phone)
      ibm_db.bind_param(prep_stmt, 4, password)
      ibm_db.bind_param(prep_stmt, 5, retypepassword)
      ibm_db.execute(prep_stmt)
    
    return render_template('home.html', msg="Student Data saved successfuly..")



@app.route('/signin',methods=['GET','POST'])
def signin():
    message = ''
    if request.method == 'POST':
        # get the data from the form
        email = request.form['email']
        password = request.form['password']
        # if nothing is entered in the form
        if not email or not password:
            message = 'Please fill all the fields!'
            return render_template('sign in.html', message=message)
        # check if the username and password are valid
        sql = "SELECT * FROM students WHERE email = '" + email + "' AND password = '" + password + "'"
        stmt = ibm_db.exec_immediate(conn, sql)
        result = ibm_db.fetch_assoc(stmt)
        # print("result", result)
        if result:
            # message = 'You have successfully logged in!'
            session['email'] = result['EMAIL']
            session['password'] = result['PASSWORD']
            return redirect('/window')
        else:
            message = 'The email or password is incorrect!'
    return render_template('sign in.html', message=message)

  
@app.route('/window')
def window():
    # Calorie Ninja
    url = "https://calorieninjas.p.rapidapi.com/v1/nutrition"

    headers = {
        "X-RapidAPI-Key": "aa95b88b45mshe4394a422ce8c48p13a698jsn9d8eb019e144",
        "X-RapidAPI-Host": "calorieninjas.p.rapidapi.com"
    }

    if request.method == 'POST':
        foodname = request.form['foodname']

        querystring = {"query": foodname}
        response = requests.request(
            "GET", url, headers=headers, params=querystring)

        return response.text

    return render_template('window.html')

@app.route('/window', methods=['POST', 'GET'])
def clarifai():
    if request.files.get('image'):
        image = request.files['image'].stream.read()
        stub = service_pb2_grpc.V2Stub(ClarifaiChannel.get_grpc_channel())

        CLARIFAI_API_KEY = "04fe7a95051541789ba44a08eaa5722e"
        APPLICATION_ID = "Nutrition_Assistant1"

        # Authenticate

        # image = '/home/bala/Desktop/Images/foodsample.jpeg'

        metadata = (("authorization", f"Key {CLARIFAI_API_KEY}"),)

        with open(image, "rb") as f:
            file_bytes = f.read()

        request = service_pb2.PostModelOutputsRequest(
            model_id='9504135848be0dd2c39bdab0002f78e9',
            inputs=[
                resources_pb2.Input(
                    data=resources_pb2.Data(
                        image=resources_pb2.Image(
                            base64=file_bytes
                        )
                    )
                )
            ])
        response = stub.PostModelOutputs(request, metadata=metadata)

        if response.status.code != status_code_pb2.SUCCESS:
            raise Exception("Request failed, status code: " +
                            str(response.status.code))

        for concept in response.outputs[0].data.concepts:
            print('%12s: %.2f' % (concept.name, concept.value))

    return render_template('window.html')

@app.route('/admin')
def admin():
  students = []
  sql = "SELECT * FROM Students"
  stmt = ibm_db.exec_immediate(conn, sql)
  dictionary = ibm_db.fetch_both(stmt)
  while dictionary != False:
    # print ("The Name is : ",  dictionary)
    students.append(dictionary)
    dictionary = ibm_db.fetch_both(stmt)

  if students:
    return render_template("admin.html", students = students)

@app.route('/delete/<name>')
def delete(name):
  sql = f"SELECT * FROM Students WHERE name='{escape(name)}'"
  print(sql)
  stmt = ibm_db.exec_immediate(conn, sql)
  student = ibm_db.fetch_row(stmt)
  print ("The Name is : ",  student)
  if student:
    sql = f"DELETE FROM Students WHERE name='{escape(name)}'"
    print(sql)
    stmt = ibm_db.exec_immediate(conn, sql)

    students = []
    sql = "SELECT * FROM Students"
    stmt = ibm_db.exec_immediate(conn, sql)
    dictionary = ibm_db.fetch_both(stmt)
    while dictionary != False:
      students.append(dictionary)
      dictionary = ibm_db.fetch_both(stmt)
    if students:
      return render_template("admin.html", students = students, msg="Delete successfully")


  
  # # while student != False:
  # #   print ("The Name is : ",  student)

  # print(student)
  return "success..."

# @app.route('/posts/edit/<int:id>', methods=['GET', 'POST'])
# def edit(id):
    
#     post = BlogPost.query.get_or_404(id)

#     if request.method == 'POST':
#         post.title = request.form['title']
#         post.author = request.form['author']
#         post.content = request.form['content']
#         db.session.commit()
#         return redirect('/posts')
#     else:
#         return render_template('edit.html', post=post)
# sendgrid
def send_mail(email):
    sg = sendgrid.SendGridAPIClient(SENDGRID_API_KEY)
    from_email = Email(os.environ.get('EMAIL_ID'))
    to_email = To(email)  # Change to your recipient
    subject = "Nutrition is a basic human need and a prerequisite for healthy life"
    content = Content("text/plain",
                      "Thank you for creating an account on our platform. Now you can utilise our platform "
                      "to maintain a healthier life.")
    mail = Mail(from_email, to_email, subject, content)

    # Get a JSON-ready representation of the Mail object
    mail_json = mail.get()
    sg.client.mail.send.post(request_body=mail_json)


def custom_send_mail(email, data):
    sg = sendgrid.SendGridAPIClient(SENDGRID_API_KEY)
    from_email = Email(os.environ.get('EMAIL_ID'))
    to_email = To(email)  # Change to your recipient
    subject = "Nutrition is a basic human need and a prerequisite for healthy life"
    content = Content("text/plain",
                      f"'{data}'")
    mail = Mail(from_email, to_email, subject, content)

    # Get a JSON-ready representation of the Mail object
    mail_json = mail.get()
    sg.client.mail.send.post(request_body=mail_json)


def generateOTP():
    digits = os.environ.get('DIGIT')
    OTP = ""
    for i in range(6):
        OTP += digits[math.floor(random.random() * 10)]
    return OTP


def get_history():
    history = []
    sql = f"SELECT * FROM PERSON WHERE email = '{session['email']}'"
    stmt = ibm_db.exec_immediate(conn, sql)
    dictionary = ibm_db.fetch_both(stmt)
    while dictionary:
        history.append(dictionary)
        dictionary = ibm_db.fetch_both(stmt)
    return history


def get_history_person(email):
    history = []
    sql = f"SELECT * FROM PERSON WHERE email = '{email}'"
    stmt = ibm_db.exec_immediate(conn, sql)
    dictionary = ibm_db.fetch_both(stmt)
    while dictionary:
        history.append(dictionary)
        dictionary = ibm_db.fetch_both(stmt)
    return history


def get_history_person_time(time):
    history = []
    sql = f"SELECT * FROM PERSON WHERE time = '{time}'"
    stmt = ibm_db.exec_immediate(conn, sql)
    dictionary = ibm_db.fetch_both(stmt)
    while dictionary:
        history.append(dictionary)
        dictionary = ibm_db.fetch_both(stmt)
    return history


def get_user():
    user = []
    sql = f"SELECT * FROM USER"
    stmt = ibm_db.exec_immediate(conn, sql)
    dictionary = ibm_db.fetch_both(stmt)
    while dictionary:
        user.append(dictionary)
        dictionary = ibm_db.fetch_both(stmt)
    return user


backend = default_backend()


@app.route('/dashboard', methods=['GET', 'POST'])
def upload_file():
    history = []
    # sql = "SELECT * FROM Students"
    sql = f"SELECT * FROM PERSON WHERE email = '{session['email']}'"
    stmt = ibm_db.exec_immediate(conn, sql)
    dictionary = ibm_db.fetch_both(stmt)
    while dictionary:
        history.append(dictionary)
        dictionary = ibm_db.fetch_both(stmt)
    if request.method == 'POST':
        # check if the post request has the file part
        if 'logout' in request.form:
            session["loggedIn"] = None
            session['name'] = None
            session['email'] = None
            return render_template('index.html', error="Successfully created")
        if 'file' not in request.files:
            # flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.

        if file.filename == '':
            return render_template('dashboard.html', msg="File not found", history=history)
        baseimage = file.read()
        if file and allowed_file(file.filename):
            requests = service_pb2.PostModelOutputsRequest(
                model_id="food-item-recognition",
                user_app_id=resources_pb2.UserAppIDSet(app_id=YOUR_APPLICATION_ID),
                inputs=[
                    resources_pb2.Input(
                        data=resources_pb2.Data(image=resources_pb2.Image(base64=baseimage))
                    )
                ],
            )
            response = stub.PostModelOutputs(requests, metadata=metadata)

            if response.status.code != status_code_pb2.SUCCESS:
                return render_template('dashboard.html', msg=f'Failed {response.status}', history=history)

            calcium = 0
            vitaminb5 = 0
            protein = 0
            vitamind = 0
            vitamina = 0
            vitaminb2 = 0
            carbohydrates = 0
            fiber = 0
            fat = 0
            sodium = 0
            vitaminc = 0
            calories = 0
            vitaminb1 = 0
            folicacid = 0
            sugar = 0
            vitamink = 0
            cholesterol = 0
            potassium = 0
            monounsaturatedfat = 0
            polyunsaturatedfat = 0
            saturatedfat = 0
            totalfat = 0
            calciumu = 'g'
            vitaminb5u = 'g'
            proteinu = 'g'
            vitamindu = 'g'
            vitaminau = 'g'
            carbohydratesu = 'g'
            sodiumu = 'g'
            vitamincu = 'g'
            caloriesu = 'cal'
            sugaru = 'g'
            cholesterolu = 'g'
            potassiumu = 'g'
            monounsaturatedfatu = 'g'
            polyunsaturatedfatu = 'g'
            saturatedfatu = 'g'

            for concept in response.outputs[0].data.concepts:
                print("%12s: %.2f" % (concept.name, concept.value))
                if concept.value > 0.5:
                    payload = "ingredientList=" + concept.name + "&servings=1"
                    response1 = res.request("POST", url, data=payload, headers=headers, params=querystring)
                    data = response1.json()
                    for i in range(0, 1):
                        nutri_array = data[i]
                        nutri_dic = nutri_array['nutrition']
                        nutri = nutri_dic['nutrients']

                        for z in range(0, len(nutri)):
                            temp = nutri[z]
                            if temp['name'] == 'Calcium':
                                calcium += round(temp['amount'], 2)
                                calciumu = temp['unit']
                            elif temp['name'] == 'Vitamin B5':
                                vitaminb5 += round(temp['amount'], 2)
                                vitaminb5u = temp['unit']
                            elif temp['name'] == 'Protein':
                                protein += round(temp['amount'], 2)
                                proteinu = temp['unit']
                            elif temp['name'] == 'Vitamin D':
                                vitamind += round(temp['amount'], 2)
                                vitamindu = temp['unit']
                            elif temp['name'] == 'Vitamin A':
                                vitamina += round(temp['amount'], 2)
                                vitaminau = temp['unit']
                            elif temp['name'] == 'Vitamin B2':
                                vitaminb2 += round(temp['amount'], 2)
                                vitaminb2u = temp['unit']
                            elif temp['name'] == 'Carbohydrates':
                                carbohydrates += round(temp['amount'], 2)
                                carbohydratesu = temp['unit']
                            elif temp['name'] == 'Fiber':
                                fiber += round(temp['amount'], 2)
                                fiberu = temp['unit']
                            elif temp['name'] == 'Vitamin C':
                                vitaminc += round(temp['amount'], 2)
                                vitamincu = temp['unit']
                            elif temp['name'] == 'Calories':
                                calories += round(temp['amount'], 2)
                                caloriesu = 'cal'
                            elif temp['name'] == 'Vitamin B1':
                                vitaminb1 += round(temp['amount'], 2)
                                vitaminb1u = temp['unit']
                            elif temp['name'] == 'Folic Acid':
                                folicacid += round(temp['amount'], 2)
                                folicacidu = temp['unit']
                            elif temp['name'] == 'Sugar':
                                sugar += round(temp['amount'], 2)
                                sugaru = temp['unit']
                            elif temp['name'] == 'Vitamin K':
                                vitamink += round(temp['amount'], 2)
                                vitaminku = temp['unit']
                            elif temp['name'] == 'Cholesterol':
                                cholesterol += round(temp['amount'], 2)
                                cholesterolu = temp['unit']
                            elif temp['name'] == 'Mono Unsaturated Fat':
                                monounsaturatedfat += round(temp['amount'], 2)
                                monounsaturatedfatu = temp['unit']
                            elif temp['name'] == 'Poly Unsaturated Fat':
                                polyunsaturatedfat += round(temp['amount'], 2)
                                polyunsaturatedfatu = temp['unit']
                            elif temp['name'] == 'Saturated Fat':
                                saturatedfat += round(temp['amount'], 2)
                                saturatedfatu = temp['unit']
                            elif temp['name'] == 'Fat':
                                fat += round(temp['amount'], 2)
                                fatu = temp['unit']
                            elif temp['name'] == 'Sodium':
                                sodium += round(temp['amount'], 2)
                                sodiumu = temp['unit']
                            elif temp['name'] == 'Potassium':
                                potassium += round(temp['amount'], 2)
                                potassiumu = temp['unit']
                            else:
                                pass

            totalfat += saturatedfat + polyunsaturatedfat + monounsaturatedfat
            data = [round(calories, 2), round(totalfat, 2), round(saturatedfat, 2), round(polyunsaturatedfat, 2),
                    round(monounsaturatedfat, 2), round(cholesterol, 2), round(sodium, 2), round(potassium, 2),
                    round(sugar, 2), round(protein, 2), round(carbohydrates, 2), round(vitamina, 2), round(vitaminc, 2),
                    round(vitamind, 2), round(vitaminb5, 2), round(calcium, 2)]

            unit = [caloriesu, "g", saturatedfatu, polyunsaturatedfatu, monounsaturatedfatu, cholesterolu, sodiumu,
                    potassiumu, sugaru, proteinu, carbohydratesu, vitaminau, vitamincu, vitamindu, vitaminb5u, calciumu]

            to_string = "{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{}".format(data[0], data[1], data[2], data[3],
                                                                                 data[4],
                                                                                 data[5], data[6], data[7], data[8],
                                                                                 data[9],
                                                                                 data[10], data[11], data[12], data[13],
                                                                                 data[14], data[15])

            to_unit = "{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{}".format(unit[0], unit[1], unit[2], unit[3],
                                                                               unit[4], unit[5], unit[6], unit[7],
                                                                               unit[8], unit[9], unit[10], unit[11],
                                                                               unit[12], unit[13], unit[14], unit[15])

            current_time = datetime.now(timezone("Asia/Kolkata")).strftime('%Y-%m-%d %H:%M:%S')

            complete_value = to_string + ',' + to_unit
            val_arr = complete_value.split(',')

            to_units = "Calories : {}{}" \
                       "Total Fat : {}{}" \
                       "Saturated Fat : {}{}" \
                       "Polyunsaturated Fat : {}{}" \
                       "Monounsaturated Fat : {}{}" \
                       "Cholesterol : {}{}" \
                       "Sodium : {}{}" \
                       "Potassium : {}{}" \
                       "Sugar : {}{}" \
                       "Protein : {}{}" \
                       "Carbohydrates : {}{}" \
                       "Vitamin A : {}{}" \
                       "Vitamin C : {}{}" \
                       "Vitamin D : {}{}" \
                       "Vitamin B5 : {}{}" \
                       "Calcium : {}{}".format(data[0], unit[1], data[1], unit[1], data[2], unit[2], data[3], unit[3],
                                               data[4], unit[4], data[5], unit[5], data[6], unit[6], data[7], unit[7],
                                               data[8], unit[8], data[9], unit[9], data[10], unit[10], data[11],
                                               unit[11], data[12], unit[12], data[13], unit[13], data[14], unit[14],
                                               data[15], unit[15])

            custom_send_mail(session['email'], to_units)

            try:
                insert_sql = "INSERT INTO PERSON VALUES (?,?,?,?)"
                prep_stmt = ibm_db.prepare(conn, insert_sql)
                ibm_db.bind_param(prep_stmt, 1, session['name'])
                ibm_db.bind_param(prep_stmt, 2, session['email'])
                ibm_db.bind_param(prep_stmt, 3, complete_value)
                ibm_db.bind_param(prep_stmt, 4, current_time)
                ibm_db.execute(prep_stmt)
                return render_template('dashboard.html', user=session['name'], email=session['email'], data=val_arr,
                                       history=history)
            except ibm_db.stmt_error:
                print(ibm_db.stmt_error())
                return render_template('dashboard.html', msg='Something wnt wrong', user=session['name'],
                                       email=session['email'], data=val_arr, history=history)

        return render_template('dashboard.html', history=history)
    if session['name'] is None:
        return render_template('index.html')
    return render_template('dashboard.html', user=session['name'], email=session['email'], history=history)
