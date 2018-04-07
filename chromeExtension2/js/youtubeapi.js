var tabId = parseInt(window.location.search.substring(1));
//document.getElementById("demo").innerHTML+=window.location.search.substring(1);
var filters = { urls: ["<all_urls>"], tabId: -1 }
var httpInfo="";
var stallingNumber=0;
var totalStallDuration=0;
var availableQualityLevels="";
var JThttpInfo="";
var resolution="";
var videoID="";
var videoDuration=0;
var QoE=1;
var clen_audio=0;
var clen_video=0;
var dur=0;
function getITUQoE(stallingInfo,ts_startPlaying,videoDur,numStalls){
    //document.getElementById("demo").innerHTML +=stallingInfo.split("|").length
    if (stallingInfo!=""){
        stallArray=stallingInfo.split("|");
        TS=[];
        cref7=0.48412879;
        cref8=10;
        stallDurW=0;
        stallDur=0;
        ts=-1;
        DIFF=[];


        for (s in stallArray){
            if (stallArray[s]!=""){
                st=stallArray[s].split(",");
                if (ts!=-1){
                    diff=Number(st[0])-ts_startPlaying - ts;
                    DIFF.push(diff);
                }
                ts=Number(st[0])-ts_startPlaying;
                tsDur=Number(st[1]);
                x=videoDur-(ts-stallDur);
                w_buff=cref7+(1-cref7)*Math.exp(-x*(Math.log10(0.5)/(-cref8)));
                TS.push(ts);
                stallDurW=stallDurW+(tsDur*w_buff);
                stallDur=stallDur+tsDur;
                x=x+1;
                document.getElementById("demo").innerHTML +=stallArray[s]+"<br>";
            }
        }
        if (DIFF.length>0){
            avgBuffLen=0;
            i=0;
            for (d in DIFF){
                avgBuffLen=avgBuffLen+Number(d);
                i=i+1;
            }
            avgBuffLen=avgBuffLen/i;
        }
        else{
            avgBuffLen=0;
        }
        totalBuffLen=stallDurW;

        s1=9.35158684;
        s2=0.91890815;
        s3=11.0567558;
        T=Number(videoDur);
        avgBuffInterval=avgBuffLen;
        SI=Math.exp(-numStalls/s1)*Math.exp(-(totalBuffLen/T)/s2)*Math.exp(-(avgBuffInterval/T)/s3);
        QoE=1.0+4.0*SI;

        return Math.floor(QoE)
    }
    else {
        return 5
    }
}

function addListeners() {
    //chrome.webRequest.onBeforeRequest.addListener(handleEvent, filters, ['requestBody']);
    chrome.webRequest.onSendHeaders.addListener(handleEvent, filters, ['requestHeaders']);
    chrome.webRequest.onBeforeRedirect.addListener(handleEvent, filters, ['responseHeaders']);
    chrome.webRequest.onCompleted.addListener(handleEvent, filters, ['responseHeaders']);
    chrome.webRequest.onErrorOccurred.addListener(handleEvent, filters);
}

function removeListeners() {
    //chrome.webRequest.onBeforeRequest.removeListener(handleEvent);
    chrome.webRequest.onSendHeaders.removeListener(handleEvent);
    chrome.webRequest.onBeforeRedirect.removeListener(handleEvent);
    chrome.webRequest.onCompleted.removeListener(handleEvent);
    chrome.webRequest.onErrorOccurred.removeListener(handleEvent);
}
function handleEvent(details) {
    url=details.url;
    if (details.responseHeaders) {
        //document.getElementById("demo").innerHTML+=url.split("?")[0]+"<br>";
    }
    if (url.search("videoplayback?")!=-1){
        mime=getParameterByName("mime",url);
        range=getParameterByName("range",url);
        itag=getParameterByName("itag",url);
        rn=getParameterByName("rn",url);
        rbuf=getParameterByName("rbuf",url);

        requestId=details.requestId;
        isVideo=mime.search("video");
        if (isVideo!=-1){
            clen_video=getParameterByName("clen",url);
            dur=getParameterByName("dur",url);
        }
        else{
            clen_audio=getParameterByName("clen",url);
        }
        cdn=url.split("/")[2];
        statusCode="REQ";
        if (details.responseHeaders && details.statusCode==200) {
            statusCode=details.statusCode;
        }
        if (details.error){
            statusCode=details.error;
        }
        chunk=new Date().getTime()+","+cdn+","+rn+","+mime+","+itag+","+range+","+rbuf+","+requestId+","+statusCode+"|";
        httpInfo=httpInfo+chunk;
        document.getElementById("demo").innerHTML+=chunk+"<br>";
    }
}
addListeners();
function timeoutFunc(){
    var xhttp = new XMLHttpRequest();
    //var params="join_time="+join_time+"&playTimeStart="+playTimeStart+"&bufferingStart="+tB1;
    var params="ts_start_js="+ts_start_js+"&ts_onYTIframeAPIReady="+ts_onYTIframeAPIReady+"&ts_onPlayerReadyEvent="+ts_onPlayerReadyEvent+"&ts_firstBuffering="+ts_firstBuffering+"&ts_startPlaying="+ts_startPlaying+"&player_load_time="+player_load_time+"&join_time="+join_time+"&httpInfo="+httpInfo+"&availableQualityLevels="+availableQualityLevels+"&totalStallDuration="+totalStallDuration+"&stallingNumber="+stallingNumber+"&stallingInfo="+stallingInfo+"&timeout=yes"+"&getVideoLoadedFraction="+player.getVideoLoadedFraction()+"&resolution="+resolution;
    //xhttp.open("GET", "http://localhost:8001"+"?"+params, true);
    //xhttp.send();
    xhttp.open("POST","http://localhost:8001",true)
    xhttp.send(params);
    //removeListeners();
    //window.close();
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            document.getElementById("demo").innerHTML = this.responseText;
            //removeListeners();
            //window.close();
            location.reload();
        }
    };

}

//var timeoutMillis=5000;
//setTimeout(timeoutFunc, timeoutMillis);

function stopHTTP(){
document.getElementById("demo").innerHTML+="stop";
removeListeners();
}


var httpReqURLs="";


function getParameterByName(name, url) {
if (!url) url = window.location.href;
name = name.replace(/[\[\]]/g, "\\$&");
var regex = new RegExp("[?&]" + name + "(=([^&#]*)|&|#|$)"),
    results = regex.exec(url);
if (!results) return null;
if (!results[2]) return '';
return decodeURIComponent(results[2].replace(/\+/g, " "));
}


// 2. This code loads the IFrame Player API code asynchronously.
var tag = document.createElement('script');
var join_time=0;
var player_load_time=0;
var playTimeStart=0;
var ts_onYTIframeAPIReady=0;
var ts_onPlayerReadyEvent=0;
var ts_firstBuffering=0;
var ts_startPlaying=0;
var ts_start_js = new Date().getTime();
setTimeout(checkBuffer, 1000);

//var videoID =getParameterByName("videoID");
//var resolution =getParameterByName("resolution");

tag.src = "https://www.youtube.com/iframe_api";
var firstScriptTag = document.getElementsByTagName('script')[0];
firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);

// 3. This function creates an <iframe> (and YouTube player)
//    after the API code downloads.
var player;
var stallingInfo="";
var qualityInfo="";
function configureQoSClient(){
    var xhttp = new XMLHttpRequest();

    xhttp.open("GET","http://localhost:8001/configureQoS",true);
    //var params="configureQoE=1";

    xhttp.send();
    xhttp.onreadystatechange = function() {
        if (this.readyState == XMLHttpRequest.DONE){
            if (xhttp.getResponseHeader("QoE")=="OK"){
                player.playVideo();
            }
        }

    }
}
function getVideo(){
    var xhttp = new XMLHttpRequest();

    xhttp.open("GET","http://localhost:8001/getVideoID_Res",true);
    xhttp.send();

    xhttp.onreadystatechange = function() {
        if (this.readyState == XMLHttpRequest.DONE){//4 && this.status == 200) {//
            videoID=xhttp.getResponseHeader("videoID");
            resolution=xhttp.getResponseHeader("resolution");
            videoDuration=1000*Number(xhttp.getResponseHeader("videoDuration"));
            document.getElementById("demo").innerHTML = xhttp.getResponseHeader("videoID");
            //document.getElementById("demo").innerHTML = "GET !!";
            //removeListeners();
            //window.close();
            if (videoID!="WAIT"){
                player = new YT.Player('player', {
                    height: '780',//'390',
                    width: '1280',//'640',
                    videoId: videoID,
                    events: {
                    'onReady': onPlayerReady,
                    'onStateChange': onPlayerStateChange,
                    'onPlaybackQualityChange':onPlaybackQualityChange
                    }
                });
            }
            else{
                setTimeout(getVideo,1000);
            }
        }
    };

}


function onYouTubeIframeAPIReady() {
    getVideo();
    //stallInfo="1500669315024,1134|1500669328554,2976|1500669336104,2934|1500669343231,7558|1500669355048,5521|1500669367337,2947|1500669374078,178|";
    //ts_startPlaying = "1500669293288";
    //videoDur=61000;
    //numStalls=7;
    //QOE=getITUQoE(stallInfo,ts_startPlaying,videoDur,61000,numStalls);
    //document.getElementById("demo").innerHTML +=QOE+"<br>";
//player = new YT.Player('player', {
//    height: '390',
//    width: '640',
//    videoId: videoID,
//    events: {
//    'onReady': onPlayerReady,
//    'onStateChange': onPlayerStateChange
//    }
//});
ts_onYTIframeAPIReady=new Date().getTime()

}

// 4. The API will call this function when the video player is ready.
function onPlayerReady(event) {	
    ts_onPlayerReadyEvent=new Date().getTime()
    player_load_time=parseFloat(ts_onPlayerReadyEvent)-parseFloat(ts_start_js);
    document.getElementById("demo").innerHTML +="player_load_time="+player_load_time+"<br>"; //player.getAvailableQualityLevels()
    
    event.target.setPlaybackQuality(resolution);
    configureQoSClient();
    //event.target.playVideo();
}


function onPlaybackQualityChange(event){
    timeQualityChange=parseFloat(new Date().getTime());
    newQuality=event.data;
    document.getElementById("demo").innerHTML+=",onPlaybackQualityChange= "+event.data+"<br>";
    qualityInfo=qualityInfo+timeQualityChange+","+newQuality+"|";
}


// 5. The API calls this function when the player's state changes.
//    The function indicates that when playing a video (state=1),
//    the player should play for six seconds and then stop.
var done = false;
var bufferingStart=0;
var bufferSizeWhenStart="0";
function onPlayerStateChange(event) {

var date = new Date().getTime();

document.getElementById("demo").innerHTML+=join_time+","+date+",event.data = "+event.data+"<br>";
if (event.data == YT.PlayerState.PLAYING) {
	document.getElementById("demo").innerHTML+="Playing "+player.getAvailableQualityLevels()+" "+player.getVideoLoadedFraction()+"<br>";
    //setTimeout(stopVideo, 6000);
    //sendVideoInfo("videoEnded");
	availableQualityLevels=player.getAvailableQualityLevels();
	if (availableQualityLevels.indexOf(resolution)==-1){
	    //skipVideo();
	}
    if (done==false){
        ts_startPlaying=parseFloat(new Date().getTime())
        join_time=ts_startPlaying-parseFloat(ts_firstBuffering);
        document.getElementById("demo").innerHTML+="join_time="+join_time+" done<br>";
        JThttpInfo=httpInfo;
        bufferSizeWhenStart=player.getVideoLoadedFraction();
    }
    //window.location.href="/home/workspaceEclipseJS/YouTubeAPI/youtubePlayerMain.html?test=1";
    //window.location.reload();
    
    //setTimeout(checkBuffer, 1000);
    
    done = true;
    if (stallingNumber>0){
    	lastStallDur=parseFloat(new Date().getTime())-timeOfLastStall;
    	totalStallDuration=totalStallDuration+lastStallDur;
    	stallingInfo=stallingInfo+timeOfLastStall+","+lastStallDur+"|";
    }
}
if (event.data == YT.PlayerState.BUFFERING) {
    
    //setTimeout(stopVideo, 6000);
    //done = true;
	bufferingStart=1;
    if (done==false){
        ts_firstBuffering = new Date().getTime();
        document.getElementById("demo").innerHTML+="ts_firstBuffering="+ts_firstBuffering+"<br>";
    }
    else{
    	stallingNumber=stallingNumber+1;
    	timeOfLastStall=new Date().getTime();
    }

}
if (event.data == YT.PlayerState.ENDED) {
    
    sendVideoInfo("videoEnded");

}
if (event.data == -1){
	if (bufferingStart==1){
		skipVideo();
	}
}



}
var realtimeStallDur=0
function checkBuffer(){
    //document.getElementById("demo").innerHTML+="ts_start_js="+ts_start_js+"&ts_onYTIframeAPIReady="+ts_onYTIframeAPIReady+"&ts_onPlayerReadyEvent="+ts_onPlayerReadyEvent+"&ts_firstBuffering="+ts_firstBuffering+"&ts_startPlaying="+ts_startPlaying+"&player_load_time="+player_load_time+"&join_time="+join_time+"&totalStallDuration="+totalStallDuration+"&stallingNumber="+stallingNumber+"&stallingInfo="+stallingInfo+"<br>";
    var ts=new Date().getTime();
    if (player_load_time==0) {
        var timeFromStart=parseFloat(ts)-parseFloat(ts_start_js);
        if (timeFromStart>30000){
            sendVideoInfo("playerLoadTimeHigh");
        }
        else{
            setTimeout(checkBuffer, 1000);
        }

    }
    else if (join_time==0) {
        if (ts_firstBuffering>0){
            var timeFromBufferingPlusplayerLoadTime=parseFloat(ts)-parseFloat(ts_firstBuffering)+player_load_time;
            var timeFromBuffering=parseFloat(ts)-parseFloat(ts_firstBuffering);
            if (timeFromBuffering>30000){
                sendVideoInfo("joinTimeHigh");
            }
            else{
                setTimeout(checkBuffer, 1000);
            }
        }
        else{
            setTimeout(checkBuffer, 1000);
        }
    }
    else if (ts_firstBuffering>0){
        //document.getElementById("demo").innerHTML+="getVideoLoadedFraction="+player.getVideoLoadedFraction()+"<br>"
        //QoE=getITUQoE(stallingInfo,ts_startPlaying,videoDuration,stallingNumber);
        //QoE==1
        if (player.getPlayerState()==3){
            realtimeStallDur=realtimeStallDur+1;
        }
        if (stallingNumber>0){
            QoE=0;
        }
        if (player.getVideoLoadedFraction()>0.98){//realtimeStallDur>5 ||  && player.getPlayerState()!=YT.PlayerState.ENDED)){
            sendVideoInfo("videoDownloaded");
        }
        else {
            setTimeout(checkBuffer, 1000);
        }
    }
    else {
        setTimeout(checkBuffer, 1000);
    }

}
function stopVideo() {
document.getElementById("demo").innerHTML+=player.getVideoBytesLoaded()
player.stopVideo();
}

function skipVideo(){
    var xhttp = new XMLHttpRequest();
    //var params="join_time="+join_time+"&playTimeStart="+playTimeStart+"&bufferingStart="+tB1;
    var params="ts_start_js=-1";
    //xhttp.open("GET", "http://localhost:8001"+"?"+params, true);
    //xhttp.send()
    xhttp.open("POST","http://localhost:8001",true)
    xhttp.send(params);

    xhttp.onreadystatechange = function() {
        if (this.readyState == 4){//} && this.status == 200) {
            document.getElementById("demo").innerHTML = this.responseText;
            removeListeners();
            //window.close();
            location.reload();
        }
    };
}

function sendVideoInfo(status){
    var xhttp = new XMLHttpRequest();
    if (status=="videoNotPlayable"){
        var params="ts_start_js=-1";
    }
    else if (status=="videoEnded" || status=="videoDownloaded"){
        var params="ts_start_js="+ts_start_js+"&ts_onYTIframeAPIReady="+ts_onYTIframeAPIReady+"&ts_onPlayerReadyEvent="+ts_onPlayerReadyEvent+"&ts_firstBuffering="+ts_firstBuffering+"&ts_startPlaying="+ts_startPlaying+"&player_load_time="+player_load_time+"&join_time="+join_time+"&httpInfo="+httpInfo+"&availableQualityLevels="+availableQualityLevels+"&totalStallDuration="+totalStallDuration+"&stallingNumber="+stallingNumber+"&stallingInfo="+stallingInfo+"&timeout=no"+"&getVideoLoadedFraction="+player.getVideoLoadedFraction()+"&resolution="+resolution+"&bufferSizeWhenStart="+bufferSizeWhenStart+"&clen_video="+clen_video+"&clen_audio="+clen_audio+"&dur="+dur+"&QoE="+QoE+"&qualityInfo="+qualityInfo;
    }
    else if (status=="playerLoadTimeHigh"){
        var params="ts_start_js="+ts_start_js+"&ts_onYTIframeAPIReady="+ts_onYTIframeAPIReady+"&ts_onPlayerReadyEvent="+ts_onPlayerReadyEvent+"&ts_firstBuffering="+ts_firstBuffering+"&ts_startPlaying="+ts_startPlaying+"&player_load_time="+"310000"+"&join_time="+join_time+"&httpInfo="+httpInfo+"&availableQualityLevels="+availableQualityLevels+"&totalStallDuration="+totalStallDuration+"&stallingNumber="+stallingNumber+"&stallingInfo="+stallingInfo+"&timeout=no"+"&getVideoLoadedFraction="+"0"+"&resolution="+resolution+"&bufferSizeWhenStart="+bufferSizeWhenStart+"&clen_video="+clen_video+"&clen_audio="+clen_audio+"&dur="+dur+"&QoE=0"+"&qualityInfo="+qualityInfo;
    }
    else if (status=="joinTimeHigh"){
        var params="ts_start_js="+ts_start_js+"&ts_onYTIframeAPIReady="+ts_onYTIframeAPIReady+"&ts_onPlayerReadyEvent="+ts_onPlayerReadyEvent+"&ts_firstBuffering="+ts_firstBuffering+"&ts_startPlaying="+ts_startPlaying+"&player_load_time="+player_load_time+"&join_time="+"310000"+"&httpInfo="+httpInfo+"&availableQualityLevels="+availableQualityLevels+"&totalStallDuration="+totalStallDuration+"&stallingNumber="+stallingNumber+"&stallingInfo="+stallingInfo+"&timeout=no"+"&getVideoLoadedFraction="+"0"+"&resolution="+resolution+"&bufferSizeWhenStart="+bufferSizeWhenStart+"&clen_video="+clen_video+"&clen_audio="+clen_audio+"&dur="+dur+"&QoE=0"+"&qualityInfo="+qualityInfo;
    }

    xhttp.open("POST","http://localhost:8001",true)
    xhttp.send(params);

    xhttp.onreadystatechange = function() {
        if (this.readyState == 4 ) {//&& this.status == 200
            document.getElementById("demo").innerHTML = this.responseText;
            removeListeners();
            location.reload();
            //window.close();
        }
    };
}
