# -*- coding: utf-8 -*-

from helper_methods import props

class Vlan:

    def __init__(self, name, settings):
        self.vid = settings.get('vid')
        self.name = name

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
            #в ином случае просто сравнить значения
            elif getattr(self, prop) != getattr(other, prop):
                return False
        return True