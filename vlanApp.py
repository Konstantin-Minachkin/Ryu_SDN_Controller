# -*- coding: utf-8 -*-

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib.ofp_pktinfilter import packet_in_filter, RequiredTypeFilter
from ryu.ofproto import ofproto_v1_3 as ofproto
from ryu.ofproto import ofproto_v1_3_parser as parser
from ryu.lib.packet import packet, ethernet, ether_types, arp, ipv4

import helper_methods as util
import table
import ofp_custom_events as c_ev
from config import Config

PRIORITY_MIN = 0
PRIORITY_DEF = 16000
PRIORITY_MAX = 32000
HARD_TIME = 40000
IDLE_TIME = 20000


class VlanApp(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto.OFP_VERSION]

    _CONTEXTS = {
        'tables': table.Tables,
        'net-config': Config
        }

    _EVENTS = [c_ev.PortNativeVlan,
        c_ev.PortTaggedVlan]

    def __init__(self, *args, **kwargs):
        super(VlanApp, self).__init__(*args, **kwargs)
        self.tables = kwargs['tables']
        self.net_config = kwargs['net-config']
        self.cookie = 20
        self.vl_in_table, self.vl_inT_id = self.tables.get_table('vl_in')
        self.vl_out_table, self.vl_outT_id = self.tables.get_table('vl_out')
        self.flood_table, self.floodT_id = self.tables.get_table('flood')


    @set_ev_cls(c_ev.NewDp, MAIN_DISPATCHER)
    def switch_features_handler(self, ev):
        dp = ev.dp
        msgs = self.add_new_datapath(dp)
        util.send_msgs(dp, msgs)


    ## Instance Helper Methods
    def add_new_datapath(self, dp):
        "Add the specified datapath to our app by adding default rules"
        msgs = self.clean_all_flows(dp)
        msgs = self.add_default_flows(dp)
        return msgs


    def clean_all_flows(self, dp):
        "Remove all flows with the Simple switch cookie from all tables"
        msgs = []
        for t in self.tables.tables:
            i = self.tables.table_id(t.name)
            msgs += [self.del_flow (dp, i)]
        return msgs


    def add_default_flows(self, dp):
        "Add the default flows needed for this environment"
        msgs = []
        sw = self.net_config.dps[dp.id]
        vlan_to_ports = {} #{vid:port.num}
        for port in sw.ports.values():
            if port.native_vlan is not None:
                vlan_num = self.net_config.vlans[port.native_vlan].vid
                ## VLAN IN TABLE
                match = parser.OFPMatch(in_port=port.num, vlan_vid=0)
                actions = [parser.OFPActionPushVlan()]
                actions += [parser.OFPActionSetField(vlan_vid = 4096+vlan_num)]
                inst = self.tables.goto_next_of(self.vl_in_table)
                msgs += [self.make_message (dp, self.vl_inT_id, PRIORITY_DEF, match, inst, actions)]

                ## VLAN OUT TABLE
                match = parser.OFPMatch(metadata=port.num, vlan_vid=4096+vlan_num)
                actions = [parser.OFPActionPopVlan()]
                actions += [parser.OFPActionOutput(port.num)]
                msgs += [self.make_message (dp, self.vl_outT_id, PRIORITY_DEF, match, actions=actions)]

                if vlan_num not in vlan_to_ports.keys():
                    vlan_to_ports[vlan_num] = [port.num]
                else:
                    vlan_to_ports[vlan_num] = vlan_to_ports[vlan_num]+[port.num]

            elif port.tagged_vlans is not None:
                for vl in port.tagged_vlans:
                    vlan_num = self.net_config.vlans[vl].vid

                    #те же самые правила, что и наверху
                    ## VLAN IN TABLE
                    match = parser.OFPMatch(in_port=port.num, vlan_vid=4096+vlan_num)
                    inst = self.tables.goto_next_of(self.vl_in_table)
                    msgs += [self.make_message (dp, self.vl_inT_id, PRIORITY_DEF, match, inst, actions)]


                    ## VLAN OUT TABLE
                    match = parser.OFPMatch(metadata=port.num, vlan_vid=4096+vlan_num)
                    actions += [parser.OFPActionOutput(port.num)]
                    msgs += [self.make_message (dp, self.vl_outT_id, PRIORITY_DEF, match, actions=actions)]

                    if vlan_num not in vlan_to_ports.keys():
                        vlan_to_ports[vlan_num] = [port.num]
                    else:
                        vlan_to_ports[vlan_num] = vlan_to_ports[vlan_num]+[port.num]
                    

        #broadcast rules
        #запоминаем порты в каких вланах, при бродкасте вылазим только по этим портам
        for vl,port in vlan_to_ports.items():
            for p in port:
                match = parser.OFPMatch(eth_dst='ff:ff:ff:ff:ff:ff', vlan_vid = 4096+vl) 
                actions = [parser.OFPActionPopVlan()] #было отключено - все работало. Вроде бы, хз. Если бродкаст работаь не будет, выключить это правило
                actions += [parser.OFPActionOutput(p)]
            msgs += [self.make_message (dp, self.vl_outT_id, PRIORITY_MAX, match, actions = actions)]

        # Drop rules
        ## VLAN IN TABLE
        match = parser.OFPMatch()
        msgs += [self.make_message (dp, self.vl_inT_id, PRIORITY_MIN, match)]

        ## VLAN OUT TABLE
        #переходить во flood table, if no match
        inst = self.tables.goto_next_of(self.vl_out_table)
        msgs += [self.make_message (dp, self.vl_outT_id, PRIORITY_MIN, parser.OFPMatch(), inst)]

        return msgs


    def make_message (self, datapath, table_id, priority, match, instructions = None, actions = None, buffer_id=None, command = None, idle_timeout = 0, hard_timeout = 0):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        inst = []
        if actions is not None:
            inst += [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        if instructions is not None:
            inst += instructions
        
        if command is None:
            command = ofproto.OFPFC_ADD
        if buffer_id:
            msg = parser.OFPFlowMod(datapath=datapath, cookie=self.cookie, table_id=table_id, priority=priority, buffer_id=buffer_id, match=match, instructions=inst, command = command, idle_timeout = idle_timeout, hard_timeout = hard_timeout)
        else:
            msg = parser.OFPFlowMod(datapath=datapath, cookie=self.cookie, table_id=table_id,priority=priority, match=match, instructions=inst, command = command, idle_timeout = idle_timeout, hard_timeout = hard_timeout)
        return msg

    
    def del_flow(self, dp, table_id = None, match = None, out_port=None, out_group=None):
        parser = dp.ofproto_parser
        ofp = dp.ofproto
        if out_port is None:
            out_port = ofp.OFPP_ANY
        if out_group is None:
            out_group = ofp.OFPG_ANY
        if table_id is None:
            table_id = ofp.OFPTT_ALL
        msg = parser.OFPFlowMod(cookie=self.cookie, datapath=dp,  table_id=table_id, command=ofp.OFPFC_DELETE, out_port=out_port, out_group=out_group, match = match)
        return msg