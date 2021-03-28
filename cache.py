# -*- coding: utf-8 -*-
import logging
import time
from helper_methods import props

class _HostCacheEntry(object):
    "Basic class to hold data on a cached host"

    def __init__(self, dpid, port, mac):
        self.dpid = dpid
        self.port = port
        self.mac = mac
        self.timestamp = time.time()
        self.counter = 0

    def __str__(self):
        args = []
        args.append('<HostCache')
        for prop in props(self):
            args.append(' %s = %s ' % (prop, getattr(self, prop)))
        args.append('>')
        return ''.join(args)

class HostCache(object):
    "Keeps track of recently learned hosts to prevent duplicate flowmods"

    def __init__(self, timeout):
        self.cache = {}
        self.logger = logging.getLogger("SS2HostCache")
        # The amount of time that the controller ignores packets matching a recently
        # learned dpid/port/mac combination. This is used to prevent the controller
        # application from processing a large number of packets forwarded to the
        # controller between the time the controller first learns a host and the
        # datapath has the appropriate flow entries fully installed.
        self.timeout = timeout

    def __str__(self):
        args = []
        args.append('<HostCache')
        for prop in props(self):
            args.append(' %s = %s ' % (prop, getattr(self, prop)))
        args.append('>')
        return ''.join(args)

    def is_new_host(self, dpid, port, mac):
        "Check if the host/port combination is new and add the host entry"
        self.clean_entries()
        entry = self.cache.get((dpid, port, mac), None)
        if entry != None:
            entry.counter += 1
            return False

        entry = _HostCacheEntry(dpid, port, mac)
        self.cache[(dpid, port, mac)] = entry
        self.logger.debug("Learned %s, %s, %s", dpid, port, mac)
        return True

    def clean_entries(self):
        "Clean entries older than self.timeout"
        curtime = time.time()
        _cleaned_cache = {}
        for host in self.cache.values():
            if host.timestamp + self.timeout >= curtime:
                _cleaned_cache[(host.dpid, host.port, host.mac)] = host
            else:
                self.logger.debug("Unlearned %s, %s, %s after %s hits",
                                  host.dpid, host.port, host.mac, host.counter)

        self.cache = _cleaned_cache
