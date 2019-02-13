import sim
from sim.core import CreateEntity, topoOf
from sim.basics import BasicHost
from hub import Hub
import sim.topo as topo


def create(switch_type=Hub, host_type=BasicHost):
    """
    Creates the topology required by the simulation:
    hA--sA -- sB--hB
         |  /  |
    hC--sC -- sD--hD
    """
    switch_type.create('sA')
    switch_type.create('sB')
    switch_type.create('sC')
    switch_type.create('sD')

    host_type.create('hA')
    host_type.create('hB')
    host_type.create('hC')
    host_type.create('hD')

    topo.link(sA, hA, latency=0)
    topo.link(sB, hB, latency=0)
    topo.link(sC, hC, latency=0)
    topo.link(sD, hD, latency=0)

    topo.link(sA, sB, latency=2)
    topo.link(sA, sC, latency=7)

    topo.link(sB, sC, latency=1)
    topo.link(sB, sD, latency=3)
    topo.link(sC, sD, latency=1)
