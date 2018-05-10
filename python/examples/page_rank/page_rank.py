"""
Proof of concept implementation of an instance of the PageRank algorithmic problem.

Sample PageRank graph:

    A---------+
    ^         |
    |         |
    |         |
    v         v
    C-------->B
    ^         |
    |         |
    |         |
    v         |
    D<--------+

    Based on: https://www.youtube.com/watch?v=P8Kt6Abq_rM&t=202s
"""
import sys
from threading import Condition

import spinnaker_graph_front_end as front_end
from pacman.model.constraints.placer_constraints.placer_chip_and_core_constraint import PlacerChipAndCoreConstraint
from spinn_front_end_common.utilities.connections.live_event_connection import LiveEventConnection
from spinn_front_end_common.utilities.notification_protocol.socket_address import SocketAddress
from spinn_front_end_common.utility_models.live_packet_gather_partitioned_vertex import LivePacketGatherPartitionedVertex
from spinnaker_graph_front_end import MultiCastPartitionedEdge
from spinnman.messages.eieio.eieio_type import EIEIOType

from examples.page_rank.page_rank_edge import PageRankEdge
from examples.page_rank.page_rank_vertex import PageRankVertexPartitioned


machine_time_step = 1000
time_scale_factor = 1
machine_port = 11111
machine_receive_port = 22222
machine_host = "0.0.0.0"
live_gatherer_label = "LiveHeatGatherer"
notify_port = 19999
database_listen_port = 19998

n_chips_required = None
if front_end.is_allocated_machine():
    n_chips_required = 2


# set up the front end and ask for the detected machines dimensions
front_end.setup(
    graph_label="page_rank_graph",
    model_binary_module=sys.modules[__name__],
    database_socket_addresses={ SocketAddress("127.0.0.1", notify_port, database_listen_port) },
    n_chips_required=n_chips_required)
machine = front_end.machine()

# Create a gatherer to read the heat values
live_gatherer = front_end.add_partitioned_vertex(
    LivePacketGatherPartitionedVertex,
    {
        'machine_time_step': machine_time_step,
        'timescale_factor': time_scale_factor,
        'label': live_gatherer_label,
        'ip_address': machine_host,
        'port': machine_receive_port,
        'payload_as_time_stamps': False,
        'use_payload_prefix': False,
        'strip_sdp': True,
        'message_type': EIEIOType.KEY_PAYLOAD_32_BIT
    }
)
LIVE_GATHERER_POS = (0, 0, 1)
live_gatherer.add_constraint(PlacerChipAndCoreConstraint(*LIVE_GATHERER_POS))

# Create a list of lists of vertices (x * 4) by (y * 4)
# (for 16 cores on a chip - missing cores will have missing vertices)
max_x_element_id = (machine.max_chip_x + 1) * 4
max_y_element_id = (machine.max_chip_y + 1) * 4


def gen_vertices():
    for x in range(0, max_x_element_id):
        for y in range(0, max_y_element_id):

            chip_x = x / 4
            chip_y = y / 4
            core_x = x % 4
            core_y = y % 4
            core_p = ((core_x * 4) + core_y) + 1

            # Skip live_gatherer vertex
            if (chip_x, chip_y, core_p) == LIVE_GATHERER_POS:
                continue
            # Skip broken chips / monitor cores
            chip = machine.get_chip_at(chip_x, chip_y)
            if chip is None:
                continue
            core = chip.get_processor_with_id(core_p)
            if core is None or core.is_monitor:
                continue

            # Add a vertex
            element = front_end.add_partitioned_vertex(
                PageRankVertexPartitioned,
                {
                    'machine_time_step': machine_time_step,
                    'time_scale_factor': time_scale_factor
                },
                label="Heat Element {}, {}".format(x, y))
            element.add_constraint(PlacerChipAndCoreConstraint(chip_x, chip_y, core_p))
            # yield x, y, element
            yield element


# build edges
receive_labels = list()


def add_live_gatherer_link((element, name)):
    lbl = "Live output from {}".format(name)

    # add a link from the heat element to the live packet gatherer
    front_end.add_partitioned_edge(
        MultiCastPartitionedEdge,
        dict(pre_subvertex=element, post_subvertex=live_gatherer),
        label=lbl,
        partition_id="TRANSMISSION")
    receive_labels.append(lbl)


def add_vertex_link((pre_vertex, pre_name), (post_vertex, post_name)):
    front_end.add_partitioned_edge(
        PageRankEdge,
        dict(pre_subvertex=pre_vertex, post_subvertex=post_vertex),
        label="Edge from {} to {}".format(pre_name, post_name),
        partition_id="TRANSMISSION")


#
# Define graph
#

node_gen = iter(gen_vertices())
node_a = (next(node_gen), 'A')
node_b = (next(node_gen), 'B')
node_c = (next(node_gen), 'C')
node_d = (next(node_gen), 'D')

add_live_gatherer_link(node_a)
add_live_gatherer_link(node_b)
add_live_gatherer_link(node_c)
add_live_gatherer_link(node_d)

add_vertex_link(node_a, node_b)
add_vertex_link(node_a, node_c)
add_vertex_link(node_b, node_d)
add_vertex_link(node_c, node_a)
add_vertex_link(node_c, node_b)
add_vertex_link(node_c, node_d)
add_vertex_link(node_d, node_c)

#
# Capture outputs
#

# Set up the live connection for receiving heat elements
live_heat_connection = LiveEventConnection(
    live_gatherer_label, receive_labels=receive_labels, local_port=notify_port, partitioned_vertices=True)
condition = Condition()


def receive_heat(lbl, atom, value):
    condition.acquire()
    print "RECEIVED {}: {}".format(lbl, value / 65536.0)
    condition.release()


# Set up callbacks to occur when spikes are received
for label in receive_labels:
    live_heat_connection.add_receive_callback(label, receive_heat)

front_end.run(1000)
front_end.stop()
