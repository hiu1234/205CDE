class image_class {
  constructor(imgElement) {
    this.path = imgElement.getAttribute("img_src");
    this.size_parent = imgElement.parentElement;
    if(!this.clientWidth)this.img_w = this.size_parent.clientWidth;
    if(!this.clientHeight)this.img_h = this.size_parent.clientHeight;
    this.mode = 0; //default use smallest ratio to scale (1: for scale with width and 2: for scale with height)
    while(!this.img_w || !this.img_h){
      this.size_parent = this.size_parent.parentElement;
      this.img_w = this.size_parent.clientWidth;
      this.img_h = this.size_parent.clientHeight;
    }
    this.blob = null;
    this.image_scale = 1.5;//scale up the img from the client width
    this.bg_blob = null;
    this.element = imgElement;
    this.bg_blur = imgElement.getAttribute("blur_bg");
    this.mode = imgElement.getAttribute("mode")
    imgElement.class = this;
    this.resizing= 0;
    this.worker = 0;
  }

  init(){
    if (this.path) {
      this.worker = new Worker('/static/js/work.js', { type: "module" });
      var self = this;
      this.worker.postMessage({"width": this.img_w*this.image_scale,
                               "height": this.img_h*this.image_scale,
                               "path" : this.path,
                               "bg" : this.bg_blur,
                               "mode" : this.mode
                             });

      this.worker.onmessage = (image)=> {
        self.worker = null;
        self.blob = image.data["blob"];
        self.update_img(image.data["img"] ? image.data["img"]:image.data["blob"]);
        if (self.bg_blur) {
          var bg_url = URL.createObjectURL(image.data["bg"]);
          var bg_div = self.element.parentElement;
          if (bg_div.clientWidth && bg_div.clientHeight) $(bg_div).animate({ opacity: 1 });
          else bg_div.style.opacity = 1;
          bg_div.style.background='url('+bg_url+')';
          bg_div.style.backgroundPosition= "center";
          bg_div.style.backgroundSize= "cover";
          bg_div.style.backgroundRepeat = "auto";
          
        }
        if (!self.bg_blur) $(this.element).animate({ opacity: 1 });
      }     
    }
    
  }

  resize(){
    this.img_w = this.size_parent.clientWidth;
    this.img_h = this.size_parent.clientHeight;
    while(!this.img_w && !this.img_h){
      this.size_parent = this.size_parent.parentElement;
      this.img_w = this.size_parent.clientWidth;
      this.img_h = this.size_parent.clientHeight;
    }
    var self = this;
    var resize_job = setInterval( ()=> {
      if (this.resizing) {
        this.worker.terminate();
        this.worker = null;
        this.resizing = 0;
      }
      if (!this.worker && this.blob && this.path) {
        this.resizing = 1;
        this.worker = new Worker('/static/js/work.js', { type: "module" });
        this.worker.postMessage({"width" : this.img_w*this.image_scale,
                                 "height" : this.img_h*this.image_scale,
                                 "blob" : this.blob,
                                 "mode" : this.mode});

        this.worker.onmessage = (image)=> {
          self.update_img(image.data["img"]);
        }
        clearInterval(resize_job);
        return;
      }
    },1000);
  }

  update_img(blob){
    var img_url = URL.createObjectURL(blob);
    this.element.src = img_url;
  }
}

class entry_class {
  constructor(entryElement) {
    this.element = entryElement;
    this.list = this.element.children;
    this.prev_btn = null;
    this.next_btn = null;
    this.limit = 0;
    this.total = this.list.length;
    for(var childelement of this.list){
      if (childelement.tagName == "A") {
        this.total--;
        switch (childelement.getAttribute("data-slide")){
          case "prev": this.prev_btn = childelement; break;
          case "next": this.next_btn = childelement; break;
        }
      }
      else if (childelement.classList.contains("show")) this.limit++;
    }
    this.current = this.limit;
    this.last = this.current;
    var self = this;
    this.next_btn.addEventListener("click",()=>{self.next_entry(self)});
    this.prev_btn.addEventListener("click",()=>{self.prev_entry(self)});

  }

  next_entry(self){
    self.last = self.current;
    if (self.current < self.total-1) {
      self.current++;
      self.update_entry();
    }
  }

  prev_entry(self){
    self.last = self.current;
    if (self.current > self.limit) {
      self.current--;
      self.update_entry();
    }
  }

  update_entry(){
    if (this.current>=this.last) {
      fading(this.list[this.current],this.list[this.current-this.limit]);//hide 
      //show
    }else{
      fading(this.list[this.current-this.limit+1],this.list[this.current+1])
      this.list[this.current+1]//hide
      
    }
  }

}

function fading(element1,element2){
  var text_box1 = element1.getElementsByClassName('text-area')[0];
  var text_box2 = element2.getElementsByClassName('text-area')[0];
  element1.style.maxWidth= "0%";
  $(element1).show(0,()=>{
    element1.style.maxWidth= "100%";
    setTimeout(ele=>{$(ele).show(400);},400,text_box1);
  });
  $(text_box2).hide(400,()=>{
    element2.style.maxWidth = "0";
    setTimeout(ele=> {ele.style.display = "none"}, 400,element2);
  });
}



