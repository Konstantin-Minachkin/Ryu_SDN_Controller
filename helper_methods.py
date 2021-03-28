# -*- coding: utf-8 -*-
from ryu.lib.packet import ethernet, ether_types as ether, packet
from ryu.ofproto import ofproto_v1_3
from ryu.ofproto import ofproto_v1_3_parser as parser
import hashlib

#contain methods that can be used by different classes and apps

def send_msgs(dp, msgs):
    "Send all the messages provided to the datapath"
    if bool(msgs):
        for msg in msgs:
            # print("!!!!  ", msg)
            # print()
            # print()
            dp.send_msg(msg)

def port_up(port, datapath):
    if port.mac is None:
        #значит такого интерфейса не сущетсвует
        return []
    proto= datapath.ofproto
    mask_all = (proto.OFPPC_PORT_DOWN | proto.OFPPC_NO_RECV | proto.OFPPC_NO_FWD | proto.OFPPC_NO_PACKET_IN)
    #hw_addr=hw_addr, 
    return [parser.OFPPortMod(datapath, port_no=port.num, config=0, mask=mask_all, hw_addr = port.mac)]  # 0 means "up" state = no flag configured

def port_shut(port, datapath):
    if port.mac is None:
        return []
    proto= datapath.ofproto
    #hw_addr=hw_addr, 
    return [parser.OFPPortMod(datapath, port_no=port.num, mask=(proto.OFPPC_PORT_DOWN), config=proto.OFPPC_PORT_DOWN, hw_addr = port.mac)]

def goto_table(table_id):
    "Generate an OFPInstructionGotoTable message"
    return parser.OFPInstructionGotoTable(table_id)

def apply_actions(dp, actions):
    "Generate an OFPInstructionActions message with OFPIT_APPLY_ACTIONS"
    return dp.ofproto_parser.OFPInstructionActions(dp.ofproto.OFPIT_APPLY_ACTIONS, actions)


def action_output(dp, port, max_len=None):
    "Generate an OFPActionOutput message"
    kwargs = {'port': port}
    if max_len != None:
        kwargs['max_len'] = max_len
    return dp.ofproto_parser.OFPActionOutput(**kwargs)


def match(dp, in_port=None, eth_dst=None, eth_src=None, eth_type=None, **kwargs):
    "Generate an OFPMatch message"
    if in_port != None:
        kwargs['in_port'] = in_port
    if eth_dst != None:
        kwargs['eth_dst'] = eth_dst
    if eth_src != None:
        kwargs['eth_src'] = eth_src
    if eth_type != None:
        kwargs['eth_type'] = eth_type
    return dp.ofproto_parser.OFPMatch(**kwargs)


def barrier_request(dp):
    """Generate an OFPBarrierRequest message
    Used to ensure all previous flowmods are applied before running the
    flowmods after this request. For example, make sure the flowmods that
    delete any old flows for a host complete before adding the new flows.
    Otherwise there is a chance that the delete operation could occur after
    the new flows are added in a multi-threaded datapath.
    """
    return [dp.ofproto_parser.OFPBarrierRequest(datapath=dp)]

def props(cls):
    #get all Class properties
    return [i for i in cls.__dict__.keys() if i[:1] != '_']


def hash_for(data):
    # Prepare the project id hash
    hashId = hashlib.md5()
    hashId.update(repr(data).encode('utf-8'))
    return hashId.hexdigest()