#!/usr/local/bin/python2
# -*- coding: utf-8 -*-

from __future__ import print_function

import socket
import requests
import json

from dnslib import DNSRecord, RCODE, RR
from dnslib.server import DNSServer, DNSHandler, BaseResolver, DNSLogger


class ProxyResolver(BaseResolver):

    def __init__(self, address, port, trustable, timeout=0):
        self.address = address
        self.port = port
        self.timeout = timeout
        self.host = self.address.split('://')[1].split('/')[0].split('@')[-1].rsplit(':', 1)[0]
        for tr in trustable:
            self.hostrecord = DNSRecord.parse(DNSRecord.question(self.host).send(tr, 53, timeout=self.timeout)).get_a()
            if self.hostrecord:
                print('[init] resolved host {} as {}'.format(self.host, self.hostrecord))
                break

    def resolve(self, request, handler):
        try:
            resprs = []

            for q in request.questions:
                if str(q.qname) == self.host + '.':
                    resprs.append(self.hostrecord)
                    continue
                resp = requests.get(self.address + '?domain={domain}&type={type}'.format(**{
                    'domain': str(q.qname),
                    'type': q.qtype
                })).content
                resp = json.loads(resp)
                if isinstance(resp, list):
                    print(resp)
                    resprs += resp

            reply = request.reply()
            for r in resprs:
                reply.add_answer(
                    *(RR.fromZone('{host}. {ttl} {class} {type} {ip}'.format(**r))
                      if isinstance(r, dict)
                      else
                      [r])
                )

        except socket.timeout:
            reply = request.reply()
            reply.header.rcode = RCODE.NXDOMAIN

        return reply


if __name__ == '__main__':

    import argparse, time

    p = argparse.ArgumentParser(description="DNS Proxy")
    p.add_argument("--port", "-p", type=int, default=53,
                   metavar="<port>",
                   help="Local proxy port (default:53)")
    p.add_argument("--address", "-a", default="",
                   metavar="<address>",
                   help="Local proxy listen address (default:all)")
    p.add_argument("--upstream", "-u", default="",
                   metavar="<resolve url>",
                   help="Upstream DNS proxy server url (use '%' to represent the domain in query) (default:blank)")
    p.add_argument("--trustable", "-t", default="114.114.114.114",
                   metavar="<dns servers>",
                   help="Trustable DNS for host name (default: 114)")
    p.add_argument("--tcp", action='store_true', default=False,
                   help="TCP proxy (default: UDP only)")
    p.add_argument("--timeout", "-o", type=float, default=5,
                   metavar="<timeout>",
                   help="Upstream timeout (default: 5s)")
    p.add_argument("--passthrough", action='store_true', default=False,
                   help="Dont decode/re-encode request/response (default: off)")
    p.add_argument("--log", default="request,reply,truncated,error",
                   help="Log hooks to enable (default: +request,+reply,+truncated,+error,-recv,-send,-data)")
    p.add_argument("--log-prefix", action='store_true', default=False,
                   help="Log prefix (timestamp/handler/resolver) (default: False)")
    args = p.parse_args()

    assert args.upstream, \
        'Please specify upstream http(s) server url'

    args.trustable = args.trustable.split(',')

    print("Starting Proxy Resolver (%s:%d -> %s) [%s]" % (
        args.address or "*", args.port,
        args.upstream,
        "UDP/TCP" if args.tcp else "UDP"))

    resolver = ProxyResolver(args.upstream, 0, args.trustable, args.timeout)
    handler = DNSHandler
    logger = DNSLogger(args.log, args.log_prefix)
    udp_server = DNSServer(resolver,
                           port=args.port,
                           address=args.address,
                           logger=logger,
                           handler=handler)
    udp_server.start_thread()

    if args.tcp:
        tcp_server = DNSServer(resolver,
                               port=args.port,
                               address=args.address,
                               tcp=True,
                               logger=logger,
                               handler=handler)
        tcp_server.start_thread()

    while udp_server.isAlive():
        time.sleep(1)
        
