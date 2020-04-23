from os import path
import sqlite3
import hashlib
import itertools
from urllib.parse import urlsplit

from clear_print import *

class backend_database(object):
	"""docstring for backend_database"""
	def __init__(self):
		super(backend_database, self).__init__()
		#variables
		self.__catalog_cache = []
		self.__catalog_update = 0

		if(not path.exists("database/song_sql.db")):
			clsprint(self,"notice: song db not exists");
			self.__create_db__("song_scheme.sql","database/song_sql.db");
		
		if(not path.exists("database/user_sql.db")):
			clsprint(self,"notice: users db not exist")
			self.__create_db__("user_scheme.sql","database/user_sql.db");

		if(not path.exists("database/sale_sql.db")):
			clsprint(self,"notice: sales db not exist")
			self.__create_db__("sale_scheme.sql","database/sale_sql.db");

		clsprint(self,"sql opened")

	def __create_db__(self,scheme_path,sql_file_path):
		if not path.exists(scheme_path):
			return 1
		sql_connection = sqlite3.connect(sql_file_path)
		statement = sql_connection.cursor()
		sql_scheme = open(scheme_path,"r")
		for lines in sql_scheme.readlines():
			try:
				statement.execute(lines)
			except sqlite3.OperationalError as e:
				clsprint(self,"execution error on: %s lines: %s %s"%(sql_file_path,lines,e))		
		sql_connection.commit()
		sql_connection.close()

	def get_catalog(self):
		sql_connection = sqlite3.connect("database/song_sql.db")
		catalog_list = []
		statement= sql_connection.cursor()
		statement.execute("select catalog_name from catalog order by catalog_id;")
		for item in statement.fetchall():
			catalog_list.append(item[0])
		sql_connection.close()
		return catalog_list

	def get_user(self):
		conn = sqlite3.connect("database/user_sql.db")
		cursor = conn.cursor()
		cursor.execute('ATTACH DATABASE "database/sale_sql.db" AS sale')
		cursor.execute('select user.username ,link_user_role.role_id, user.password, sale.credit.credit from link_user_role join user on user.user_id = link_user_role.user_id left join sale.credit on sale.credit.user_id = link_user_role.user_id')
		userdata = [{"username": u[0],"role_id": u[1],"password": u[2],"credit": 0 if not u[3] else u[3]} for u in cursor.fetchall()]
		for a in userdata:
			print(a)

		cursor.execute('select role_id , role_name from role')
		role = [{"id": a[0],"name": a[1]} for a in cursor.fetchall()]
		conn.close()
		return {"data": userdata,"role": role}

	def update_user(self,in_json):
		conn = sqlite3.connect("database/user_sql.db")
		cursor = conn.cursor()
		for json in in_json['content']:
			if json.get('deleted'):
				cursor.execute('ATTACH DATABASE "database/sale_sql.db" AS sale')
				cursor.execute('delete from user where username = ?',(json['username'],))
				cursor.execute('delete from link_user_role where user_id not in (select user_id from user)')
				cursor.execute('delete from sale.credit where sale.credit.user_id not in (select user_id from user)')
			if json.get('update'):
				for x in json['update']:
					if x.get('role_id'):
						cursor.execute('update link_user_role set role_id = ? where user_id = (select user_id from user where username = ?)',(x['role_id'],json['username']))
					if x.get('username'):
						cursor.execute('update user set username = ? where username = ?',(x['username'],json['username']))
					if x.get('password'):
						cursor.execute('update user set password = ? where username = ?',(x['password'],json['username']))
					if x.get('credit'):
						cursor.execute('select user_id from user where username = ?',(json['username'],))
						user_id = cursor.fetchone()[0]
						temp_conn = sqlite3.connect("database/sale_sql.db")
						temp_conn.cursor().execute('update credit set credit = ? where user_id = ?',(x['credit'],user_id))
						temp_conn.commit()
						temp_conn.close()
			if json.get('new'):
				cursor.execute('insert into user (username,password) select ?,?',(json['username'],json['password']))
				conn.commit()
				cursor.execute('select user_id from user where username = ?',(json['username'],))
				user_id = cursor.fetchone()[0]
				cursor.execute('insert into link_user_role (user_id,role_id) select ?,?',(user_id,json['role_id']))
				temp_conn = sqlite3.connect("database/sale_sql.db")
				temp_conn.cursor().execute('insert into credit (credit,user_id) select ?,?',(json['credit'],user_id))
				temp_conn.commit()
				temp_conn.close()


		conn.commit()
		conn.close()
		return

	def change_pass(self,json):
		conn = sqlite3.connect("database/user_sql.db")
		cursor = conn.cursor()
		cursor.execute('update user set password = ? where username = ? and password = ? and user_id in (select user_id from link_user_role where role_id = 2)',(json['new'],json['username'],json['old']))
		conn.commit()
		data = conn.total_changes
		conn.close()
		return data

	def get_purchase_rec(self):
		conn = sqlite3.connect("database/sale_sql.db")
		cursor = conn.cursor()
		cursor.execute('ATTACH DATABASE "database/user_sql.db" AS user')
		cursor.execute('ATTACH DATABASE "database/song_sql.db" AS song')
		cursor.execute('select user.user.username , song.song.title , song.album.album_name , song.song.price , sales.purchase_time from sales \
						join song.link_album_song on sales.song_id = song.link_album_song.song_id \
						join song.album on song.album.album_id = song.link_album_song.album_id \
						join song.song on song.song.song_id = sales.song_id \
						join user.user on user.user.user_id = sales.user_id ')
		data = cursor.fetchall()
		conn.close()
		return [{"username": u[0],"title": u[1],"album": u[2],"price": u[3],"date": u[4]} for u in data]

	def del_purchase_rec(self,json):
		print(json)
		if json.get('content'):
			for x in json.get('content'):
				conn = sqlite3.connect("database/sale_sql.db")
				cursor = conn.cursor()
				cursor.execute('ATTACH DATABASE "database/user_sql.db" AS user')
				cursor.execute('ATTACH DATABASE "database/song_sql.db" AS song')
				cursor.execute('delete from sales where user_id=(select user_id from user.user where username = ?) \
								and song_id=(select song_id from song.song where title = ?)',(x['username'],x['title']))
				conn.commit()
				conn.close()
		return

	def get_user_library(self,user_id):
		conn = sqlite3.connect("database/song_sql.db")
		cursor = conn.cursor()
		cursor.execute('ATTACH DATABASE "database/user_sql.db" AS user')
		cursor.execute('ATTACH DATABASE "database/sale_sql.db" AS rec')
		cursor.execute('select distinct album_name ,image ,artist_name ,album.album_id from album \
							   join link_album_song on album.album_id = link_album_song.album_id \
							   join link_album_artist on album.album_id = link_album_artist.album_id \
							   join artist on link_album_artist.artist_id = artist.artist_id \
							   where song_id in\
							  (select song_id from rec.sales where user_id = \
							  (select user_id from user.user where username = ?))',(user_id,))
		data = cursor.fetchall()
		conn.close()
		return [{"album": u[0],"cover": u[1],"artist": u[2],"url": u[3]} for u in data]

	def user_auth(self,auth_json,admin_auth):
		user_auth = sqlite3.connect("database/user_sql.db")
		statement=user_auth.cursor()
		result = None
		if admin_auth and auth_json:
			statement.execute('SELECT user.username, role.role_id FROM link_user_role \
						   join user on \
						   user.user_id = link_user_role.user_id \
						   join role on\
						    role.role_id = link_user_role.role_id\
						    WHERE user.username=? and user.password=? and role.role_id=1;'
						    ,(auth_json['username'],auth_json['password']))
			result = statement.fetchall()
		elif auth_json:
			statement.execute('SELECT user.username FROM user \
						    WHERE user.username=? and user.password=?;'
						    ,(auth_json['username'],auth_json['password']))
			result = statement.fetchall()
		user_auth.close()
		return result

	def user_reg(self,json):
		conn = sqlite3.connect("database/user_sql.db")
		cursor = conn.cursor()
		print(json)
		data = {}
		if json.get('check'):
			cursor.execute('select 1 from user where username = ?',(json['check'],))

			data = cursor.fetchone()
			if data:
				data = {"used": 1}
			else:
				data = {"used": 0}
		elif json.get('username') and json.get('password'):
			cursor.execute('insert into user (username,password) select ?,? WHERE NOT EXISTS (select 1 from user where username = ?)',(json['username'],json['password'],json['username']))
			conn.commit()
			cursor.execute('select user_id from user where username = ?',(json['username'],))
			data = cursor.fetchone()[0]
			cursor.execute('insert into link_user_role (user_id,role_id) select ?,2 ',(data,))#role_id 2 must be normal user role_id
			if data:
				temp_conn = sqlite3.connect("database/sale_sql.db",isolation_level=None)
				temp_conn.cursor().execute('insert into credit (credit,user_id) select 0,?',(data,))
				temp_conn.close()
			conn.commit()
			data = {"add": 0}
		conn.close()
		return data

	def get_catalog_album(self,catalog_name):
		conn = sqlite3.connect("database/song_sql.db")
		cursor = conn.cursor()
		cursor.execute('select album.album_id , album_name , image ,artist_name from album \
						join link_album_artist on album.album_id = link_album_artist.album_id \
					    join artist on link_album_artist.artist_id = artist.artist_id \
						join link_catalog_album on album.album_id = link_catalog_album.album_id \
						join catalog on link_catalog_album.catalog_id = catalog.catalog_id where catalog_name = ? order by album.album_id DESC',(catalog_name,))
		data = cursor.fetchall()
		conn.close()
		return [{"album": u[1],"cover": u[2],"artist": u[3],"url": u[0]} for u in data]


	def get_album(self,album,username = None):
		conn = sqlite3.connect("database/song_sql.db")
		cursor = conn.cursor()
		cursor.execute('select album.album_name , album.image , song.title , song.duration , song.price , song.track , artist.artist_name , catalog.catalog_name , song.song_id \
					    from link_album_song join album on link_album_song.album_id = album.album_id \
					    join song on link_album_song.song_id = song.song_id \
					    join link_album_artist on album.album_id = link_album_artist.album_id \
					    join artist on link_album_artist.artist_id = artist.artist_id \
					    join link_catalog_album on album.album_id = link_catalog_album.album_id \
					    join catalog on link_catalog_album.catalog_id = catalog.catalog_id where album.album_id = ? order by song.song_id DESC',(album,))
		data = cursor.fetchall();
		conn.close()

		if username:
			temp_conn = sqlite3.connect("database/user_sql.db")
			temp_cursor = temp_conn.cursor()
			temp_cursor.execute('select user_id from user where username = ?',(username,))
			user_id = temp_cursor.fetchone()[0]
			temp_conn.close()
			temp_conn = sqlite3.connect("database/sale_sql.db")
			temp_cursor = temp_conn.cursor()


		album = {"album": data[0][0],"artist": data[0][6],"catalog": data[0][7],"track": []}
		if data[0][1]:
			album['cover'] = data[0][1]
		for track in data:
			temp = {"track": track[5],
				    "title": track[2],
				    "duration": track[3],
				    "price": track[4],
				    "url": track[8]
				    }
			if username:
				temp_cursor.execute('select 1 from sales where user_id = ? and song_id = ?',(user_id,track[8]))
				purchased = temp_cursor.fetchone()
				if purchased:
					temp['download'] = 1
			album["track"].append(temp)
		if username:
			temp_conn.close()
		return album

	def get_song(self,song):
		conn = sqlite3.connect("database/song_sql.db")
		cursor = conn.cursor()
		cursor.execute('select album.album_name , album.image , song.title , song.duration , song.price , song.track , artist.artist_name , catalog.catalog_name , song.song_id \
					    from link_album_song join album on link_album_song.album_id = album.album_id \
					    join song on link_album_song.song_id = song.song_id \
					    join link_album_artist on album.album_id = link_album_artist.album_id \
					    join artist on link_album_artist.artist_id = artist.artist_id \
					    join link_catalog_album on album.album_id = link_catalog_album.album_id \
					    join catalog on link_catalog_album.catalog_id = catalog.catalog_id where link_album_song.song_id = ?',(song,))

		data = cursor.fetchone()
		conn.close()

		album = {"album": data[0],"cover": data[1],"artist": data[6],"catalog": data[7],"track": data[5],"title": data[2],"duration": data[3],"price": data[4],"url": data[8]}
		return album

	def get_album_list(self):
		conn = sqlite3.connect("database/song_sql.db")
		cursor = conn.cursor()
		album_json = {"album_list": []}
		cursor.execute('select album.album_name , album.image , song.title , song.duration , song.price , song.track , artist.artist_name , catalog.catalog_name , album.album_id \
					    from link_album_song join album on link_album_song.album_id = album.album_id \
					    join song on link_album_song.song_id = song.song_id \
					    join link_album_artist on album.album_id = link_album_artist.album_id \
					    join artist on link_album_artist.artist_id = artist.artist_id \
					    join link_catalog_album on album.album_id = link_catalog_album.album_id \
					    join catalog on link_catalog_album.catalog_id = catalog.catalog_id')
		temp = cursor.fetchall()
		conn.close()
		for album in temp:
			current_album = None
			for check in album_json["album_list"]:
				if check["album"] == album[0] and check["artist"] == album[6]:
					current_album = check
					break
			if not current_album:
				current_album = {}
				current_album["album"] = album[0]
				current_album["artist"] = album[6]
				current_album["catalog"] = album[7]
				current_album["url"] = album[8]
				if album[1]:
					current_album['cover'] = album[1]
				current_album["track"] = []
				album_json["album_list"].append(current_album)

			current_album["track"].append({"track": album[5],
										   "title": album[2],
										   "duration": album[3],
										   "price": album[4],
										   })

		return album_json

	def get_song_by_sid(self,sid):
		conn = sqlite3.connect("database/song_sql.db")
		cursor = conn.cursor()
		cursor.execute('select path from song where song_id = ?',(sid,))
		path = cursor.fetchone()[0]
		conn.close()
		return path.split("/")[-1]

	def get_user_info(self,username):
		conn = sqlite3.connect("database/sale_sql.db")
		cursor = conn.cursor()
		cursor.execute('ATTACH DATABASE "database/user_sql.db" AS user')
		cursor.execute('select credit from credit where user_id = (select user_id from user.user where username = ?)',(username,))
		data = cursor.fetchone()
		if not data:
			cursor.execute('insert into credit (user_id,credit) select (select user_id from user.user where username = ?),0',(username,))
			conn.commit()
			cursor.execute('select credit from credit where user_id = (select user_id from user.user where username = ?)',(username,))
			data = cursor.fetchone()
		conn.close()
		return {"username": username,"credit": data[0]}

	def purchase(self,json):
		conn = sqlite3.connect("database/sale_sql.db")
		cursor = conn.cursor()
		cursor.execute('ATTACH DATABASE "database/song_sql.db" AS song')
		cursor.execute('select price from song.song where song_id = ?',(json['song_id'],))
		price = cursor.fetchone()[0]
		if json['credit'] - price > 0:
			cursor.execute('ATTACH DATABASE "database/user_sql.db" AS user')
			cursor.execute('update credit set credit = credit - ? where user_id = (select user_id from user.user where username = ?)',(price,json['user']))
			cursor.execute('insert into sales (user_id,song_id,purchase_time) select (select user_id from user.user where username = ?),?,CURRENT_TIMESTAMP',(json['user'],json['song_id']))
			conn.commit()
			cursor.execute('select user_id , song_id from sales where ROWID = ?',(cursor.lastrowid,))
			purchase_id = cursor.fetchone()
			conn.close()
			return {"song_id": json['song_id'],"purchase_id": "%s%s"%(str(purchase_id[0]).zfill(10),str(purchase_id[1]).zfill(10))}
		else:
			conn.close()
			return {'error':1}

	def check_purchase(self,json):
		conn = sqlite3.connect("database/sale_sql.db")
		cursor = conn.cursor()
		cursor.execute('ATTACH DATABASE "database/user_sql.db" AS user')
		cursor.execute('select 1 from sales where user_id = (select user_id from user.user where username = ?) and song_id = ?',(json['username'],json['song_id']))
		data = cursor.fetchone()
		conn.close()
		if data:
			return data[0]
		else:
			return None

	def save(self,data_json):
		print(data_json)
		conn = sqlite3.connect("database/song_sql.db",isolation_level=None)
		cursor = conn.cursor()
		album_info = data_json.get('album')
		catalog = data_json.get('catalog')
		album_id = 0

		if catalog:
			if len(catalog):
				for catalog_json in catalog:
					key = list(catalog_json.keys())[0]
					value = catalog_json[key]
					print(value)
					print(type(value))
					if key == "delete":
						cursor.execute('delete from catalog where catalog_name = ?',(value,))
					if key == "new":
						cursor.execute('insert into catalog (catalog_name) select ?',(value,))
					if key == "change":
						cursor.execute('update catalog set catalog_name = ? where catalog_name = ?'(value["original"],value["new"]))
		if album_info:
			for album_json_task in album_info:
				if album_json_task.get('new'):
					album_json = album_json_task.get('new')
					if not album_json.get("track") or not len(album_json.get("track")):
						return
					if not  album_json.get('album') or not album_json.get('artist') or not album_json.get('catalog'):
						return
					

					cursor.execute('select artist_id from artist where artist_name = ?',(album_json['artist'],))
					artist_id = cursor.fetchone()
					if not artist_id:
						cursor.execute('insert into artist (artist_name) select ?',(album_json['artist'],))
						cursor.execute('select artist_id from artist where ROWID = ?',(cursor.lastrowid,))
						artist_id = cursor.fetchone()
					
					cursor.execute('select album_id from album where album_name = ?',(album_json['album'],))
					album_id = cursor.fetchone()
					if not album_id:
						cursor.execute('insert into album (album_name,image) select ?,?',(album_json.get('album'),urlsplit(album_json.get('cover')).path))
						cursor.execute('select album_id from album where ROWID = ?',(cursor.lastrowid,))
						album_id = cursor.fetchone()
					
					cursor.execute('insert into link_catalog_album (catalog_id,album_id) select \
									(select catalog_id from catalog where catalog_name = ?),?',(album_json['catalog'],album_id[0]))

					cursor.execute('select ROWID from link_album_artist where album_id = ? and artist_id = ?',(album_id[0],artist_id[0]))
					linked = cursor.fetchone()
					if not linked:
						cursor.execute('insert into link_album_artist (album_id,artist_id) select ?,?',(album_id[0],artist_id[0]))
					track = 1
					for each in album_json.get('track'):
						cursor.execute('insert into song (path,title,duration,price,track) select ?,?,?,?,?',(each['path'],
																											  each['title'],
																											  int(each['duration']),
																											  each['price'],
																											  track))
						cursor.execute('select song_id from song where ROWID = ?',(cursor.lastrowid,))
						cursor.execute('insert into link_album_song (album_id,song_id) select ?,?',(album_id[0],cursor.fetchone()[0]))
				elif album_json_task.get("update"):
					album_json = album_json_task.get("update")['origin']
					new_json = album_json_task.get("update")

					artist = new_json.get("new").get('artist')
					if artist:
						cursor.execute('update artist set artist_name = ? where artist_name = ?',(artist,album_json['artist']))

					album = new_json.get("new").get('album')
					if album:
						cursor.execute('update album set album_name = ? where album_name = ?',(album,album_json['album'],))
					
					cover = new_json.get("new").get('cover')
					if cover:
						cursor.execute('update album set path = ? where album_name = ?',(cover,album_json['album'],))

					catalog = new_json.get("new").get('catalog')
					if catalog:
						cursor.execute('update link_catalog_album set catalog_id = \
										(select catalog_id from catalog where catalog_name = ?) where album_id =\
										(select album_id from album where album_name = ?)'
										,(catalog,album_json['album']))

					track = new_json.get("new").get('track')
					if track:
						for x in track:
							if x.get('price'):
								cursor.execute('update song set price = ? where song_id in \
												(select song_id from link_album_song where album_id = (select album_id from album where album_name = ?)) and track = ?'
												,(x.get('price'),album_json['album'],x.get('track')))
							if x.get('title'):
								cursor.execute('update song set title = ? where song_id in \
												(select song_id from link_album_song where album_id = (select album_id from album where album_name = ?)) and track = ?'
												,(x.get('title'),album_json['album'],x.get('track')))

							if x.get('deleted'):
								cursor.execute('select song_id from song where song_id in (select song_id from link_album_song where album_id = \
												(select album_id from album where album_name = ?)) and track = ?'
												,(album_json['album'],x.get('track')))
								song_id = cursor.fetchone()
								
								cursor.execute('delete from song where song_id in \
												(select song_id from link_album_song where album_id = (select album_id from album where album_name = ?)) and track = ?'
												,(album_json['album'],x.get('track')))
								
								cursor.execute('delete from link_album_song where album_id = (select album_id from album where album_name = ?) and song_id = ?'
												,(album_json['album'],song_id[0]))

					cursor.execute('delete from album WHERE album_id not in (select album_id from link_album_song)')

					cursor.execute('delete from link_album_artist where album_id not in (select album_id from album)')
					cursor.execute('delete from artist WHERE artist_id not in (select artist_id from link_album_artist)')

		conn.commit()
		conn.close()
		return