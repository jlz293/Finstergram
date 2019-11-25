# Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect, send_file
import pymysql.cursors
import datetime
import hashlib
import os

IMAGES_DIR = os.path.join(os.getcwd(), "Images")




#Shalom, Namaste, butter my back and call me Irene were doing it.
#This is pathetic people

# Initialize the app from Flask
app = Flask(__name__)

# Configure MySQL
conn = pymysql.connect(host='localhost',
                       port=3306,
                       user='root',
                       password='root',
                       db='Finstagram',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)

SALT = 'yeehaw!'

# Define a route to hello function
@app.route('/')
def hello():
    return render_template('index.html')


# Define route for login
@app.route('/login')
def login():
    return render_template('login.html')


# Define route for register
@app.route('/register')
def register():
    return render_template('register.html')




# Authenticates the login
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    # grabs information from the forms
    username = str(request.form['username'])
    plain_text_password = str(request.form['password']) + SALT
    password = hashlib.sha256(plain_text_password.encode("utf-8")).hexdigest()



    # cursor used to send queries
    cursor = conn.cursor()
    # executes query
    query = 'SELECT * FROM Person WHERE username = %s and password = %s'
    login_tuple = (username, password)
    cursor.execute(query, login_tuple)
    # stores the results in a variable
    data = cursor.fetchone()
    # use fetchall() if you are expecting more than 1 data row
    cursor.close()
    error = None
    if (data):
        # creates a session for the the user
        # session is a built in
        session['username'] = username
        return redirect(url_for('home'))
    else:
        # returns an error message to the html page
        error = 'Invalid login or username'
        return render_template('login.html', error=error)


# Authenticates the register
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    # grabs information from the forms
    username = str(request.form['username'])
    plain_text_password = str(request.form["password"]) + SALT
    password = hashlib.sha256(plain_text_password.encode("utf-8")).hexdigest()




    first_name = request.form['first_name']
    last_name = request.form['last_name']

    # cursor used to send queries
    cursor = conn.cursor()
    # executes query
    query = 'SELECT * FROM Person WHERE username = %s'
    cursor.execute(query, (username))
    # stores the results in a variable
    data = cursor.fetchone()
    # use fetchall() if you are expecting more than 1 data row
    error = None
    if (data):
        # If the previous query returns data, then user exists
        error = "This user already exists"
        return render_template('register.html', error=error)
    else:
        ins = 'INSERT INTO Person(username, firstName, lastName, password) VALUES(%s, %s, %s, %s)'
        cursor.execute(ins, (username, first_name, last_name, password))
        conn.commit()
        cursor.close()
        return render_template('index.html')


@app.route("/photo/<image_name>", methods=["GET"])
def image(image_name):
    image_location = os.path.join(IMAGES_DIR, image_name)
    if os.path.isfile(image_location):
        return send_file(image_location, mimetype="image/jpg")

@app.route('/home')
def home():
    user = session['username']
    cursor = conn.cursor()
    query = 'SELECT * FROM Photo JOIN Person ON (photoPoster = username)'
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    return render_template('home.html', username=user, photos=data)


@app.route('/post', methods=['GET', 'POST'])
def post():
    username = session['username']
    file_name = request.form['filepath']
    caption = request.form['caption']
    filepath = os.path.join(IMAGES_DIR, file_name)
    allFollowers = request.form['allFollowers']

    cursor = conn.cursor()
    query = 'INSERT INTO Photo (photoPoster, filepath, caption, postingdate, allFollowers) VALUES(%s, %s, %s, %s)'
    timestamp = datetime.datetime.now()
    cursor.execute(query, (username, filepath, caption, timestamp, allFollowers))
    conn.commit()
    cursor.close()
    return redirect(url_for('home'))


@app.route('/select_blogger')
def select_blogger():
    # check that user is logged in
    # username = session['username']
    # should throw exception if username not found

    cursor = conn.cursor()
    query = 'SELECT DISTINCT username FROM blog'
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    return render_template('select_blogger.html', user_list=data)


@app.route('/show_posts', methods=["GET", "POST"])
def show_posts():
    poster = request.args['poster']
    cursor = conn.cursor()
    query = 'SELECT ts, blog_post FROM blog WHERE username = %s ORDER BY ts DESC'
    cursor.execute(query, poster)
    data = cursor.fetchall()
    cursor.close()
    return render_template('show_posts.html', poster_name=poster, posts=data)


@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')


@app.route('/view_further_info', methods=["GET", "POST"])
def view_further_info():
    user = session['username']
    photoID = request.form['photoID']
    cursor = conn.cursor()
    query = 'SELECT * FROM Photo JOIN Person ON Photo.photoPoster = Person.username WHERE photoID = %s'
    cursor.execute(query, photoID)
    data = cursor.fetchall()
    cursor.close()

    cursor = conn.cursor ()
    tagged = 'SELECT username, firstName, lastName FROM Tagged NATURAL JOIN Person WHERE photoID = %s AND tagstatus = 1'
    cursor.execute (tagged, photoID)
    tagData = cursor.fetchall ()
    cursor.close()

    cursor = conn.cursor()
    rating = 'SELECT username, rating FROM Likes WHERE photoID = %s'
    cursor.execute (rating, photoID)
    likeData = cursor.fetchall ()
    cursor.close()

    return render_template('view_further_info.html', username=user, photos=data, tag = tagData, like = likeData)

app.secret_key = 'some key that you will never guess'
# Run the app on localhost port 5000
# debug = True -> you don't have to restart flask
# for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug=True)
