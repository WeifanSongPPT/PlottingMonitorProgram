import socket 
import string
import threading 
import time 
import random 
import json 

class TelemetryServer:
    def __init__(self, hostname:str, port:int, server_channel_cnt = 3):
        self._hostName = hostname 
        self._port = port 
        self._sendingInterval = 4
        self._waitingScanningTimeout = 10 
        self._bufferLength = 30
        self._buffers = []
        for i in range(server_channel_cnt):
            self._buffers.append([0.0]*self._bufferLength) 

    def TelemetryDataCollection(self,channel,sample_interval = 0.1):
       _read_result = [] 
       _sum = 0
       for i in range(self._bufferLength):
           _read_value = round(50.0 + random.uniform(-0.5, 0.5), 2)
           _read_result.append(_read_value) 
           _sum += _read_value 
        #Average the data 
       
       self._buffers[channel] = _read_result 
       return _sum / self._bufferLength 



       
    def RunTelemetryServer(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((self._hostName, self._port))
            s.listen(self._waitingScanningTimeout)
            print(f"Listening for Telemetry clients on port {self._port}") 
        except Exception as e:
            print(f"Error binding to {self._hostName}:{self._port} - {e}")
            s.close()
            return


        while True: 
            try:
                client_sock,client_addr = s.accept()
                while True:
                  telemetrydata = {
                    "ch1": self.TelemetryDataCollection(0),
                    "ch2": self.TelemetryDataCollection(1) , 
                    "ch3": self.TelemetryDataCollection(2) 
                    }
                  payload = json.dumps(telemetrydata) + "\n" 
                  client_sock.sendall(payload.encode('utf-8'))
                  time.sleep(self._sendingInterval)
            except ConnectionResetError as cre:
                print(f"Connection {self._hostName}: {self._port} aborted due to Connect Reset Error")
                client_sock.close() 
            except BrokenPipeError as bpe:
                print(f"Connection {self._hostName}: {self._port} aborted due to Broken Pipe Error")
                client_sock.close() 
            except Exception as e:
                print(f"Error happened, reason {e}")  




        

    

       
      
