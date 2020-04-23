from flask import Flask , render_template, flash, request, redirect, url_for ,send_file ,jsonify, send_from_directory , make_response
from flask_bootstrap import Bootstrap
import os
import json
import secrets
import time
import shutil
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

from db import backend_database
from media import media_process
from clear_print import *

#debug
import sys

UPLOAD_FOLDER = 'media/'
ALLOWED_EXTENSIONS = {'mp3', 'flac', 'alac', 'dsf', 'dff','m4a','tak','ogg','opus'}
LIST_VIEW_MAX = 15

class web_backend(object):
	"""docstring for web_backend"""
	def __init__(self):
		super(web_backend, self).__init__()
		self.__db_conn = backend_database()
		self.catalog_list = self.__db_conn.get_catalog()

		self.front_data = []

		self.token =[]

	def user_auth(self,json,admin = 0):
		return self.__db_conn.user_auth(json,admin)

	def user_reg(self,json):
		return self.__db_conn.user_reg(json)

	def savetodb(self,json):
		return self.__db_conn.save(json)

	def get_album_list(self):
		return self.__db_conn.get_album_list()

	def update_user(self,json):
		return self.__db_conn.update_user(json)

	def refreshcatalog(self):
		self.catalog_list = self.__db_conn.get_catalog()
		self.frontpagedata()

		self.nav_item = [(a,'catalog',{'catalog_name': a}) for a in self.catalog_list]
		self.nav_item.insert(0,("Home","base",{'': None}))

	def get_user(self):
		return self.__db_conn.get_user()

	def get_catalog_album(self,catalog_name):
		return self.__db_conn.get_catalog_album(catalog_name)

	def get_purchase_rec(self):
		return self.__db_conn.get_purchase_rec()

	def del_purchase_rec(self,json):
		return self.__db_conn.del_purchase_rec(json)

	def change_pass(self,json):
		return self.__db_conn.change_pass(json)

	def frontpagedata(self):
		temp = self.get_album_list()
		catalog = []
		search = []
		for x in self.catalog_list:
			search.append(x)
			catalog.append({"title": x,"content": []})
		for y in temp['album_list']:
			catalog[search.index(y['catalog'])]['content'].append({"cover": y.get("cover"),"album": y['album'],"artist": y['artist'],"url": y['url']})
		
		self.front_data = catalog

	def get_content(self,album,username = None):
		return self.__db_conn.get_album(album,username)

	def get_song_detail(self,song):
		return self.__db_conn.get_song(song)

	def purchase(self,json):
		return self.__db_conn.purchase(json)

	def gen_token(self,data):
		token = secrets.token_hex()
		for entry in self.token:
			if entry['username'] == data[0]:
				self.token.remove(entry)
		if len(data) == 2:
			self.token.append({"token": token,"username": data[0],"role": data[1]})
		else:
			self.token.append({"token": token,"username": data[0]})
		return token

	def check_purchase(self,json):
		data = self.__db_conn.check_purchase(json)
		if data:
			return 1
		return 0

	def library_view(self,username):
		return self.__db_conn.get_user_library(username)
	
	def get_song_path(self,sid):
		return self.__db_conn.get_song_by_sid(sid)

	def checkuser(self,user_token):
		username = None
		if user_token:
			for token in self.token:
				if token['token'] == user_token:
					return self.__db_conn.get_user_info(token['username'])
		return


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

secret = secrets.token_hex()
		
nav_manage=[("Song Management","manage",{'': None}),("Sales Record","manage_sale",{'': None}),("User Management","manage_user",{'': None})]

app = Flask(__name__)

@app.route('/management/login.html', methods=['GET','POST'])
def login():
	user_token = request.cookies.get('auth')
	if user_token:
		auth = 0
		for token in back.token:
			if token['token'] == user_token:
				auth = 1
				break
		if auth:
			return redirect(url_for('manage'))
	if request.method == 'POST':
		auth_json = request.get_json()
		userdata = back.user_auth(auth_json,1)
		if len(userdata):
			resp = make_response(redirect(url_for('manage')))
			resp.set_cookie('auth', back.gen_token(userdata[0]) )
			return resp
	return render_template("management_login.html",title="Login")

@app.route('/management/save', methods=['POST'])
def savetodb():
	auth = 0
	user_token = request.cookies.get('auth')
	if not user_token:
		return redirect(url_for('login'))
	for token in back.token:
		if token['token'] == user_token:
			auth = 1
			break
	if not auth:
		return redirect(url_for('login'))
	if request.method == 'POST':
		changes = request.get_json()
		back.savetodb(changes)
		back.refreshcatalog()
		pass
	return redirect(url_for('manage'))

@app.route('/management/' , methods=['GET', 'POST']) #this should not bind to public ip
@app.route('/management/index.html' ,methods=['GET', 'POST'])
def manage():
	auth = 0
	user_token = request.cookies.get('auth')
	if not user_token:
		return redirect(url_for('login'))
	for token in back.token:
		if token['token'] == user_token:
			auth = 1
			break
	if not auth:
		return redirect(url_for('login'))
	if request.method == 'POST':
	    # check if the post request has the file part
	    if 'file' not in request.files:
	        print('No file part')
	        return redirect(request.url)
	    file = request.files['file']
	    if file.filename == '':
	        print('No selected file')
	        return redirect(request.url)
	    print(file.filename)
	    if file: #and allowed_file(file.filename):
	    	print("saving")
	    	filename = time.strftime("%Y%m%d-%H%M%S")+file.filename
	    	file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
	    	info = media_process(os.path.join(app.config['UPLOAD_FOLDER'], filename))
	    	info["path"] = os.path.join(app.config['UPLOAD_FOLDER'], filename)
	    	if not info.get("title"):
	    		info['title'] = filename
	    	return jsonify(info)
	else:
		catalog_list = back.catalog_list;
		user_token = request.cookies.get('auth')
		username = back.checkuser(user_token)
		return render_template("management.html",
							nav_item={"item": nav_manage,"username": username},
							management = 1,
							catalog_list=json.dumps(catalog_list),
							album_list = json.dumps(back.get_album_list()))


@app.route('/management/upload/cover' , methods=['POST'])
def upload_img():
	auth = 0
	user_token = request.cookies.get('auth')
	if not user_token:
		return redirect(url_for('login'))
	for token in back.token:
		if token['token'] == user_token:
			auth = 1
			break
	if not auth:
		return redirect(url_for('login'))


	if request.method == 'POST':
	    # check if the post request has the file part
	    if 'file' not in request.files:
	        print('No file part')
	        return redirect(request.url)
	    file = request.files['file']
	    if file.filename == '':
	        print('No selected file')
	        return redirect(request.url)
	    print(file.filename)
	    if file: #and allowed_file(file.filename):
	    	print("saving")
	    	filename = time.strftime("%Y%m%d-%H%M%S")+file.filename
	    	file.save(os.path.join(app.config['UPLOAD_FOLDER']+"img/", filename))
	    return url_for('uploaded_img',filename=filename)

@app.route('/management/user', methods=['GET','POST'])
def manage_user():
	auth = 0
	user_token = request.cookies.get('auth')
	if not user_token:
		return redirect(url_for('login'))
	for token in back.token:
		if token['token'] == user_token:
			auth = 1
			break
	if not auth:
		return redirect(url_for('login'))

	if request.method == 'POST':
		upd_json = request.get_json()
		back.update_user(upd_json)
		return url_for('manage_user')

	return render_template("management_user.html",
							nav_item={"item": nav_manage,"username": back.checkuser(user_token)},
							management = 1,
							user=back.get_user())

@app.route('/management/sale', methods=['GET','POST'])
def manage_sale():
	auth = 0
	user_token = request.cookies.get('auth')
	if not user_token:
		return redirect(url_for('login'))
	for token in back.token:
		if token['token'] == user_token:
			auth = 1
			break
	if not auth:
		return redirect(url_for('login'))

	if request.method == 'POST':
		json = request.get_json()
		back.del_purchase_rec(json)
		return url_for('manage_sale')

	return render_template("management_sales.html",
							nav_item={"item": nav_manage,"username": back.checkuser(user_token)},
							management = 1,
							user=back.get_user(),
							data = back.get_purchase_rec())

@app.errorhandler(404)
def invalid_page(e):
	home_url = url_for('base')
	return render_template("404.html",
							title = 'Page Not Found',
							nav_item={"item": back.nav_item,"hideuser": 1},
							url=home_url)

@app.route('/change_pass', methods=['GET','POST'])
def password():
	if request.method == 'POST':
		user_token = request.cookies.get('login_token')
		userdata = back.checkuser(user_token)
		json = request.get_json()
		json["username"] = userdata['username']
		if json.get("old") and json.get("new"):
			result = back.change_pass(json)
			return str(result)
	
	user_token = request.cookies.get('login_token')
	userdata = back.checkuser(user_token)
	if userdata:
		data = back.library_view(userdata['username'])
		return render_template("password.html",
						title = 'Change Password',
						nav_item={"item": back.nav_item,"username": userdata}) 
	return render_template("login.html",
							title= 'Login',
							login= 1,
							url = url_for('library'))

@app.route('/album/<int:album>')
def album_page(album):
	user_token = request.cookies.get('login_token')
	username = back.checkuser(user_token)
	if username:
		data = back.get_content(album,username.get("username"))
	else:
		data = back.get_content(album)
	data['cover'] = "http://localhost:5000"+data['cover']
	return render_template("content.html",
							title = 'Content',
							nav_item={"item": back.nav_item,"username": username},
							content=data
							)

@app.route('/library')
def library():
	user_token = request.cookies.get('login_token')
	userdata = back.checkuser(user_token)
	if userdata:
		data = back.library_view(userdata['username'])
		return render_template("library.html",
						title = "Library",
						data = data,
						nav_item={"item": back.nav_item,"username": userdata}
						)
	return render_template("login.html",
							title= 'Login',
							login= 1,
							url = url_for('library'))

@app.route('/catalog/<catalog_name>')
def catalog(catalog_name):
	data = back.get_catalog_album(catalog_name)
	user_token = request.cookies.get('login_token')
	userdata = back.checkuser(user_token)
	new_content = 0
	return render_template("catalog.html",
						title = catalog_name,
						carousel_list = data,
						nav_item={"item": back.nav_item,"username": userdata},
						album_list=[{"title":catalog_name,"content":data}],
						data=data,
						entry_limit=3,
						nav_patch = 1
						)


@app.route('/uploads/<filename>')
def uploaded_img(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER']+"img/",
                               filename)

@app.route('/download/<song_id>')
def download_song(song_id):
	user_token = request.cookies.get('login_token')
	userdata = back.checkuser(user_token)
	if userdata:
		check = back.check_purchase({"username": userdata['username'],"song_id": song_id})
		if check:
			path = back.get_song_path(song_id)#song_id
			return send_from_directory(app.config['UPLOAD_FOLDER'],path)
	
	home_url = url_for('base')
	return render_template("404.html",
							title = 'Page Not Found',
							nav_item={"item": back.nav_item,"hideuser": 1},
							url=home_url)

@app.route('/', methods=['GET','POST']) #this should bind to public ip
@app.route('/index.html', methods=['GET','POST'])
def base():
	if request.method == 'POST':
		auth_json = request.get_json()
		userdata = back.user_auth(auth_json)
		if len(userdata):
			resp = make_response(url_for('base'))
			resp.set_cookie('login_token', back.gen_token(userdata[0]) )
			return resp
	else:
		user_token = request.cookies.get('login_token')
		username = back.checkuser(user_token)
		carousel_data = []
		for a in back.front_data:
			if len(a['content']):
				temp={}
				if a['content'][0].get('url'):
					temp["url"] = a['content'][0]['url']
				else:
					temp["url"] = "/static/img/nocover.jpg"
				temp["cover"]	= a['content'][0]['cover']
				temp["album"]	= a['content'][0]['album']
				temp["artist"]	= a['content'][0]['artist']
				carousel_data.append(temp)
		return render_template("index.html",
							   title = 'Online Store',
							   nav_item={"item": back.nav_item,"username": username},
							   carousel_list=carousel_data,
							   album_list=back.front_data,
							   entry_limit=3,
							   more_btn = 1)

@app.route('/purchase/<song>', methods=['GET','POST'])
def purchase(song):
	if request.method == 'POST':
		purchase_json = request.get_json()
		if purchase_json.get("user"):
			info = back.checkuser(purchase_json['user'])
			if not info:
				return render_template(url_for('user_login'))
			check = back.check_purchase({"username": info['username'],"song_id": song})
			if not check:
				purchase = back.purchase({"user": info['username'],"song_id": song,"credit": info['credit']})
				if not purchase.get('error'):
					down_url = url_for('download_song',song_id = song)
					return render_template("purchase_success.html",
											title = 'Purchase',
										    nav_item={"item": back.nav_item,"username": back.checkuser(purchase_json['user'])},
											song_info = back.get_song_detail(purchase['song_id']),
											pid = purchase["purchase_id"],
											url = down_url) 
	user_token = request.cookies.get('login_token')
	username = back.checkuser(user_token)
	purchased= 0
	if username:
		purchased = back.check_purchase({"username": username['username'],"song_id": song})
	return render_template("purchase.html",
						   title = 'Purchase',
						   nav_item={"item": back.nav_item,"username": username},
						   data=back.get_song_detail(song),
						   purchased = purchased)

@app.route('/success.html')
def success():
	return render_template("purchase_success.html")

@app.route('/login.html', methods=['GET','POST'])
def user_login():
	if request.method == 'POST':
		auth_json = request.get_json()
		userdata = back.user_auth(auth_json)
		if len(userdata):
			resp = make_response(url_for('base'))
			resp.set_cookie('login_token', back.gen_token(userdata[0]) )
			return resp
	return render_template("login.html",
							title= 'Login',
							login= 1)

@app.route('/register.html', methods=['GET','POST'])
def register():
	if request.method == 'POST':
		data_json = request.get_json()
		data = back.user_reg(data_json)
		if data.get('add'):
			userdata = back.user_auth(data_json)
			if len(userdata):
				resp = make_response(url_for('base'))
				resp.set_cookie('login_token', back.gen_token(userdata[0]) )
				return resp
		else:
			return data
	return render_template("register.html",
							nav_item={"item": back.nav_item,"hideuser": 1},
							title= 'Register')

bootstrap = Bootstrap(app)

if __name__ == '__main__':
	back = web_backend()
	back.get_album_list()
	back.frontpagedata()
	back.refreshcatalog()
	app.secret_key = secret
	app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
	app.run(debug=1,host= '0.0.0.0')