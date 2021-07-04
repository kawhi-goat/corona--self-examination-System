var constraints = { video: { facingMode: "user" }, audio: false};
var dataURL;

const cameraView = document.querySelector("#camera--view"),
    cameraOutput = document.querySelector("#camera--output"),
    cameraSensor = document.querySelector("#camera--sensor"),
    cameraTrigger = document.querySelector("#camera--trigger"),
    preview = document.querySelector("#preview"),
    nextPage = document.querySelector("#nextPage");

function cameraStart(){
    navigator.mediaDevices
        .getUserMedia(constraints)
        .then(function(stream) {
            track = stream.getTracks()[0];
            cameraView.srcObject = stream;
        })
        .catch(function(error) {
            console.error("작동하지 않습니다!", error);
        });
}

cameraTrigger.onclick = function(){
    cameraSensor.width = cameraView.videoWidth;
    cameraSensor.height = cameraView.videoHeight;
    cameraSensor.getContext("2d").drawImage(cameraView, 0, 0);
    preview.src = cameraSensor.toDataURL("image/png");
};

window.addEventListener("load", cameraStart, false);