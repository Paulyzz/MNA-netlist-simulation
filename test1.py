import matplotlib.pyplot as plt
import numpy as np
import matlab.engine
import Element
import copy
import time
import math
import random
eng = matlab.engine.start_matlab()
netlist_name=raw_input('Enter the file name: ')
tstart=time.time()
netlist_fileID=eng.fopen(str(netlist_name))
#Initialize
num_Elements=0; #Number of passive elements
num_V=0; #Number of independent voltage sources
num_ACV=0 #Number of independent AC voltage sources
num_I=0; #Number of independent current sources
num_ACI=0 #Number of independent AC current sources
num_Nodes=0; #Number of nodes, excluding ground (node 0)
num_L=0; #Number of inductors
num_C=0; #Number of Capacitors
num_VCVS=0
num_VCCS=0
num_CCVS=0
num_CCCS=0
num_DependentSources=0
curr_node=0
minfreq=0
maxfreq=0
freqAn=0
tranAn=0
time_step=0
stop_time=0
Elements=[]
Inductors=[]
Capacitors=[]
Volt_sources=[]
Current_sources=[]
VCVS=[]
VCCS=[]
CCVS=[]
CCCS=[]

netlist=eng.textscan(netlist_fileID,'%s %s %s %s %s %s %s')
eng.fclose(netlist_fileID)

def loaddata(s,Name,N1,N2,N3,N4,V):
    if (s[0]=="R" or s[0]=="L" or s[0]=="C"):
        nElement=Element.Element(Name,N1,N2,V)
        Elements.append(nElement)
        global num_Elements
        num_Elements=num_Elements+1
        if (s[0]=="L"):
            nElement=Element.Element(Name,N1,N2,V)
            Inductors.append(nElement)
            global num_L
            num_L=num_L+1
        elif (s[0]=="C"):
            nElement=Element.Element(Name,N1,N2,V)
            Capacitors.append(nElement)
            global num_C
            num_C=num_C+1
    elif (s[0]=="V"):
        if (N4==0):
            print(N3)
            nVolt=Element.Element(Name,N1,N2,V)
            Volt_sources.append(nVolt)
            global num_V
            num_V=num_V+1
        else:
            nACVolt=Element.Dependent_Source(Name,N1,N2,N3,N4,V)
            Volt_sources.append(nACVolt)
            global num_ACV
            num_ACV=num_ACV+1
            global num_V
            num_V=num_V+1
    elif (s[0]=="I"):
        if (N4==0):
            nCurr=Element.Element(Name,N1,N2,V)
            Current_sources.append(nCurr)
            global num_I
            num_I=num_I+1
        else:
            print("error")
            nACCurr=Element.Dependent_Source(Name,N1,N2,N3,N4,V)
            Current_sources.append(nACCurr)
            global num_ACI
            num_ACI=num_ACI+1
            global num_I
            num_I=num_I+1
    elif (s[0]=="E"):
        nVCVS=Element.Dependent_Source(Name,N1,N2,N3,N4,V)
        VCVS.append(nVCVS)
        global num_VCVS
        num_VCVS=num_VCVS+1
        global num_DependentSources
        num_DependentSources=num_DependentSources+1
    elif (s[0]=="G"):
        y=""
        for i in V:
          if (i=="E"):
            y+="*10**"
          else:
            y+=i
        V=eval(y)
        nVCCS=Element.Dependent_Source(Name,N1,N2,N3,N4,V)
        VCCS.append(nVCCS)
        global num_VCCS
        num_VCCS=num_VCCS+1
        num_DependentSources=num_DependentSources+1
    elif (s[0]=="H"):
        nCCVS=Element.Dependent_Source(Name,N1,N2,N3,N4,V)
        CCVS.append(nCCVS)
        global num_CCVS
        num_CCVS=num_CCVS+1
        global num_DependentSources
        num_DependentSources=num_DependentSources+1
    elif (s[0]=="F"):
        y=""
        for i in V:
          if (i=="E"):
            y+="*10**"
          else:
            y+=i
        V=eval(y)
        nCCCS=Element.Dependent_Source(Name,N1,N2,N3,N4,V)
        CCCS.append(nCCCS)
        global num_CCCS
        num_CCCS=num_CCCS+1
        num_DependentSources=num_DependentSources+1
    global num_Nodes
    num_Nodes=max(N1,max(N2,num_Nodes));
    

for i in range(np.size(netlist[0])):
    s = netlist[0][i]
    if (s[0]!="."):
        Name=netlist[0][i]
        N1=int(netlist[1][i])
        N2=int(netlist[2][i])
        V=netlist[3][i]
    else:
        if (s[1]=="a"):
            freqAn=1
            minfreq=int(netlist[1][i])
            maxfreq=int(netlist[2][i])
        else:
            tranAn=1
            time_step=float(netlist[1][i])
            stop_time=float(netlist[2][i])
    if (s[0]=="E" or s[0]=="G"):
        N3=int(netlist[3][i])
        N4=int(netlist[4][i])
        V=netlist[5][i]
        loaddata(s,Name,N1,N2,N3,N4,V)
    elif(s[0]=="H" or s[0]=="F"):
        N3=netlist[3][i]
        N4=0
        V=netlist[4][i]
        loaddata(s,Name,N1,N2,N3,N4,V)
    elif(s[0]=="V" or s[0]=="I"):
        if (V[0]=="A"):
            V=float(netlist[4][i])
            N3=float(netlist[5][i])
            N4=float(netlist[6][i])
            loaddata(s,Name,N1,N2,N3,N4,V)
        else:
            loaddata(s,Name,N1,N2,0,0,V)
    elif(s[0]=="."):
        break
    else:
        loaddata(s,Name,N1,N2,0,0,V)

def MNA(freq):
    Gmatrix=np.zeros((int(num_Nodes),int(num_Nodes)),dtype = 'complex_')
    Bmatrix=np.zeros((int(num_Nodes),int(num_V+num_VCVS+num_CCVS)),dtype = 'complex_')
    Cmatrix=np.zeros((int(num_V+num_VCVS+num_CCVS),int(num_Nodes)),dtype = 'complex_')
    Dmatrix=np.zeros((int(num_V+num_VCVS+num_CCVS),int(num_V+num_VCVS+num_CCVS)),dtype = 'complex_')

    for i in Elements:
        Node1=i.Node1-1
        Node2=i.Node2-1
        Value=float(i.Value)
        if(i.Name[0]=="R"):
            if (i.Node1==0):
                Gmatrix[Node2][Node2]=Gmatrix[Node2][Node2]+float(1)/Value
            elif (i.Node2==0):
                Gmatrix[Node1][Node1]=Gmatrix[Node1][Node1]+float(1)/Value
            else:
                Gmatrix[Node1][Node1]=Gmatrix[Node1][Node1]+float(1)/Value
                Gmatrix[Node2][Node2]=Gmatrix[Node2][Node2]+float(1)/Value
                Gmatrix[Node1][Node2]=Gmatrix[Node1][Node2]-float(1)/Value
                Gmatrix[Node2][Node1]=Gmatrix[Node2][Node1]-float(1)/Value
        elif(i.Name[0]=="C"):
            if(freqAn==1):
                if (i.Node1==0):
                    Gmatrix[Node2][Node2]=Gmatrix[Node2][Node2]+complex(0,Value*freq)
                elif (i.Node2==0):
                    Gmatrix[Node1][Node1]=Gmatrix[Node1][Node1]+complex(0,Value*freq)
                else:
                    Gmatrix[Node1][Node1]=Gmatrix[Node1][Node1]+complex(0,Value*freq)
                    Gmatrix[Node2][Node2]=Gmatrix[Node2][Node2]+complex(0,Value*freq)
                    Gmatrix[Node1][Node2]=Gmatrix[Node1][Node2]-complex(0,Value*freq)
                    Gmatrix[Node2][Node1]=Gmatrix[Node2][Node1]-complex(0,Value*freq)
        elif(i.Name[0]=="L"):
            if(freqAn==1):
                if (i.Node1==0):
                    Gmatrix[Node2][Node2]=Gmatrix[Node2][Node2]+float(1)/complex(0,Value*freq)
                elif (i.Node2==0):
                    Gmatrix[Node1][Node1]=Gmatrix[Node1][Node1]+float(1)/complex(0,Value*freq)
                else:
                    Gmatrix[Node1][Node1]=Gmatrix[Node1][Node1]+float(1)/complex(0,Value*freq)
                    Gmatrix[Node2][Node2]=Gmatrix[Node2][Node2]+float(1)/complex(0,Value*freq)
                    Gmatrix[Node1][Node2]=Gmatrix[Node1][Node2]-float(1)/complex(0,Value*freq)
                    Gmatrix[Node2][Node1]=Gmatrix[Node2][Node1]-float(1)/complex(0,Value*freq)

    for S in VCCS:
        Node1=S.Node1-1
        Node2=S.Node2-1
        Node3=S.Node3-1
        Node4=S.Node4-1
        Value=float(S.Value)
        if (S.Node1==0):
            if (S.Node3==0):
                Gmatrix[Node2][Node4]+=Value
            elif(S.Node4==0):
                Gmatrix[Node2][Node3]-=Value
            else:
                Gmatrix[Node2][Node4]+=Value
                Gmatrix[Node2][Node3]-=Value
        elif(S.Node2==0):
            if (S.Node3==0):
                Gmatrix[Node1][Node4]-=Value
            elif(S.Node4==0):
                Gmatrix[Node1][Node3]+=Value
            else:
                Gmatrix[Node1][Node4]-=Value
                Gmatrix[Node1][Node3]+=Value
        else:
            if (S.Node3==0):
                Gmatrix[Node1][Node4]-=Value
                Gmatrix[Node2][Node4]+=Value
            elif(S.Node4==0):
                Gmatrix[Node2][Node3]-=Value
                Gmatrix[Node1][Node3]+=Value
            else:
                Gmatrix[Node1][Node4]-=Value
                Gmatrix[Node1][Node3]+=Value
                Gmatrix[Node2][Node4]+=Value
                Gmatrix[Node2][Node3]-=Value

    y=0
    for i in Volt_sources:
        Node1=i.Node1-1
        Node2=i.Node2-1
        Value=float(i.Value)
        if (i.Node1==0):
            Bmatrix[Node2][y]=-1
        elif (i.Node2==0):
            Bmatrix[Node1][y]=1
        else:
            Bmatrix[Node2][y]=-1
            Bmatrix[Node1][y]=1
        y+=1
    for V in VCVS:
        Node1=V.Node1-1
        Node2=V.Node2-1
        Value=float(V.Value)
        if (V.Node1==0):
            Bmatrix[Node2][y]=-1
        elif (V.Node2==0):
            Bmatrix[Node1][y]=1
        else:
            Bmatrix[Node2][y]=-1
            Bmatrix[Node1][y]=1
        y+=1
    for V in CCVS:
        Node1=V.Node1-1
        Node2=V.Node2-1
        Value=float(V.Value)
        if (V.Node1==0):
            Bmatrix[Node2][y]=-1
        elif (V.Node2==0):
            Bmatrix[Node1][y]=1
        else:
            Bmatrix[Node2][y]=-1
            Bmatrix[Node1][y]=1
        y+=1
    
    if(num_VCVS==0 and num_CCCS==0):
        Cmatrix=np.transpose(Bmatrix)
        
    else:
        Cmatrix=np.transpose(copy.deepcopy(Bmatrix))
        for C in CCCS:
            y=0
            Node1=C.Node1-1
            Node2=C.Node2-1
            for i in Volt_sources:
                if (C.Node3==i.Name):
                    if (C.Node1==0):
                        Bmatrix[Node2][y]-=float(C.Value)
                    elif (C.Node2==0):
                        Bmatrix[Node1][y]+=float(C.Value)
                    else:
                        Bmatrix[Node2][y]-=float(C.Value)
                        Bmatrix[Node1][y]+=float(C.Value)
                y+=1
            
        i=0
        for V in VCVS:
            Node3=V.Node3-1
            Node4=V.Node4-1
            Value=float(V.Value)
            if(V.Node3==0):
                Cmatrix[num_V+i][Node4]+=Value
            elif(V.Node4==0):
                Cmatrix[num_V+i][Node3]-=Value
            else:
                Cmatrix[num_V+i][Node3]-=Value
                Cmatrix[num_V+i][Node4]+=Value
            i+=1
    count=0
    for V in CCVS:
        x=0
        for i in Volt_sources:
            if (V.Node3==i.Name):
                Dmatrix[num_V+count][x]-=float(V.Value)
            x+=1
        count+=1
    N1matrix=np.concatenate((Gmatrix,Bmatrix),axis=1)
    N2matrix=np.concatenate((Cmatrix,Dmatrix),axis=1)
    Amatrix=np.concatenate((N1matrix,N2matrix))
    Zmatrix=np.zeros((int(num_V)+int(num_Nodes)+int(num_VCVS)+int(num_CCVS),1),dtype = 'complex_')
    for i in Current_sources:
        Node1=i.Node1-1
        Node2=i.Node2-1
        Value=float(i.Value)
        if (i.Node1==0):
            Zmatrix[Node2]+=Value
        elif (i.Node2==0):
            Zmatrix[Node1]-=Value
        else:
            Zmatrix[Node1]-=Value
            Zmatrix[Node2]+=Value
    count=0
    
    for v in Volt_sources:
        Zmatrix[int(num_Nodes)+count]=float(v.Value)
        count+=1
    Vmatrix=np.linalg.inv(Amatrix).dot(Zmatrix)
    
    return Vmatrix[0:int(num_Nodes)]

def MNAtran(curr_t, t_step, past_voltage, past_current):
    Gmatrix=np.zeros((int(num_Nodes),int(num_Nodes)),dtype = 'complex_')
    Bmatrix=np.zeros((int(num_Nodes),int(num_V+num_VCVS+num_CCVS)),dtype = 'complex_')
    Cmatrix=np.zeros((int(num_V+num_VCVS+num_CCVS),int(num_Nodes)),dtype = 'complex_')
    Dmatrix=np.zeros((int(num_V+num_VCVS+num_CCVS),int(num_V+num_VCVS+num_CCVS)),dtype = 'complex_')
    
    ACElements=copy.deepcopy(Elements)
    ACCurrent_sources=copy.deepcopy(Current_sources)
    num_c=1
    num_i=0
    for i in Capacitors:
        Node1=i.Node1
        Node2=i.Node2
        Value= t_step/float(i.Value)
        Name="RC{}".format(num_c)
        cElements=Element.Element(Name, Node1, Node2, Value)
        ACElements.append(cElements)
        if len(past_voltage) == 0:
            Value=0
            cCurrent_sources=Element.Element(Name, Node1, Node2,Value)
            ACCurrent_sources.append(cCurrent_sources)
        else:
            if (Node1==0):
                Value=float(i.Value)/t_step*past_voltage[Node2-1]
                cCurrent_sources=Element.Element(Name, Node1, Node2,Value)
                ACCurrent_sources.append(cCurrent_sources)
            elif (Node2==0):
                Value=float(i.Value)/t_step*past_voltage[Node1-1]
                cCurrent_sources=Element.Element(Name, Node2, Node1,Value)
                ACCurrent_sources.append(cCurrent_sources)
            else:
                if (Node1<Node2):
                    Value=float(i.Value)/t_step*(past_voltage[Node1-1]-past_voltage[Node2-1])
                    cCurrent_sources=Element.Element(Name, Node2, Node1,Value)
                    ACCurrent_sources.append(cCurrent_sources)
                else:
                    Value=float(i.Value)/t_step*(past_voltage[Node1-1]-past_voltage[Node2-1])
                    cCurrent_sources=Element.Element(Name, Node1, Node2,Value)
                    ACCurrent_sources.append(cCurrent_sources)
        num_c+=1

    for i in Inductors:
        num_i+=1
        Node1=i.Node1
        Node2=i.Node2
        Value= float(i.Value)/t_step
        Name="RL{}".format(num_i)
        cElements=Element.Element(Name, Node1, Node2, Value)
        ACElements.append(cElements)
        if len(past_current) == 0:
            Value=0
            cCurrent_sources=Element.Element(Name, Node1, Node2,Value)
            ACCurrent_sources.append(cCurrent_sources)
        else:
            if (Node1==0):
                Value=past_current[num_i-1]
                cCurrent_sources=Element.Element(Name, Node2, Node1,Value)
                ACCurrent_sources.append(cCurrent_sources)
            elif (Node2==0):
                Value=past_current[num_i-1]
                cCurrent_sources=Element.Element(Name, Node1, Node2,Value)
                ACCurrent_sources.append(cCurrent_sources)
            else:
                if (Node1<Node2):
                    Value=past_current[num_i-1]
                    cCurrent_sources=Element.Element(Name, Node1, Node2,Value)
                    ACCurrent_sources.append(cCurrent_sources)
                else:
                    Value=past_current[num_i-1]
                    cCurrent_sources=Element.Element(Name, Node2, Node1,Value)
                    ACCurrent_sources.append(cCurrent_sources)
        
    for i in ACElements:
        Node1=i.Node1-1
        Node2=i.Node2-1
        Value=float(i.Value)
        if(i.Name[0]=="R"):
            if (i.Node1==0):
                Gmatrix[Node2][Node2]=Gmatrix[Node2][Node2]+float(1)/Value
            elif (i.Node2==0):
                Gmatrix[Node1][Node1]=Gmatrix[Node1][Node1]+float(1)/Value
            else:
                Gmatrix[Node1][Node1]=Gmatrix[Node1][Node1]+float(1)/Value
                Gmatrix[Node2][Node2]=Gmatrix[Node2][Node2]+float(1)/Value
                Gmatrix[Node1][Node2]=Gmatrix[Node1][Node2]-float(1)/Value
                Gmatrix[Node2][Node1]=Gmatrix[Node2][Node1]-float(1)/Value
        

    for S in VCCS:
        Node1=S.Node1-1
        Node2=S.Node2-1
        Node3=S.Node3-1
        Node4=S.Node4-1
        Value=float(S.Value)
        if (S.Node1==0):
            if (S.Node3==0):
                Gmatrix[Node2][Node4]+=Value
            elif(S.Node4==0):
                Gmatrix[Node2][Node3]-=Value
            else:
                Gmatrix[Node2][Node4]+=Value
                Gmatrix[Node2][Node3]-=Value
        elif(S.Node2==0):
            if (S.Node3==0):
                Gmatrix[Node1][Node4]-=Value
            elif(S.Node4==0):
                Gmatrix[Node1][Node3]+=Value
            else:
                Gmatrix[Node1][Node4]-=Value
                Gmatrix[Node1][Node3]+=Value
        else:
            if (S.Node3==0):
                Gmatrix[Node1][Node4]-=Value
                Gmatrix[Node2][Node4]+=Value
            elif(S.Node4==0):
                Gmatrix[Node2][Node3]-=Value
                Gmatrix[Node1][Node3]+=Value
            else:
                Gmatrix[Node1][Node4]-=Value
                Gmatrix[Node1][Node3]+=Value
                Gmatrix[Node2][Node4]+=Value
                Gmatrix[Node2][Node3]-=Value

    y=0
    for i in Volt_sources:
        Node1=i.Node1-1
        Node2=i.Node2-1
        Value=float(i.Value)
        if (i.Node1==0):
            Bmatrix[Node2][y]=-1
        elif (i.Node2==0):
            Bmatrix[Node1][y]=1
        else:
            Bmatrix[Node2][y]=-1
            Bmatrix[Node1][y]=1
        y+=1
    for V in VCVS:
        Node1=V.Node1-1
        Node2=V.Node2-1
        Value=float(V.Value)
        if (V.Node1==0):
            Bmatrix[Node2][y]=-1
        elif (V.Node2==0):
            Bmatrix[Node1][y]=1
        else:
            Bmatrix[Node2][y]=-1
            Bmatrix[Node1][y]=1
        y+=1
    for V in CCVS:
        Node1=V.Node1-1
        Node2=V.Node2-1
        Value=float(V.Value)
        if (V.Node1==0):
            Bmatrix[Node2][y]=-1
        elif (V.Node2==0):
            Bmatrix[Node1][y]=1
        else:
            Bmatrix[Node2][y]=-1
            Bmatrix[Node1][y]=1
        y+=1
    
    if(num_VCVS==0 and num_CCCS==0):
        Cmatrix=np.transpose(Bmatrix)
        
    else:
        Cmatrix=np.transpose(copy.deepcopy(Bmatrix))
        for C in CCCS:
            y=0
            Node1=C.Node1-1
            Node2=C.Node2-1
            for i in Volt_sources:
                if (C.Node3==i.Name):
                    if (C.Node1==0):
                        Bmatrix[Node2][y]-=float(C.Value)
                    elif (C.Node2==0):
                        Bmatrix[Node1][y]+=float(C.Value)
                    else:
                        Bmatrix[Node2][y]-=float(C.Value)
                        Bmatrix[Node1][y]+=float(C.Value)
                y+=1
            
        i=0
        for V in VCVS:
            Node3=V.Node3-1
            Node4=V.Node4-1
            Value=float(V.Value)
            if(V.Node3==0):
                Cmatrix[num_V+i][Node4]+=Value
            elif(V.Node4==0):
                Cmatrix[num_V+i][Node3]-=Value
            else:
                Cmatrix[num_V+i][Node3]-=Value
                Cmatrix[num_V+i][Node4]+=Value
            i+=1
    count=0
    for V in CCVS:
        x=0
        for i in Volt_sources:
            if (V.Node3==i.Name):
                Dmatrix[num_V+count][x]-=float(V.Value)
            x+=1
        count+=1
    N1matrix=np.concatenate((Gmatrix,Bmatrix),axis=1)
    N2matrix=np.concatenate((Cmatrix,Dmatrix),axis=1)
    Amatrix=np.concatenate((N1matrix,N2matrix))
    Zmatrix=np.zeros((int(num_V)+int(num_Nodes)+int(num_VCVS)+int(num_CCVS),1),dtype = 'complex_')
    for i in ACCurrent_sources:
        Node1=i.Node1-1
        Node2=i.Node2-1
        Value=i.Value
        if (i.Node1==0):
            Zmatrix[Node2]+=Value
        elif (i.Node2==0):
            Zmatrix[Node1]-=Value
        else:
            Zmatrix[Node1]-=Value
            Zmatrix[Node2]+=Value
    count=0
    
    for v in Volt_sources:
        Zmatrix[int(num_Nodes)+count]=float(v.Value)*math.sin(2*math.pi*float(v.Node4)*curr_t+float(v.Node3))
        count+=1
    Vmatrix=np.linalg.inv(Amatrix).dot(Zmatrix)
    num_i=0
    Ind_current=[]
    for i in Inductors:
        num_i+=1
        Node1=i.Node1
        Node2=i.Node2
        Value=float(i.Value)
        if len(past_current) == 0:
            if (Node1==0):
                value_i=t_step*Vmatrix[Node2-1]/Value 
                Ind_current.append(value_i)
            elif (Node2==0):
                value_i=t_step*Vmatrix[Node1-1]/Value
                Ind_current.append(value_i)
            else:
                if (Node1<Node2):
                    value_i=t_step*(Vmatrix[Node1-1]-Vmatrix[Node2-1])/Value
                    Ind_current.append(value_i)
                else:
                    value_i=t_step*(Vmatrix[Node2-1]-Vmatrix[Node1-1])/Value
                    Ind_current.append(value_i)
        else:
            if (Node1==0):
                value_i=t_step*Vmatrix[Node2-1]/Value+past_current[num_i-1] 
                Ind_current.append(value_i)
            elif (Node2==0):
                value_i=t_step*Vmatrix[Node1-1]/Value+past_current[num_i-1]
                Ind_current.append(value_i)
            else:
                if (Node1<Node2):
                    value_i=t_step*(Vmatrix[Node1-1]-Vmatrix[Node2-1])/Value+past_current[num_i-1]
                    Ind_current.append(value_i)
                else:
                    value_i=t_step*(Vmatrix[Node2-1]-Vmatrix[Node1-1])/Value+past_current[num_i-1]
                    Ind_current.append(value_i)
    if len(Ind_current) == 0:
        Resultmatrix=Vmatrix[0:int(num_Nodes)]
    else:
        Resultmatrix=np.concatenate((Vmatrix[0:int(num_Nodes)],Ind_current))
    return Resultmatrix


if (tranAn!=0):
    print("----------------------------------")
    print("Node Voltage:")
    times=np.arange(0,stop_time, time_step)
    results=[]
    ansresult=[]
    for i in times:
        if not results:
            result=MNAtran(i,time_step,[],[])
            for x in range(0,num_Nodes):
                ansresult.append([])
                ansresult[x].append(result[x])
            results.append(result)
        else:
            if (len(results[-1]) == num_Nodes):
                result=MNAtran(i,time_step,results[-1],[])
                for x in range(0,num_Nodes):
                    ansresult[x].append(result[x])
                results.append(result)
            else:
                result=MNAtran(i,time_step,results[-1][0:int(num_Nodes)],results[-1][int(num_Nodes):])
                for x in range(0,num_Nodes):
                    ansresult[x].append(result[x])
                results.append(result)
    num_grap=1
    random.seed(5)
    for x in ansresult:
        plot=plt.figure(num_grap)
        color = (random.random(), random.random(), random.random())
        plt.plot(times, x, label='V{}'.format(num_grap),c=color)
        plt.xlabel('time(s)')
        plt.ylabel('Voltage(V)')
        plt.legend(loc='best')
        plt.tight_layout()
        num_grap+=1
    tfinish=time.time()-tstart
    print("time:")
    print(tfinish)
    plt.show()
    
elif (freqAn!=0):
    print("----------------------------------")
    print("Node Voltage:")
    freqlist=np.arange(minfreq, maxfreq, float(maxfreq-minfreq)/200)
    curr_node=0
    miny=0
    maxy=0
    for x in range(0,num_Nodes):
        curr_node+=1
        x=[]
        for i in freqlist:
            if (i==0):
                i=0.00000001
            x.append(float(MNA(i)[curr_node-1].real**2+MNA(i)[curr_node-1].imag**2)**(0.5))
        x=np.array(x)
        maxy=np.amax(x) if max(x)>maxy else maxy
        miny=np.amin(x) if min(x)<maxy else miny
        plt.plot(freqlist, x, label='V{}'.format(curr_node))
    tfinish=time.time()-tstart
    print("time:")
    print(tfinish)
    plt.xlabel('time(s)')
    plt.ylabel('Voltage(V)')
    plt.ylim(miny-(maxy-miny)/50, maxy+(maxy-miny)/50)
    plt.legend(loc='best')
    plt.tight_layout()
    plt.show()
elif(num_C==0 and num_L==0):
    print("----------------------------------")
    print("Node Voltage:")
    result=MNA(0)
    for x in result:
        global curr_node
        curr_node+=1
        print("V{:d} = {:.3f}".format(curr_node,x[0].real))
    tfinish=time.time()-tstart
    print("time:")
    print(tfinish)   
    #time=np.arange(0.001, 4, 0.1)
    #result=MNA()
    #for x in result:
        #curr_node+=1
        #x=[x for i in time]
        #plt.plot(time, x, label='V{}'.format(curr_node))
    #plt.xlabel('time(s)')
    #plt.ylabel('Voltage(V)')
    #plt.ylim(-0.1, 13)
    #plt.legend(loc='best')
    #plt.tight_layout()
    #plt.show()
else:
    C_range=[]
    C_range.append([1,int(num_Nodes)])
    for C in Capacitors:
        C_loop=0
        if(abs(C.Node1-C.Node2)<2):
            if (min(C.Node1,C.Node2)!=0):
                check=0
                for i in Elements:
                    if(i.Node1==C.Node1 and i.Node2==C.Node2 and i.Name[0]=="R"):
                        check=1
                        break
                    if(i.Node2==C.Node1 and i.Node1==C.Node2 and i.Name[0]=="R"):
                        check=1
                        break
                if(check==0):   
                    for R in C_range: 
                        if(int(max(C.Node1,C.Node2))<=R[1] and R[0]<=int(min(C.Node1,C.Node2))):
                            C_range.pop(C_loop)
                            C_range.insert(C_loop,[R[0],min(C.Node1,C.Node2)])
                            C_range.insert(C_loop+1,[max(C.Node1,C.Node2),R[1]])
                            break;
                        C_loop=+1
   
    print("----------------------------------")
    print("Node Voltage:")
    for R in C_range:
        num_Elements=0; #Number of passive elements
        num_V=0; #Number of independent voltage sources
        num_I=0; #Number of independent current sources
        num_Nodes=0; #Number of nodes, excluding ground (node 0)
        Elements=[]
        Volt_sources=[]
        Current_sources=[]
        VCVS=[]
        VCCS=[]
        netlist_fileID=eng.fopen(netlist_name)
        netlist=eng.textscan(netlist_fileID,'%s %s %s %s %s %s')
        eng.fclose(netlist_fileID)
        for i in range(np.size(netlist[0])):
            s = netlist[0][i]
            Name=netlist[0][i]
            N1=int(netlist[1][i])
            N2=int(netlist[2][i])
            V=netlist[3][i]
            if (min(N1,N2)!=0):
                if(max(N1,N2)<=R[1] and R[0]<=min(N1,N2)):
                    N1=N1-(R[0]-1)
                    N2=N2-(R[0]-1)
                    if (s[0]=="E" or s[0]=="G"):
                        N3=int(netlist[3][i])
                        N4=int(netlist[4][i])
                        if(N3==0):
                            N4=N4-(R[0]-1)
                        elif(N4==0):
                            N3=N3-(R[0]-1)
                        else:
                            N3=N3-(R[0]-1)
                            N4=N4-(R[0]-1)
                        V=netlist[5][i]
                        loaddata(s,Name,N1,N2,N3,N4,V)
                    elif (s[0]=="F" or s[0]=="H"):
                        N3=netlist[3][i]
                        N4=0
                        V=netlist[4][i]
                        loaddata(s,Name,N1,N2,N3,N4,V)
                    else:
                        loaddata(s,Name,N1,N2,0,0,V)
            else:
                if(max(N1,N2)<=R[1] and R[0]<=max(N1,N2)):
                    if (N1==0):
                        N2=N2-(R[0]-1)
                    else:
                        N1=N1-(R[0]-1)
                        if (s[0]=="E" or s[0]=="G"):
                            N3=int(netlist[3][i])
                            N4=int(netlist[4][i])
                            if(N3==0):
                                N4=N4-(R[0]-1)
                            elif(N4==0):
                                N3=N3-(R[0]-1)
                            else:
                                N3=N3-(R[0]-1)
                                N4=N4-(R[0]-1)
                            V=netlist[5][i]
                            loaddata(s,Name,N1,N2,N3,N4,V)
                        elif (s[0]=="F" or s[0]=="H"):
                            N3=netlist[3][i]
                            N4=0
                            V=netlist[4][i]
                            loaddata(s,Name,N1,N2,N3,N4,V)
                        else:
                            loaddata(s,Name,N1,N2,0,0,V)
        for L in Inductors:
            nElement=Element.Element("R"+Name,N1,N2,0.0000001)
            Elements.append(nElement)
        result=MNA(0)
        for x in result:
            global curr_node
            curr_node+=1
            print("V{:d} = {:.3f}".format(curr_node,x[0].real))
        """times=np.arange(0.001, 1, 0.001)
        result=MNA(0)
        for x in result:
            global curr_node
            curr_node+=1
            x=[x for i in times]
            plt.plot(times, x, label='V{}'.format(curr_node))
    tfinish=time.time()-tstart
    print("time:")
    print(tfinish)
    plt.xlabel('time(s)')
    plt.ylabel('Voltage(V)')
    plt.legend(loc='best')
    plt.tight_layout()
    plt.show()"""
    

        
