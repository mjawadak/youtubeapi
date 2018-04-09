import numpy as np
import copy
import math
import warnings
from sklearn.cluster import KMeans
import time

warnings.filterwarnings("ignore")
class ClfClass:
    def __init__(self, clf, totalRuns,nIterations,numberOfClasses,features,noOfFeatures,ranges,type=1):
        self.clf=copy.copy(clf)
        self.numberOfClasses=numberOfClasses
        self.classCount=np.zeros((totalRuns,numberOfClasses))


        self.features=features
        self.noOfFeatures=noOfFeatures

        self.training=np.zeros(noOfFeatures+1).reshape(1,noOfFeatures+1)

        self.RANGES=ranges
        self.SAMPLING_TYPE=type #1 =active, 0=random_real
        #print "self.RANGES",self.RANGES



    def initialize(self, pool):#,totalRuns,nIterations,numberOfClasses):
        #self.training=np.copy(initialTrainingSet)
        self.pool=np.copy(pool)
        #self.CLASS=np.unique(pool[:,3])
        #self.tempC=np.zeros(len(self.CLASS))

        #self.totalClassCounts=[]
        totalClassCountsValidation=[]
        #for c in range(0,self.numberOfClasses):
            #self.totalClassCounts.append(len(pool[pool[:,3]==self.CLASS[c],:]))

    def selectPointIndex(self,runs,iteration,data,type,threshold=0,kmeansType="min"):#POOL BASED SAMPLING



        if type=="random" or iteration<=20:
            indexRandom=np.random.randint(0,len(data))
            return {"indexRandom":indexRandom,"indexOfMaxEntropy":indexRandom}

        if type=="max"or type=="threshold":#type=="max" or
            prob=self.clf.predict_proba(data[:,0:3])
            logProb=self.clf.predict_log_proba(data[:,0:3])
            logProb=np.nan_to_num(logProb)
            #print "logProb",logProb
            entropy=(-1*np.sum(np.multiply(prob,logProb),axis=1))

        if type=="max":

            maxEntropy=np.nanmax(entropy)
            if math.isnan(maxEntropy):
                maxEntropy=0.0

            if maxEntropy>0:
                maxEntropyIndexes=np.where(entropy==maxEntropy)[0]
                maxIndex=np.random.randint(0,len(maxEntropyIndexes))
                indexOfMaxEntropy=maxEntropyIndexes[maxIndex]
            else:
                indexOfMaxEntropy= np.random.randint(0,len(data))
                maxEntropyIndexes=[]
            #print "maxEntropy",maxEntropy,len(data),indexOfMaxEntropy
            #self.uncertainty_array[runs,iteration]=maxEntropy
            #print "maxEntropy",maxEntropy,len(entropy),np.unique(entropy,return_counts=True),np.array(self.clf.tree_.__getstate__())
            return {"maxEntropy":maxEntropy,
                "indexOfMaxEntropy":indexOfMaxEntropy,
                "len(maxEntropyIndexes)":len(maxEntropyIndexes)}


    def avgGlobalAccuracy(self):
        return np.average(self.globalAccuracy_array,axis=0)
    def avgMeanDeviation(self):
        return np.average(self.meanDeviaion_array,axis=0)
    def avgUncertainty(self):
        return np.average(self.uncertainty_array,axis=0)
    def avgUncertaintyNormalized(self):
        u=np.average(self.uncertainty_array,axis=0)
        uMax=float(np.max(u))
        u_normalized=u/uMax
        return u_normalized
    def avgClassCount(self):
        return np.average(self.count_array,axis=0)
    def avgClassCDF(self):
        avgClassCDF=np.average(self.count_array,axis=0)
        for c in range(0,self.numberOfClasses):
            avgClassCDF[c,:]=avgClassCDF[c,:]/self.totalClassCounts[c]
        return avgClassCDF
    def avgHomogeneityMean(self):
        return np.average(self.homogeneityMean_array,axis=0)
    def avgHomogeneityMin(self):
        return np.average(self.homogeneityMin_array,axis=0)
    def avgHomogeneityMax(self):
        return np.average(self.homogeneityMax_array,axis=0)
    def avgConfMean(self):
        return np.average(self.ConfMean_array,axis=0)
    def avgConfMin(self):
        return np.average(self.ConfMin_array,axis=0)
    def avgConfMax(self):
        return np.average(self.ConfMax_array,axis=0)
    def avgDTleafCount(self):
        return np.average(self.DTleafCount_array,axis=0)
    def avgDTConfMeanDiff(self):
        return np.average(self.DTConfMeanDiff_array,axis=0)


    def trainAndUpdateAccuracy(self,runs,iteration,isDT=True):
        t1=time.clock()
        self.clf.fit(self.training[:,0:3],self.training[:,3])
        #self.globalAccuracy_array[runs,iteration]=self.clf.score(validation[:,0:3],validation[:,3])

        #absDiff=np.abs(self.clf.predict(validation[:,0:3])-validation[:,3])
        #self.meanDeviaion_array[runs,iteration]=np.average(absDiff[absDiff!=0])

        self.homogeneityMean_array[runs,iteration]=self.getHomogeneityOfDTleaves()['avgent']
        self.homogeneityMin_array[runs,iteration]=self.getHomogeneityOfDTleaves()['minent']
        self.homogeneityMax_array[runs,iteration]=self.getHomogeneityOfDTleaves()['maxent']

        self.ConfMean_array[runs,iteration]=self.getHomogeneityOfDTleaves()['avgConf']
        self.ConfMin_array[runs,iteration]=self.getHomogeneityOfDTleaves()['minConf']
        self.ConfMax_array[runs,iteration]=self.getHomogeneityOfDTleaves()['maxConf']

        if isDT==True:
            self.updateLeafCountAndDiffConfArray(runs,iteration)
            

        #if runs==1 and iteration==478:
        #print self.globalAccuracy_array[runs,iteration]
    def loadCells(self):
        self.cells=np.loadtxt("cell_distributionALL.csv",delimiter=",")
        cell_col=10#11
        self.cells=self.cells[np.argsort(self.cells[:,cell_col])]
        self.ncp=np.cumsum(self.cells[:,cell_col])
        with open('cell_distributionALL.csv') as f:
            first_line = f.readline()
        self.cell_headers=first_line.split("#")[1].split(",")
        self.cellsMlab=np.loadtxt("cell_distributionMlab.csv",delimiter=",")
        self.cellsNetz=np.loadtxt("cell_distributionNetz.csv",delimiter=",")
        with open('cell_distributionMlab.csv') as f:
            first_line = f.readline()
        self.cellMlab_headers=first_line.split("#")[1].split(",")
        with open('cell_distributionNetz.csv') as f:
            first_line = f.readline()
        self.cellNetz_headers=first_line.split("#")[1].split(",")
    def selectPoint(self,runs,iteration,type):

        if type=="random_real":

            #cp=np.sort(self.cells[:,10])[::-1]

            #print self.cells[:,11]
            #print ncp
            t1=time.time()
            r=np.random.uniform(low=0,high=1)
            for i in range(1,len(self.ncp)):
                if r>=self.ncp[i-1] and r<self.ncp[i]:
                    break
            #if self.cells[i][0]==7000.7 and self.cells[i][0][2]==300.3:
            #print r,self.cells[i],i,time.time()-t1
            #download_kbps_low,upload_kbps_low,ping_ms_low,std_ms_low,loss_low
            dl_tp=np.random.uniform(self.cells[i][0],self.cells[i][5])
            ul_tp=np.random.uniform(self.cells[i][1],self.cells[i][6])
            rtt=np.random.uniform(self.cells[i][2],self.cells[i][7])
            rtt_std=np.random.uniform(self.cells[i][3],self.cells[i][8])
            loss=np.random.uniform(self.cells[i][4],self.cells[i][9])
            return [dl_tp,ul_tp,rtt,rtt_std,loss]

        elif type=="random" or iteration<=20:
            if self.features=="rtt,loss,tp":
                rtt=np.random.uniform(self.RANGES[0][0],self.RANGES[0][1])
                loss=np.random.uniform(self.RANGES[1][0],self.RANGES[1][1])
                tp=np.random.uniform(self.RANGES[2][0],self.RANGES[2][1])
                return [rtt,loss,tp]
            if self.features=="synthetic_2":
                rtt=np.random.uniform(0,1)
                loss=np.random.uniform(0,1)
                return [rtt,loss]
            if self.features=="rtt,tp,bitrate,dur":
                rtt=np.random.uniform(self.RANGES[0][0],self.RANGES[0][1])
                tp=np.random.uniform(self.RANGES[1][0],self.RANGES[1][1])
                br=np.random.uniform(self.RANGES[2][0],self.RANGES[2][1])
                dur=np.random.uniform(self.RANGES[3][0],self.RANGES[3][1])
                return [rtt,tp,br,dur]



        if type=="DT":

            dtNodes=np.array(self.clf.tree_.__getstate__()['nodes'].tolist())
            dtValues=np.array(self.clf.tree_.__getstate__()['values'].tolist())

            #print np.array(self.clf.tree_.__getstate__())


            leafIndexes=np.where(dtNodes[:,0]==-1)[0]
            #print "dtValues[leafIndexes]",dtValues[leafIndexes]
            #print dtNodes
            #print "---"
            leafDetails=[]
            leafEntropies=[]
            leafProbs=[]
            for p in leafIndexes:

                d=np.where(dtNodes[:,0]==p)[0]
                lg=-1
                index=p
                v=[]
                path=[]
                #print "-----",p
                indexOfDT=-1

                while index!=0:
                    d=np.where(dtNodes[:,0]==index)[0]
                    if d.shape[0]==1:
                        lg=0
                        index=np.where(dtNodes[:,0]==index)[0]
                    else:
                        lg=1
                        index=np.where(dtNodes[:,1]==index)[0]
                    featureIndex=int(dtNodes[index,2])
                    threshold=dtNodes[index,3]
                    #print "--->",p,index,featureIndex,lg,threshold,values,leafProb,leafEntropy#,dtNodes[index,:]
                    path.append([index,featureIndex,lg,threshold])#,values,leafProb,leafEntropy])
                path=np.array(path)
                values=dtValues[p]
                leafProb=values/np.sum(values)
                leafEntropy=np.sum(-1*np.nan_to_num(np.log(leafProb))*leafProb)
                leafDetails.append([p,path,values,leafProb,leafEntropy])
                leafProbs.append(leafProb)
                leafEntropies.append(leafEntropy)
            leafProbs=np.array(leafProbs)

                #print "leafEntropy",leafEntropy#,values,len(leafIndexes),"-",dtNodes
                #print path[:,6],#np.max(path[:,6])
                #print np.where(path[:,6]==np.max(path[:,6]))[0]
            #print "leafEntropies:",leafEntropies
            #print "leafDetails",leafDetails

            leafEntropies=np.array(leafEntropies)
            uniqueEnts=np.sort(np.unique(leafEntropies))[::-1]
            indexOfDT=-1
            #print "maxEntLeaf=",leafDetails[0][2]
            found=0
            #print np.where(leafEntropies==np.max(leafEntropies))[0]
            indexesOfMaxEntLeaf=np.where(leafEntropies==np.max(leafEntropies))[0]
            indexOfMaxEntLeaf=indexesOfMaxEntLeaf[np.random.randint(0,len(indexesOfMaxEntLeaf))]
            maxPath=leafDetails[indexOfMaxEntLeaf][1]
            #print "maxPath",maxPath
            _id=np.linspace(0,len(data)-1,len(data))# id of points in dataset
            _id=_id.reshape(len(_id),1)
            vM=np.concatenate((_id,data),axis=1)#Pool data with IDs
            v=np.concatenate((_id,data),axis=1)#Pool data with IDs. This is sliced and compared with vM
            for g in maxPath:
                #print "GBefore",len(v),g[3],g[1],g[2]
                if g[2]==0:
                    v=v[v[:,g[1]+1]<=float(g[3])]#g[1]+1=Index of the feature(+1 for additional id column)
                else:
                    v=v[v[:,g[1]+1]>float(g[3])]
                #print "GAfter",len(v)
            if len(v)>0:
                found=1
                iV=np.random.randint(0,len(v))
                indexOfDT=np.where(vM[:,0]==v[iV,0])[0][0]
                #break
            #print len(vM),len(data),maxPath,"leafDetails",leafDetails,np.max(self.clf.predict_proba(data[:,0:3]),axis=0)
            #print "np.max",np.unique(np.max(self.clf.predict_proba(data[:,0:3]),axis=1)).shape
            indexesToExclude=[]
            indexesToExclude.append(indexOfMaxEntLeaf)
            while(found!=1):#Only start this loop if the sliced data size is zero and no point is found
                m=np.zeros(len(leafEntropies))
                for iExclude in indexesToExclude:
                    m[iExclude]=1
                leafEntropiesMasked=np.ma.array(leafEntropies,mask=m)
                #print np.max(leafEntropiesMasked)
                indexesOfMaxEntLeaf=np.where(leafEntropies==np.max(leafEntropiesMasked))[0]
                indexOfMaxEntLeaf=indexesOfMaxEntLeaf[np.random.randint(0,len(indexesOfMaxEntLeaf))]
                maxPath=leafDetails[indexOfMaxEntLeaf][1]
                _id=np.linspace(0,len(data)-1,len(data))# id of points in dataset
                _id=_id.reshape(len(_id),1)
                vM=np.concatenate((_id,data),axis=1)#Pool data with IDs
                v=np.concatenate((_id,data),axis=1)#Pool data with IDs. This is sliced and compared with vM
                for g in maxPath:
                    if g[2]==0:
                        v=v[v[:,g[1]+1]<=g[3]]
                    else:
                        v=v[v[:,g[1]+1]>g[3]]
                #print "len(v)",len(v)
                if len(v)>0:
                    found=1
                    iV=np.random.randint(0,len(v))
                    indexOfDT=np.where(vM[:,0]==v[iV,0])[0][0]
                    break
                else:
                    indexesToExclude.append(indexOfMaxEntLeaf)


            '''for l in range(len(uniqueEnts)):

                indexesOfLeafMaxEnt=np.where(leafEntropies==uniqueEnts[l])[0]
                print "len(indexesOfLeafMaxEnt)",len(indexesOfLeafMaxEnt),indexesOfLeafMaxEnt
                while len(indexesOfLeafMaxEnt)>0:#found!=1:
                    #print p,leafEntropy

                    iMaxLeaf=np.random.randint(0,len(indexesOfLeafMaxEnt))
                    #print indexesOfLeafMaxEnt,leafDetails[indexesOfLeafMaxEnt[iMaxLeaf]][1].shape

                    path=leafDetails[indexesOfLeafMaxEnt[iMaxLeaf]][1]
                    print "path",path
                    _id=np.linspace(0,len(data)-1,len(data))# id of points in dataset
                    _id=_id.reshape(len(_id),1)
                    vM=np.concatenate((_id,data),axis=1)
                    v=np.concatenate((_id,data),axis=1)
                    #print v
                    #exit()
                    for g in path:
                        if g[2]==0:
                            v=v[v[:,g[1]]<=g[3]]
                        else:
                            v=v[v[:,g[1]]>g[3]]
                    #print l,len(v),indexesOfLeafMaxEnt,len(indexesOfLeafMaxEnt)
                    if len(v)==0:
                        #if len(indexesOfLeafMaxEnt)>1:
                        indexesOfLeafMaxEnt=np.delete(indexesOfLeafMaxEnt,iMaxLeaf)
                        #else:
                            #break
                    elif len(v)>0 :
                        found=1
                        iV=np.random.randint(0,len(v))
                        indexOfDT=np.where(vM[:,0]==v[iV,0])[0][0]
                        break
                #print '----whileEnd'
                if found==1:
                    break

            if p==0:
                indexOfDT=np.random.randint(0,len(data))

            #exit()'''
            prob=self.clf.predict_proba(data[indexOfDT,0:3])
            logProb=self.clf.predict_log_proba(data[indexOfDT,0:3])
            logProb=np.nan_to_num(logProb)
            #print "logProb",logProb
            entropy=(-1*np.sum(np.multiply(prob,logProb),axis=1))
            print "indexOfDT",indexOfDT,entropy,leafEntropies[indexOfMaxEntLeaf]#,len(v),len(leafIndexes),leafDetails

            return {"index":indexOfDT}


        if (type=="DTHybridMaxEntropy" or type=="DTHybrid" or type=="DTHybridScaled" or type=="DTHybridScaled2") and iteration>20:

            dtNodes=np.array(self.clf.tree_.__getstate__()['nodes'].tolist())
            dtValues=np.array(self.clf.tree_.__getstate__()['values'].tolist())

            #print np.array(self.clf.tree_.__getstate__())


            leafIndexes=np.where(dtNodes[:,0]==-1)[0]
            leafValues=dtValues[leafIndexes]
            #print "dtValues[leafIndexes]",dtValues[leafIndexes]
            #print dtNodes
            #print "---"
            leafDetails=[]
            leafEntropies=[]
            leafProbs=[]
            for p in leafIndexes:

                d=np.where(dtNodes[:,0]==p)[0]
                lg=-1
                index=p
                v=[]
                path=[]
                #print "-----",p
                indexOfDT=-1

                while index!=0:
                    d=np.where(dtNodes[:,0]==index)[0]
                    if d.shape[0]==1:
                        lg=0
                        index=np.where(dtNodes[:,0]==index)[0]
                    else:
                        lg=1
                        index=np.where(dtNodes[:,1]==index)[0]
                    featureIndex=int(dtNodes[index,2])
                    threshold=dtNodes[index,3]
                    #print "--->",p,index,featureIndex,lg,threshold,values,leafProb,leafEntropy#,dtNodes[index,:]
                    path.append([index,featureIndex,lg,threshold])#,values,leafProb,leafEntropy])
                path=np.array(path)
                values=dtValues[p]
                leafProb=values/np.sum(values)
                leafEntropy=np.sum(-1*np.nan_to_num(np.log(leafProb))*leafProb)
                leafDetails.append([p,path,values,leafProb,leafEntropy])
                leafProbs.append(leafProb)
                leafEntropies.append(leafEntropy)
            leafProbs=np.array(leafProbs)

                #print "leafEntropy",leafEntropy#,values,len(leafIndexes),"-",dtNodes
                #print path[:,6],#np.max(path[:,6])
                #print np.where(path[:,6]==np.max(path[:,6]))[0]
            #print "leafEntropies:",leafEntropies
            #print "leafDetails",leafDetails

            leafEntropies=0.1+np.array(leafEntropies)
            uniqueEnts=np.sort(np.unique(leafEntropies))[::-1]
            indexOfDT=-1
            #print "maxEntLeaf=",leafDetails[0][2]
            found=0
            #print np.where(leafEntropies==np.max(leafEntropies))[0]
            #indexesOfMaxEntLeaf=np.where(leafEntropies==np.max(leafEntropies))[0]
            if type=="DTHybrid" or type=="DTHybridScaled" or type=="DTHybridScaled2":
                indexOfMaxEntLeaf=self.chooseBestLeafForHybrid(leafEntropies,leafProbs,leafValues,type)#indexesOfMaxEntLeaf[np.random.randint(0,len(indexesOfMaxEntLeaf))]
            elif type=="DTHybridMaxEntropy":
                leafEntropies=np.array(leafEntropies)
                indexOfMaxEntLeaf=np.argmax(leafEntropies)
            maxPath=leafDetails[indexOfMaxEntLeaf][1]
            #print "maxPath",maxPath

            if self.features=="rtt,loss,tp":
                A=(self.RANGES)#np.array([[0,5000],[0,0.25],[0,10000]])#RTT/LOSS/TP MIN/MAX array
                MIN=0
                MAX=1
                RTT=0
                LOSS=1
                TP=2
                for g in maxPath:
                    if g[2]==0 and g[3]<=A[g[1],MAX]:
                        A[g[1],MAX]=g[3]
                        #print oper[g[1]],"<=",g[3]
                    elif g[2]==1 and g[3]>A[g[1],MIN]:
                        A[g[1],MIN]=g[3]

                #print A
                #print "selectedLeafIndex=",indexOfMaxEntLeaf
                #print leafEntropies
                #print "selectedLeafValues=",leafValues[indexOfMaxEntLeaf]
                rtt=np.random.uniform(A[RTT,MIN],A[RTT,MAX])
                loss=np.random.uniform(A[LOSS,MIN],A[LOSS,MAX])
                tp=np.random.uniform(A[TP,MIN],A[TP,MAX])

                return [rtt,loss,tp]

            if self.features=="synthetic_2":
                A=np.array(self.RANGES)#np.array([[0.0,1.0],[0.0,1.0]])#RTT/LOSS/TP MIN/MAX array
                MIN=0
                MAX=1
                RTT=0
                LOSS=1

                for g in maxPath:
                    if g[2]==0 and g[3]<=A[g[1],MAX]:
                        A[g[1],MAX]=g[3]
                        #print oper[g[1]],"<=",g[3]
                    elif g[2]==1 and g[3]>A[g[1],MIN]:
                        A[g[1],MIN]=g[3]

                #print A
                #print leafValues
                #print "A",A
                #print "selectedLeafIndex=",indexOfMaxEntLeaf
                #print leafEntropies
                #print "selectedLeafValues=",leafValues[indexOfMaxEntLeaf]
                rtt=np.random.uniform(A[RTT,MIN],A[RTT,MAX])
                loss=np.random.uniform(A[LOSS,MIN],A[LOSS,MAX])

                return [rtt,loss]
            if self.features=="rtt,tp,bitrate,dur":
                A=np.array(self.RANGES)#np.array([[0,5000],[0,0.25],[0,10000]])#RTT/LOSS/TP MIN/MAX array
                MIN=0
                MAX=1
                RTT=0
                TP=1
                BITR=2
                DUR=3
                #print "before",A,self.RANGES
                for g in maxPath:
                    if g[2]==0 and g[3]<=A[g[1],MAX]:
                        A[g[1],MAX]=g[3]
                        #print oper[g[1]],"<=",g[3]
                    elif g[2]==1 and g[3]>A[g[1],MIN]:
                        A[g[1],MIN]=g[3]
                    #print "--",A

                #print A
                #print "selectedLeafIndex=",indexOfMaxEntLeaf
                #print leafEntropies
                #print "selectedLeafValues=",leafValues[indexOfMaxEntLeaf]
                rtt=np.random.uniform(A[RTT,MIN],A[RTT,MAX])
                tp=np.random.uniform(A[TP,MIN],A[TP,MAX])
                br=np.random.uniform(A[BITR,MIN],A[BITR,MAX])
                dur=np.random.uniform(A[DUR,MIN],A[DUR,MAX])
                return [rtt,tp,br,dur]
    def updateTrainingSet(self,iteration,point):
        point=point.reshape(1,len(point))
        #print point.shape,self.training.shape
        self.training=np.append(self.training,point,axis=0)
        if iteration==0:
            self.training=np.delete(self.training,0,axis=0)#remove 1st zeros row

    def train(self):
        self.clf.fit(self.training[:,0:self.noOfFeatures],self.training[:,self.noOfFeatures])

    def updateTrainingSetandPool(self,runs,iteration,index):
        #c=np.where(self.CLASS==self.pool[index,3])[0][0]
        #self.classCount[runs,c]+=1.0
        #for c in range(0,self.numberOfClasses):
            #self.count_array[runs,c,iteration]=self.classCount[runs,c]
        print self.pool.shape,self.training.shape
        self.training=np.append(self.training,[self.pool[index,0:4]],axis=0)
        self.pool=np.delete(self.pool,index,0)

    def getMinDistIndex(self,clusterPoints,points,selectedCluster):
        #for i in range(clusterPoints.shape[0]):
        c=clusterPoints[selectedCluster,:]
        #print c
        distancesFromSelectedCluster=np.sum(np.square(points[:,0:3]-c),axis=1)
        indexOfminDist=np.argmin(distancesFromSelectedCluster)
        return indexOfminDist

    def getHomogeneityOfDTleaves(self):
        values=np.array(self.clf.tree_.value)
        childrenLeft=np.array(self.clf.tree_.children_left)
        childrenRight=np.array(self.clf.tree_.children_right)
        dif=childrenLeft-childrenRight
        leaves=np.sum(values[np.where(dif==0)[0]],axis=1)#np.sum just to change the shape of leaves
        m=np.sum(leaves,axis=1)
        m=m.reshape(len(m),1)

        prob=leaves/m
        log=np.log(prob)
        #print "-leaves",leaves
        #print "prob",prob
        #print "log",log
        #print "ents",np.sum(-1*np.nan_to_num(log)*prob,axis=1)
        avgent=np.average(np.sum(-1*np.nan_to_num(log)*prob,axis=1))
        minent=np.min(np.sum(-1*np.nan_to_num(log)*prob,axis=1))
        maxent=np.max(np.sum(-1*np.nan_to_num(log)*prob,axis=1))

        avgConf=np.average(np.max(prob,axis=1))
        minConf=np.min(np.max(prob,axis=1))
        maxConf=np.max(np.max(prob,axis=1))
        #print "prob",prob,avgConf,minConf,maxConf
        #exit()
        #print {"avgent":avgent,"minent":minent,"maxent":maxent}

        return {"avgent":avgent,"minent":minent,"maxent":maxent,"avgConf":avgConf,"minConf":minConf,"maxConf":maxConf}

    def updateLeafCountAndDiffConfArray(self,runs,iteration):
        dtNodes=np.array(self.clf.tree_.__getstate__()['nodes'].tolist())
        dtValues=np.array(self.clf.tree_.__getstate__()['values'].tolist())

        leafIndexes=np.where(dtNodes[:,0]==-1)[0]
        leafProbs=[]
        for p in leafIndexes:
            values=dtValues[p]
            leafProb=values/np.sum(values)
            leafProbs.append(leafProb)

        leafProbs=np.array(leafProbs)


        leafClass=[]
        leafProbs=np.sum(leafProbs,axis=1)#to reduce the number of dimensions from 3 to 2
        confPerClass=np.concatenate((np.max(leafProbs,axis=1).reshape(len(leafProbs),1),np.argmax(leafProbs,axis=1).reshape(len(leafProbs),1)),axis=1)
        diffConf=0
        for i in range(len(self.CLASS)-1):
            diffConf=np.abs(np.average(confPerClass[confPerClass[:,1]==i][:,0])-np.average(confPerClass[confPerClass[:,1]==i+1][:,0]))
        #print "-----------------conf",np.average(confPerClass[confPerClass[:,1]==0][:,0]),np.average(confPerClass[confPerClass[:,1]==1][:,0])
        #print "conf",np.average(confPerClass[confPerClass[:,1]==0],axis=1),np.average(confPerClass[confPerClass[:,1]==1],axis=1)
        #for leaf in leafProbs:
            #print len(leafProbs),np.argmax(leaf[3])
        self.DTleafCount_array[runs,iteration]=len(leafProbs)
        self.DTConfMeanDiff_array[runs,iteration]=diffConf

    def chooseBestLeafForHybrid(self,leafEntropies,leafProbs,leafValues,type):
        leafEntropies=np.array(leafEntropies)
        leafWeights=leafEntropies/float(np.sum(leafEntropies))
        #print "leafEntropies",leafEntropies
        if type=="DTHybridScaled" or type=="DTHybridScaled2":
            leafValues=np.array(leafValues).astype(float)
            CLASSVALUES=np.sum(leafValues,axis=0)
            C=CLASSVALUES/np.sum(CLASSVALUES)
            Cinv=1/C
            if type=="DTHybridScaled2":
                Cinv=1/(C**4)
            C=Cinv/np.sum(Cinv)
            leafWP=leafProbs*C
            leafWP=np.sum(leafWP,axis=1)#to remove addtional axis
            leafWP=np.sum(leafWP,axis=1)
            # leafWP: Weight for each class calculated based on the respected overall ratio in collected
            # dataset. For minor class, higher weight
            leafWP=leafWP/np.sum(leafWP)
            leafWeights=leafWeights*leafWP
            #print "leafValues",leafValues
            #print leafWeights/np.sum(leafWeights)
            #print np.sum(leafWeights/np.sum(leafWeights))
            ##print C
           # print leafWP
            #print "CLASSVALUES",CLASSVALUES

        leafWeights=leafWeights/np.sum(leafWeights)
        #print "leafWeights",leafWeights
        b=np.cumsum(leafWeights)
        a=np.zeros(len(b)+1)
        a[1:]=b
        p=np.random.uniform(0,1)
        for i in range(len(leafEntropies)):
            if p>=a[i] and p<b[i]:
                break
        #print "leafProbs:",leafProbs,a,b,"best=",leafProbs[i],p,len(leafProbs)
        return i
    def getDTclassPredictions(self):
        dtNodes=np.array(self.clf.tree_.__getstate__()['nodes'].tolist())
        dtValues=np.array(self.clf.tree_.__getstate__()['values'].tolist())

        leafIndexes=np.where(dtNodes[:,0]==-1)[0]
        leafValues=dtValues[leafIndexes]
        leafValues=np.sum(leafValues,axis=1)#to remove one axis
        #print leafValues.shape
        classPred=np.argmax(leafValues,axis=1)
        classPredUnique=np.unique(np.argmax(leafValues,axis=1))
        print np.max(leafValues,axis=1)
        print np.sum(leafValues,axis=1)
        classProb=np.max(leafValues,axis=1)/np.sum(leafValues,axis=1)
        for c in classPredUnique:
            print c,np.min(classProb[np.where(classPred==c)])


    def getLeafEntropies(self):
        dtNodes=np.array(self.clf.tree_.__getstate__()['nodes'].tolist())
        dtValues=np.array(self.clf.tree_.__getstate__()['values'].tolist())

        #print np.array(self.clf.tree_.__getstate__())


        leafIndexes=np.where(dtNodes[:,0]==-1)[0]
        leafValues=dtValues[leafIndexes]
        #print "dtValues[leafIndexes]",dtValues[leafIndexes]
        #print dtNodes
        #print "---"
        leafDetails=[]
        leafEntropies=[]
        leafProbs=[]
        for p in leafIndexes:

            d=np.where(dtNodes[:,0]==p)[0]
            lg=-1
            index=p
            v=[]
            path=[]
            #print "-----",p
            indexOfDT=-1

            while index!=0:
                d=np.where(dtNodes[:,0]==index)[0]
                if d.shape[0]==1:
                    lg=0
                    index=np.where(dtNodes[:,0]==index)[0]
                else:
                    lg=1
                    index=np.where(dtNodes[:,1]==index)[0]
                featureIndex=int(dtNodes[index,2])
                threshold=dtNodes[index,3]
                #print "--->",p,index,featureIndex,lg,threshold,values,leafProb,leafEntropy#,dtNodes[index,:]
                path.append([index,featureIndex,lg,threshold])#,values,leafProb,leafEntropy])
            path=np.array(path)
            values=dtValues[p]
            leafProb=values/np.sum(values)
            leafEntropy=np.sum(-1*np.nan_to_num(np.log(leafProb))*leafProb)
            leafDetails.append([p,path,values,leafProb,leafEntropy])
            leafProbs.append(leafProb)
            leafEntropies.append(leafEntropy)
        leafProbs=np.array(leafProbs)

            #print "leafEntropy",leafEntropy#,values,len(leafIndexes),"-",dtNodes
            #print path[:,6],#np.max(path[:,6])
            #print np.where(path[:,6]==np.max(path[:,6]))[0]
        #print "leafEntropies:",leafEntropies
        #print "leafDetails",leafDetails

        leafEntropies=np.array(leafEntropies)

        #A=np.array([[0,5000],[0,0.25],[0,10000]])#RTT/LOSS/TP MIN/MAX array
        totalVolume=1
        rangesPerFeature=[]
        for s in self.RANGES:
            rangesPerFeature.append(s[1]-s[0])
            totalVolume=totalVolume*(s[1]-s[0])#5000.0*0.25*10000.0
        leafVolumeRatios=[]
        #print "--",len(dtNodes),len(leafEntropies)
        for i in range(len(leafEntropies)):
            thisPath=leafDetails[i][1]
                #print "maxPath",maxPath

            A=np.array(self.RANGES)#np.array([[0,5000],[0,0.25],[0,10000]])#RTT/LOSS/TP MIN/MAX array

            MIN=0
            MAX=1
            RTT=0
            LOSS=1
            TP=2
            oper=["RTT","LOSS","TP"]
            o=["<=",">"]
            for g in thisPath:
                #print oper[g[1]],o[g[2]],g[3]
                if g[2]==0 and g[3]<=A[g[1],MAX]:
                    A[g[1],MAX]=g[3]
                    #print oper[g[1]],"<=",g[3]
                elif g[2]==1 and g[3]>A[g[1],MIN]:
                    A[g[1],MIN]=g[3]
                    #print oper[g[1]],">",g[3]
            #print thisPath
            #print "A",A
            leafVolumeRatio=1
            for i in range(len(A)):
                leafVolumeRatio=leafVolumeRatio*float((A[i,1]-A[i,0]))/rangesPerFeature[i]
            #print i,A#A[RTT,MAX]-A[RTT,MIN],A[LOSS,MAX]-A[LOSS,MIN],A[TP,MAX]-A[TP,MIN]
            #leafVolumeRatio=(float(A[RTT,MAX]-A[RTT,MIN])*float(A[LOSS,MAX]-A[LOSS,MIN])*float(A[TP,MAX]-A[TP,MIN]))/totalVolume
            leafVolumeRatios.append(leafVolumeRatio)

        return leafValues,leafProbs,leafEntropies,leafVolumeRatios

    def getWeightedConf(self,CLASS):
        leafValues,leafProbs,leafEntropies,leafVolumeRatios=self.getLeafEntropies()

        MIN_ENTROPY=np.min(leafEntropies)
        MAX_ENTROPY=np.max(leafEntropies)
        STD_ENTROPY=np.std(leafEntropies)

        leafProbs=np.average(leafProbs,axis=1)##remove one axis
        le=leafProbs.shape[0]
        classArgs=np.argmax(leafProbs,axis=1).reshape(le,1)
        conf=np.concatenate((CLASS[classArgs],np.max(leafProbs,axis=1).reshape(le,1)),axis=1)
        vol=np.array(leafVolumeRatios)
        #print vol.shape,conf[:,1].shape
        volC=np.concatenate((conf[:,0].reshape(le,1),vol.reshape(le,1)),axis=1)

        confVol=(conf[:,1]*vol)
        confVol=np.concatenate((conf[:,0].reshape(le,1),confVol.reshape(le,1)),axis=1)
        print conf
        print leafProbs
        print leafValues
        #entropyAVG.append(np.average(leafEntropies))
        #print np.sum(leafEntropies*vol)
        WEIGHTED_AVG_ENTROPY=np.sum(leafEntropies*vol)#np.average(leafEntropies))

        MIN_CONF_PERCLASS=[]
        MAX_CONF_PERCLASS=[]
        STD_CONF_PERCLASS=[]
        WEIGHTED_AVG_CONF_PERCLASS=[]
        VOL_PERCLASS=[]
        LEAFCOUNT=[]
        cfWeightedSum=[]
        #print "conf",len(conf)
        #print conf[conf[:,0]==1]

        self.CLASS=CLASS
        for i in self.CLASS:#range(len(CLASS)):
            if len(conf[conf[:,0]==i])==0:

                MIN_CONF_PERCLASS.append(0)
                MAX_CONF_PERCLASS.append(0)
                STD_CONF_PERCLASS.append(0)
                WEIGHTED_AVG_CONF_PERCLASS.append(0)
                VOL_PERCLASS.append(0)
                cfWeightedSum.append(0)
            else:
                #cfAVG.append(np.average(conf[conf[:,0]==i][:,1]))
                MIN_CONF_PERCLASS.append(np.min(conf[conf[:,0]==i][:,1]))
                MAX_CONF_PERCLASS.append(np.max(conf[conf[:,0]==i][:,1]))
                STD_CONF_PERCLASS.append(np.std(conf[conf[:,0]==i][:,1]))
                VOL_PERCLASS.append(np.sum(volC[volC[:,0]==i][:,1]))
                cfWeightedSum.append(np.sum(confVol[confVol[:,0]==i][:,1]))

            #volPerClass.append()
        WEIGHTED_AVG_CONF_PERCLASS=np.nan_to_num(np.array(cfWeightedSum)/np.array(VOL_PERCLASS))

        LEAFCOUNT=len(leafEntropies)

        return [MIN_ENTROPY,\
               MAX_ENTROPY,\
               STD_ENTROPY,\
               MIN_CONF_PERCLASS,\
               MAX_CONF_PERCLASS,\
               STD_CONF_PERCLASS,\
               WEIGHTED_AVG_CONF_PERCLASS,\
               VOL_PERCLASS,\
               LEAFCOUNT]

    def getWeightedConfMeasure(self,CLASS):
        leafValues,leafProbs,leafEntropies,leafVolumeRatios=self.getLeafEntropies()
        leafProbs=np.average(leafProbs,axis=1)##remove one axis
        le=leafProbs.shape[0]
        conf=np.concatenate((np.argmax(leafProbs,axis=1).reshape(le,1),np.max(leafProbs,axis=1).reshape(le,1)),axis=1)
        vol=np.array(leafVolumeRatios)
        confVol=(conf[:,1]*vol)
        confVol=np.concatenate((conf[:,0].reshape(le,1),confVol.reshape(le,1)),axis=1)
        volC=np.concatenate((conf[:,0].reshape(le,1),vol.reshape(le,1)),axis=1)
        #print "leafValues",np.sum(leafValues,axis=1)
        leafCounts=np.sum(np.sum(leafValues,axis=1),axis=1)
        #print "leafCounts",leafCounts
        #print "totalCount",np.sum(leafCounts)
        #print "leafCountRatio",leafCounts/np.sum(leafCounts)
        volRow=[]
        cfWeightedSum=[]

        for i in CLASS:
            if len(conf[conf[:,0]==i])==0:
                volRow.append(0)
                cfWeightedSum.append(0)
            else:
                volRow.append(np.sum(volC[volC[:,0]==i][:,1]))
                cfWeightedSum.append(np.sum(confVol[confVol[:,0]==i][:,1]))

        return np.nan_to_num(np.array(cfWeightedSum)/np.array(volRow)),volRow

  
