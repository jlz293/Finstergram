# Import Flask Library
from flask import Flask, render_template, request, session, redirect, url_for, send_file, flash
import pymysql.cursors
import datetime
import hashlib
import os
from functools import wraps


IMAGES_DIR = os.path.join(os.getcwd(), "Images")

# Initialize the app from Flask
app = Flask(__name__)

# Configure MySQL
conn = pymysql.connect(host='database-1.cuhugvcusx5j.us-east-2.rds.amazonaws.com',
                       port=3306,
                       user='admin',
                       password='1A2b3c4d',
                       db='Finstagram',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)

SALT = 'yeehaw!'


def login_required(f):
    @wraps(f)
    def dec(*args, **kwargs):
        if not "username" in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return dec

@app.route("/")
def index():
    if "username" in session:
        return redirect(url_for("home"))
    return render_template("index.html")

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



@app.route('/home')
@login_required
def home():
    user = session['username']
    cursor = conn.cursor()
    photo_query = 'SELECT * FROM Photo JOIN Person ON (photoPoster = username) WHERE photoID IN (SELECT photoID FROM Follow JOIN Photo ON (Follow.username_followed = Photo.photoPoster) WHERE allFollowers = 1 AND acceptedFollow = 1 AND username_follower = %s) OR photoID IN (SELECT photoID from Photo WHERE photoPoster = %s) OR photoID IN (SELECT photoID FROM SharedWith WHERE groupName IN (SELECT groupName FROM BelongTo WHERE member_username = %s OR owner_username = %s)) ORDER BY postingdate DESC'
    #query = 'SELECT * FROM Photo WHERE photoID IN (SELECT photoID FROM Follow JOIN Photo ON (Follow.username_followed = Photo.photoPoster) WHERE allFollowers = 1 AND username_follower = %s) OR photoID IN (SELECT photoID FROM SharedWith WHERE groupName IN (SELECT groupName FROM BelongTo WHERE member_username = %s OR owner_username = %s)) ORDER BY postingdate DESC'
    cursor.execute(photo_query, (user, user, user, user))
    data = cursor.fetchall()



    # #query = "SELECT * FROM Photo JOIN Person ON (photoPoster = username) ORDER BY postingdate DESC"



    cursor.close()
    return render_template('home.html', username=user, photos=data)


@app.route('/post', methods=['GET', 'POST'])
@login_required
def post():
    username = session['username']
    caption = request.form['caption']
    shared_to = request.form.getlist('share_to')

    image_file = request.files.get("image_to_upload", "")
    image_name = image_file.filename
    filepath = os.path.join(IMAGES_DIR, image_name)
    image_file.save(filepath)

    insert_query = 'INSERT INTO Photo (photoPoster, filepath, caption, postingdate, allFollowers) VALUES(%s, %s, %s, %s, %s)'
    timestamp = datetime.datetime.now()

    if shared_to[0] == "True":
        cursor = conn.cursor()
        cursor.execute(insert_query, (username, image_name, caption, timestamp, 1))
        conn.commit()
        cursor.close()

    else:
        cursor = conn.cursor()
        cursor.execute(insert_query, (username, image_name, caption, timestamp, 0))
        conn.commit()
        last_photo_query = 'SELECT max(photoID) FROM Photo'
        cursor.execute(last_photo_query)
        max_item_id = cursor.fetchone()

        for friendgroup in shared_to:
            group = friendgroup.split('-')
            groupName = group[1]
            groupOwner = group[0]
            insert = 'INSERT into SharedWith(groupName, groupOwner, photoID) VALUES(%s, %s, %s)'
            cursor.execute(insert, (groupName, groupOwner, max_item_id['max(photoID)']))
            conn.commit()
        cursor.close()

    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')

@app.route('/upload')
@login_required
def upload():
    user = session['username']
    cursor = conn.cursor()


    friendgroups_query = 'SELECT * FROM BelongTo WHERE member_username = %s'
    cursor.execute(friendgroups_query, user)
    friendgroups = cursor.fetchall()
    cursor.close()

    return render_template('upload.html', friendgroups=friendgroups, username=user)




@app.route("/likePhoto", methods=["POST"])
@login_required
def likePhoto():
    username = session["username"]
    photoID = request.form['photoID']
    rating = request.form['rating']
    if rating == '':
        rating = 0

    if (not likedAlready(username, photoID)):
        liketime = datetime.datetime.today()
        query = "INSERT INTO Likes (username, PhotoID, liketime, rating) values (%s, %s, %s, %s)"
        with conn.cursor() as cursor:
            cursor.execute(query, (username, photoID, liketime.strftime('%Y-%m-%d %H:%M:%S'), rating))
    conn.commit()

    return redirect("home")


def likedAlready(username, photoID):
    query = "SELECT EXISTS(SELECT * FROM Likes WHERE photoID=%s AND username=%s) "
    with conn.cursor() as cursor:
        cursor.execute(query, (photoID, username))
    exists = list(cursor.fetchone().values())[0]
    return exists




@app.route("/leaveComment", methods=["POST"])
@login_required
def leaveComment():
    username = session["username"]
    photoID = request.form['photoID']
    theComment = request.form['theComment']

    if theComment == '':
        theComment = 'No Comment.'

    if (not alreadyCommented(username, photoID)):
        commenttime = datetime.datetime.today()
        query = "INSERT INTO Comments (username, PhotoID, commenttime, theComment) values (%s, %s, %s, %s)"
        with conn.cursor() as cursor:
            cursor.execute(query, (username, photoID, commenttime.strftime('%Y-%m-%d %H:%M:%S'), theComment))
    conn.commit()

    return redirect("home")


def alreadyCommented(username, photoID):
    query = "SELECT EXISTS(SELECT * FROM Comments WHERE photoID=%s AND username=%s) "
    with conn.cursor() as cursor:
        cursor.execute(query, (photoID, username))
    exists = list(cursor.fetchone().values())[0]
    return exists




@app.route('/show_posts/<username>', methods=['GET', 'POST'])
@login_required
def show_posts(username):
    user = session['username']
    cursor = conn.cursor()
    query = 'SELECT * from Photo JOIN Person WHERE photoposter = %s'
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    return render_template("/show_posts.html", photos= data)




@app.route("/view_further_info/<photoID>", methods=["GET","POST"])
@login_required
def view_further_info(photoID):
    user = session['username']
    photoID = photoID
    cursor = conn.cursor()
    query = 'SELECT firstName, lastName, postingdate, filepath FROM Photo JOIN Person ON Photo.photoPoster = Person.username WHERE photoID = %s'
    cursor.execute(query, (photoID))
    data = cursor.fetchall()
    cursor.close()

    cursor = conn.cursor ()
    tagged = 'SELECT username, firstName, lastName FROM Tagged NATURAL JOIN Person WHERE photoID = %s AND tagstatus = 1'
    cursor.execute(tagged, (photoID))
    tagData = cursor.fetchall()
    cursor.close()

    cursor = conn.cursor()
    rating = 'SELECT username, rating FROM Likes WHERE photoID = %s'
    cursor.execute(rating, (photoID))
    likeData = cursor.fetchall ()
    cursor.close()

    cursor = conn.cursor()
    count = 'SELECT COUNT(username) AS num_likes FROM Likes WHERE photoID = %s'
    cursor.execute(count, (photoID))
    countData = cursor.fetchone()
    cursor.close()

    cursor = conn.cursor()
    comments = 'SELECT username, commenttime, theComment FROM Comments WHERE photoID = %s'
    cursor.execute(comments, (photoID))
    commentData = cursor.fetchall ()
    cursor.close()



    return render_template('view_further_info.html', username=user, photo=data, tag = tagData, like = likeData, photoID=photoID, comment = commentData, likeCount = countData)


@app.route('/follow')
@login_required
def follow():
    user = session['username']
    cursor = conn.cursor()


    users_query = 'SELECT * FROM Person WHERE username != %s AND username NOT IN (SELECT username_followed FROM Follow WHERE username_follower = %s)'
    cursor.execute(users_query, (user, user))
    all_users = cursor.fetchall()
    cursor.close()

    if not all_users:
        reason = "You are already following all Finstagram users! \n You seem to be a pro user, congratulations!"
        return render_template("return_home.html", message=reason)

    return render_template('follow.html', users=all_users, username=user)


@app.route('/follow_request', methods=["POST"])
@login_required
def follow_request():
    user = session['username']
    to_be_followed = request.form['to_be_followed']
    cursor = conn.cursor()

    query = "INSERT INTO Follow(username_followed, username_follower, followstatus, acceptedFollow) VALUES (%s, %s, %s, %s)"
    cursor.execute(query, (to_be_followed, user, 0, 0))
    conn.commit()
    cursor.close()

    return redirect("/follow")

@app.route('/requests')
@login_required
def manage_follow_requests():
    user = session['username']
    cursor = conn.cursor()
    users_query = 'SELECT * FROM Person WHERE username != %s AND username IN (SELECT username_follower FROM Follow WHERE username_followed = %s AND acceptedFollow = 0)'
    cursor.execute(users_query, (user, user))
    all_users = cursor.fetchall()
    cursor.close()

    if not all_users:
        reason = "There are no new follow requests! You seem to be on top of your game"
        return render_template("return_home.html", message=reason)


    return render_template('manage.html', users=all_users, username=user)



@app.route('/follow_accept', methods=["POST"])
@login_required
def follow_accept():
    user = session['username']
    to_be_accepted = request.form['to_be_accepted']
    cursor = conn.cursor()
    query = "UPDATE Follow SET acceptedFollow = 1 WHERE username_follower = %s AND username_followed = %s"
    cursor.execute(query, (to_be_accepted, user))
    conn.commit()
    cursor.close()

    return redirect("/requests")

@app.route('/follow_decline', methods=["POST"])
@login_required
def follow_decline():
    user = session['username']
    to_be_declined = request.form['to_be_declined']
    cursor = conn.cursor()
    query = "DELETE FROM Follow WHERE username_follower = %s AND username_followed = %s"
    cursor.execute(query, (to_be_declined, user))
    conn.commit()
    cursor.close()

    return redirect("/requests")

@app.route('/unfollow')
@login_required
def unfollow():
    user = session['username']
    cursor = conn.cursor()
    users_query = 'SELECT * FROM Person WHERE username != %s AND username IN (SELECT username_followed FROM Follow WHERE username_follower = %s)'
    cursor.execute(users_query,(user, user))
    all_users = cursor.fetchall()
    cursor.close()

    if not all_users:
        reason = "You are currently not following anyone! Maybe change that?"
        return render_template("return_home.html", message=reason)


    return render_template('unfollow.html', users=all_users, username=user)


@app.route('/unfollow_action', methods=["POST"])
@login_required
def unfollow_action():
    user = session['username']
    to_be_unfollowed = request.form['to_be_unfollowed']
    cursor = conn.cursor()
    query = "DELETE FROM Follow WHERE username_followed = %s AND username_follower = %s"
    cursor.execute(query, (to_be_unfollowed, user))
    conn.commit()
    cursor.close()

    return redirect("/unfollow")

@app.route('/who_is_king')
@login_required
def who_is_king():
    user = session['username']
    king_query = "(SELECT username, Person.firstName, Person.lastName, count(username_follower) AS num_followers FROM Follow JOIN Person ON Follow.username_followed = Person.username GROUP BY username_followed, Person.firstName, Person.LastName ORDER BY count(username_follower) DESC LIMIT 1)"
    cursor = conn.cursor()
    cursor.execute(king_query)
    king_user = cursor.fetchone()
    cursor.close()
    if king_user["username"] == user:
        return render_template("you_are_the_king.html", king=king_user)


    return render_template('king.html',king=king_user)


@app.route ('/add_FriendGroup', methods=["GET","POST"])
@login_required
def add_FriendGroup():
    if request.method == 'POST':
        user = session['username']
        groupName = request.form['groupName']
        description = request.form['description']
        cursor = conn.cursor()

        try:
            create_group_query = 'INSERT INTO Friendgroup(groupOwner, groupName, description) VALUES (%s, %s, %s)'
            addtoBelong_query = 'INSERT INTO BelongTo(member_username, owner_username, groupName) VALUES (%s, %s, %s)'
            cursor.execute (create_group_query, (user, groupName, description))
            cursor.execute(addtoBelong_query, (user, user, groupName))
            conn.commit ()
            cursor.close ()
            message = "You created a Friend Group!"

        except:
            message = "You already made this group!"
        return render_template('add_FriendGroup.html', message=message)
    else:
        return render_template('add_FriendGroup.html')

@app.route ('/addFriend', methods=["GET","POST"])
@login_required
def addFriend():
    if request.method == 'POST':
        user = session['username']
        member_username = request.form['member_username']
        groupName = request.form['groupName']
        cursor = conn.cursor()

        try:
            create_group_query = 'INSERT INTO BelongTo(member_username, owner_username, groupName) VALUES (%s, %s, %s)'
            cursor.execute (create_group_query, (member_username, user, groupName))
            conn.commit()
            cursor.close ()
            message = "You added " + member_username + " to " + groupName + "!"
        except:
            message = "Did you forget?? You already added " + member_username + " into " + groupName

        return render_template('add_FriendGroup.html', message1=message)
    else:
        message = "Failed to add friend"
        return render_template('add_FriendGroup.html', message1=message)

app.secret_key = 'some key that you will never guess'
# Run the app on localhost port 5000
# debug = True -> you don't have to restart flask
# for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug=True)
