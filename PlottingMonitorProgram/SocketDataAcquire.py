from ast import Dict
import socket 
import string
import asyncio 
import threading 
import time
from typing import Callable  

class DataLogging:
    def __init__(self, log_file_path: str):
        self.log_file_path = log_file_path
        self.lock = threading.Lock()  # Ensure thread-safe logging

    def LogDataPage(self, data: list[float]):
        with self.lock:
            with open(self.log_file_path, 'a') as f:
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                data_str = ', '.join(f"{d:.2f}" for d in data)
                f.write(f"{timestamp}, {data_str}\n") 


class DataTeachingRecords:
    def __init__(self, records_count = 3):
        self._recordsCount = records_count 
        self.teachedDict:dict = None  
        self.channelDictList:list[dict] = [] 
        for i in range(self._recordsCount):
            self.channelDictList.append(dict()) 


    def AddingNewRecords(self, records_name, value):
        self.teachedDict[records_name] = value 

    def GetFromRecords(self, records_name):
        if self.teachedDict.get(records_name) is not None:
            return self.teachedDict[records_name]
        else:
            return None

    def AddRecordInChannel(self, channel_name, records_name, records_value):
        if channel_name not in range(self._recordsCount):
            raise ValueError("Channel name is not in range") 
        else:
            _para = self.channelDictList[channel_name] 
            _para.update({records_name: records_value})
            self.channelDictList[channel_name] = _para 

    


class SocketDataAcquire:

    def __init__(self, hostname:str, port:int, dataAquireCb:Callable):
        self._hostName = hostname 
        self._port = port 
        self._cbFunction = dataAquireCb 
        self._socketAcquireTimeout = 5.0 
        self._receievedTime = time.time() 

    def AcquireDataEvent(self, aquireEvent:threading.Event):
        while not aquireEvent.is_set():
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(self._socketAcquireTimeout) 
                s.connect((self._hostName, self._port))
                while not aquireEvent.is_set():
                    data = s.recv(1024)
                    if not data:
                        break
                    try:
                        self._receievedTime = time.time() 
                        self._cbFunction(data) 
                    except Exception:
                        pass
                s.close()
            except Exception:
                time.sleep(1.0) # Retry delay

    async def WriteDataToSocketAsync(self, data: bytes): 
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        s.setblocking(False)

        loop = asyncio.get_running_loop() 
        try:
            await loop.sock_connect(s, (self._hostName, self._port)) 
            await loop.sock_sendall(s,data) 
            return True 
        except Exception as e:
            return False 
        finally:
            s.close() 







class ChannelDef:
    def __init__(self, name:str, unit:str, scale:int, color:str):
        self.ChannelName = name
        self.ChannelUnit = unit
        self.DataScale = [0.0] * scale 
        self.ChannelColor = color 
        self.ChannelMax = 80 

        self._index = 0 
        self._datalog = [0.0] * scale

    def EmplaceDataScale(self, value):
        self._datalog[self._index] = value 
        self._index =+ 1
        if(self._index > len(self._datalog) - 1):
            self._index = 0 

    