var upload_list = [];
var catalog_list=[];
var album_editor_list =[];
var catalog_template = null;
var catalog_editor_list = null;
var upload_template = null;
var album_editor_area = null;
var album_edit_template = null;
var upload_cover = null;
var current_album = null;
var send = {"album":[],"catalog":[]};
var album_img_uploaded = 0;
var album_list_view_root = null;
var album_list_view_template = null;
var album_list_view_list = [];

function addcatalog(){
	new catalog_class();
}

function gen_list(){
	console.log(album_list_data["album_list"])
    for (var album_list_entry of album_list_data["album_list"])
      new album_list_view(album_list_entry);
}

function set_cover_upload(){
	upload_cover = document.getElementById('album_cover');
	var cover_upload_btn = document.getElementById('upload_cover_template').cloneNode(1);
	cover_upload_btn.style.display = "flex";
	upload_cover.img = upload_cover.getElementsByTagName('img')[0];
	upload_cover.img.src = "";
	album_img_uploaded = 0;
	upload_cover.img.style.display = "none";
	upload_cover.appendChild(cover_upload_btn);
	upload_cover.upload = new file_upload(cover_upload_btn);
	upload_cover.upload.url = "/management/upload/cover";
	upload_cover.upload.xhr.responseType = '';
	upload_cover.upload.input.accept = "image/*";

	upload_cover.upload.received_function = ()=> {
		if (!upload_cover.upload.xhr.response) return;
		console.log(upload_cover.upload.xhr.response);
		upload_cover.img.src = upload_cover.upload.xhr.response;
		album_img_uploaded = 1;
		upload_cover.img.style.display = "block";
	}
}

function prepare_send(){
	if (album_editor_list.length) var result = current_album.result();
	if (result == "error") {}
	catalog_send();
	console.log(send);
	json = new json_upload(send,"/management/save");
	json.__proto__.onreceive = (xhr)=>{
		window.location.href = window.location.href
	}
	json.send();
	send = {"album":[],"catalog":[]};
}

function newalbum(json){
	document.getElementById("album_editor_area").style.display = "flex";
	if (current_album) {
		if (current_album.result() == "error") {document.getElementById('album_editor_alert').style.display = "flex"; return;}
	}
	current_album = new album(json);
}

function catalog_send(){
	for (var tmp of catalog_list){
		tmp.result();
	}
}

function search(element){
	var criteria = element.value;
	for (var album_result of album_list_view_list){
		var found = 0
		if (album_result.album_json['album'].search(criteria) == -1) 
			if (album_result.album_json['artist'].search(criteria) == -1)
				found = 0; else found = 1;
		else  found = 1;

		if (!found) album_result.element.style.display = "none";
		else album_result.element.style.display = "flex";
	}
}

//----------class--------------------------------

class album_list_view {
	constructor(album_json) {
		if (!album_list_view_root) album_list_view_root = document.getElementById('album_list_viewer_root');
		if(!album_list_view_template) album_list_view_template = document.getElementById('album_list_view_template');
		this.element = album_list_view_template.cloneNode(1);
		this.element.style.display = "flex";
		album_list_view_list.push(this);
		var img = this.element.getElementsByTagName('img')[0];
		if (album_json['cover']) {
			img.src = album_json['cover'];
		}else{
			img.style.display = "none";
		}
		this.text_album = this.element.getElementsByClassName("album_list_view_album")[0];
		this.text_artist = this.element.getElementsByClassName("album_list_view_artist")[0];
		this.text_album.innerHTML = album_json['album'];
		this.text_artist.innerHTML = album_json['artist'];
		this.album_json = album_json;
		album_list_view_root.appendChild(this.element);

		var self = this;
		this.element.addEventListener('click',()=>{
			console.log(self.album_json)
			newalbum(self.album_json);
		})
	}
}

class catalog_class {
	constructor(catalog) {
		if (!catalog_template) {
			catalog_template = document.getElementById("catalog_editor_template");
			catalog_editor_list = document.getElementById("catalog_editor_div");
		}
		catalog_list.push(this);
		this.catalog = catalog;
		this.new;
		this.deleted;
    	this.block = catalog_template.cloneNode(true);
    	this.block.style.display = "flex";
    	this.input = this.block.firstElementChild;
    	this.new = 0;
    	if (this.catalog) {
    		this.input.defaultValue = this.catalog;
    		this.input.value = this.catalog;
    	}
    	else this.new = 1;
    	this.deleted = 0;
    	this.del_custom;
    	var btn = this.block.getElementsByTagName("button")[0];
    	catalog_editor_list.appendChild(this.block);

		var self = this;
		this.input.addEventListener('change',()=>{
			self.catalog = self.input.value;
			self.change_custom();
		});
    	btn.addEventListener('click', () => {self.del()});

  	}

  	del() {
  		this.block.style.display = "none";
  		this.deleted = 1;
  		if (this.new) catalog_list = catalog_list.filter(item => item !== this);
  		var self = this;
  		self.del_custom();
  	}

  	del_custom() {
  		return
  	}

  	change_custom() {
  		return;
  	}

  	result(){
  		if (this.deleted) {
  			send['catalog'].push({"delete":this.input.defaultValue});
  		}else if (this.new) {
  			send['catalog'].push({"new":this.input.value});
  		}else if(this.input.defaultValue !=	this.input.value && this.input.value){
  			for (var x of catalog_list){
  				if (x != this) {
  					if (this.input.value == x.input.value) {
  						return
  					}
  				}
  			}
  			send['catalog'].push({"change": {"original": this.input.defaultValue,"new": this.input.value}});
  		}
  	}
}

class json_upload {
	constructor(json,url = null){
		this.json = json;
		this.connection = new XMLHttpRequest();
		if (!url) this.url = window.location.href;
		else this.url = url;
	}

	send(){
		this.connection.open('POST', this.url);
		this.connection.setRequestHeader('Content-Type', 'application/json;charset=UTF-8');
		var self = this;
		this.connection.onreadystatechange = ()=>{
			self.onreceive(this);
		}
		this.connection.send(JSON.stringify(this.json));
	}

	onreceive(){
		return;
	}
}

class file_upload {
	constructor(upload_element = null) {
		this.custom = 0;
		if (!upload_element){
			if (!album_editor_area) album_editor_area = document.getElementById('album_edit_area');
			if (!upload_template) upload_template = document.getElementById("upload_template");
			this.element = upload_template.cloneNode(1);
			this.element.style.display = "block";
			album_editor_area.appendChild(this.element);
			this.album_edit = this.element.getElementsByClassName("album_edit")[0];

			upload_list.push(this);
		}else{
			this.element = upload_element;
		}
		this.upload_btn = this.element.getElementsByClassName("btn")[0];
		this.progressbar = this.element.getElementsByClassName("progress-bar")[0];
		this.progressdiv = this.element.getElementsByClassName("upload_progress")[0];
		this.xhr = new XMLHttpRequest();
		this.xhr.responseType = 'json';
		this.url = window.location.href
		this.input = document.createElement('input');
		this.input.type = 'file';
		this.input.accept = "audio/*,.dff,.dsf,.opus,.tak,.acc,.m4a";
		var self = this;
		this.upload_btn.addEventListener('click',()=>{self.onclick_event();});
  	}

  	onclick_event(){
  		var self = this;
	    this.input.addEventListener('change', ()=>{self.upload();});
	    this.input.click();
  	}

	upload(){
		if (!this.input.value) return;

		this.upload_btn.style.display = 'none';
		this.progressdiv.style.display = "flex";
		var self = this;
	    this.xhr.upload.addEventListener("progress", this.progress.bind(self) , false);
		var form = new FormData();
		form.append('file', this.input.files[0]);
		this.xhr.open("POST", this.url , true);

		this.xhr.onreadystatechange = function() {
			self.received_function(self);
		}
	    this.xhr.send(form);

	}

	progress (e){
	    if (e.lengthComputable) {
	    	var precent = String(parseInt(e.loaded/e.total*100));
	    	this.progressbar.style.width = precent+'%';
	    	this.progressbar.innerHTML = precent+'%';
		}
	}

	received_function (self){
		if (!self.xhr.response) return;

		self.progressdiv.style.display = 'none';
		self.result = new album_editor(self.xhr.response);
		upload_btn_element = new file_upload();
	}
}

class album{
	constructor(json){  					
		//if load data
		set_cover_upload();
		this.new = 0;
		this.cover_upload = document.getElementById('upload_cover_template');
		var cata_selector = document.getElementsByClassName("catalog_selector")[0];
		cata_selector.innerHTML = "";

		if (album_editor_list) {
			for (var editor_entry of album_editor_list){
				editor_entry.remove()
			}
		}
		album_editor_list =[];


		for(var catalog_item of catalog_list){
			catalog_item.__proto__.del_custom = ()=>{
				cata_selector.innerHTML = "";
				for (var catalog_name of catalog_list){
					if (catalog_name.deleted) continue;
					var selector_option = document.createElement("option");
					selector_option.innerHTML = catalog_name.catalog;
					cata_selector.appendChild(selector_option);
				}
			}

			if (catalog_item.deleted) continue;

			var selector_option = document.createElement("option");
			selector_option.innerHTML = catalog_item.catalog;
			cata_selector.appendChild(selector_option);

		}
		addcatalog = ()=>{
			var temp = new catalog_class();
			temp.change_custom = ()=>{
				var self = temp;
				cata_selector.innerHTML = "";
				for (var catalog_name of catalog_list){
					if (catalog_name.deleted) continue;
					var catalog_option = document.createElement("option");
					catalog_option.innerHTML = catalog_name.catalog;
					console.log(catalog_name.catalog)
					cata_selector.appendChild(catalog_option);
				}
			}
		}

		this.artist_field = document.getElementById("artist_input");
		this.album_name_field = document.getElementById("album_input");
		if (json) {

			this.json = json;
			console.log(document.getElementById("artist_input"));
			if (json['artist']) {
				this.artist_field.value = json['artist'];
			}
			if (json['album']) {
				this.album_name_field.value = json['album'];
			}

			this.album_name = json['album'];			//json {'album name'
			this.album_img  = json['cover'];	
			console.log(this.album_img)		//	   'album img'
			if (this.album_img) {
				this.cover_upload.remove();
				upload_cover.img.style.display = "block";
				upload_cover.img.src = this.album_img;
			}
			this.album_catalog = json['catalog'];	//     'album catalog'
			var option_index = 0;
			for(var options of document.getElementsByClassName("catalog_selector")[0].options){
				console.log(options.innerHTML,this.album_catalog,option_index)
				if (options.innerHTML == this.album_catalog) break;
				option_index++;
			}
			if (option_index+1 > document.getElementsByClassName("catalog_selector")[0].options.length) {
				option_index = -1;
			}
			this.album_artist = json['artist'];		//	   'album artist'
			this.track = json['track'];	
			for(var x of this.track){
				new album_editor(x);
			}			//	   'album track [{'path','title','price',duration'}]}

		}else{
			this.new = 1;
			this.album_name = null;
			this.album_img = null;
			this.album_catalog = null;
			this.album_artist = null;
			this.track = [];
			option_index = -1;
			this.artist_field.value = "";
			this.album_name_field.value = "";
		}

		document.getElementsByClassName("catalog_selector")[0].selectedIndex = option_index;
	}

	result(){
		var msg = document.getElementById('album_editor_alert');
		msg.style.display = "none";
		var temp = {"track": []};
		if (this.album_artist != this.artist_field.value && this.artist_field.value) temp["artist"] = this.artist_field.value;
		if(this.album_name != this.album_name_field.value && this.album_name_field.value) temp["album"] = this.album_name_field.value;

		var option = document.getElementsByClassName("catalog_selector")[0].selectedOptions[0];
		
		if (!option) {msg.style.display = "flex"; return "error";}

		if (option && this.album_catalog != option.innerHTML) temp["catalog"] = option.innerHTML;
		for(var track of album_editor_list){
			var track_json = track.json()
			if (track_json == "error") {
				msg.style.display = "flex";
				return "error";
			}
			if (Object.keys(track_json).length > 1){
				temp['track'].push(track_json);
			}

		}
		if (album_img_uploaded && upload_cover.img.src != this.img)	temp["cover"] = upload_cover.img.src;
		if (Object.keys(temp).length >1 || temp['track'].length) send['album'].push((this.new ? {"new": temp}: {"update": {"origin": this.json,"new": temp}}));

		if (this.cover_upload)
			this.cover_upload.remove();
	}
}

class album_editor{
	constructor(json){
		console.log(json)
		if (!album_editor_area)		album_editor_area = document.getElementById('album_edit_area');
		if (!album_edit_template) 	album_edit_template = document.getElementById('album_edit_template');

		if (json['artist'] && !document.getElementById("artist_input").value) {
			document.getElementById("artist_input").value = json['artist'];
		}
		if (json['album'] && !document.getElementById("album_input").value) {
			document.getElementById("album_input").value = json['album'];
		}

		album_editor_list.push(this);
		this.element = album_edit_template.cloneNode(1);
		this.in_json = json
		this.track = json['track'];
		this.element.style.display = 'block';
		album_editor_area.insertBefore(this.element,upload_btn_element.element);
		this.element.class = this;
		this.deleted = 0;
		this.delete_btn = this.element.getElementsByClassName("delete_btn")[0];
		var self = this;
		this.delete_btn.addEventListener('click',()=>{
			self.remove_from_album()
		})
		this.path = json['path'];
		this.title = this.element.getElementsByClassName("title_input")[0];
		this.price = this.element.getElementsByClassName("price_input")[0];
		if (json['price']) this.price.value = json['price'];
		this.duration = this.element.getElementsByClassName("duration_input")[0];
		if (json['title']) this.title.value = json['title'];
		if (json['duration']){
			this.duration_raw = json['duration'];
			var min = Math.floor(parseInt(json['duration'])/60);
			var sec = parseInt(json['duration'])%60;
			var hr = 0;
			if (min >=60){
				hr = Math.floor(min/60);
				min = min%60;
			}
			this.duration.value = (hr ?  String(hr)+":":"")+
								  (min ? String(min)+":":"")+
								  (sec ? String(sec):"")
		}
	}

	json(){

		if (!this.price.value || !this.title.value) {
			return "error";
		}

		var temp = {};
		if (this.deleted) {
			if (this.in_json) {
				temp['track'] = this.track;
				temp['deleted'] = 1;
				return temp;
			}else return;
		}
		if(!this.in_json || !this.in_json['track'] || (this.in_json['track'] && this.title.value != this.in_json['title'])) temp["title"]	 =  this.title.value;
		if(!this.in_json || !this.in_json['track'] || (this.in_json['track'] && this.price.value != this.in_json['price'])) temp["price"]	 =  parseInt(this.price.value);
		if (Object.keys(temp)) {
			if (!this.in_json || !this.in_json['track']) temp["duration"] =  this.duration_raw;
			if (this.track)  	temp['track'] = this.track
			if(this.path)    	temp["path"] =  this.path;
		}
		return temp;
	}

	remove_from_album(){
		this.element.remove()
		this.deleted = 1
	}
	remove(){
		this.element.remove()
		album_editor_list = album_editor_list.filter(item => item !== this);
	}
}