# -*- coding: utf-8 -*-

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib.ofp_pktinfilter import packet_in_filter, RequiredTypeFilter
from ryu.ofproto import ofproto_v1_3
from ryu.ofproto import ofproto_v1_3_parser as parser
from ryu.lib.packet import packet, ethernet, ether_types, arp, ipv4

import helper_methods as util
from cache import HostCache
from ospf_util import add_flow
import table

import ofp_custom_events as c_ev
from config import Config


from faucet.valve_of import output_controller


class MainApp(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    _CONTEXTS = {
        'tables': table.Tables,
        'net-config': Config
        }

    _EVENTS = [c_ev.NewPort,
        c_ev.DelPort,
        c_ev.NewDp, 
        c_ev.StartBackground,
        c_ev.PortNativeVlan,
        c_ev.PortTaggedVlan]

    def __init__(self, *args, **kwargs):
        super(MainApp, self).__init__(*args, **kwargs)
        self.Tables = kwargs['tables']
        self.net_config = kwargs['net-config']
        self.back_is_started = False

        #Adding tables for an app
        acl = table.Table('acl')
        vl_in = table.Table('vl_in')
        eth_src = table.Table('eth_src', 'eth_dst')
        eth_dst = table.Table('eth_dst')
        vl_out = table.Table('vl_out')
        flood = table.Table('flood')
        
        self.Tables.add_table(acl)
        self.Tables.add_table(vl_in, 'acl')
        self.Tables.add_table(eth_src, 'vl_in')
        self.Tables.add_table(eth_dst, 'eth_src')
        self.Tables.add_table(vl_out, 'eth_dst')
        self.Tables.add_table(flood, 'vl_out')

        
    # @set_ev_cls(ofp_event.EventOFPPortStatus, MAIN_DISPATCHER)
    # def port_status_handler(self, ev):
    #     print('Stats changed', ev.msg)
        #TODO высылать запрос по состоянию портов
        #сделать, чтобы бэекграунд опрашивал периодически свитчи на сосотояния их портов и потом что-нить с этим делал

    @set_ev_cls(ofp_event.EventOFPPortDescStatsReply, CONFIG_DISPATCHER)
    def port_desc_stats_reply_handler(self, ev):
        # print('switch_reply', ev.msg.body)
        dp = ev.msg.datapath
        #узнаем, какие у dp есть порты
        self.net_config.ports_info_for_dp[dp.id] = ev.msg.body
        #register switch
        events = self.net_config.register_dp(dp)
        for ev in events:
            self.send_event_to_observers(ev)


    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def new_switch_handler(self, ev):
        dp = ev.msg.datapath
        if dp.id not in self.net_config.ports_info_for_dp.keys():
            # print('switch question')
            dp.send_msg(parser.OFPPortDescStatsRequest(dp, 0))
        #start background app
        if not self.back_is_started:
            self.back_is_started = True
            self.send_event_to_observers(c_ev.StartBackground())


    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, DEAD_DISPATCHER)
    def del_switch_handler(self, ev):
        #TODO не работает
        dp = ev.msg.datapath
        print('Switch is removed', dp.id)
        events = self.net_config.unregister_dp(dp)
        for ev in events:
            self.send_event_to_observers(ev)


    # @set_ev_cls(c_ev.NewPort, CONFIG_DISPATCHER)
    # def port_up_handler(self, ev):
    #     print('Glush')
    #     # print('NewPort ', ev.dp.id, ev.port, ev.port.mac)
    #     # util.send_msgs(ev.dp.dp_obj, util.port_up(ev.port, ev.dp.dp_obj))


    # @set_ev_cls(c_ev.DelPort, CONFIG_DISPATCHER)
    # def port_down_handler(self, ev):
    #     print('glush')
        # util.send_msgs(ev.dp.dp_obj, util.port_shut(ev.port, ev.dp.dp_obj))

    