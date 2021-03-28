# -*- coding: utf-8 -*-

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib.ofp_pktinfilter import packet_in_filter, RequiredTypeFilter
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ether_types, ospf, arp, ipv4
#для ospf
from array import array
from ospf_util import make_arp, answ_arp, ospf_advertise, ospf_hello, add_flow, ospf_lsack, ospf_upd
from faucet.valve_of import output_controller

class Ospf(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(Ospf, self).__init__(*args, **kwargs)
        self.area = '0.0.0.0'
        self.route_id = '0.0.0.1'
        self.mac = 'ca:00:0c:c0:00:22'
        self.int5ip = '192.168.2.254'
        self.arp_table = {}
        # self.arp_table['192.168.2.1'] = '0c:ce:63:33:07:03'
        self.external_port = 5
        self.neighours = []
        self.dbd_ack = 0
        self.ospf_lsas = []
        self.seq = 0x80000004
        self.dr = self.route_id
        self.asPort = 5

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        dp = ev.msg.datapath
        ofproto = dp.ofproto
        parser = dp.ofproto_parser

        #так можно устанавливать dp свитча, по идее
        # dp.id = 1
        # print('!!!', dp.id)

        # if (dp.id == 1):
        #     print('!!!! dp 1 adding flows for ', dp.id)

        #     match = parser.OFPMatch(in_port=2, vlan_vid=0)
        #     actions = []
        #     actions += [parser.OFPActionPushVlan()]
        #     actions += [parser.OFPActionSetField(vlan_vid = 4097)]
        #     table = 0
        #     goto_table = 1
        #     add_flow(dp, table_id = table, priority = 20480, match = match, actions = actions,  goto_table = goto_table)

        #     match = parser.OFPMatch()
        #     actions = []
        #     table = 1
        #     add_flow(dp, table_id = table, priority = 0, match = match, actions = actions)

        #     match = parser.OFPMatch(in_port=1, vlan_vid = 4098)
        #     actions = []
        #     table = 0
        #     goto_table = 1
        #     add_flow(dp, table_id = table, priority = 20480, match = match, actions = actions, goto_table = goto_table)
            
        #     match = parser.OFPMatch(eth_dst = '01:00:00:00:00:22', eth_type= 2048, vlan_vid = 4097)
        #     actions = []
        #     table = 1
        #     goto_table = 2
        #     add_flow(dp, table_id = table, priority = 20480, match = match, actions = actions, goto_table = goto_table)
            
        #     match = parser.OFPMatch(eth_dst = '01:00:00:00:00:22', eth_type= 2048, vlan_vid = 4098)
        #     actions = []
        #     table = 1
        #     goto_table = 2
        #     add_flow(dp, table_id = table, priority = 20480, match = match, actions = actions, goto_table = goto_table)

        #     #вместо dl_vlan vlan_id #dl_vlan не принимает
        #     match = parser.OFPMatch(vlan_vid=4097, eth_type= 2048, ipv4_dst='192.168.3.15')
        #     actions = []
        #     actions += [parser.OFPActionSetField(eth_src = '01:00:00:00:00:22')]
        #     actions += [parser.OFPActionSetField(eth_dst = '02:00:00:00:00:22')]
        #     actions += [parser.OFPActionDecNwTtl()]
        #     table = 2
        #     add_flow(dp, table_id = table, priority = 20480, match = match, actions = actions, goto_table = 4)
            
        #     match = parser.OFPMatch(vlan_vid=4098, eth_type= 2048, ipv4_dst='192.168.2.11')
        #     actions = []
        #     #+= [parser.OFPActionSetField(vlan_vid = 4097)]
        #     actions += [parser.OFPActionSetField(eth_src = '01:00:00:00:00:22')]
        #     actions += [parser.OFPActionSetField(eth_dst = '00:00:00:00:00:03')]
        #     actions += [parser.OFPActionDecNwTtl()]
        #     table = 2
        #     goto_table = 4
        #     add_flow(dp, table_id = table, priority = 20480, match = match, actions = actions, goto_table = goto_table)

        #     match = parser.OFPMatch(eth_dst='02:00:00:00:00:22')
        #     actions = []
        #     actions = [parser.OFPActionOutput(1)]
        #     table = 4
        #     add_flow(dp, table_id = table, priority = 20480, match = match, actions = actions)

        #     match = parser.OFPMatch(eth_dst='00:00:00:00:00:03', vlan_vid=4098)
        #     actions = []
        #     actions += [parser.OFPActionPopVlan()]
        #     actions += [parser.OFPActionOutput(2)]
        #     table = 4
        #     add_flow(dp, table_id = table, priority = 20480, match = match, actions = actions)

        # if (dp.id == 2):
        #     print('!!!! dp 2 adding flows for ', dp.id)

        #     match = parser.OFPMatch(in_port=3, vlan_vid=0)
        #     actions = []
        #     actions += [parser.OFPActionPushVlan()]
        #     actions += [parser.OFPActionSetField(vlan_vid = 4098)]
        #     table = 0
        #     goto_table = 1
        #     add_flow(dp, table_id = table, priority = 20480, match = match, actions = actions,  goto_table = goto_table)

        #     match = parser.OFPMatch(in_port=1, vlan_vid=4097)
        #     actions = []
        #     table = 0
        #     add_flow(dp, table_id = table, priority = 20480, match = match, actions = actions,  goto_table = 1)

        #     match = parser.OFPMatch()
        #     actions = []
        #     table = 0
        #     add_flow(dp, table_id = table, priority = 0, match = match, actions = actions)

        #     match = parser.OFPMatch()
        #     actions = []
        #     table = 1
        #     add_flow(dp, table_id = table, priority = 0, match = match, actions = actions)

        #     match = parser.OFPMatch(eth_src='02:00:00:00:00:22')
        #     actions = []
        #     table = 1
        #     add_flow(dp, table_id = table, priority = 20480, match = match, actions = actions,  goto_table = 2)

        #     match = parser.OFPMatch(eth_src='01:00:00:00:00:22')
        #     actions = []
        #     table = 1
        #     add_flow(dp, table_id = table, priority = 20480, match = match, actions = actions,  goto_table = 2)

        #     match = parser.OFPMatch(eth_dst='02:00:00:00:00:22', eth_type=2048, vlan_vid = 4098)
        #     actions = []
        #     table = 1
        #     goto_table = 2
        #     add_flow(dp, table_id = table, priority = 20480, match = match, actions = actions,  goto_table = goto_table)

        #     match = parser.OFPMatch(vlan_vid=4097, eth_type= 2048, ipv4_dst='192.168.3.15')
        #     actions = []
        #     #actions += [parser.OFPActionSetField(vlan_vid = 4098)]
        #     actions += [parser.OFPActionSetField(eth_src = '02:00:00:00:00:22')]
        #     actions += [parser.OFPActionSetField(eth_dst = '00:00:00:00:00:02')]
        #     actions += [parser.OFPActionDecNwTtl()]
        #     table = 2
        #     add_flow(dp, table_id = table, priority = 20480, match = match, actions = actions, goto_table = 4)

        #     match = parser.OFPMatch(vlan_vid=4098, eth_type= 2048, ipv4_dst='192.168.2.11')
        #     actions = []
        #     #actions += [parser.OFPActionSetField(vlan_vid = 4098)]
        #     actions += [parser.OFPActionSetField(eth_src = '02:00:00:00:00:22')]
        #     actions += [parser.OFPActionSetField(eth_dst = '01:00:00:00:00:22')]
        #     actions += [parser.OFPActionDecNwTtl()]
        #     table = 2
        #     goto_table = 4
        #     add_flow(dp, table_id = table, priority = 20480, match = match, actions = actions, goto_table = goto_table)

        #     match = parser.OFPMatch(eth_dst='00:00:00:00:00:02', vlan_vid=4097)
        #     actions = []
        #     actions += [parser.OFPActionPopVlan()]
        #     actions += [parser.OFPActionOutput(3)]
        #     table = 4
        #     add_flow(dp, table_id = table, priority = 20480, match = match, actions = actions)

        #     match = parser.OFPMatch(eth_dst='01:00:00:00:00:22', vlan_vid=4098)
        #     actions = []
        #     actions += [parser.OFPActionOutput(1)]
        #     table = 4
        #     add_flow(dp, table_id = table, priority = 20480, match = match, actions = actions)

        #     match = parser.OFPMatch(eth_dst='01:00:00:00:00:22', vlan_vid=4097)
        #     actions = []
        #     actions += [parser.OFPActionOutput(1)]
        #     table = 4
        #     add_flow(dp, table_id = table, priority = 20480, match = match, actions = actions)

        #для передачи ospf в контроллер примем его и отправим в контроллер
        # if (dp.id == 1):
        #     match = parser.OFPMatch(in_port = self.external_port, eth_type=0x0800, ip_proto=89)
        #     actions = [output_controller()]
        #     table = 0
        #     add_flow(dp, table_id = table, priority = 20480, match = match, actions = actions)

        #     match = parser.OFPMatch(in_port = self.external_port, eth_type=0x0806)
        #     actions = [output_controller()]
        #     table = 0
        #     add_flow(dp, table_id = table, priority = 20480, match = match, actions = actions)

        #     match = parser.OFPMatch()
        #     actions = []
        #     table = 0
        #     add_flow(dp, table_id = table, priority = 0, match = match, actions = actions)
            
        match = parser.OFPMatch()
        actions = [output_controller()]
        table = 0
        add_flow(dp, table_id = table, priority = 0, match = match, actions = actions)
        
        ospf_hello(dp = dp, mac_src=self.mac, ip_src=self.int5ip, router_id=self.route_id, neighbors=self.neighours, out_ports = [self.asPort], mask = '255.255.255.0', designated_router = self.dr, area_id = self.area, options = 0x02) 

    def find_mac(self, ip, dp, from_port):
        #или ловить keyError exception
        print(self.arp_table)
        if ip in self.arp_table.keys():
            return self.arp_table[ip]
        else:
            make_arp(dp = dp, out_ports = [from_port], eth_src = self.mac, src_ip = self.int5ip, dst_ip = ip)
            return -1


    def ospf_hello_handler(self, ev):
        msg = ev.msg
        from_port = msg.match['in_port']
        #print('hello ospf from port ', from_port)
        dp = msg.datapath
        pkt = packet.Packet(array('B', ev.msg.data))
        ospfP = pkt.get_protocol(ospf.OSPFHello)
        rid = ospfP.router_id
        if rid not in self.neighours:
            self.neighours += [rid]
        self.dr = str(ospfP.designated_router)
        ospf_hello(dp = dp, mac_src=self.mac, ip_src=self.int5ip, router_id=self.route_id, neighbors=self.neighours, out_ports = [self.asPort], mask = '255.255.255.0', designated_router = self.dr, area_id = self.area, options = 0x02) #backup_router = self.int5ip
        

    def ospf_dbd_handler(self, ev):
        dp = ev.msg.datapath
        pkt = packet.Packet(array('B', ev.msg.data))
        ipP = pkt.get_protocol(ipv4.ipv4)
        neigh_mac = self.find_mac(ipP.src, dp, 5)
        if isinstance(neigh_mac, int):
            return 0
        ospfP = pkt.get_protocol(ospf.OSPFDBDesc)
        print('!!!', ospfP)
        if self.dbd_ack == 0:
            #если пустой, значит отправился первый пакет DBD, в котором указан master bit, i bit и проч
            #  I-bit — Init bit. Значение бита равное 1, означает, что этот пакет первый в последовательности DBD-пакетов
            # M-bit — More bit. Значение бита равное 1, означает, что далее последуют дополнительные DBD-пакеты 
            ospf_advertise(dp = dp, mac_src = self.mac, ip_src=self.int5ip, router_id = self.route_id, out_ports = [5], area_id = self.area, ip_dst = ipP.src, mac_dst = neigh_mac, dd = ospfP.sequence_number-104, m_flag=1, i_flag = 1, ms_flag = 1, options = 0x02)
            self.dbd_ack = 1
        elif self.dbd_ack == 1:
            #шлем пакет, притворяясь слейвом. В пакете все lsa маршруты и флаг more
            # тип линка - обязательно не СТАБ!! иначе маршруты из других зон не пройдут + надо еще слать флаг 0х03 чтобы быть и ASBR и BR
            link2 = ospf.RouterLSA.Link(id_='192.168.2.1', data='192.168.2.254', type_=ospf.LSA_LINK_TYPE_TRANSIT, metric=1)
            lsa1 = ospf.RouterLSA(id_=self.route_id, adv_router=self.route_id, links=[link2], ls_seqnum=self.seq, options = 0x22, flags=0x03)
            
            lsa31 = ospf.SummaryLSA(id_='192.168.3.0', adv_router=self.route_id, mask='255.255.255.0', metric = 1, ls_seqnum=self.seq, options = 0x22)

            net2 = ospf.ASExternalLSA.ExternalNetwork(mask='255.255.255.0', metric=20, fwd_addr='0.0.0.0')
            lsa32 = ospf.ASExternalLSA( id_='192.168.5.0', extnws=[net2], adv_router=self.route_id, ls_seqnum=self.seq, options = 0x20)

            heads = []
            heads = [lsa1.header]
            heads += [lsa31.header]
            heads += [lsa32.header]
            # heads += [lsa33.header]
            self.ospf_lsas += [lsa1]
            self.ospf_lsas += [lsa31]
            self.ospf_lsas += [lsa32]
            # self.ospf_lsas += [lsa33]
            ospf_advertise(dp = dp, mac_src = self.mac, ip_src=self.int5ip, router_id = self.route_id, out_ports = [self.asPort], area_id = self.area, ip_dst = ipP.src, m_flag=1, mac_dst = neigh_mac, dd = ospfP.sequence_number, lsa_headers = heads, options = 0x02) #
            self.dbd_ack = 2
        else:
            ospf_advertise(dp = dp, mac_src = self.mac, ip_src=self.int5ip, router_id = self.route_id, out_ports = [self.asPort], area_id = self.area, ip_dst = ipP.src, mac_dst = neigh_mac, dd = ospfP.sequence_number, options = 0x02)
        

    def ospf_upd_handler(self, ev):
        #update от других машрутизаторов, просто подтверждаем их
        dp = ev.msg.datapath
        pkt = packet.Packet(array('B', ev.msg.data))
        macP = pkt.get_protocol(ethernet.ethernet)
        ipP = pkt.get_protocol(ipv4.ipv4)
        #если мы DR router то слать надо на общий адрес 224.0.0.5, иначе - шлем только DR роутеру
        #тк мы не DR, то это нам не нужно
        neigh_mac = self.find_mac(ipP.src, dp, ev.msg.match['in_port'])
        if isinstance(neigh_mac, int):
            return 0
        ospfP = pkt.get_protocol(ospf.OSPFLSUpd)
        acks = []
        for lsa in ospfP.lsas:
            #по хорошему - запоминаем этот lsa где-то у себя
            #но мы этого щас не делаем
            # отправляем подтверждение
            acks += [lsa.header]
        if acks != []:
            ospf_lsack(dp = dp, mac_src=self.mac, ip_src=self.int5ip, router_id = self.route_id, out_ports = [self.asPort], area_id = self.area, ip_dst = ipP.src, mac_dst = neigh_mac, headers = acks)


    def find_lsa(self, req):
        for lsa in self.ospf_lsas:
            head = lsa.header
            if head.adv_router == req.adv_router and head.id_ == req.id and head.type_ == req.type_:
                return lsa
        return None


    def ospf_req_handler(self, ev):
        #если приходит запрос определнного/ых lsu, которые мы отправляли
        dp = ev.msg.datapath
        pkt = packet.Packet(array('B', ev.msg.data))
        ipP = pkt.get_protocol(ipv4.ipv4)
        neigh_mac = self.find_mac(ipP.src, dp, ev.msg.match['in_port'])
        if isinstance(neigh_mac, int):
            return 0
        ospfP = pkt.get_protocol(ospf.OSPFLSReq)
        #приходит вот такое поле lsa_requests=[Request(adv_router='0.0.0.1',id='192.168.3.0',type_=3), Request(adv_router='0.0.0.1',id='192.168.5.0',type_=3)],
        temp_lsa = []
        for req in ospfP.lsa_requests:
            #отправить lsa, найдя его по lsa header
            lsa = self.find_lsa(req)
            if lsa is not None:
                temp_lsa +=[lsa]
        ospf_upd(dp = dp, mac_src=self.mac, ip_src=self.int5ip, router_id = self.route_id, out_ports = [5], area_id = self.area, ip_dst = ipP.src, mac_dst = neigh_mac, lsas = temp_lsa)
        

    def ospf_ack_handler(self, ev):
        #при подтверждении от других роутеров (пока) ничего не делаем
        dp = ev.msg.datapath
        pkt = packet.Packet(array('B', ev.msg.data))
        ipP = pkt.get_protocol(ipv4.ipv4)
        neigh_mac = self.find_mac(ipP.src, dp, ev.msg.match['in_port'])
        if isinstance(neigh_mac, int):
            return 0
        ospfP = pkt.get_protocol(ospf.OSPFLSAck)
        if self.dbd_ack == 1:
            link = ospf.RouterLSA.Link(id_=self.dr, data=self.int5ip, type_=ospf.LSA_LINK_TYPE_TRANSIT, metric=10)
            lsa = ospf.RouterLSA(id_=self.route_id, adv_router=self.route_id, links=[link])
            self.ospf_lsas += [lsa]
            ospf_upd(dp = dp, mac_src=self.mac, ip_src=self.int5ip, router_id = self.route_id, out_ports = [5], area_id = self.area, ip_dst = ipP.src, mac_dst = neigh_mac, lsas = [lsa])
            self.dbd_ack = 2
        
        # if ospfP.lsa_headers in self.dbd_lacks:
        #     удалить lsa header из self.dbd_lacks
        #     self.dbd_lacks.pop(spfP.lsa_headers)
        # если
        #     self.dbd_lacks пустой
        #     self.dbd_ack = False
        # иначе
        #     продолжаем анонсить маршруты


    # @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    # @packet_in_filter(RequiredTypeFilter, {'types': [arp.arp]})
    def arp_handler(self, ev):
        pkt = packet.Packet(array('B', ev.msg.data))
        arpP = pkt.get_protocol(arp.arp)
        if arpP.opcode == 1:
            msg = ev.msg
            from_port = msg.match['in_port']
            dp = msg.datapath
            print('!Arp request from port', from_port)
            answ_arp(dp = dp, out_ports = [from_port], eth_dst = arpP.src_mac, eth_src = self.mac, src_ip = self.int5ip, dst_ip = arpP.src_ip)
        elif arpP.opcode == 2:
            print('!Arp answer')
            self.arp_table[arpP.src_ip] = arpP.src_mac
        else:
            print('Error arp invalid')
        

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    # @packet_in_filter(RequiredTypeFilter, {'types': [arp.arp]})
    def _packet_in_handler(self, ev):
        pkt = packet.Packet(array('B', ev.msg.data))
        if ospf.OSPFHello in pkt:
            self.ospf_hello_handler(ev)
        elif ospf.OSPFDBDesc in pkt:
            self.ospf_dbd_handler(ev)
        elif ospf.OSPFLSUpd in pkt:
            self.ospf_upd_handler(ev)
        elif ospf.OSPFLSAck in pkt:
            self.ospf_ack_handler(ev)
        elif ospf.OSPFLSReq in pkt:
            self.ospf_req_handler(ev)
        elif arp.arp in pkt:
            self.arp_handler(ev)
        else:
            print('!!!!MainThread')
            print (pkt.get_protocol(ospf.OSPFMessage))
            for p in pkt:
                print('!!!', p)
            print()