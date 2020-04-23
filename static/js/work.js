import * as stackblur from "/static/js/StackBlur.js";

onmessage = (input)=>{
  var startthread = async ()=>{
    var carosuel_image;
    if (input.data["path"]) {
      var response = await fetch(input.data["path"])
      var blob = await response.blob()
      carosuel_image = await createImageBitmap(blob);
    }
    else carosuel_image = await createImageBitmap(input.data["blob"]);
    var target_ratio;
    var transform = 0;
    var canvas_blob = null;
    switch (input.data["mode"]) {
      case 1 :input.data["width"]/carosuel_image.width;   break;
      case 2 :input.data["height"]/carosuel_image.height; break;
      default :
        var h_target_ratio = input.data["height"]/carosuel_image.height;
        var v_target_ratio = input.data["width"]/carosuel_image.width;
        if (h_target_ratio > v_target_ratio) target_ratio = v_target_ratio;
        else target_ratio = h_target_ratio;
        break;
    }
    if (target_ratio < 1) {
      var width = carosuel_image.width*target_ratio
      var height= carosuel_image.height * target_ratio
      var canvas = new OffscreenCanvas(width,height);
      //console.log(width,height)
      canvas.getContext("2d").drawImage(carosuel_image, 0, 0, width, height);
      carosuel_image.close();
      carosuel_image = canvas;
      transform = 1;
      canvas_blob = await canvas.convertToBlob({type: "image/webp",quality: 1.0})
    }

    if (input.data["blob"]) {
      postMessage({"img" : canvas_blob ? canvas_blob:input.data["blob"]});
      return;
    }

    if (input.data["bg"]) {
      var blur_bg = new OffscreenCanvas(carosuel_image.width,carosuel_image.height);
      blur_bg.getContext("2d").drawImage(carosuel_image,0,0,carosuel_image.width,carosuel_image.height);

      stackblur.stackBlurImage(carosuel_image,blur_bg,20
        ,false);
      var bg_blob = await blur_bg.convertToBlob({type: "image/webp",quality: 1.0})  
    }

    if (transform) {

      postMessage({"img" : canvas_blob,
                   "bg" : bg_blob,
                   "blob" : blob});
    }
    else postMessage({"blob" : blob,
                      "bg" : bg_blob
                     });
  }

  startthread().then( ()=> {close();} )
}