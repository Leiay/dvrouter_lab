# Readme for dv_router

### difference between switch and host
**SWITCH** is switch, it receive package and send them according to some rules.
However, **HOST** is the network N(in the guide book), it can ping or receive pong packet.
To check these things' api, you can go to:
> Switch: \
> sim.api in Entity \
> override in: dv_rounter in DVRounter

> Host: \
> sim.api in Entity \
> override in: sim.basic in BasicHost



## definition of scenarios
the guide book indicate 



        firstly, the 
        self.name is free to use, it indicate this entity's name
        self.rip_table refers to the routing table this entity has, it is a dict:
        :key the target host, ranged in [hA, hB, hC, hD]
        :val also a dict
            :key
            'distance':
                :type int
                refers to the hop count to the target host
            'nextJump':
                :type Entity, ranged in [sA, sB, sC, sD, hA, hB, hC, hD]
                refers to the next jump to the target host
            'nextPort':
                :type int, ranged according to the topology of this entity\
                          hA--sA -- sB--hB
                               |  /  |
                          hC--sC -- sD--hD
                      e.g. if it is sA, it should in range[0, 2]
                           if it is sB, it should in range[0, 3]
                refers to the actual port the packet should go in next hop
                
        """# dvrouter_lab
