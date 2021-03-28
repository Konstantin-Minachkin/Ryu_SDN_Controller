# -*- coding: utf-8 -*-

from ryu.base import app_manager
from ryu.ofproto import ofproto_v1_3
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.controller import ofp_event

import time

from config import Config
import ofp_custom_events as c_ev
import copy


class BackgroundApp(app_manager.RyuApp):

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    
    _CONTEXTS = {
        'net-config': Config
        }

    _EVENTS = [c_ev.NewPort,
        c_ev.DelPort,
        c_ev.NewDp, 
        c_ev.StartBackground,
        c_ev.PortNativeVlan,
        c_ev.PortTaggedVlan]

    def __init__(self, *args, **kwargs):
        super(BackgroundApp, self).__init__(*args, **kwargs)
        self.interval = 60
        self.net_config = kwargs['net-config']
        

    @set_ev_cls(c_ev.StartBackground, CONFIG_DISPATCHER)
    def new_switch_handler(self, ev):
        self.run() 


    def run(self):
        """ Method that runs forever """
        while True:
            time.sleep(self.interval)
            res, changes = self.net_config.check_config_for_difference('myK/conf_old.yaml')
            if self.net_config.conf_review():
                if res:
                    print('!! ', changes)
                    evs = []
                    #создать changes
                    for key,val in changes.items():
                        if key == 'dps_tobe_changed':
                            print('!Datapath need change')
                            self.net_config.state()
                            for d in val:
                                print('work with val  ', d, ' old dp = ', self.net_config.old_dps[d.id])
                                evs += d.configure(self.net_config.old_dps[d.id])
                            print('!Datapaths changed')
                            self.net_config.state()
                        if key == 'only_new_dps':
                            #MainApp при присоединении свитча, пишет его айди в очередь на регистрацию, если для свитча еще нет конфиги
                            # здесь уже проверяется, есть ли указанный в конфиге новый свитч в очереди на присоединение
                            # если есть - регистрируем его, иначе ничего не делаем, тк при присоединении такого свитча MainApp его зарегает 
                            for d in val:
                                if d.id in self.net_config.waiting_to_connect_dps:
                                    self.net_config.register_dp(d)
                        elif key == 'only_old_dps':
                            for d in val:
                                self.net_config.unregister_dp(d)
                        elif key == 'settings_changes':
                            print('settings_changes - doing nothing')
                        elif key == 'old_settings':
                            print('old_settings - doing nothing')
                        elif key == 'new_settings':
                            print('new_settings - doing nothing')
                    #применить changes
                    for ev in evs:
                        self.send_event_to_observers(ev)
            else:
                #если конфига не правильная вернуть ее старую копию
                self.net_config.dps = copy.deepcopy(self.old_dps)
                self.net_config.glob_settings = copy.deepcopy(self.old_glob_settings)
                self.net_config.vlans = copy.deepcopy(self.old_vlans)

