from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
from urlparse import urlparse
#from youtubeSearch import youtube_search
#from oauth2client.tools import argparser
from apiclient.discovery import build
from apiclient.errors import HttpError
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
import requests
#tshark -r speedtest25percentloss.pcap -Y "ip&&(udp||tcp)" -T fields -e frame.time_epoch -e ip.src -e ip.dst -e tcp.srcport -e tcp.dstport -e udp.srcport -e udp.dstport -e ip.len -E separator=,





def getBufInfo(stallingInfo,ts_startPlaying,videoDur):
    if stallingInfo!="":
        stallArray=stallingInfo.split("|")
        #stallArray.insert(str(ts_firstBuffering)+","+str(join_time),0)
        #videoDur=60000000.0
        TS=[]
        cref7=0.48412879
        cref8=10
        stallDurW=0
        stallDur=0
        ts=-1
        DIFF=[]
        #print "stallArray",stallArray
        for s in stallArray:
            if s!="":
                st=s.split(",")
                if ts!=-1:
                    diff=float(st[0])-ts_startPlaying - ts
                    DIFF.append(diff)
                #print "--------->>>>>>",st[0]
                ts=float(st[0])-ts_startPlaying
                tsDur=float(st[1])
                x=videoDur-(ts-stallDur)
                w_buff=cref7+(1-cref7)*np.exp(-x*(np.log10(0.5)/(-cref8)))
                TS.append(ts)
                stallDurW=stallDurW+(tsDur*w_buff)
                stallDur=stallDur+tsDur
                x=x+1
        if len(DIFF)>0:
            DIFF=np.array(DIFF)
            avgBuffLen=np.average(DIFF)
        else:
            avgBuffLen=0
        totalBuffLen=stallDurW


        return avgBuffLen,totalBuffLen
    else:
        return 0.0,0.0

def getQoE_ITU(numStalls,totalBuffLen,avgBuffInterval,T):
    s1=9.35158684
    s2=0.91890815
    s3=11.0567558
    T=float(T)
    SI=np.exp(-numStalls/s1)*np.exp(-(totalBuffLen/T)/s2)*np.exp(-(avgBuffInterval/T)/s3)
    QoE=1.0+4.0*SI
    return int(QoE)
#print lastPlayedVideoIndex

timeString=time.strftime("%Y%m%d%H%M%S", time.gmtime())

PORT_NUMBER = 8000
SAMPLING_TYPE=0#0 for random, 1 for active


#This class will handles any incoming request from
#the browser
i=0

ts_start_python=0

v=0
r=0
resolutions_api={"240p":"small","360p":"medium","480p":"large","720p":"hd720","1080p":"hd1080"}

#A unified objtective QoS-QoE model of youtube streaming: A network point of view
minSamplesLeaf=20
totalRuns=1
nIterations=10000
numberOfClasses=2
iteration=0

if SAMPLING_TYPE==1:
    clf=tree.DecisionTreeClassifier(min_samples_leaf=minSamplesLeaf,min_samples_split=2)#max_depth=5,
    #ranges=np.array([[0,1000],[0,0.1],[0,10000]])
    #clfObjectDTHybrid=ClfClass(clf,totalRuns,nIterations,numberOfClasses,"rtt,loss,tp",3,ranges)
    ranges=np.array([[0,1000],[0,10000],[0,3000000],[60,240]])#rtt,BW,Bitrate,dur
    clfObjectDTHybrid=ClfClass(clf,totalRuns,nIterations,numberOfClasses,"rtt,tp,bitrate,dur",4,ranges)

if SAMPLING_TYPE==0:
    clfObjectDTHybrid=ClfClass("",totalRuns,nIterations,numberOfClasses,"",4,[],0)
    clfObjectDTHybrid.loadCells()

mongoDBclient = MongoClient('localhost', 27017)
db = mongoDBclient.youtubeapi
#datasetMongo =db["datasetAL_Par_QoE_ITU11_DT_minSampLeaf_"+str(minSamplesLeaf)]
datasetMongo =db["datasetYouTubePassive2"]
iteration=0

if SAMPLING_TYPE==1:
    bitrateDB=db["datasetGetVideoInfo3_bitrateAxis"]


if SAMPLING_TYPE==0:
    print "reading videos db"
    bitrateDB=db["datasetGetVideoInfo3_br1080_webm_dur"]
    brDBCount=bitrateDB.count()


def getVideoSample(bitrate,dur):
    global bitrateDB
    count=1
    k=1
    while 1:
        bMin=np.max([bitrate-10000*k,0])
        bMax=bitrate+10000*k
        dMin=dur-k
        dMax=dur+k
        #0 index in bitratelist is bitrate, 1->duration
        b=bitrateDB.find({"$and":[{"bitrate":{"$gt":bMin,"$lt":bMax}},{"dur":{"$gt":dMin,"$lt":dMax}}]})
        count=b.count()

        #b=bitrateList[(bitrateList[:,0]>bMin)&(bitrateList[:,0]<bMax)&(bitrateList[:,1]>dMin)&(bitrateList[:,1]<dMax)]
        #count=len(b)
        print "finding Video"
        k=k+1
        if count>0:
            break
    '''index=np.random.randint(0,count)
    videoID=b[index,2]
    res=b[index,4]
    br=b[index,0]
    dur=b[index,1]'''
    d=b[np.random.randint(count)]
    videoID=d["videoID"]
    res=d["res"]
    br=d["bitrate"]
    dur=d["dur"]
    #print count,k,
    return [videoID,res,br,dur]

'''for i in range(1000):
    t1=time.time()
    dd=getVideoSample(np.random.randint(3000000),np.random.randint(240))
    print "Time to filter:",time.time()-t1'''
#exit()
point=[]
WINDOWSIZE=500
VARIATION_THRESHOLD=0.02
CLASS=[0,1]
pastConfValuesWindow=[]#np.zeros(WINDOWSIZE,len(CLASS))
STOPFLAG=0
#data=[]
#datasetYouTube_W500_P2
if SAMPLING_TYPE==1:
    if datasetMongo.count()>0:
        for item in datasetMongo.find():
            clfObjectDTHybrid.updateTrainingSet(iteration,np.array(item["labeledPoint"].split(",")).astype(float))
            if clfObjectDTHybrid.SAMPLING_TYPE==1:
                clfObjectDTHybrid.train()
                WeightedconfidencePerClass=clfObjectDTHybrid.getWeightedConfMeasure(CLASS)[0]
                pastConfValuesWindow.append(WeightedconfidencePerClass)

                if iteration>WINDOWSIZE:
                    del pastConfValuesWindow[0]
                    window=np.array(pastConfValuesWindow)
                    if np.product(np.std(window,axis=0)<VARIATION_THRESHOLD*np.average(window,axis=0))==1:
                        STOPFLAG=1
                        print "STOPFLAG",STOPFLAG
            iteration=iteration+1
            #data.append(item["labeledPoint"].split(","))
            #print item["labeledPoint"]



print "iteration",iteration


class myHandler(BaseHTTPRequestHandler):
	#Handler for the GET requests
    '''def do_POST(self):
        print self.headers
        print self.address_string()
        print parse_qs(self.rfile.read(int(self.headers.getheader("content-length", 0))))'''

    def do_GET(self):
        global i,videoIDs,videoDurations,pcapProcess,v,r,n,resolutions,ts_start_python,iteration,point,STOPFLAG

        if STOPFLAG==0:
            #print self.client_address
            #print self.headers
            #point=clfObjectDTHybrid.selectPoint(0,iteration,"DTHybrid")#DTHybridScaled2")DTHybridMaxEntropy
            #point=clfObjectDTHybrid.selectPoint(0,iteration,"random_real")#DTHybridScaled2")DTHybridMaxEntropy
            if clfObjectDTHybrid.SAMPLING_TYPE==1:
                point=clfObjectDTHybrid.selectPoint(0,iteration,"DTHybrid")#DTHybridScaled2")DTHybridMaxEntropy
                print type(point),point
                br=point[2]
                dur=point[3]
                videoInfo=getVideoSample(br,dur)
                br=videoInfo[2]
                dur=videoInfo[3]
                print "sampled video:",videoInfo
                point=point[0:2]# if rtt,tp,br,dur
                self.send_response(200)
                self.send_header("point",point)
                self.send_header("videoID",videoInfo[0])
                self.send_header("resolution",resolutions_api[videoInfo[1]])
                self.send_header("bitrate",br)
                self.send_header("dur",dur)
                self.send_header("STOPFLAG","0")
                self.end_headers()
            if clfObjectDTHybrid.SAMPLING_TYPE==0:
                point=clfObjectDTHybrid.selectPoint(0,iteration,"random_real")#DTHybridScaled2")DTHybridMaxEntropy
                print type(point),point
                indexOfVideo=np.random.randint(0,brDBCount)
                videoItem=bitrateDB.find()[indexOfVideo]
                br=videoItem["br_248"]
                dur=videoItem["dur"]
                print "sampled video:",videoItem["videoID"]
                self.send_response(200)
                self.send_header("point",point)
                self.send_header("videoID",videoItem["videoID"])
                self.send_header("resolution","default")#DASH
                self.send_header("bitrate",br)
                self.send_header("dur",dur)
                self.send_header("STOPFLAG","0")
                self.end_headers()

        if STOPFLAG==1:
            self.send_response(200)
            self.send_header("STOPFLAG","1")
            self.end_headers()

    def do_POST(self):#do_GET(self):

            print "POST"
        #try:
            global i,videoIDs,videoDurations,pcapProcess,v,r,n,resolutions,ts_start_python,iteration,point,STOPFLAG
            #queryDict = parse_qs(urlparse(self.path).query)
            content=self.rfile.read(int(self.headers.getheader("content-length", 0)))
            #print "----->",content
            self.send_response(200)
            self.end_headers()
            content=content.split("&")
            data={}
            for c in content:
                d=c.split("=")
                data[d[0]]=d[1]
            #data["client IP"]=self.client_address
            #queryDict=parse_qs(self.rfile.read(int(self.headers.getheader("content-length", 0))))
            i=i+1
            #print queryDict,i,len(videoIDs)
            #resp=self.rfile.read()

            print self.path

            #pcapProcess.terminate()
            #pcapSize=0
            #pcapSize=int(os.stat("YouTube_"+videoKeywords[v]+"_"+videoIDs[v]+"_"+resolutions[r]+".pcap").st_size)



            if data['ts_start_js'][0]!="-1":
                point=data["point"]
                print "pointBefore",point
                bitrate=float(data["bitrate"])
                dur=float(data["dur"])
                point=np.array(point.split(",")).astype(float)
                point=np.concatenate((point,np.array([bitrate,dur])))
                print "point ",point
                #if float(data["player_load_time"])<=30000 and float(data["join_time"])<=30000:
                    #avgBuffInterval,totalBuffLen=getBufInfo(data["stallingInfo"],int(data["ts_startPlaying"]),61000)
                    #print avgBuffInterval,totalBuffLen,data["stallingNumber"]
                    #qoe=getQoE_ITU(int(data["stallingNumber"]),totalBuffLen,avgBuffInterval,61000)
                qoe=int(data["QoE"])
                point=np.concatenate((point,[qoe]),axis=0)
                print "stallingInfo",data["stallingInfo"],"QOE=",data["QoE"]
                #else:
                    #point=np.concatenate((point,[1]),axis=0)
                data["labeledPoint"]=",".join(str(e) for e in point)#list(point)
                if clfObjectDTHybrid.SAMPLING_TYPE==1:
                    clfObjectDTHybrid.updateTrainingSet(iteration,point)
                    clfObjectDTHybrid.train()
                    WeightedconfidencePerClass=clfObjectDTHybrid.getWeightedConfMeasure(CLASS)[0]
                    print "WeightedconfidencePerClass",WeightedconfidencePerClass
                    pastConfValuesWindow.append(WeightedconfidencePerClass)
                    if iteration>WINDOWSIZE:
                        del pastConfValuesWindow[0]
                        window=np.array(pastConfValuesWindow)
                        if np.product(np.std(window,axis=0)<VARIATION_THRESHOLD*np.average(window,axis=0))==1:
                            STOPFLAG=1
                            print "STOPFLAG",STOPFLAG
                    print "labeledPoint:",point
                    print "trainingClasses+counts:",np.unique(clfObjectDTHybrid.training[:,4],return_counts=True)
                    print "DT node Count:",len(clfObjectDTHybrid.clf.tree_.__getstate__()['nodes'].tolist())

                datasetMongo.insert_one(data)
                iteration=iteration+1




            ts_start_python=int(time.time()*1000)

            resolutions=["hd720"]
            r=0
            v=0


            #clfObjectDTHybrid.train()






try:
    #Create a web server and define the handler to manage the
    #incoming request
    server = HTTPServer(('', PORT_NUMBER), myHandler)
    print 'Started httpserver on port ' , PORT_NUMBER#YqeW9_5kURI
    ts_start_python=int(time.time()*1000)
    #iteration=0
    #point=clfObjectDTHybrid.selectPoint(0,iteration,"DTHybrid")
    #resetNetworkQoS()
    #configNetworkQoS(point)
    #print point
    #pcapProcess=subprocess.Popen(["tcpdump","-s","0","-w","YouTube_"+videoKeywords[v]+"_"+videoIDs[v]+"_"+resolutions[r]+".pcap"])
    #call(["/opt/google/chrome/chrome","localhost/youtubePlayer.html?videoID="+videoIDs[0]+"&resolution="+resolutions[0]])
    #sample 4k video id=iNJdPyoqt8U
    #print pcapProcess.pid



    #call(["/opt/google/chrome/chrome","chrome-extension://jkgdfpidaphgomdepphnapkabjgihjai/headers.html?videoID="+videoIDs[v]+"&resolution="+resolutions[r]])#+resolutions[0]

    #Wait forever for incoming htto requests
    server.serve_forever()
    #/opt/google/chrome/chrome chrome-extension://jkgdfpidaphgomdepphnapkabjgihjai/headers.html


except KeyboardInterrupt:
    print '^C received, shutting down the web server'
    server.socket.close()
