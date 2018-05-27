# -*- coding: utf-8 -*-
"""
Script class base station
 
"""
import threading 
import thread
import time
import socket
from  MsgHandler import MsgHandler 
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
        self.networkLock = threading.Lock()
        self.clusterH = []
        self.adrrCH = "0.0.0.0"
        
        

    def _get_IPadress(self):
        return self._IPadress

    def _set_IPadress(self, IP):
        self._IPadress  =  IP
        
    _IPadress = property(_get_IPadress, _set_IPadress)
    
    def _get_coordinate(self):
        return self._coordinate

    def _set_coordinate(self, (x,y)):
        self._coordinate  =  (x,y)
    
    _coordinate = property(_get_coordinate, _set_coordinate)
        
    def _get_network(self):
        return self.network
    network = property(_get_network)
    
    def _get_adrrCH(self):
        return self.adrrCH
    adrrCH = property(_get_adrrCH)
    
    
    def receive(self,addr_source, port_source):
        print 'thread start'
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
                    print '-----------------3.--------'
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
                            if self.network[i][0][0] == self.addrCH:
                                self.network[i][0][3] = time.time()
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
        energy_level =  int(info[1])
        coor         =  info[2]
        try:
            print'rentre ds le lock' 
            print len(self.network)
            for i in range(len(self.network)):
                if self.network[i][0][0] == address:
                    self.network[i][0][1] = int(energy_level)
                    self.network[i][0][2] = coor
                    self.network[i][0][3] = time.time()
                    IsChange = True
                    break
            if IsChange==False:
                print str(info)
                self.network.append([info,time.time()])
                #self.network[len(self.network)][3] = time.time()    
        except :
            print 'info updata failed.'
            code=1
        return IsChange
    
    
    def send(self, addr_des, port_des, msg):
        code=0
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        addr = (addr_des, port_des)
        try:
            s.sendto(msg, addr)
            print 'sent:' + msg
        except:
            code=1
            print 'send error.'
        finally:
            s.close()
            
    
    def alive(self, addr):
        print(len(self.network))
        for i in range(len(self.network)):
            if self.network[i][0][0] == addr:
                print(i)
                if (time.time()-self.network[i][1])<1000:
                    return 1
                else:
                    return 0 
                
                
    def toBeCH(self):
        listNodeNoCH=[]
        for i in range(len(self.network)):
            NodeCH = False
            for j in range(len(self.clusterH)):
                if self.network[i][0][0] == self.clusterH[j][0]:
                    NodeCH = True 
            if NodeCH == False and self.alive(self.network[i][0][0]) == 1:
                listNodeNoCH.append(self.network[i])
        
        if len(listNodeNoCH) == 0:  
            listNodeNoCH = copy.deepcopy(self.network)
            self.clusterH [:] = []
        print('lisnoch')
        print(listNodeNoCH )

        e = listNodeNoCH[0][0][1]
        print("ener",e)
        coorCH = listNodeNoCH[0][0][2]
        for i in range(len(listNodeNoCH)):
            if listNodeNoCH[i][0][1] >= e:
                self.adrrCH = listNodeNoCH[i][0][0]
                e           = listNodeNoCH[i][0][1]
                coorCH      = listNodeNoCH[i][0][2]
        self.clusterH.append([self.adrrCH,e])
        print(self.clusterH)
        msgHandler = MsgHandler()
        print(coorCH)
        msgCH = msgHandler.Encode_CH_Change_Msg(self.adrrCH,e,coorCH)
        print("New Cluster Head :", self.adrrCH, e)
        
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
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    try :
        thread.start_new_thread(base.receive,( '', 14800,))
    except:
        print 'no'
        
    time.sleep(1)
    msgHandler=MsgHandler()
    msg = msgHandler.Encode_Info_Msg('12',100,[3,5])
    try:
        s.sendto(msg, ('127.0.0.1',14800))
        print 'sent:' + msg
    except:
        print'no send'
    '''finally:
        s.close()'''

    msg = msgHandler.Encode_Info_Msg('1',110,[2,8])
    try:
        s.sendto(msg, ('127.0.0.1',14800))
        print 'sent:' + msg
    except:
        print'no send'
    '''finally:
        s.close()'''
        
    msg = msgHandler.Encode_Info_Msg('2',80,[2,4])
    try:
        s.sendto(msg, ('127.0.0.1',14800))
        print 'sent:' + msg
    except:
        print'no send'
    finally:
        s.close()

        
    
    while(1):
        time.sleep(1)
        if len(base._get_network()) == 2:
           adrrCH, msgCH = base.toBeCH()
           base.send('127.0.0.1',12800,msgCH)
           choseCH=time.time()
           print(adrrCH+'1')
        
        if(time.time()-choseCH)>5:
            adrrCH, msgCH = base.toBeCH()
            base.send('127.0.0.1',12800,msgCH)
            choseCH=time.time()
            print(adrrCH+'2')
            
        if base.alive(base._get_adrrCH()) == 0:
            adrrCH, msgCH = base.toBeCH()
            base.send('127.0.0.1',12800,msgCH)
            choseCH=time.time()
            print(adrrCH+'3')
       
        
        
        
        
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
