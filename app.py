######################################
# author ben lawson <balawson@bu.edu>
# Edited by: Craig Einstein <einstein@bu.edu>
######################################
# Some code adapted from
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

import flask
from flask import Flask, Response, flash, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
import flask_login

#for image uploading
import os, base64

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'KrispyKreme99'
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users")
users = cursor.fetchall()

def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email from Users")
	return cursor.fetchall()

class User(flask_login.UserMixin):
	pass

@login_manager.user_loader
def user_loader(email):
	users = getUserList()
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	return user

@login_manager.request_loader
def request_loader(request):
	users = getUserList()
	email = request.form.get('email')
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	cursor = mysql.connect().cursor()
	cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
	pwd = str(data[0][0] )
	user.is_authenticated = request.form['password'] == pwd
	return user

'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return '''
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
	#The request method is POST (page is recieving data)
	email = flask.request.form['email']
	cursor = conn.cursor()
	#check if email is registered
	if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
		data = cursor.fetchall()
		pwd = str(data[0][0] )
		if flask.request.form['password'] == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('hello.html', message='Logged out')

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html')

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
	return render_template('register.html', supress='True')

@app.route("/register", methods=['POST'])
def register_user():
	try:
		email=request.form.get('email')
		password=request.form.get('password')
	except:
		print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	cursor = conn.cursor()
	test =  isEmailUnique(email)
	if test:
		print(cursor.execute("INSERT INTO Users (email, password) VALUES ('{0}', '{1}')".format(email, password)))
		conn.commit()
		#log user in
		user = User()
		user.id = email
		flask_login.login_user(user)
		return render_template('hello.html', name=email, message='Account Created!')
	else:
		print("couldn't find all tokens")
		flask.flash('Error: Email already exists. Please try logging in or Using another email to register:')
		return flask.redirect(flask.url_for('register'))

def getUsersPhotos(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]

def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id  FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]

def getUserAlbums(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT name, albums_id FROM Album WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall()

def getUserScore(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]

def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)):
		#this means there are greater than zero entries with that email
		return False
	else:
		return True
#end login code

def doesEmailExist(email):
    	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)):
		#this means there are greater than zero entries with that email
		return True
	else:
		return False

@app.route('/profile')
@flask_login.login_required
def protected():
	return render_template('hello.html', name=flask_login.current_user.id, message="Here's your profile")

#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		imgfile = request.files['photo']
		caption = request.form.get('caption')
		tag_blob = request.form.get('tags')
		tags = tag_blob.split(' ')
		album = request.form.get('album')
		photo_data = imgfile.read()
		cursor = conn.cursor()
		currentscore = getUserScore(flask_login.current_user.id)
		flask_login.current_user.id = currentscore + 1
		#get the album id for the entered album
		cursor.execute('''SELECT albums_id FROM Albums WHERE name=%s AND user_id=%s''', (album, uid))
		albums_id = cursor.fetchone()
		#insert the uploaded picture and its associated information into Pictures
		cursor.execute('''INSERT INTO Pictures (imgdata, user_id, caption, albums_id) VALUES (%s, %s, %s, %s)''' ,(photo_data,uid, caption, albums_id))
		conn.commit()
		#get the photo id for the uploaded photo
		cursor.execute('''SELECT photo_id FROM Pictures WHERE imgdata=%s AND user_id=%s''', (photo_data, uid))
		photo_id = cursor.fetchone()
		for tag in tags:
			#get the tag id for the entered tag
			cursor.execute('''SELECT tag_id FROM Tags WHERE name=%s''', (tag))
			req_tag_id = cursor.fetchone()
			#insert the (tag, photo) tuple into Tagged
			cursor.execute('''INSERT INTO Tagged (photo_id, tag_id) VALUES (%s, %s)''', (photo_id, req_tag_id))
		return render_template('hello.html', name=flask_login.current_user.id, message='Photo uploaded!', photos=getUsersPhotos(uid),base64=base64)
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('upload.html')
#end photo uploading code


#default page
@app.route("/", methods=['GET'])
def hello():
	return render_template('hello.html', message='Welecome to Photoshare')

@app.route('/createTag', methods=['GET', 'POST'])
@flask_login.login_required
def create_tag():
	if request.method == 'POST':
		name = request.form.get('name')
		cursor = conn.cursor()
		cursor.execute('''INSERT INTO Tags (name) VALUES (%s)''' ,(name))
		conn.commit()
		return render_template('createdTag.html', name=flask_login.current_user.id, message='Tag created!')
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('createTag.html')

@app.route('/createAlbum', methods=['GET', 'POST'])
@flask_login.login_required
def create_album():
	if request.method == 'POST':
		name = request.form.get('name')
		user_id = getUserIdFromEmail(flask_login.current_user.id)
		cursor = conn.cursor()
		cursor.execute('''INSERT INTO Albums (name, user_id) VALUES (%s, %s)''' ,(name, user_id))
		conn.commit()
		return render_template('createdAlbum.html', name=flask_login.current_user.id, message='Album created!')
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('createAlbum.html')

@app.route('/deleteAlbum', methods=['GET', 'POST'])
@flask_login.login_required
def delete_album():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		name = request.form.get('name')
		cursor = conn.cursor()
		cursor.execute('''SELECT albums_id FROM Albums WHERE album_name = %s AND user_id = %s''', (name, uid))
		req_id = cursor.fetchone()
		cursor.execute('''DELETE * FROM Pictures WHERE albums_id = %s''', (req_id))
		cursor.commit()
		cursor.execute('''DELETE FROM Albums WHERE albums_id = %s''', (req_id))
		cursor.commit()
		return render_template('albumDeleted.html', name=flask_login.current_user.id, message='Album deleted!')
	else:
		return render_template('deleteAlbum.html')

@app.route('/view', methods=['GET'])
def view_photos():
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, photo_id, caption FROM Pictures WHERE TRUE")
	pics = cursor.fetchall()
	return render_template('gallery.html', photos=pics, base64=base64)

def fetch_my_photos_with_tags(tag):
	uid = getUserIdFromEmail(flask_login.current_user.id)
	cursor = conn.cursor()
	cursor.execute('''SELECT tag_id FROM Tags WHERE name = %s''', (tag))
	tag_id = cursor.fetchone()
	cursor.execute('''SELECT photo_id FROM Tagged WHERE tag_id = %s''', (tag_id))
	photo_ids = cursor.fetchall()
	photos = []
	for id in photo_ids:
		cursor.execute('''SELECT imgdata, photo_id, caption FROM Pictures WHERE photo_id  = %s AND user_id = %s''', (id, uid))
		photos.append(cursor.fetchone())
	return photos

def fetch_photos_with_tags(tag):
	cursor = conn.cursor()
	cursor.execute('''SELECT tag_id FROM Tags WHERE name = %s''', (tag))
	tag_id = cursor.fetchone()
	cursor.execute('''SELECT photo_id FROM Tagged WHERE tag_id = %s''', (tag_id))
	photo_ids = cursor.fetchall()
	photos = []
	for id in photo_ids:
		cursor.execute('''SELECT imgdata, photo_id, caption FROM Pictures WHERE photo_id  = %s''', id)
		photos.append(cursor.fetchone())
	return photos

@flask_login.login_required
@app.route('/mytaggedphotos', methods=['GET'])
def get_photos_with_tag():
	tags = request.form.get('tags').split(' ')
	photos = []
	for tag in tags:
		photos.append(fetch_my_photos_with_tags(tag))
	return render_template('display.html', photos=photos, base64=base64)

@app.route('/alltaggedphotos', methods=['GET'])
def get_my_photos_with_tag():
	tags = request.form.get('tags').split(' ')
	photos = []
	for tag in tags:
		photos.append(fetch_photos_with_tags(tag))
	return render_template('display.html', photos=photos, base64=base64)

@app.route('/top_users', methods=['GET'])
def top_users_display():
	cursor = conn.cursor()
	cursor.execute("SELECT score, user_id FROM Users ORDER BY score LIMIT 10")
	topten = cursor.fetchall()
	return render_template('topusers.html', rows=topten, base64=base64)

@app.route('/add_friends', methods=['GET'])
@flask_login.login_required
def adding_friends():
	return render_template('friends.html', supress='True')

@app.route("/add_friends", methods=['POST'])
@flask_login.login_required
def search_friends():
	try:
		email=request.form.get('email')
	except:
		print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('add_friends'))
	cursor = conn.cursor()
	test =  doesEmailExist(email)
	if test:
		return render_template('add_friend.html', name=email)
	else:
		print("Email doesn't exist")
		return render_template('friends.html', message='No such email exists. Please try again')
		
@app.route('/friendslist', methods=['GET'])
@flask_login.login_required
def friends_display():
	cursor = conn.cursor()
	cursor.execute("SELECT user_id2 FROM Friends")
	list = cursor.fetchall()
	return render_template('friend_list.html', thelist=list, base64=base64)

if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=5000, debug=True)
