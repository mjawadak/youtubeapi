import dpkt
import socket
import numpy as np
from sklearn.cluster import KMeans
import dns.resolver
import subprocess
import os
from pymongo import MongoClient
#mongoDBclient = MongoClient('localhost', 27017)
#db = mongoDBclient.youtubeapi
#collection=db["youtubePCAPdata"]
##Indexes in Tuples array
PROTO=0
IP_SRC=1
IP_DST=2
SPORT=3
DPORT=4
IP_LEN=5
TS_START=6
TS_END=7
DUR=8
COUNT=9
GOOGLECDN=10

'''
FEATURES TO BE EXTRACTED FROM PCAP:
avg,min,max,std,median,10%,20%,80%,90%
chunk size -- partially done
chunk interval
chunk count
ul interarrival time --DONE
dl interarrival time --DONE
dl packet size --DONE
dl throughput --DONE
'''
'''
To obtain Chunk Information:
Get CDN URLs from HTTP Logs
Get CDN IPs from DNS Lookup of CDN URLs
Get CDN Flows of corresponding CDN IPs from Traffic Traces
Get ChunkInfo from Traces Traces for all CDN Flows:
    Let set u_i denote all uplink packet sizes for flow c_i
    Fit Kmeans on u_i with two clusters: cluster 0 for UL ack packets, cluster 1 for UL HTTP Chunk requests
    Chunk
To obtain In-Band Features:
Get In-band Features from Traffic Traces
'''


#tshark -2 -r yt.pcap  -R 'ssl.handshake.extensions_server_name contains "googlevideo.com" || quic.tag.sni contains "googlevideo.com"'
#-R 'ssl.handshake.extensions_server_name contains \"googlevideo.com\" || quic.tag.sni contains \"googlevideo.com\"'
def searchTCPUDPTuple(ip,ts,tuples,fileName,searchGoogle=0):
    foundStatus="NotFound"
    i=0
    payload=ip.data
    #udptcp/tcp,ip.src,ip.dst,sport,dport,ip.len,ts_start,ts_end
    for t in tuples:
        foundStatus="NotFound"
        if (socket.inet_ntop(socket.AF_INET, ip.src)==t[IP_SRC] or socket.inet_ntop(socket.AF_INET, ip.src)==t[IP_DST]) and\
                           (socket.inet_ntop(socket.AF_INET, ip.dst)==t[IP_SRC] or socket.inet_ntop(socket.AF_INET, ip.dst)==t[IP_DST]) and\
                           (payload.sport==t[SPORT] or payload.sport==t[DPORT]) and\
                           (payload.dport==t[SPORT] or payload.dport==t[DPORT] and\
                            ip.p==t[PROTO]):
            foundStatus="Found"
            t[IP_LEN]=t[IP_LEN]+ip.len
            t[TS_END]=ts
            t[DUR]=t[TS_END]-t[TS_START]
            t[COUNT]=t[COUNT]+1
            #tuplesNP[i][5]=tuplesNP[i][5]+ip.len
            #print t
            if searchGoogle==1 and payload.dport==443 and t[COUNT]<15:
                payloadStr=str(payload.data)
                indexGoogle=payloadStr.find("googlevideo.com")
                if indexGoogle!=-1:
                    e=payloadStr.find("\x00",indexGoogle)
                    s=payloadStr.rfind("\x00",0,indexGoogle)
                    cdn=str(payloadStr[s+2:e])
                    #print cdn
                    t[GOOGLECDN]=cdn
                    #print t,cdn
                    #collection.insert_one({"fileName":fileName,"CDN":cdn,"IP":socket.inet_ntop(socket.AF_INET, ip.dst)})
            break
        else:
            foundStatus="NotFound"
        i=i+1
    return foundStatus

def dictToNParray(iDict):
    for d in iDict:
        d["tcp.sport"]

def tupleWithMaxData(tuples):
    max=0
    selected={}
    for t in tuples:
        if t["ip.len"]>max:
            max=t["ip.len"]
            selected=t
    return selected
def getKMeansChunkOLD(fileName):
    f=open(fileName)
    pcap = dpkt.pcap.Reader(f)
    IPs=[]
    tuples=[]
    for ts,pkt in pcap:
        #print ts,len(pkt)
        if pcap.datalink()==dpkt.pcap.DLT_EN10MB:
            eth = dpkt.ethernet.Ethernet(pkt)
            if isinstance(eth.data, dpkt.ip.IP):
                ip=eth.data
                if isinstance(ip.data,dpkt.udp.UDP):
                    udp=ip.data
                    udpStr=udp.data
                    '''if udp.dport!=53 and udpStr.find("googlevideo.com")!=-1:
                        #print socket.inet_ntop(socket.AF_INET, ip.dst)#,udpStr
                        print IPs.index(socket.inet_ntop(socket.AF_INET, ip.dst))'''
                    if len(tuples)==0 or searchUDPTuple(ip,udp,tuples)=="NotFound":
                        tuple={}
                        tuple.update({"ip.src":socket.inet_ntop(socket.AF_INET, ip.src)})
                        tuple.update({"ip.dst":socket.inet_ntop(socket.AF_INET, ip.dst)})
                        tuple.update({"udp.sport":udp.sport})
                        tuple.update({"udp.dport":udp.dport})
                        tuple.update({"ip.len":ip.len})
                        tuples.append(tuple)

                        #tuple.append(socket.inet_ntop(socket.AF_INET, ip.src))
                        #print ip.dst

        #print len(eth.data.data.data)
        #exit()
    #print tuples#,socket.inet_pton(socket.AF_INET,IPs[0])
    tuple=tupleWithMaxData(tuples)
    f=open(fileName)
    pcap = dpkt.pcap.Reader(f)
    lenOfYTreq=0
    i=0
    uplinkLens=[]
    DLDatas=[]
    DLdata=0
    uLreqs=[]
    from decimal import Decimal
    for ts,pkt in pcap:
        #print Decimal(ts)
        if pcap.datalink()==dpkt.pcap.DLT_EN10MB:
            eth = dpkt.ethernet.Ethernet(pkt)
            if isinstance(eth.data, dpkt.ip.IP):
                ip=eth.data
                if isinstance(ip.data,dpkt.udp.UDP):
                    udp=ip.data
                    udpStr=udp.data
                    if (socket.inet_ntop(socket.AF_INET, ip.src)==tuple["ip.src"] or socket.inet_ntop(socket.AF_INET, ip.src)==tuple["ip.dst"]) and\
                       (socket.inet_ntop(socket.AF_INET, ip.dst)==tuple["ip.src"] or socket.inet_ntop(socket.AF_INET, ip.dst)==tuple["ip.dst"]) and\
                       (udp.sport==tuple["udp.sport"] or udp.sport==tuple["udp.dport"]) and\
                       (udp.dport==tuple["udp.sport"] or udp.dport==tuple["udp.dport"]):
                        lenOfYTreq+=ip.len
                        i+=1

                        if socket.inet_ntop(socket.AF_INET, ip.src)==tuple["ip.src"]:#If uplink data
                            #print i,ts,socket.inet_ntop(socket.AF_INET, ip.src),lenOfYTreq,ip.len
                            uplinkLens.append(ip.len)

    uplinkLens=np.array(uplinkLens).reshape(len(uplinkLens),1)

    uLreqs=np.array(uLreqs).reshape(len(uLreqs),1)
    kmeans = KMeans(n_clusters=2, random_state=0).fit(uplinkLens)
    #print kmeans.cluster_centers_,np.unique(kmeans.labels_,return_counts=True)
    #print "----"


    f=open(fileName)
    pcap = dpkt.pcap.Reader(f)
    for ts,pkt in pcap:
        #print Decimal(ts)
        if pcap.datalink()==dpkt.pcap.DLT_EN10MB:
            eth = dpkt.ethernet.Ethernet(pkt)
            if isinstance(eth.data, dpkt.ip.IP):
                ip=eth.data
                if isinstance(ip.data,dpkt.udp.UDP):
                    udp=ip.data
                    udpStr=udp.data
                    if (socket.inet_ntop(socket.AF_INET, ip.src)==tuple["ip.src"] or socket.inet_ntop(socket.AF_INET, ip.src)==tuple["ip.dst"]) and\
                       (socket.inet_ntop(socket.AF_INET, ip.dst)==tuple["ip.src"] or socket.inet_ntop(socket.AF_INET, ip.dst)==tuple["ip.dst"]) and\
                       (udp.sport==tuple["udp.sport"] or udp.sport==tuple["udp.dport"]) and\
                       (udp.dport==tuple["udp.sport"] or udp.dport==tuple["udp.dport"]):
                        lenOfYTreq+=ip.len
                        i+=1

                        if socket.inet_ntop(socket.AF_INET, ip.src)==tuple["ip.src"]:
                            #print i,ts,socket.inet_ntop(socket.AF_INET, ip.src),lenOfYTreq,ip.len
                            #print ip.len,kmeans.predict(ip.len)
                            if kmeans.predict(ip.len)>0:#if the ip.len is a bigger packet
                                DLDatas.append(DLdata)
                                DLdata=0
                        else:
                            DLdata+=ip.len

    DLDatas=np.array(DLDatas).reshape(len(DLDatas),1)

    kmeansDL = KMeans(n_clusters=5, random_state=0).fit(DLDatas)
    #print "----",uLreqs
    #print "----",DLDatas
    #print "----"

    return DLDatas#[tuple['ip.len'],len(DLDatas)]

def getKMeansChunk(maxTuples,packets):
    lenOfYTreq=0
    i=0

    from decimal import Decimal
    START_TIME_FILE=float(packets[0,TS_START])
    #print START_TIME_FILE
    #exit()
    DLDatasStr=""
    for t in maxTuples:
        uplinkLens=[]
        DLDatas=[]
        chunkDLdurs=[]
        chunkStartTimes=[]
        deltas=[]
        DLdata=0
        uLreqs=[]
        reqCounter=0
        lastDLTimestamp=0.0
        for p in packets:

            if (p[IP_SRC]==t[IP_SRC] or p[IP_SRC]==t[IP_DST]) and\
               (p[IP_DST]==t[IP_SRC] or p[IP_DST]==t[IP_DST]) and\
               (p[SPORT]==t[SPORT] or p[SPORT]==t[DPORT]) and\
               (p[DPORT]==t[SPORT] or p[DPORT]==t[DPORT]) and\
                p[0]==t[0]:#Check udp/tcp
                i+=1
                #print p[IP_SRC],t[IP_SRC],type(p[IP_SRC]),type(t[IP_SRC])
                if p[IP_SRC]==t[IP_SRC]:#If uplink data
                    #print i,ts,socket.inet_ntop(socket.AF_INET, ip.src),lenOfYTreq,ip.len
                    uplinkLens.append(p[IP_LEN])

        uplinkLens=np.array(uplinkLens).reshape(len(uplinkLens),1)

        uLreqs=np.array(uLreqs).reshape(len(uLreqs),1)
        #print ",".join(t),uplinkLens.shape
        if (len(uplinkLens)>3):
            kmeans = KMeans(n_clusters=2, random_state=0).fit(uplinkLens)
            #print kmeans.cluster_centers_,np.unique(kmeans.labels_,return_counts=True)
            #print "----"
            for p in packets:
                if (p[IP_SRC]==t[IP_SRC] or p[IP_SRC]==t[IP_DST]) and\
                   (p[IP_DST]==t[IP_SRC] or p[IP_DST]==t[IP_DST]) and\
                   (p[SPORT]==t[SPORT] or p[SPORT]==t[DPORT]) and\
                   (p[DPORT]==t[SPORT] or p[DPORT]==t[DPORT]) and\
                    p[0]==t[0]:#Check udp/tcp

                    i+=1

                    if p[IP_SRC]==t[IP_SRC]:
                        #print i,ts,socket.inet_ntop(socket.AF_INET, ip.src),lenOfYTreq,ip.len
                        #print p[TS_START],kmeans.predict(int(p[IP_LEN])),DLdata
                        if kmeans.predict(int(p[IP_LEN]))>0:#if the ip.len is a bigger packet ->UPLINK CHUNK REQUEST PACKET
                            if reqCounter>0:
                                DLDatas.append(DLdata)
                                chunkDLdur=lastDLTimestamp-ts_chunkStart
                                #print "chunkDLdur",chunkDLdur
                                chunkDLdurs.append(chunkDLdur)


                            DLdata=0
                            ts_chunkStart=float(p[TS_START])
                            chunkStartTimes.append(ts_chunkStart-START_TIME_FILE)
                            delta=ts_chunkStart-lastDLTimestamp
                            if reqCounter>0:
                                #print "delta",delta
                                deltas.append(delta)

                            reqCounter=reqCounter+1
                    else:
                        DLdata+=int(p[IP_LEN])
                        lastDLTimestamp=float(p[TS_START])
            if len(chunkStartTimes)>0:
                chunkStartTimes.pop()
                #print "lengths",len(DLDatas),len(chunkDLdurs),len(deltas),len(chunkStartTimes)
                #DLDatas=np.array(DLDatas).reshape(len(DLDatas),1)

                chunkData=np.vstack((DLDatas,chunkStartTimes,chunkDLdurs,deltas)).transpose()
                #print "chunkData",chunkData
                #exit()
                #print "DLDatas",DLDatas,len(DLDatasArray)
                #kmeansDL = KMeans(n_clusters=3, random_state=0).fit(DLDatas)
                #print "----",uLreqs
                #print "----",DLDatas
                #print "----"
                chunkDataStr= '|'.join(','.join(str(cell) for cell in row) for row in chunkData)
                if np.average(DLDatas)>10000:
                    DLDatasStr=DLDatasStr+"|"+chunkDataStr
            else:
                DLDatasStr=""
    return DLDatasStr#DLDatas#[tuple['ip.len'],len(DLDatas)]

def getGoogleIPs(cdns):
    myResolver = dns.resolver.Resolver()
    cdnIPs=[]
    cdnTuples=[]
    for c in cdns:
        myAnswers = myResolver.query(c, "A")
        for rdata in myAnswers: #for each response
            #print "rdata",rdata #print the data
            cdnIPs.append(str(rdata))
    return cdnIPs

def getGoogleTuples(cdns,tuples):
    myResolver = dns.resolver.Resolver()
    cdnIPs=[]
    cdnTuples=[]
    for c in cdns:
        myAnswers = myResolver.query(c, "A")
        for rdata in myAnswers: #for each response
            #print "rdata",rdata #print the data
            cdnIPs.append(str(rdata))
    for t in tuples:
        for cIP in cdnIPs:
            #print "t",t,"c",str(cIP),str(t[IP_DST]),IP_DST
            if str(t[IP_DST])==str(cIP) or str(t[IP_DST])==str(cIP):
                cdnTuples.append(t)
    return cdnTuples

def getPackets(fileName,cdnIPs,machineIP):
    f=open(fileName)
    tuples=[]#np.empty([0,5])#[]
    packetsUDPTCP=[]
    try:
        pcap = dpkt.pcap.Reader(f)
        IPs=[]
        #tuples=[]

        for ts,pkt in pcap:
            #print ts,len(pkt)
            if pcap.datalink()==dpkt.pcap.DLT_EN10MB:
                #print ts
                try:
                    eth = dpkt.ethernet.Ethernet(pkt)
                    if isinstance(eth.data, dpkt.ip.IP):
                        ip=eth.data

                        #print ip.p,dpkt.ip.IP_PROTO_UDP
                        if ip.p==dpkt.ip.IP_PROTO_UDP or ip.p==dpkt.ip.IP_PROTO_TCP:
                            udptcp=ip.data
                            udptcpStr=udptcp.data
                            protocol=ip.p
                            packetsUDPTCP.append([protocol,socket.inet_ntop(socket.AF_INET, ip.src),socket.inet_ntop(socket.AF_INET, ip.dst),udptcp.sport,udptcp.dport,ip.len,ts])
                            #print str(protocol)+"_"+ip.src+"_"+ip.dst+"_"+str(udptcp.sport)+"_"+str(udptcp.dport)#[protocol,socket.inet_ntop(socket.AF_INET, ip.src),socket.inet_ntop(socket.AF_INET, ip.dst),udptcp.sport,udptcp.dport,ip.len,ts]

                            #if len(tuples)==0 or searchTCPUDPTuple(ip,ts,tuples,fileName,0)=="NotFound":
                                #udptcp/tcp,ip.src,ip.dst,sport,dport,ip.len,ts_start,ts_end,dur,count,googlevideo
                                #tuples.append([protocol,socket.inet_ntop(socket.AF_INET, ip.src),socket.inet_ntop(socket.AF_INET, ip.dst),udptcp.sport,udptcp.dport,ip.len,ts,0.0,0.0,1,""])
                            #if ip.dst==cdnIPs
                            if socket.inet_ntop(socket.AF_INET, ip.src)==machineIP:
                                try:
                                    cdnIPs.index(socket.inet_ntop(socket.AF_INET, ip.dst))
                                    #print tuples
                                    if len(tuples)==0 or searchTCPUDPTuple(ip,ts,tuples,fileName,0)=="NotFound":
                                        #udptcp/tcp,ip.src,ip.dst,sport,dport,ip.len,ts_start,ts_end,dur,count,googlevideo
                                        tuples.append([protocol,socket.inet_ntop(socket.AF_INET, ip.src),socket.inet_ntop(socket.AF_INET, ip.dst),udptcp.sport,udptcp.dport,ip.len,ts,0.0,0.0,1,""])
                                        #print tuples
                                except Exception as e:#if not found in cdnIPs
                                    pass
                except Exception as e:
                    #print e
                    pass
    except Exception as e:
        pass
    #print len(tuplesNP)
    #if type=="getPackets":
    #    return np.array(packetsUDPTCP)#np.array(tuplesNP),
    #if type=="getTuples":
    return np.array(packetsUDPTCP),np.array(tuples)

def getTPInterTimePacketSize(maxTuples,packets,machineIP):
    dl=0
    ul=0
    DLThroughputs=[]
    ULThroughputs=[]
    t_start=0 # variable for calculating DL Throughput per bin
    t_start_v=0 # variable for calculating DL Throughput per bin_v
    DLbuffer=0 # buffer for calculating DL Throughput per bin
    DLbuffer_v=0 # buffer for calculating DL Throughput per bin_v
    bin_v_Index=0 # Index of bin_v in DLThroughputsVector
    bin=1.0
    prevUL=[]
    prevDL=[]
    ULinterTimes=[]
    DLinterTimes=[]
    DLPacketSizes=[]
    totalPacketCount=len(packets)
    NUMBER_OF_BINS=100

    totalDuration=float(packets[totalPacketCount-1,TS_START])-float(packets[0,TS_START])
    bin_v=totalDuration/NUMBER_OF_BINS # Time Bins for calculating the DL throughput vector
    DLThroughputsVector=np.zeros(NUMBER_OF_BINS)
    DLThroughputsVector30=[]#First 30 seconds DL TP vector

    print "totalDuration",totalDuration
    print "bin_v",bin_v
    for p in packets:
        srcIP=""
        if machineIP!="":
            srcIP=machineIP
        else:
            srcIP=maxTuples[0][IP_SRC]
        if p[IP_SRC]==srcIP:#p[IP_DST]==maxTuples[0][IP_DST] and p[IP_SRC]==maxTuples[0][IP_SRC] :#UPLINK
            #print "UPLINK",p
            ul=ul+int(p[IP_LEN])
            #print "---------------------------------------------",srcIP,prevUL
            if len(prevUL)!=0:
                ULinterTimes.append(1000*float(p[TS_START])-1000*float(prevUL[TS_START]))
            prevUL=p
        elif p[IP_DST]==srcIP:#if p[IP_DST]==maxTuples[0][IP_SRC] and p[IP_SRC]==maxTuples[0][IP_DST] :#DOWNLINK
            #print "DOWNLINK",p[IP_LEN]
            DLPacketSizes.append(int(p[IP_LEN]))
            if len(prevDL)!=0:
                DLinterTimes.append(1000*float(p[TS_START])-1000*float(prevDL[TS_START]))
            prevDL=p
            dl=dl+int(p[IP_LEN])
            if t_start==0:
                t_start=float(p[TS_START])
                #DLbuffer=int(p[IP_LEN])
            diff=float(p[TS_START])-t_start
            if diff<= bin:
                DLbuffer=DLbuffer+int(p[IP_LEN])
            else:
                DLbuffer=int(8*DLbuffer/bin)
                DLThroughputs.append(DLbuffer)
                if len(DLThroughputsVector30)<30:
                    DLThroughputsVector30.append(DLbuffer)
                DLbuffer=int(p[IP_LEN])#Initialize the buffer again
                diff=float(p[TS_START])-t_start
                t_start=float(p[TS_START])

            ####Calculating the DL TP vector#####
            if t_start_v==0:
                t_start_v=float(p[TS_START])
                bin_v_Index=0
            diff_v=float(p[TS_START])-t_start_v
            '''if diff_v <= bin_v:
                DLbuffer_v=DLbuffer_v+int(p[IP_LEN])
            else:#Initialize the buffer

                DLbuffer_v=int(8*DLbuffer_v/bin_v)
                bin_v_Index=bin_v_Index+int(diff_v/bin_v)-1#Is the current packet in the next bin or not? Check index of bin relative to last bin
                DLThroughputsVector[bin_v_Index]=DLbuffer_v
                bin_v_Index=bin_v_Index+1

                DLbuffer_v=int(p[IP_LEN])#Initialize the buffer again

                diff_v=float(p[TS_START])-t_start_v
                t_start_v=float(p[TS_START])'''
            bin_v_Index=int(diff_v/bin_v)

            #print "t_start_v",t_start_v,"bin_v_Index",bin_v_Index,"diff_v",diff_v
            try:
                DLThroughputsVector[bin_v_Index]=DLThroughputsVector[bin_v_Index]+int(p[IP_LEN])
            except Exception as e:
                pass
            #####################################



    DLThroughputs.append(int(8*DLbuffer/bin))
    if len(DLThroughputsVector30)<30:
        DLThroughputsVector30.append(int(8*DLbuffer/bin))
    DLThroughputsVector30=np.append(np.array(DLThroughputsVector30),np.zeros(30-len(DLThroughputsVector30)))
    #print "DLThroughputsVector30",len(DLThroughputsVector30),",",DLThroughputsVector30
    #DLThroughputsVector[bin_v_Index]=int(8*DLbuffer_v/bin)
    DLThroughputsVector=8.0*DLThroughputsVector/bin_v

    return DLThroughputs,ULinterTimes,DLinterTimes,DLPacketSizes,DLThroughputsVector,DLThroughputsVector30,totalDuration,totalPacketCount
import time
def getPcapFeature(fileName,machineIP,cdns):
    t1s=time.time()
    print fileName
    #output=subprocess.call(["pcapfix",fileName])#,shell=True)
    #correctedFile="fixed_"+fileName
    #t1=time.time()
    #if os.path.isfile(correctedFile):
    cdnIPs=getGoogleIPs(cdns)
    packetsUDPTCP,tuples=getPackets(fileName,cdnIPs,machineIP)#,"getPackets")
    #print "time getPackets",time.time()-t1
    #tuples=[]
    #print type(tuples),tuples
    cdnTuples=[]
    output=""
    '''t2=time.time()
    try:
        print "Trying to read via tshark"
        output=subprocess.check_output("tshark -2 -r "+fileName+" -R 'ssl.handshake.extensions_server_name contains \"googlevideo.com\" || quic.tag.sni contains \"googlevideo.com\"' -E separator=, -T fields -e ip.proto -e ip.src -e ip.dst -e tcp.srcport -e tcp.dstport -e udp.srcport -e udp.dstport -e ssl.handshake.extensions_server_name -e quic.tag.sni -e tcp.stream -e udp.stream",shell=True)
        #output=subprocess.check_output("tshark -2 -r "+fileName+" -E separator=, -T fields -e ip.proto -e ip.src -e ip.dst -e tcp.srcport -e tcp.dstport -e udp.srcport -e udp.dstport -e ssl.handshake.extensions_server_name -e quic.tag.sni -e tcp.stream -e udp.stream",shell=True)

        #print output
    except Exception as e:
        pass


    for s in output.split("\n"):
        d=s.split(",")
        if len(d[0])>0:
        #[protocol,socket.inet_ntop(socket.AF_INET, ip.src),socket.inet_ntop(socket.AF_INET, ip.dst),udptcp.sport,udptcp.dport,ip.len,ts]
            tuples.append([int(d[0]),d[1],d[2],int(d[3]+d[5]),int(d[4]+d[6]),d[7]+d[8]])
       #    [6, '138.96.203.5', '193.51.224.141', 44176, 443, 1998086, 1511445317.159531, 1511445324.450589, 7.291057825088501, 1629, 'r2---sn-gxo5uxg-jqbe.googlevideo.com']

    tuples=np.array(tuples)
    print "t2",time.time()-t2'''
    #exit()



    t1=time.time()

    if cdns!="":
        chunkInfo=getKMeansChunk(tuples,packetsUDPTCP)
        #print "getKMeansChunk",time.time()-t1
        #print "chunkInfo",chunkInfo
    else:
       chunkInfo=[]

    #exit()
    DLTP,ULt,DLt,DLpkt,DLTPvector,DLTPvector30,totalDuration,totalPacketCount=getTPInterTimePacketSize(tuples,packetsUDPTCP,machineIP)
    if len(DLTP)==0:
        DLTP=[0]
    if len(ULt)==0:
        ULt=[0]
    if len(DLt)==0:
        DLt=[0]
    if len(DLpkt)==0:
        DLpkt=[0]

    return [np.average(DLTP),np.average(ULt),np.average(DLt),np.average(DLpkt),\
            np.max(DLTP),np.max(ULt),np.max(DLt),np.max(DLpkt),\
            np.std(DLTP),np.std(ULt),np.std(DLt),np.std(DLpkt),\
            np.percentile(DLTP,10),np.percentile(ULt,10),np.percentile(DLt,10),np.percentile(DLpkt,10),\
            np.percentile(DLTP,20),np.percentile(ULt,20),np.percentile(DLt,20),np.percentile(DLpkt,20),\
            np.percentile(DLTP,30),np.percentile(ULt,30),np.percentile(DLt,30),np.percentile(DLpkt,30),\
            np.percentile(DLTP,40),np.percentile(ULt,40),np.percentile(DLt,40),np.percentile(DLpkt,40),\
            np.percentile(DLTP,50),np.percentile(ULt,50),np.percentile(DLt,50),np.percentile(DLpkt,50),\
            np.percentile(DLTP,60),np.percentile(ULt,60),np.percentile(DLt,60),np.percentile(DLpkt,60),\
            np.percentile(DLTP,70),np.percentile(ULt,70),np.percentile(DLt,70),np.percentile(DLpkt,70),\
            np.percentile(DLTP,80),np.percentile(ULt,80),np.percentile(DLt,80),np.percentile(DLpkt,80),\
            np.percentile(DLTP,90),np.percentile(ULt,90),np.percentile(DLt,90),np.percentile(DLpkt,90),\
            ]+list(DLTPvector)+list(DLTPvector30)+[totalDuration,totalPacketCount],chunkInfo,cdnIPs

if __name__=="__main__":
    #pcapStats,chunkInfoPcap,cdnIPs=getPcapFeature("pcapTestcases/youtubeTest.pcap","172.20.10.3",["r1---sn-4gxx-25gel.googlevideo.com"])#
    tm=time.time()
    pcapStats,chunkInfoPcap,cdnIPs=getPcapFeature("pcapTestcases/YouTube_corrupted.pcap","138.96.203.5",["r5---sn-hgn7rn7k.googlevideo.com"])#
    #pcapStats2,chunkInfoPcap2,cdnIPs2=getPcapFeature("pcapTestcases/fixed_YouTube_corrupted.pcap","138.96.203.5",["r5---sn-hgn7rn7k.googlevideo.com"])#
    #pcapStats,chunkInfoPcap,cdnIPs=getPcapFeature("pcapTestcases/youtubeTest.pcap","172.20.10.3",["r1---sn-4gxx-25gel.googlevideo.com"])#

    print pcapStats
    print chunkInfoPcap
    print cdnIPs
    print time.time()-tm



    #print pcapStats2,chunkInfoPcap2,cdnIPs2

