window.addEventListener("DOMContentLoaded", function() {
  var video = document.querySelector('video');
  var constraints = { video: { width: 854, height: 480 } };

  var recordedChunks = [];
  var options = {mimeType: 'video/webm; codecs=vp9'};
  var superBuffer;

  navigator.mediaDevices.getUserMedia(constraints)
  .then(function(stream) {
        video.srcObject = stream;
        video.play();
  }).catch(function(err) {
      console.log(err.name + ": " + err.message); 
  });

  function startCapture() {
    mediaRecorder = new MediaRecorder(video.srcObject, options);
    mediaRecorder.ondataavailable = handleDataAvailable
    mediaRecorder.start(1000)
    window.setTimeout(stopAndPlay, 7000)

    function handleDataAvailable(event) {
      console.log(event.data.size)
      if (event.data.size > 0) {
        recordedChunks.push(event.data);
      } 
    }

    function stopAndPlay() {
      video.pause()
      mediaRecorder.stop()
      replay()
    }

    function replay() {
      video.srcObject = null
      superBuffer = new Blob(recordedChunks);
      video.src = window.webkitURL.createObjectURL(superBuffer);
      video.controls = true
      video.loop = true 
      video.load()
    }
  }

  function upload() {
      console.log("Uploading...")
      var formData = new FormData();
      formData.append("file", superBuffer, 'video.webm');
      
      var xmlhttp = new XMLHttpRequest();
      xmlhttp.open("POST", "/video");

      // check when state changes, 
      xmlhttp.onreadystatechange = function() {

      if(xmlhttp.readyState == 4 && xmlhttp.status == 200) {
          alert(xmlhttp.responseText);
          }
      }

      xmlhttp.send(formData);
      console.log(formData.get('file'));
  }


  document.getElementById("capture").addEventListener("click", function() {
    startCapture();
  });

  document.getElementById("send").addEventListener("click", function() {
    upload();
  });
}, false);