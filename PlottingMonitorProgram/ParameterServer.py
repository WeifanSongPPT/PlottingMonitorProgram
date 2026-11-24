from SocketDataAcquire import DataTeachingRecords 

class ParameterServer:
    def __init__(self):
        self._ChannelTeachingRecords = DataTeachingRecords(3) 
        self._ParaChannelCount = self._ChannelTeachingRecords._recordsCount 
        self._CommonRecords = {} 

    def AddInServer(self, channel_name, name ,value):
        self._ChannelTeachingRecords.AddRecordInChannel(channel_name,name, value) 


    def AddCommonParameters(self, name, value):
        self._CommonRecords.update({name: value}) 

    def GetCommonParameters(self, name):
        return self._CommonRecords[name]

    def GetFromServer(self, channel_name, name):
        if channel_name not in range(self._ParaChannelCount): 
            raise ValueError("Channel Not exists") 


pServer = ParameterServer() 
