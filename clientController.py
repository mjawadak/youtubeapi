from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
from urlparse import urlparse
#from youtubeSearch import youtube_search
#from oauth2client.tools import argparser
#from apiclient.discovery import build
#from apiclient.errors import HttpError
from subprocess import call
from cgi import parse_header, parse_multipart
from multiprocessing import Process
import subprocess
from multiprocessing import Pool
import numpy as np
import os
from pymongo import MongoClient
import time
from urlparse import parse_qs
import sys
#from readPcap import getPcapFeature
from sklearn import tree
from ClfClass import ClfClass
from readPcap import getPcapFeature
import httplib
import re
from urllib import urlencode
import socket
#from om import getOrKillProcess
import signal
import sys
#tshark -r speedtest25percentloss.pcap -Y "ip&&(udp||tcp)" -T fields -e frame.time_epoch -e ip.src -e ip.dst -e tcp.srcport -e tcp.dstport -e udp.srcport -e udp.dstport -e ip.len -E separator=,

server_address=sys.argv[1]#"fit07"#"localhost"#"138.96.203.5"
SERVER_PORT=443#8000
interface="eth0"
chromeExtension="ndoppbjkgpenhhocidoanikdgpllkbdo"#"fifmhpcpkaingagnbnmnlmolpimjkdmi"#"bdbejdogckpdpdajccdgcljmnihcbmkg"
args="no-sandbox"
def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]
clientIP=get_ip_address()
clientID="client_"+str(clientIP)
print clientIP,type(clientIP)
#exit()
def configNetworkQoS():
    global point,STOPFLAG
    #resetNetworkQoS()#point="[10000,2000,200,100,0.1]"
    point=re.split("\[|\]|,",point)
    del point[0]
    del point[-1]
    #delay=float(point[0])
    #lossrate=float(point[1])
    #bandwidth=float(point[1])
    #subprocess.call(["tcset","--device","eth0","--delay","%s"%(delay),"--loss","%s"%(100.0*lossrate),"--rate","%sk"%(bandwidth),"--direction","incoming","--overwrite"])
    #subprocess.call(["tcset","--device",interface,"--delay","%s"%(delay),"--rate","%sk"%(bandwidth),"--direction","incoming","--overwrite"])

    dl_tp=float(point[0])
    ul_tp=float(point[1])
    rtt=float(point[2])
    rtt_std=float(point[3])
    loss=float(point[4])
    subprocess.call(["tcset","--device",interface,"--delay","%s"%(rtt/2.),"--delay-distro",str(rtt_std/2.),"--loss","%s"%(100.0*loss/2.),"--rate","%sk"%(dl_tp),"--direction","incoming","--overwrite"])
    subprocess.call(["tcset","--device",interface,"--delay","%s"%(rtt/2.),"--delay-distro",str(rtt_std/2.),"--loss","%s"%(100.0*loss/2.),"--rate","%sk"%(ul_tp),"--direction","outgoing"])


def resetNetworkQoS():
    #subprocess.call(["tcdel", "--device", "enp0s3"])
    #subprocess.call(["tcset", "--device", "eth0", "--delay", "1", "--loss", "0.01", "--rate", "10000k", "--direction", "incoming","--overwrite"])
    subprocess.call(["tcset", "--device", interface, "--delay", "1", "--rate", "10000k", "--direction", "incoming","--overwrite"])



#print lastPlayedVideoIndex

timeString=time.strftime("%Y%m%d%H%M%S", time.gmtime())

def sendDataToMainController(data):
    conn = httplib.HTTPConnection(server_address,8000)
    params=data+"\r\n"
    headers = {"Content-type": "application/x-www-form-urlencoded","Accept": "text/plain"}
    conn.request("POST","/",params,headers)

    response = conn.getresponse()
    print "sendDataToMainController",response

#sendDataToMainController("heloo")
#exit()
STOPFLAG=0
def getPointAndVideo():
    global state,videoID,resolution,videoDuration,pcapProcess,point,dur,bitrate,resolution,STOPFLAG
    print "getPointAndConfigureQoSBefore"
    conn = httplib.HTTPConnection(server_address,8000)#138.96.203.5
    conn.request("GET","/getPoint")
    #print "conn",conn
    r1 = conn.getresponse()
    print "getPointAndConfigureQoS"
    headers=dict(r1.getheaders())
    #print headers
    if headers["stopflag"]=="0":
        point=headers["point"]
        videoID=headers["videoid"]
        resolution=headers["resolution"]
        dur=headers["dur"]
        bitrate=headers["bitrate"]

        configNetworkQoS()
        #print state
        #"YouTube_"+videoKeyword+"_"+videoID+"_"+resolution+".pcap"
        pcapProcess=subprocess.Popen(["tcpdump","-U","port","443","-s","0","-w","YouTube.pcap"])

        state="READY"

        STOPFLAG=0
    elif headers["stopflag"]=="1":
        STOPFLAG=1


def chunkAnalysis(chunk):
    REQUESTID=7
    TIMESTAMP=0
    STATUSCODE=8
    RANGE=5
    strList=np.array(chunk.split("|"))
    chunkList=[]
    requestids=[]
    timestamps=[]
    completedReqs=[]
    numberOfVideoChunkRequests=0
    numberOfAudioChunkRequests=0
    numberOfRequests=0
    numberOfAudioChunks=0
    numberOfVideoChunks=0
    arrVideoChunkSizes=[]
    arrAudioChunkSizes=[]
    arrVideoChunkDurs=[]
    arrAudioChunkDurs=[]


    for s in strList:
        if s!="":
            ss=s.split(",")
            if ss[3].find("video")!=-1:
                ss.append("video")
                if ss[STATUSCODE]=="REQ":
                    numberOfVideoChunkRequests=numberOfVideoChunkRequests+1

            elif ss[3].find("audio")!=-1:
                ss.append("audio")
                if ss[STATUSCODE]=="REQ":
                    numberOfAudioChunkRequests=numberOfAudioChunkRequests+1

            chunkList.append(ss)

            if (ss[REQUESTID] in requestids) == False:
                requestids.append(ss[REQUESTID])
                timestamps.append(ss[TIMESTAMP])
            else:
                if (ss[STATUSCODE] == "200"):
                    index=requestids.index(ss[REQUESTID])
                    chunkDLdur=float(ss[TIMESTAMP])-float(timestamps[index])
                    reqid=requestids[index]
                    completedReqs.append([reqid,chunkDLdur])
                    if ss[9]=="video":
                        numberOfVideoChunks=numberOfVideoChunks+1
                        arrVideoChunkDurs.append(chunkDLdur)
                        range=ss[RANGE].split("-")
                        arrVideoChunkSizes.append(int(range[1])-int(range[0]))

                    if ss[9]=="audio":
                        numberOfAudioChunks=numberOfAudioChunks+1
                        arrAudioChunkDurs.append(chunkDLdur)
                        range=ss[RANGE].split("-")
                        arrAudioChunkSizes.append(int(range[1])-int(range[0]))


    numberOfRequests=numberOfVideoChunkRequests+numberOfAudioChunkRequests
    #print "completedReqs",completedReqs
    chunkList=np.array(chunkList)
    #print "times"+",".join(chunkList[:,0])
    #print "times"+",".join(chunkList[:,3])

    chunks=[]
    for cp in completedReqs:
        for c in chunkList:
            if c[REQUESTID]==cp[0]:
                chunks.append(np.append(c,cp[1]))
                break
    chunks=np.array(chunks)
    #print "chunks",chunks
    #print ",".join(chunkList[chunkList[:,8]=="REQ"][chunkList[chunkList[:,8]=="REQ"][:,3]=="video/webm"][:,0])
    #print ",".join(chunkList[chunkList[:,8]!="REQ"][chunkList[chunkList[:,8]!="REQ"][:,3]=="video/webm"][:,0])

    #chunkList[]
    if len(chunkList)>0:

        cdns=chunkList[:,1]
        unique_cdns=list(np.unique(cdns))
        httpInfoUpdated=""
        for c in chunks:
            httpInfoUpdated=httpInfoUpdated+",".join(c)+"|"
    else:
        unique_cdns=""
        httpInfoUpdated=""
    #print httpInfoUpdated
    return [httpInfoUpdated,
            unique_cdns,
            numberOfVideoChunkRequests,
            numberOfAudioChunkRequests,
            numberOfRequests,
            numberOfVideoChunks,
            numberOfAudioChunks,
            arrVideoChunkSizes,
            arrAudioChunkSizes,
            arrVideoChunkDurs,
            arrAudioChunkDurs]

httpInfo='1509466428668,r4---sn-gxo5uxg-jqbe.googlevideo.com,0,video/webm,247,0-497221,0,349824,REQ|1509466428673,r4---sn-gxo5uxg-jqbe.googlevideo.com,1,audio/webm,251,0-65922,0,349825,REQ|1509466428693,r4---sn-gxo5uxg-jqbe.googlevideo.com,0,video/webm,247,0-497221,0,349828,REQ|1509466428697,r4---sn-gxo5uxg-jqbe.googlevideo.com,1,audio/webm,251,0-65922,0,349829,REQ|1509466430934,r4---sn-gxo5uxg-jqbe.googlevideo.com,1,audio/webm,251,0-65922,0,349829,200|1509466432544,r4---sn-gxo5uxg-jqbe.googlevideo.com,2,video/webm,247,497222-994004,0,349840,REQ|1509466432553,r4---sn-gxo5uxg-jqbe.googlevideo.com,2,video/webm,247,497222-994004,0,349841,REQ|1509466433933,r4---sn-gxo5uxg-jqbe.googlevideo.com,0,video/webm,247,0-497221,0,349828,200|1509466435018,r4---sn-gxo5uxg-jqbe.googlevideo.com,3,audio/webm,251,65923-131458,3909,349843,REQ|1509466435035,r4---sn-gxo5uxg-jqbe.googlevideo.com,3,audio/webm,251,65923-131458,3909,349844,REQ|1509466435052,r4---sn-gxo5uxg-jqbe.googlevideo.com,2,video/webm,247,497222-994004,0,349841,200|1509466435514,r4---sn-gxo5uxg-jqbe.googlevideo.com,4,audio/webm,251,131459-196994,7818,349846,REQ|1509466435717,r4---sn-gxo5uxg-jqbe.googlevideo.com,4,audio/webm,251,131459-196994,7818,349847,REQ|1509466435959,r4---sn-gxo5uxg-jqbe.googlevideo.com,3,audio/webm,251,65923-131458,3909,349844,200|1509466436530,r4---sn-gxo5uxg-jqbe.googlevideo.com,4,audio/webm,251,131459-196994,7818,349847,200|1509466436537,r4---sn-gxo5uxg-jqbe.googlevideo.com,5,video/webm,247,994005-1293780,8253,349849,REQ|1509466436544,r4---sn-gxo5uxg-jqbe.googlevideo.com,5,video/webm,247,994005-1293780,8253,349850,REQ|1509466438111,r4---sn-gxo5uxg-jqbe.googlevideo.com,5,video/webm,247,994005-1293780,8253,349850,200|1509466438147,r4---sn-gxo5uxg-jqbe.googlevideo.com,6,video/webm,247,1293781-1917021,10677,349852,REQ|1509466438166,r4---sn-gxo5uxg-jqbe.googlevideo.com,6,video/webm,247,1293781-1917021,10677,349853,REQ|1509466440840,r4---sn-gxo5uxg-jqbe.googlevideo.com,6,video/webm,247,1293781-1917021,10677,349853,200|1509466440878,r4---sn-gxo5uxg-jqbe.googlevideo.com,7,audio/webm,251,196995-262530,11744,349854,REQ|1509466441009,r4---sn-gxo5uxg-jqbe.googlevideo.com,7,audio/webm,251,196995-262530,11744,349855,REQ|1509466441492,r4---sn-gxo5uxg-jqbe.googlevideo.com,8,video/webm,247,1917022-3309815,14081,349856,REQ|1509466441543,r4---sn-gxo5uxg-jqbe.googlevideo.com,8,video/webm,247,1917022-3309815,14081,349857,REQ|1509466442005,r4---sn-gxo5uxg-jqbe.googlevideo.com,7,audio/webm,251,196995-262530,11744,349855,200|1509466444467,r4---sn-gxo5uxg-jqbe.googlevideo.com,9,audio/webm,251,262531-334054,15528,349864,REQ|1509466444507,r4---sn-gxo5uxg-jqbe.googlevideo.com,9,audio/webm,251,262531-334054,15528,349865,REQ|1509466444733,r4---sn-gxo5uxg-jqbe.googlevideo.com,8,video/webm,247,1917022-3309815,14081,349857,200|'
#print "chunkAnalysis",chunkAnalysis(httpInfo)[0]
#exit()


PORT_NUMBER = 8001


#This class will handles any incoming request from
#the browser
i=0

ts_start_python=0

#videoKeywords=["movies"]
#videoIDs=["oFkulzWMotY"]
#videoDurations=["0"]
v=0
r=0
#resolutions=["hd720"]
videoID=""
videoKeyword=""
resolution="0"
videoDuration="0"

URL="http://138.96.203.5:8000"

point=[]
bitrate=0
dur=0
state="WAIT";
#state="POINTCONFIGURED";

class myHandler(BaseHTTPRequestHandler):
	#Handler for the GET requests
    '''def do_POST(self):
        print self.headers
        print self.address_string()
        print parse_qs(self.rfile.read(int(self.headers.getheader("content-length", 0))))'''

    def do_GET(self):
        global i,videoID,videoDurations,pcapProcess,v,r,n,resolutions,ts_start_python,iteration,point,state,STOPFLAG,bitrate,dur
        #queryDict=parse_qs(self.rfile.read(int(self.headers.getheader("content-length", 0))))
        print state
        if state=="WAIT":
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin","*")
            self.send_header("videoID","WAIT")
            self.end_headers()
            getPointAndVideo()
            if STOPFLAG==1:
                getOrKillProcess("chrome",1)
                resetNetworkQoS()
                exit()

        elif state=="READY":
            if self.path=="/getVideoID_Res":
                self.send_response(200)
                self.send_header("Access-Control-Allow-Origin","*")
                self.send_header("videoID",videoID)
                self.send_header("resolution",resolution)
                self.send_header("videoDuration",videoDuration)
                self.end_headers()
            if self.path=="/configureQoS":
                print "Configuring QOS",self.path
                #configNetworkQoS()
                self.send_response(200)
                self.send_header("Access-Control-Allow-Origin","*")
                self.send_header("QoE","OK")
                self.end_headers()
        #getPointAndConfigureQoS()
        print "do_GET"#,queryDict

    def do_POST(self):#do_GET(self):
        #try:
            global i,videoID,videoDurations,pcapProcess,v,r,n,resolutions,ts_start_python,iteration,point,state,resolution,STOPFLAG,bitrate,dur
            state="WAIT"
            print "do_POST"
            #queryDict = parse_qs(urlparse(self.path).query)
            content=self.rfile.read(int(self.headers.getheader("content-length", 0)))
            queryDict=parse_qs(content)
            i=i+1
            #print queryDict,i,len(videoIDs)
            #resp=self.rfile.read()
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin","*")
            print "queryDict",queryDict
            #print "queryDict",queryDict

            #print "dataQ",dataQ


            resetNetworkQoS()

            if queryDict['ts_start_js'][0]!="-1":

                print "sending data"
                #data={"point":point,"keyword":videoKeyword,"v":v,"ts_start_python":str(ts_start_python),"videoID":videoID,"videoDuration":videoDuration,"resolution":resolution,"pcapSize":pcapSize,"pcapStats":pcapStats}
                #data.update(queryDict)
                #print "data",data
                #print "point---",point,",".join(str(e) for e in point)
                contentProcess=content.split("&")
                s=content.find("&httpInfo=")
                e=content.find("&",s+1)
                content=content.replace(content[s:e],"")#Remove the httpInfo coming from the browser
                data={}
                for c in contentProcess:
                    d=c.split("=")
                    data[d[0]]=d[1]
                #print content

                #print data["httpInfo"]
                clen_video=0
                clen_audio=0
                if data["dur"]!="0":
                    dur=float(data["dur"])
                    clen_video=float(data["clen_video"])
                    clen_audio=float(data["clen_audio"])
                if clen_video!=0 and clen_audio!=0 and dur!=0:
                    bitrate=float(8*clen_video/dur)

                chunkInfo=chunkAnalysis(data["httpInfo"])
                cdns=chunkInfo[1]
                #print "cdns",cdns

                #pcapProcess.terminate()
                #pcapProcess.wait()
                #os.kill(pcapProcess.pid, signal.SIGINT)
                pcapSize=0
                pcapSize=int(os.stat("YouTube.pcap").st_size)
                t1=time.time()
                pcapStats,chunkInfoPcap,cdnIPs=getPcapFeature("YouTube.pcap",clientIP,cdns)#"138.96.203.5"
                #cdnIPs=np.unique(np.array(cdnTuples)[:,2])
                print "pcapStatsTIme",time.time()-t1
                import shutil
                #shutil.copy("YouTube.pcap","YouTube_"+videoKeyword+"_"+videoID+"_"+resolution+str(time.time())+".pcap")

                #print "pcapStats",pcapStats,type(pcapStats)

                print "----------->>>>>>>",type(",".join(str(round(e,4)) for e in pcapStats)),type(chunkInfo[0]),type(cdnIPs)
                content=content+"&point="+",".join(str(e) for e in point)\
                        +"&keyword="+videoKeyword+\
                        "&v="+str(v)+\
                        "&ts_start_python="+str(ts_start_python)+\
                        "&videoID="+videoID+\
                        "&videoDuration="+videoDuration+\
                        "&resolution="+resolution+\
                        "&pcapSize="+str(pcapSize)+\
                        "&pcapStats="+",".join(str(round(e,4)) for e in pcapStats)+\
                        "&chunkInfoPcap="+str(chunkInfoPcap)+\
                        "&clientID="+clientID+\
                        "&cdnIPs="+str(cdnIPs)+\
                        "&cdns="+str(cdns)+\
                        "&bitrate="+str(bitrate)+\
                        "&dur="+str(dur)+\
                        "&clen_audio="+str(clen_audio)+\
                        "&clen_video="+str(clen_video)+\
                        "&httpInfo="+chunkInfo[0]


                #print "content",content
                #print urlencode(data)

                sendDataToMainController(content)


            #print "filesize=",pcapSize

            print "point:",point

            ts_start_python=int(time.time()*1000)



try:
    #Create a web server and define the handler to manage the
    #incoming request
    server = HTTPServer(('', PORT_NUMBER), myHandler)
    print 'Started clientserver on port ' , PORT_NUMBER#YqeW9_5kURI
    ts_start_python=int(time.time()*1000)
    resetNetworkQoS()

    call(["/opt/google/chrome/chrome","chrome-extension://"+chromeExtension+"/headers.html",args])#?videoID="+videoID+"&resolution="+resolutions[r]])#+resolutions[0]
    server.serve_forever()



except KeyboardInterrupt:
    print '^C received, shutting down the web server'
    server.socket.close()
