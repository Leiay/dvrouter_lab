import copy
from sim import api
from sim import basics
from sim.basics import *

'''
Create your distance vector router in this file.
'''


class DVRouter(Entity):  # switch

    def __init__(self):
        self.routingTable = {}  # routingTable[dstHost] = {port: dict(hopCount, hopLatency)}
        self.portToHop = {}  # portToHop[port] = dict(hop, latency)
        self.unreachableHopCount = 16
        self.unreachableHopLatency = 16
        self.crit = 'hopLatency'

    def handle_rx(self, packet, port):
        """
        handle_rx is the function we need to override
        :type port: int, specify the port the packet go into this entity
        :type packet: api.Packet
        """
        print(packet)
        if isinstance(packet, basics.DiscoveryPacket):
            self.handle_discovery_packet(packet, port)
        elif isinstance(packet, MyRoutingUpdate):  # in case there is a routing update
            self.handle_routing_update(packet, port)
        else:
            self.handle_anything_else(packet)

    def handle_timer(self):
        pass

    def handle_link_up(self, newHop, port, latency):
        self.portToHop[port] = dict(hop=newHop, latency=latency)
        if isinstance(newHop, basics.HostEntity):
            self.routingTable[newHop] = {port: {'hopCount': 1, 'hopLatency': latency}}

    def handle_link_down(self, port):
        for dstHost in self.routingTable:
            dstDict = self.routingTable[dstHost]
            if port in dstDict:
                dstDict[port]['hopCount'] = self.unreachableHopCount
                dstDict[port]['hopLatency'] = float("inf")
        del self.portToHop[port]

    def handle_discovery_packet(self, packet, port):
        """
        HostDiscoveryPacket is defined in sim.basics, which is a subclass of Packet

        basics.HostDiscoveryPackets are sent automatically by host entities
        when they are attached to a link.
        Your DVRouter should monitor for these packets so that
        it knows what hosts exist and where they are attached.
        Your DVRouter should never send or forward HostDiscoveryPackets.
        """
        latency = packet.latency
        newHop = packet.src
        if packet.is_link_up:
            self.handle_link_up(newHop, port, latency)
        else:
            self.handle_link_down(port)
        self.send_routing_update()

    def send_routing_update(self):
        """
        send routing update to my every neighbors
        :return: nothing
        """
        for port in self.portToHop:
            updatePacket = MyRoutingUpdate()
            for dstHost in self.routingTable:
                _, bestHopCount, _, bestHopLatency = self.getBestHostDistance(dstHost)
                updatePacket.add_dst(dstHost, bestHopCount, bestHopLatency)
            self.send(updatePacket, port, False)

    def getBestHostDistance(self, dstHost):
        """
        get the shortest path according to hopCount or hopLatency
        :param dstHost: the destination of the packet
        :return: bestPort, and corresponding distence
        """
        dstDict = self.routingTable[dstHost]
        bestPortForCount, bestPortForLatency = -1, -1
        bestHopCount, bestHopLatency = self.unreachableHopCount, self.unreachableHopLatency
        for port in dstDict:
            hopCount = dstDict[port]['hopCount']
            hopLatency = dstDict[port]['hopLatency']
            if bestHopCount > hopCount:
                bestHopCount = hopCount
                bestPortForCount = port
            if bestHopLatency > hopLatency:
                bestHopLatency = hopLatency
                bestPortForLatency = port
        return bestPortForCount, bestHopCount, bestPortForLatency, bestHopLatency

    def handle_routing_update(self, packet, port):
        """
        RoutingUpdate is defined in sim.basics, which is a subclass of Packet

        basics.RoutePacket contains a single route.
        It has a destination attribute (the Entity that the route is routing to)
        and a latency attribute which is the distance to the destination.
        Take special note that RoutePacket.destination and Packet.dst are not the same thing.
        They are essentially at different layers.
        dst is like an L2 address -- it's where this particular packet is destined
        (and since RoutePackets should never be directly forwarded, this should probably be None).
        destination is at a higher layer and specifies which destination this route is for.
        """
        is_updated = False
        for dstHost in packet.all_dsts():
            hopCount = packet.get_hop_count(dstHost)
            hopLatency = packet.get_hop_latency(dstHost)
            addLatency = self.portToHop[port]['latency']
            portDict = dict(hopCount=hopCount + 1, hopLatency=hopLatency + addLatency)
            if hopCount+1 < self.unreachableHopCount and hopLatency+addLatency < self.unreachableHopLatency:
                if dstHost not in self.routingTable:
                    is_updated = True
                    self.routingTable[dstHost] = {port: portDict}
                else:
                    if port not in self.routingTable[dstHost]:
                        is_updated = True
                        self.routingTable[dstHost][port] = portDict
                    elif not self.routingTable[dstHost][port]['hopCount'] == hopCount + 1:
                        is_updated = True
                        self.routingTable[dstHost][port] = portDict
                    elif not self.routingTable[dstHost][port]['hopLatency'] == hopLatency + addLatency:
                        is_updated = True
                        self.routingTable[dstHost][port] = portDict
        if is_updated:
            self.send_routing_update()

    def handle_anything_else(self, packet):
        dstHost = packet.dst
        if dstHost not in self.routingTable.keys():
            self.log("Entity {} is not in routingTable".format(dstHost))
            return True
        if len(self.routingTable[dstHost].items()) == 0:
            self.log("No ports for host {} in routingTable".format(dstHost))
            return True
        if self.crit == 'hopCount':
            if self.getBestHostDistance(dstHost)[1] > self.unreachableHopCount:
                self.log("Best Path for entity {} is too long".format(dstHost))
                return True
        elif self.crit == 'hopLatency':
            if self.getBestHostDistance(dstHost)[3] > self.unreachableHopLatency:
                self.log("Best Path for entity {} is too long".format(dstHost))
                return True

        self.log('destination: {}'.format(dstHost.name))
        self.log('table for destination:')
        for entry in self.routingTable[dstHost]:
            if entry in self.portToHop:
                self.log('port: {}, hopCount: {}, hopLatency: {}, nextHop: {}'
                         .format(entry, self.routingTable[dstHost][entry]['hopCount'],
                                 self.routingTable[dstHost][entry]['hopLatency'],
                                 self.portToHop[entry]))
        if self.crit == 'hopCount':
            self.send(packet, self.getBestHostDistance(dstHost)[0], False)
        elif self.crit == 'hopLatency':
            self.send(packet, self.getBestHostDistance(dstHost)[2], False)
        return True

    def useless_handle(self, packet, port):
        # the packet has hopped more than one times
        import_entity = copy.deepcopy(packet.trace[-2])
        if isinstance(import_entity, api.HostEntity):
            import_host = import_entity
            self.routingTable[import_host.name] = dict(nextJump=import_host.name, distance=1, nextPort=port)
        else:
            import_switch = import_entity
            import_switch_table = import_switch.get_entity_table()
            for key_host in import_switch_table:  # pre-fixing
                import_switch_table[key_host]['distance'] += 1
                import_switch_table[key_host]['nextJump'] = import_switch.name
                import_switch_table[key_host]['nextPort'] = port
            for key_host in import_switch_table:
                if import_switch_table[key_host]['distance'] > 15:  # inaccessible to that host
                    if key_host not in self.routingTable:
                        self.routingTable[key_host] = dict(nextJump=None, distance=16, nextPort=None)
                else:
                    if key_host not in self.routingTable:
                        self.routingTable[key_host] = import_switch_table[key_host]
                    else:  # check nextJump
                        import_next_jump = import_switch_table[key_host]['nextJump']
                        my_next_jump = self.routingTable[key_host]['nextJump']
                        if import_next_jump == my_next_jump:  # then update the table
                            self.routingTable[key_host] = import_switch_table[key_host]
                        else:
                            import_distance = import_switch_table[key_host]['distance']
                            my_distance = import_switch_table[key_host]['distance']
                            if import_distance > my_distance:
                                pass
                            else:
                                self.routingTable[key_host] = import_switch_table[key_host]


class MyRoutingUpdate(Packet):
    """
    A Routing Update message to use with your DVRouter implementation.

    basically defined in basics.RoutingUpdate, but I add the latency attr
    """

    def __init__(self):
        Packet.__init__(self)
        self.hopCountPaths = {}
        self.hopLatencyPaths = {}

    def add_dst(self, dstHost, hopCount, hopLatency):
        self.hopCountPaths[dstHost] = hopCount
        self.hopLatencyPaths[dstHost] = hopLatency

    def get_hop_count(self, dstHost):
        return self.hopCountPaths[dstHost]

    def get_hop_latency(self, dstHost):
        return self.hopLatencyPaths[dstHost]

    def all_dsts(self):
        assert self.hopCountPaths.keys() == self.hopLatencyPaths.keys()
        return self.hopCountPaths.keys()

    def str_routing_table(self):
        raise NotImplementedError
