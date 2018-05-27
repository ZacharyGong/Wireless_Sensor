# -*- coding: utf-8 -*-
"""
Script class base station
 
"""
from threading import  RLock
import thread

import time
import socket
import MsgHandler
import copy


class BaseStation():
    """Class defining a base station :
    - IPadresse
    - coordinate 
    - table of network """
    
    def __init__(self) :
        self._Ipadress = "127.0.0.1"
        self._coordinate   = [0,0]
        self.network = []
        self.allSensorData = "xixixixixi"
        self.networkLock = RLock()
        self.clusterH = []
        self.adrrCH = "0.0.0.0"
        
        
    @property
    def IPadress(self):
        return self._IPadress

    @IPadress.setter
    def IPadress(self, IP):
        self._IPadress  =  IP
        
        
    @property
    def coordinate(self):
        return self._coordinate

    @coordinate.setter
    def coordinate(self, (x,y)):
        self._coordinate  =  (x,y)
      
    
    def receive(self,addr_source, port_source):
        code=0
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind((addr_source, port_source)) 
        msgHandler=MsgHandler()
        while True:                                          
            data, addr = s.recvfrom(1024)
            print 'received' + data
            type_msg=msgHandler.Decode(data)
            if type_msg==1:
                temp,code=msgHandler.Decode_CH_Change_Msg(data)
                if code==0:
                    self.clusterHead=temp
                    self.RefreshNetwork(temp)
                    print 'CH changed:' + self.clusterHead
                else:
                    print "error in decoding CH change msg."
            elif type_msg==2:
                temp,code=msgHandler.Decode_List_Info_Msg(data)
                if code==0:
                    self.network=temp
                    print self.network
                else:
                    print "error in decoding list of info msg"
            elif type_msg==3:
                temp,code=msgHandler.Decode_Info_Msg(data)
                if code==0:                 
                    Ischanged=self.RefreshNode(temp)
                    print temp
                    print Ischanged
                else:
                    print 'Error in decoding info msg'
            elif type_msg==4:
                temp,code=msgHandler.Decode_Sensor_Data(data)
                if code==0:
                    self.allSensorData=self.allSensorData+temp  
                    with self.networkLock:
                        for i in range(len(self.network)):
                            if self.network[i][0] == self.addrCH:
                                self.network[i][3] = time.time()
                    print temp
                else:
                    print 'Error in decoding sensor data'               
                
            elif type_msg==0:
                print 'error in decode message'
                
            
    def RefreshNode(self,info):
        code    = 0
        coor    = [0,0]
        IsChange= False
        address      =  info[0]
        energy_level =  info[1]
        coor         =  info[2]
        try:
            with self.networkLock:
                for i in range(len(self.network)):
                    if self.network[i][0] == address:
                        self.network[i][1] = energy_level
                        self.network[i][2] = coor
                        self.network[i][3] = time.time()
                        IsChange = True
                        break
                if IsChange==False:
                    self.network.append(info)
                    self.network[len(self.network)][3] = time.time()
                
        except :
            print 'info updata failed.'
            code=1
    
    
    def send(self, addr_des, port_des, msg):
        code=0
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        addr = (addr_des, port_des)
        try:
            s.sendto(msg, addr)
            print 'sent:' + msg
        except:
            code=1
        finally:
            s.close()
            
    
    def alive(self, addr):
        for i in range(len(self.network)):
            if self.network[i][0] == addr:
                if (time.time()-self.network[i][3])<60:
                    return 1
                else:
                    return 0 
                
                
    def toBeCH(self):
        listNodeNoCH=[]
        with self.networkLock:
            
            for i in range(len(self.network)):
                NodeCH = False
                for j in range(len(self.clusterH)):
                    if self.network[i][0] == self.clusterH:
                        NodeCH = True 
                if NodeCH == False and self.alive(self.network[i][0]) == 1:
                    listNodeNoCH.append(self.network[i])
                    
            if len(listNodeNoCH) == 0:
                listNodeNoCH = copy.deepcopy(self.network)
                self.clusterH [:] = []

        e = listNodeNoCH[0][1]
        for i in range(1,listNodeNoCH):
            if listNodeNoCH[i][1] > e:
                self.adrrCH = listNodeNoCH[i][0]
                e           = listNodeNoCH[i][1]
                coorCH      = listNodeNoCH[i][2]
        self.clusterH.append(self.adrrCH)
        msgHandler = MsgHandler()
        msgCH = msgHandler.Encode_CH_Change_Msg(self.adrrCH,e,coorCH)
        print("New Cluster Head :", self.adrrCH)
        
        return self.adrrCH,msgCH
            
    def broadcast(self,msgCH):
        code=0
        try:
            broadcast = '<broadcast>'
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            broadcast_addr = (broadcast, 12800)
            s.sendto(msgCH, broadcast_addr)
            s.close()
        except:
            code=1
        return code
    
        
if __name__ == '__main__':
    base    = BaseStation()
    choseCH = time.time()
    while(1):
        
        if(time.time()-choseCH)>30:
            adrrCH, msgCH = base.toBeCH()
            base.send(adrrCH,12800,msgCH)
        
       
        
        
        
        
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    