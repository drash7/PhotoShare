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
		fn=request.form.get('first_name')
		ln=request.form.get('last_name')
		dob=request.form.get('birth_date')
		ht=request.form.get('hometown')
		gd=request.form.get('gender')
	except:
		print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	cursor = conn.cursor()
	test =  isEmailUnique(email)
	if test:
		print(cursor.execute("INSERT INTO Users (email, password, first_name, last_name, birth_date, hometown, gender, score) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}', '{7}')".format(email, password, fn, ln, dob, ht, gd, 0)))
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
	cursor.execute("SELECT imgdata, photo_id, caption FROM Photos WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]

def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]

def getUserIdFromPhoto(photo):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id  FROM Photos WHERE photo_id = '{0}'".format(photo))
	return cursor.fetchone()[0]

def getUserScore(email):
	cursor = conn.cursor()
	cursor.execute("UPDATE Users SET score = score + 1 WHERE email = '{0}'".format(email))
	return 0

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

def isAFriend(a,b):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id2 FROM Friends WHERE user_id1 = '{0}'".format(a))
	list = cursor.fetchall()
	for i in list:
		if i == b:
			return True
	return False

def lttot(a):
	b = []
	for i in a:
		b.append(a)
	return b

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
		photo_data =imgfile.read()
		cursor = conn.cursor()
		#get the album id for the entered album
		cursor.execute('''SELECT albums_id FROM Albums WHERE name = (%s) AND user_id = (%s)''', (album, uid))
		albums_id = cursor.fetchone()
		if uid != None:
			score = getUserScore(flask_login.current_user.id)
		cursor.execute('''INSERT INTO Photos(imgdata, user_id, caption) VALUES (%s, %s, %s )''' ,(photo_data,uid, caption))
		conn.commit()
		#get the photo id for the uploaded photo
		cursor.execute('''SELECT photo_id FROM Photos WHERE imgdata= (%s) AND user_id= (%s)''', (photo_data, uid))
		photo_id = cursor.fetchone()
		for tag in tags:
			#get the tag id for the entered tag
			cursor.execute('''SELECT tag_id FROM Tags WHERE name= (%s)''',(tag))
			req_tag_id = cursor.fetchone()
			#insert the (tag, photo) tuple into Tagged
			cursor.execute('''INSERT INTO Tagged (photo_id, tag_id) VALUES (%s, %s)''',(photo_id, 1))
			cursor.execute('''UPDATE Tags SET num_used = num_used+1 WHERE tag_id = (%s)''',(1))
		return render_template('hello.html', name=flask_login.current_user.id, message='Photo uploaded!', photos=getUsersPhotos(uid),base64=base64)
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('upload.html')
#end photo uploading code


#default page
@app.route("/", methods=['GET'])
def hello():
	return render_template('hello.html', message='Welecome to Photoshare')

@app.route('/view', methods=['GET'])
def view_photos():
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, photo_id, caption FROM Photos WHERE TRUE")
	pics = cursor.fetchall()
	pics2 = []
	for i in range(len(pics)):
		cursor.execute("SELECT ctext FROM Comments WHERE photo_id = '{0}'".format(pics[i][1]))
		coma = cursor.fetchall()
		a = (pics[i])
		if len(coma) > 0:	
			for x in coma:	
				a = (a + (x))		
		pics2.append(a)
	pics3 = []
	for i in range(len(pics2)):
		cursor.execute("SELECT COUNT(user_id) FROM Likes WHERE photo_id = '{0}'".format(pics[i][1]))
		nolikes = cursor.fetchall()
		a = (pics2[i])
		if len(nolikes) > 0:
			b = nolikes
			a = (a + (b))
		pics3.append(a)
	pics4 = []
	for i in range(len(pics3)):
		cursor.execute("SELECT email FROM Users WHERE user_id IN (SELECT user_id FROM Likes WHERE photo_id = '{0}')".format(pics[i][1]))
		who = cursor.fetchall()
		abc = (pics3[i])
		if len(nolikes) > 0:
			bc = (who)
			d = ""
			for i in who:
				d = d + str(i)  
			abc = (abc + (d,))
		pics4.append(abc)
	return render_template('gallery.html', ex=pics4, base64=base64)

@app.route('/view', methods=['POST'])
def cl_photos():
	emma = []
	coma = []
	comment=request.form.get('enter')
	pic=request.form.get('picid')
	resp=request.form.get('like')
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, photo_id, caption FROM Photos WHERE TRUE")
	pics = cursor.fetchall()
	if flask_login.current_user.is_authenticated == False:
		cursor.execute("INSERT INTO Comments (ctext, photo_id,user_id) VALUES ('{0}', '{1}', '{2}')".format(comment, pic, ('1')))
		conn.commit()
		return render_template('hello.html', base64=base64, message='Comment added!')
	email1 = getUserIdFromEmail(flask_login.current_user.id)
	email2 = getUserIdFromPhoto(pic)
	if resp == 'yes':
		cursor.execute("INSERT INTO Likes (photo_id, user_id) VALUES ('{0}', '{1}')".format(pic, email1))
		conn.commit()
		return render_template('hello.html', base64=base64, message='Like added!')
	elif email1 == email2:
		return render_template('hello.html', base64=base64, message='You Cannot add a comment to your own photo')
	else:
		score = getUserScore(flask_login.current_user.id)
		cursor.execute("INSERT INTO Comments (ctext, photo_id, user_id) VALUES ('{0}', '{1}', '{2}')".format(comment, pic, email1))
		conn.commit()
		return render_template('hello.html', base64=base64, message='Comment added!')

@app.route('/top_users', methods=['GET'])
def top_users_display():
	cursor = conn.cursor()
	cursor.execute("SELECT score, email FROM Users ORDER BY score LIMIT 10")
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
		return render_template('add_friend.html', em=email)
	else:
		print("Email doesn't exist")
		return render_template('friends.html', message='No such email exists. Please try again')
	
@app.route('/finaladd', methods=['GET'])
@flask_login.login_required
def friends_final_add1():
	return render_template('Finadd_friend.html')

@app.route('/finaladd', methods=['POST'])
@flask_login.login_required
def friends_final_add2():
	try:
		email=request.form.get('email')
	except:
		print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('finaladd'))
	cursor = conn.cursor()
	test =  doesEmailExist(email)
	email1 = getUserIdFromEmail(flask_login.current_user.id)
	email2 = getUserIdFromEmail(email)
	if test:
		if email1 == email2:
			return render_template('Finadd_friend.html', message='You Cannot add yourself as a friend')
		else:
			if isAFriend(email1, email2) == True:
				return render_template('Finadd_friend.html', message='Already a Friend')
			else:
				cursor.execute("INSERT INTO Friends (user_id1, user_id2) VALUES ('{0}', '{1}')".format(email1, email2))
				conn.commit()
				return render_template('hello.html', message='friend added!')
	else:
		print("Email doesn't exist")
		return render_template('Finadd_friend.html', message='No such email exists. Please try again')
	
@app.route('/friendslist', methods=['GET'])
@flask_login.login_required
def friends_display():
	email1 = getUserIdFromEmail(flask_login.current_user.id)
	cursor = conn.cursor()
	cursor.execute("SELECT email FROM Users WHERE user_id IN (SELECT user_id2 FROM Friends WHERE user_id1 = {0})".format(email1))
	list = cursor.fetchall()
	return render_template('friend_list.html', thelist=list, base64=base64)

@app.route('/createTag', methods=['GET', 'POST'])
@flask_login.login_required
def create_tag():
	if request.method == 'POST':
		name = request.form.get('name')
		cursor = conn.cursor()
		cursor.execute("INSERT INTO Tags (num_used, name) VALUES ('{0}', '{1}')".format(0, name))
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
		cursor.execute("INSERT INTO Albums (name, user_id) VALUES ('{0}', '{1}')".format(name, user_id))
		conn.commit()
		return render_template('createdAlbum.html', name=flask_login.current_user.id, message='Album created!')
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('createAlbum.html')
		
@app.route('/comsearch', methods=['GET'])
@flask_login.login_required
def com_tem():
	return render_template('searchcom.html')
	

@app.route('/comsearch', methods=['POST'])
@flask_login.login_required
def com_tem2():
	try:
		query=request.form.get('sc')
	except:
		print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('comsearch'))
	cursor = conn.cursor()
	cursor.execute("(SELECT Comments.user_id, COUNT(Comments.user_id) FROM Comments WHERE Comments.ctext = {0} GROUP BY Comments.user_id ORDER BY COUNT(Comments.user_id))".format(query))
	userss = cursor.fetchall()
	us = []
	for i in range(len(userss)-1,-1,-1):
		cursor.execute("SELECT email FROM Users WHERE user_id = {0}".format(userss[i][0]))
		ls = cursor.fetchall()
		us.append(ls)
	return render_template('listquery.html', users2=us)

@app.route('/friendrec', methods=['GET'])
@flask_login.login_required
def rec_friends():
	user_id = getUserIdFromEmail(flask_login.current_user.id)	
	cursor = conn.cursor()
	cursor.execute("(SELECT F.user_id2, COUNT(F.user_id2) FROM Friends F WHERE F.user_id1 IN (SELECT F2.user_id2 FROM Friends F2 WHERE F2.user_id1 = {0}) AND F.user_id2 <> {0} GROUP BY F.user_id2 HAVING COUNT(F.user_id2)>1 ORDER BY COUNT(F.user_id2))".format(user_id))
	fflist = cursor.fetchall()
	flist = []
	for i in range(len(fflist)-1,-1,-1):
		cursor.execute("SELECT email FROM Users WHERE user_id = {0}".format(fflist[i][0]))
		alist = cursor.fetchall()
		aa = (alist[0])
		flist.append(aa)

		
	return render_template('recfriends.html', ll = flist)
	
if __name__ == "__main__":
	#this is invoked when in the shell  you run 
	#$ python app.py
	app.run(port=5000, debug=True)