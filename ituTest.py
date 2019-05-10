import numpy as np
from pymongo import MongoClient
import subprocess
import json
from multiprocessing import Pool
from itu_p1203 import P1203Standalone
from itu_p1203 import P1203Pq
from itu_p1203 import P1203Pa
from itu_p1203 import P1203Pv
#from p1203Pv_extended import P1203Pv_codec_extended
DISPLAYSIZE="1280x780"#"1920x1080"#"1280x780"#"1920x1080"
codec="h264"
#RUN in python3.5 from folder /user/mkhokhar/home/PycharmProjects/youtubeALParallel/randomCollectionYouTubeR2Lab/ITU/model/itu-p1203/
#datasetYouTubePassive3_QoE_ITU codec h264 1920x1080
#datasetYouTubePassive3_QoE_ITU_1920x1080_codecUpdated codec vp9 or h264
#datasetYouTubePassive3_QoE_ITU_1280x780_codecUpdated codec vp9 or h264
#datasetYouTubePassive3_QoE_ITU_1280x780 codec h264


def chunkAnalysisHTTP(chunk,joinTime=0,ts=0):
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
    codecUsed="video/webm"


    for s in strList:
        ss=s.split(",")
        if len(ss)==11:######### NEED TO CHECK IF ANY MODIFICATION IS DONE #########
            range=ss[RANGE].split("-")
            #print "range",range
            chunkList.append(ss+[int(range[1])-int(range[0])])
            #print len(ss)

    chunkList=np.array(chunkList)
    numberOfVideoChunkRequests=len(chunkList[chunkList[:,9]=="video"])
    numberOfAudioChunkRequests=len(chunkList[chunkList[:,9]=="audio"])
    numberOfRequests=len(chunkList)
    beforeCount=chunkList.shape[0]

    ranges=chunkList[:,RANGE][::-1]#reverse the items to get last unique element
    chunkList= chunkList[::-1]
    chunkList=chunkList[np.unique(ranges,return_index=True)[1]]
    chunkList=chunkList[chunkList[:,0].argsort()]


    MissedReqCount=beforeCount-chunkList.shape[0]
    arrVideo=chunkList[chunkList[:,9]=="video"]
    arrVideoChunkSizes=arrVideo[:,11].astype(int)
    arrVideoChunkDurs=arrVideo[:,10].astype(int)
    arrVideoItags=arrVideo[:,4]
    arrVideoRanges=arrVideo[:,5]
    #print arrVideoRanges
    arrAudio=chunkList[chunkList[:,9]=="audio"]
    arrAudioChunkSizes=arrAudio[:,11].astype(int)
    arrAudioChunkDurs=arrAudio[:,10].astype(int)
    numberOfVideoChunks=len(chunkList[chunkList[:,9]=="video"])
    numberOfAudioChunks=len(chunkList[chunkList[:,9]=="audio"])

    #print "chunkList",chunkList[chunkList[:,0].argsort()]
    '''cV=chunkList#[chunkList[:,9]=="audio"]
    DLDurV=cV[:,10].astype(int)
    tsV=cV[:,0].astype(int)
    ts_endV=tsV+DLDurV
    tstart= np.sort(tsV-ts).astype(int)
    print list(np.sort(ts_endV-ts))
    dur= cV[np.argsort(ts_endV-ts)][:,10].astype(int)#DLdur
    v= cV[np.argsort(ts_endV-ts)][:,9]#audio/video
    print list(cV[np.argsort(ts_endV-ts)][:,11])#DLsize
    plt.figure()
    print "join_time",join_time,type(dur)
    for i in np.arange(len(dur)):
        x=tstart[i]+np.linspace(0,dur[i])
        if v[i]=="audio":
            y=1*np.ones(len(x))
        if v[i]=="video":
            y=2*np.ones(len(x))
        plt.scatter(x,y)
        #plt.plot([join_time,join_time],[1,2])
    plt.show()'''
    cV=chunkList[chunkList[:,9]=="audio"]
    DLDurV=cV[:,10].astype(int)
    tsV=cV[:,0].astype(int)
    ts_endV=tsV+DLDurV
    nAudioStart=len(ts_endV[ts_endV<(ts+joinTime)])
    cV=chunkList[chunkList[:,9]=="video"]
    DLDurV=cV[:,10].astype(int)
    tsV=cV[:,0].astype(int)
    ts_endV=tsV+DLDurV
    nVideoStart=len(ts_endV[ts_endV<(ts+joinTime)])
    #print np.sort(ts_endV-(ts+joinTime))
    #print joinTime,"audio/video at start",nAudioStart,nVideoStart
    #exit()
    #print "after",chunkList.shape

    #codecUnique,codecCount=np.unique(cV[:,3],return_counts=True)
    if len(cV)>0:
        codecUsed=cV[0,3]#codecCount
    #print("codecUsed",codecUsed)

    return [numberOfVideoChunkRequests,
            numberOfAudioChunkRequests,
            numberOfRequests,
            numberOfVideoChunks,
            numberOfAudioChunks,
            arrVideoChunkSizes,
            arrAudioChunkSizes,
            arrVideoChunkDurs,
            arrAudioChunkDurs,
            arrVideoItags,
            MissedReqCount,
            nAudioStart,
            nVideoStart,
            arrVideoRanges,
            codecUsed]

def itagToRes(itag):
    if int(itag)==278 or int(itag)==160:
        return "176x144"
    elif int(itag)==242 or int(itag)==133:
        return "320x240"
    elif int(itag)==243 or int(itag)==134:
        return "640x360"
    elif int(itag)==244 or int(itag)==135:
        return "854x480"
    elif int(itag)>=247 or int(itag)==136 or int(itag)==137:
        return "1280x720"

mongoDBclient = MongoClient('localhost', 27017)
db = mongoDBclient.youtubeapi
c=0
i=0
jtv=[]
point=[]
dur=[]
QoE_ITU_arr=[]
data=[]
for d in db["datasetYouTubePassive3_updated"].find():
    data.append(d)

def getQoE_ITU(d,startIndex):
    if d["httpInfo"]!="" and d["join_time"]!="310000":
        stallInfo=d["stallingInfo"].split("|")
        ts_firstBuffering=int(d["ts_firstBuffering"])

        chunkInfoAllHTTP=chunkAnalysisHTTP(d["httpInfo"],int(d["join_time"]),int(d["ts_firstBuffering"]))#,int(d["pcapSize"]))
        #jtv.append(chunkInfoAllHTTP[13])#,list(chunkInfoAllHTTP[5]),list(chunkInfoAllHTTP[9])
        #print chunkInfoAllHTTP
        '''if len(d["qualityInfo"].split("|"))>5:
            print d["videoID"],d["clen_video"]
            print list(chunkInfoAllHTTP[-1])
            print list(chunkInfoAllHTTP[9])'''
        arrVideoChunkSizes=chunkInfoAllHTTP[5]
        indexes=np.where((arrVideoChunkSizes>1000))[0]#arrVideoChunkSizes=arrVideoChunkSizes[arrVideoChunkSizes>1000]
        #print indexes
        arrVideoItags=chunkInfoAllHTTP[9]
        arrRes=list(map(itagToRes,arrVideoItags))
        codecUsed=chunkInfoAllHTTP[14]
        #print ("arrRes",arrRes)
        #print len(arrVideoChunkSizes),d["httpInfo"]
        #if codecUsed=="video/webm":

        jsonDict={}
        jsonDict["I11"]={}
        jsonDict["I13"]={"segments": [],"streamId": 42}
        jsonDict["I23"]={"stalling": [],
                         "streamId": 42}
        jsonDict["IGen"]={"device": "pc",
                          "displaySize": DISPLAYSIZE,
                          "viewingDistance": "250cm"}
        if len(arrVideoChunkSizes)>0:
            chunkDuration=float(d["dur"])/float(len(arrVideoChunkSizes))
            chunkBitrates=arrVideoChunkSizes*8/float(chunkDuration)/1000.
            chunkStartTimes=np.arange(0,float(d["dur"]),len(arrVideoChunkSizes))
            s=0
            segments=[]
            for index in indexes:
                mode={"bitrate":chunkBitrates[index],
                      "codec": codec,#"h264",
                      "duration": chunkDuration,
                      "fps": 30.0,
                      "resolution": list(arrRes)[index],
                      "start": s}
                jsonDict["I13"]["segments"].append(mode)
                s=s+chunkDuration
                #print mode

        stalling=[]
        sCum=0
        jsonDict["I23"]["stalling"].append([0,float(d["join_time"])/1000.])
        print ("join time ",[0,float(d["join_time"])/1000.])
        for s in stallInfo:
            if s!="":
                sA=s.split(",")
                ts_stall=int(sA[0])
                dur_stall=int(sA[1])
                jsonDict["I23"]["stalling"].append([(float(ts_stall-ts_firstBuffering)/1000.)-sCum,dur_stall/1000.])
                sCum=sCum+dur_stall/1000.
        print ("stalling",jsonDict["I23"]["stalling"])
        if len(jsonDict["I13"]["segments"])>0:
            #print jsonDict["I13"]["segments"]
            '''with open('/home/mkhokhar/test'+str(startIndex)+'.json', 'w') as file:
                file.write(json.dumps(jsonDict))'''

            try:
                #print (jsonDict)
                output=P1203Standalone(jsonDict).calculate_complete()#subprocess.check_output("p1203-standalone /home/mkhokhar/test"+str(startIndex)+".json",shell=True)
                #print(output)
                #exit()
                #output=json.loads(getOutput)
                QoE_ITU=[output["O23"],output["O35"],output["O46"],output["O46"]]
                print ("QoE_ITU before",QoE_ITU)
                if codecUsed=="video/webm":
                    x=output["O46"]
                    COEFFS_VP9 = [-0.04129014, 0.30953836, 0.32314399, 0.5284358]
                    a,b,c,d=COEFFS_VP9
                    O46_VP9 = a*x**3 + b*x**2 + c*x + d
                    QoE_ITU=[output["O23"],output["O35"],output["O46"],O46_VP9]
                    print ("QoE_ITU after",QoE_ITU)

            except Exception as e:
                print(e)
                QoE_ITU=[-1,-1,-1,-1]
        else:
            QoE_ITU=[-1,-1,-1,-1]#print jsonDict
    else:
        QoE_ITU=[-1,-1,-1,-1]

    return QoE_ITU
    #exit()
def subData(input_tuple):
    global QOE,data,db
    startIndex,endIndex=input_tuple
    for i in range(startIndex,endIndex):
        qoe=getQoE_ITU(data[i],startIndex)
        #QOE.append(getQoE_ITU(data[i],startIndex))
        print (i,data[i]["_id"])
        row={"QoE_ITU":qoe,"index":data[i]["_id"]}
        db["datasetYouTubePassive3_QoE_ITU_JT_"+DISPLAYSIZE+"_codecUpdated"].insert_one(row)
##################################
'''
This script creates a new SQL DB named datasetYouTubePassive3_QoE_ITU_DISPLAYSIZE to save the itu results.
'''
##################################
'''
for i in range(1000):
    DISPLAYSIZE="1280x780"
    codec="h264"
    print (i,data[i]["videoID"],DISPLAYSIZE,codec, getQoE_ITU(data[i],0))
    DISPLAYSIZE="1920x1080"
    #codec="vp9"
    print (i,data[i]["videoID"],DISPLAYSIZE,codec, getQoE_ITU(data[i],0))
    i+=1
exit()'''
#subData((0,len(data)))
QOE=[]
numberOfProcesses=5
se=range(0,len(data),int(len(data)/numberOfProcesses))
print (se)
inputArray=[]
for i in range(len(se)):
    start=se[i]
    if i+1>=len(se):
        end=len(data)
    else:
        end=se[i+1]
    inputTuples=(start,end)
    inputArray.append(inputTuples)
    print (start,end)
print (inputArray)

p = Pool(numberOfProcesses)
p.map(subData, inputArray)



#exit()








while(1):
    user_input = raw_input("Completed reading data Some input please: ")
    try:
        if user_input=="break":
            break
        exec(user_input)
    except Exception as e:
        print (e)


'''
                "bitrate": 7172.66,
                "codec": "h264",
                "duration": 5.0,
                "fps": 25.0,
                "resolution": "1920x1080",
                "start": 10.48'''
