# -*- coding: utf-8 -*-

from helper_methods import props, barrier_request
from ryu.ofproto import ofproto_v1_3_parser as parser
import ofp_custom_events as c_ev

class DatapathConfig:

    def __init__(self, i, name, settings):
        self.id = i
        self.dp_obj = None
        self.name = name
        #dictionary (port_num:its settings)
        self.native_vlan = settings.get('native_vlan')
        self.ports = self.parse_ports(settings.get('ports'))
        

    def __str__(self):
        args = []
        args.append('<DatapathConfig')
        for prop in props(self):
            if isinstance(getattr(self, prop), dict):
                #взять каждый элемент новых настроек
                for key in getattr(self, prop).keys():
                    args.append('\n%s = %s' % (prop, getattr(self, prop).get(key)))
            else:
                args.append(' %s = %s ' % (prop, getattr(self, prop)))
        args.append('>')
        return ' '.join(args)


    def __eq__(self, other):
        """funcion of eq of two DatapathConfigs. 
        Dont compare some DP settings (like description or name, for example)"""
        # assert(isinstance(other, DatapathConfig), 'DatapathConfig must eq only with DatapathConfig')
        for prop in props(self):
            #если характиристика - словарь
            if isinstance(prop, dict):
                #взять каждый элемент новых настроек
                for key in getattr(self, prop).keys():
                    old_p = getattr(other, prop).get(key)
                    new_p = getattr(self, prop).get(key)
                    #если порты не равны
                    if new_p != old_p:
                        return False
            #в ином случае просто сравнить значения
            elif isinstance(getattr(self, prop), list):
                if set(getattr(self, prop)) != set(getattr(other, prop)):
                    return False

            elif getattr(self, prop) != getattr(other, prop):
                    return False
        return True

    def state(self):
        print()
        print('State of DatapathConfig class')
        print('Self = ', id(self))
        print('ports = ', id(self.ports) )
        print()
        print('Self.ports')
        for d, a in self.ports.items():
            print (d, a)


    def get_port(self, port_id):
        return self.ports.get(port_id)


    def parse_ports(self, ports_settings):
        ports = {}
        for num, settings in ports_settings.items():
            if settings is None:
                settings = {}
            settings['dp_native_vlan'] = self.native_vlan
            ports[num] = Port(num, settings)
        return ports


    def configure(self, old_dp = None, ports_info = []):
        #old_dp = DatapathConfig

        #словари словарей содержащие объекты, которые
        #есть в обоих
        temp_dict_ch = {}
        #есть только в новом
        temp_dict_add = {}
        #есть только в старом
        temp_dict_del = {}

        #{port_num: Port}
        ports_dict_add = {}
        ports_dict_del = {}
        ports_dict_ch = {}

        #заполняем портов для датапафы
        # есть еще такие поля (p., , p.name, p.config, p.state, p.peer, p.curr_speed, p.max_speed))
        for p in ports_info:
            if p.port_no in self.ports.keys():
                self.ports[p.port_no].mac = p.hw_addr
            elif p.port_no <= 96: #чтобы не зацепить порт контроллера в ovs, так то в "реальности", порт, который будет идти от свитча к контроллеру, должен быть указан в конфиге
                ports_dict_del[p.port_no] = Port(p.port_no, settings = {'mac':p.hw_addr})
                
        #dictionary of settings we need to change
        settings = {} 
        for prop in props(self):
            if old_dp is None:
            #настроить с нуля свитч на основе характеристик экзмепляра DP
                if isinstance(getattr(self, prop), dict):
                    for key in getattr(self, prop).keys():
                        new_p = getattr(self, prop).get(key)
                        if isinstance(new_p, Port):
                            if new_p.state == 1:
                                ports_dict_add[key] = new_p
                            else:
                                ports_dict_del[key] = new_p
                else:
                    settings[prop] = getattr(self, prop)

            else:
                #изменить настройки свитча, основываясь на его нынешних и прошлых настройках, указанных в old_dp
                #если характиристика - словарь
                if isinstance(getattr(self, prop), dict):
                    #взять каждый элемент новых настроек
                    
                    
                    in_both = getattr(self, prop).keys() & getattr(old_dp, prop).keys()
                    in_one = getattr(self, prop).keys() ^ getattr(old_dp, prop).keys()

                    for key in in_both:
                        old_p = getattr(old_dp, prop).get(key)
                        new_p = getattr(self, prop).get(key)
                        if new_p != old_p:
                            if isinstance(new_p, Port):
                                ports_dict_ch[key] = old_p
                    
                    for key in in_one:
                        old_p = getattr(old_dp, prop).get(key)
                        new_p = getattr(self, prop).get(key)
                        if new_p is None:
                            if isinstance(old_p, Port): #если сравниваем порты
                                ports_dict_del[key] = old_p
                        if old_p is None:
                            if isinstance(new_p, Port):
                                ports_dict_add[key] = new_p

                elif getattr(self, prop) != getattr(old_dp, prop):
                    #need to change switch settings to the current state
                    settings[prop] = getattr(self, prop)

        if bool(ports_dict_add):
            temp_dict_ch['port'] = ports_dict_ch
        if bool(ports_dict_add):
            temp_dict_add['port'] = ports_dict_add
        if bool(ports_dict_del):
            temp_dict_del['port'] = ports_dict_del

        if bool(temp_dict_ch):
            settings['temp_dict_ch'] = temp_dict_ch
        if bool(temp_dict_add):
            settings['temp_dict_add'] = temp_dict_add
        if bool(temp_dict_del):
            settings['temp_dict_del'] = temp_dict_del
        return self.apply_settings(settings)


    def apply_settings(self, settings):
        """TODO make OPFmessages, that apply settings to datapath
        settings - словарь характеристик которые надо установить {имя характеристики :значение}"""
        events = []
        try:
            for setting in settings.keys():
                #просмотреть все пришедшие настройки портов. Выполнить опредленные действия в зависимости от этого
                if setting == 'temp_dict_add':
                    #add new objects to switch
                    dict_add = settings[setting]
                    for add_setting in dict_add.keys():
                        if add_setting == 'port':
                            #add new ports
                            ports_add = dict_add[add_setting]
                            for port_id in ports_add.keys():
                                #добавляет список ивентов для первоначальной настройки порта
                                events += self.add_port(ports_add[port_id])

                elif setting == 'temp_dict_ch':
                    dict_ch = settings[setting]
                    for ch_setting in dict_ch.keys():
                        if ch_setting == 'port':
                            ports_ch = dict_ch[ch_setting]
                            for port_id in ports_ch.keys():
                                #добавляет список сообщений для конфигурации порта
                                events += self.get_port(port_id).configure(self, ports_ch[port_id])

                elif setting == 'temp_dict_del':
                    dict_del = settings[setting]
                    for del_setting in dict_del.keys():
                        if del_setting == 'port':
                            ports_del = dict_del[del_setting]
                            for port_id in dict_del[del_setting]:
                                events += self.del_port(ports_del[port_id])
            
            #обработка общих настроек порта  
                elif setting == 'name':
                    print('!New name is ', settings['name'])
                    #как пример - генерация ивента для какой-то общий DP настройки, передается в таком случае весь DP объект
                    # events += [events.NewName(self)}

        except TypeError as e:
            print('DPconfig Type Error ', e)
            return []
        return events

    
    def add_port(self, port):
        """возвращает список ивентов для настройки нового порта, который уже указан в DatapathConfig"""
        events = []
        #если порт указан в конфигурации
        if port.num in self.ports.keys():
            #шлем сообщения, что порт надо сконфигурить(DatapathConfig, Port). Каждый модуль ловит такое сообщение и на основании нужных ему данных объекта Порт, конфигруит его
            events += [c_ev.NewPort(self, port)]
            #add port to DatapathConfig.ports
            self.ports[port.num] = port
        return events


    def change_port(self, port, old_port):
        """возвращает список ивентов для изменения настроек порта, который уже указан в DatapathConfig"""
        events = []
        #шлем сообщения, что порт надо сконфигурить(DatapathConfig, Port). Каждый модуль ловит такое сообщение и на основании нужных ему данных объекта Порт, конфигруит его
        events += port.configure(self, old_port)
        return events


    def del_port(self, port):
        """возвращает список ивентов для удаления порта"""
        events = []
        events += [c_ev.DelPort(self, port)]
        if port.num in self.ports.keys():
            #if port is in DPconfig - delete port from DatapathConfig.ports
            del self.ports[port.num]
        return events




class Port:

    def __init__(self, num, settings):
        self.num = num
        #0 - down, 1 up. If none then up
        self.state = settings.get('state')
        if self.state is None:
            self.state = 1
        self.mac = None

        #храним только имена вланов, их vid будем получать из настроек конфиги уже в самом модуле
        self.tagged_vlans = settings.get('tagged_vlans')
        self.native_vlan = settings.get('native_vlan')
        if self.native_vlan is None and self.tagged_vlans is None:
            self.native_vlan = settings.get('dp_native_vlan')

    
    def __str__(self):
        args = []
        args.append('<Port')
        for prop in props(self):
            if isinstance(getattr(self, prop), dict):
                for key in getattr(self, prop).keys():
                    args.append('\n%s = %s' % (prop, getattr(self, prop).get(key)))
            else:
                args.append(' %s = %s ' % (prop, getattr(self, prop)))
        args.append('>')
        return ' '.join(args)
    

    def __eq__(self, other):
        if (other is None and self is not None) or (self is None and other is not None):
            return False
        for prop in props(self):
            #если характиристика - словарь
            if isinstance(getattr(self, prop), dict):
                #взять каждый элемент новых настроек
                for key in getattr(self, prop).keys():
                    old_p = getattr(other, prop).get(key)
                    new_p = getattr(self, prop).get(key)
                    #если значения в словаре не равны
                    if new_p != old_p:
                        return False
            elif isinstance(getattr(self, prop), list):
                if set(getattr(self, prop)) != set(getattr(other, prop)):
                    return False
            #в ином случае просто сравнить значения
            elif getattr(self, prop) != getattr(other, prop):
                return False
        return True


    def configure(self, dp_config, old_p):
        """создает словарь натсроек, которые надо будет применить к порту
        возвращает список событий на основе этих настроек"""
        settings = {}
        for prop in props(self):
            #изменить настройки, основываясь на  нынешних и прошлых настройках, указанных в old_p
            #для обработки vlan
            if isinstance(getattr(self, prop), list):
                if set(getattr(self, prop)) != set(getattr(old_p, prop)):
                    settings[prop] = getattr(self, prop)
            #
            elif getattr(self, prop) != getattr(old_p, prop):
                #need to change settings to the current state
                settings[prop] = getattr(self, prop)
        return self.apply_settings(dp_config, settings)



    def apply_settings(self, dp_config, settings):
        """создает из словаря настроек список ивентов
        settings - словарь характеристик которые надо установить {имя характеристики :значение}"""
        events = []
        try:
            for setting in settings.keys():
                setting_val = settings[setting]
                if setting == 'state':
                    if setting_val == 1:
                        print('**********PortUp')
                        events += [c_ev.PortUp(dp_config, self)]
                    elif setting_val == 0:
                        print('!!!!!!!!!!PortDown')
                        events += [c_ev.PortDown(dp_config, self)]
                elif setting == 'native_vlan':
                    events += [c_ev.PortNativeVlan(dp_config, self)]
                elif setting == 'tagged_vlans':
                    events += [c_ev.PortTaggedVlan(dp_config, self)]
        except TypeError as e:
            print('Port Type Error ', e)
            return []
        return events

    
    