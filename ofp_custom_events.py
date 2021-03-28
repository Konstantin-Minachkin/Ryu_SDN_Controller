# -*- coding: utf-8 -*-

from ryu.controller import event 


class NewPort(event.EventBase):
    def __init__(self, dp_config_obj, port):
        super(NewPort, self).__init__()
        self.dp = dp_config_obj
        self.port = port

    def __str__(self):
        return '%s<Datapath=%s  Port=%s>' % (self.__class__.__name__, self.dp, self.port)

    # @property
    # def table_name(self):
    #     return self.table

class DelPort(event.EventBase):
    def __init__(self, dp_config_obj, port):
        super(DelPort, self).__init__()
        self.dp = dp_config_obj
        self.port = port

    def __str__(self):
        return '%s<Datapath=%s  Port=%s>' % (self.__class__.__name__, self.dp, self.port)

class NewDp(event.EventBase):
    def __init__(self, dp):
        #dp = ryu Datapath object
        super(NewDp, self).__init__()
        self.dp = dp

    def __str__(self):
        return '%s<Datapath=%s>' % (self.__class__.__name__, self.dp)

class LostDp(event.EventBase):
    def __init__(self, dp):
        super(LostDp, self).__init__()
        self.dp = dp

    def __str__(self):
        return '%s<Datapath=%s>' % (self.__class__.__name__, self.dp)        

class StartBackground(event.EventBase):
    def __init__(self):
        super(StartBackground, self).__init__()

    def __str__(self):
        return '%s' % (self.__class__.__name__)  
         

class PortNativeVlan(event.EventBase):
    def __init__(self, dp_config_obj, port):
        super(PortNativeVlan, self).__init__()
        self.dp = dp_config_obj
        self.port = port

    def __str__(self):
        return '%s<Datapath=%s  Port=%s>' % (self.__class__.__name__, self.dp, self.port)


class PortTaggedVlan(event.EventBase):
    def __init__(self, dp_config_obj, port):
        super(PortTaggedVlan, self).__init__()
        self.dp = dp_config_obj
        self.port = port

    def __str__(self):
        return '%s<Datapath=%s  Port=%s>' % (self.__class__.__name__, self.dp, self.port)


        