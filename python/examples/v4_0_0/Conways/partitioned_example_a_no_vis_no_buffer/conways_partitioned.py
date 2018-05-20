import os

import spinnaker_graph_front_end as front_end
from pacman.model.graphs.machine import MachineEdge

from examples.v4_0_0.Conways.partitioned_example_a_no_vis_no_buffer.conways_basic_cell import ConwayBasicCell


runtime = 50
# machine_time_step = 100
MAX_X_SIZE_OF_FABRIC = 7
MAX_Y_SIZE_OF_FABRIC = 7

# set up the front end and ask for the detected machines dimensions
front_end.setup(n_chips_required=2, model_binary_folder=os.path.dirname(__file__))

# figure out if machine can handle simulation
cores = front_end.get_number_of_available_cores_on_machine()
if cores <= (MAX_X_SIZE_OF_FABRIC * MAX_Y_SIZE_OF_FABRIC):
    raise KeyError("Don't have enough cores to run simulation")

# contain the vertices for the connection aspect
vertices = [[None] * MAX_X_SIZE_OF_FABRIC for _ in range(MAX_Y_SIZE_OF_FABRIC)]

active_states = [(2, 2), (3, 2), (3, 3), (4, 3), (2, 4)]

# build vertices
for x in range(MAX_X_SIZE_OF_FABRIC):
    for y in range(MAX_Y_SIZE_OF_FABRIC):
        v = ConwayBasicCell("cell{}".format((x * MAX_X_SIZE_OF_FABRIC) + y), (x, y) in active_states)
        vertices[x][y] = v
        front_end.add_machine_vertex_instance(v)

# verify the initial state
output = ""
for y in range(MAX_X_SIZE_OF_FABRIC - 1, 0, -1):
    for x in range(0, MAX_Y_SIZE_OF_FABRIC):
        output += "X" if vertices[x][y].state else " "
    output += "\n"
print output
print "\n\n"

# build edges
for x in range(MAX_X_SIZE_OF_FABRIC):
    for y in range(MAX_Y_SIZE_OF_FABRIC):

        positions = [
            (x,     y + 1, "N"),
            (x + 1, y + 1, "NE"),
            (x + 1, y,     "E"),
            (x + 1, y - 1, "SE"),
            (x,     y - 1, "S"),
            (x - 1, y - 1, "SW"),
            (x - 1, y,     "W"),
            (x - 1, y + 1, "NW")
        ]
        positions = [(_x % MAX_X_SIZE_OF_FABRIC, _y % MAX_Y_SIZE_OF_FABRIC, _c)
                     for _x, _y, _c in positions]

        for dest_x, dest_y, compass in positions:
            front_end.add_machine_edge_instance(
                MachineEdge(vertices[x][y], vertices[dest_x][dest_y], label=compass),
                ConwayBasicCell.PARTITION_ID
            )

# run the simulation
front_end.run(runtime)

# get recorded data
recorded_data = dict()

# get the data per vertex
for x in range(MAX_X_SIZE_OF_FABRIC):
    for y in range(MAX_Y_SIZE_OF_FABRIC):
        recorded_data[(x, y)] = vertices[x][y].get_data(
            front_end.transceiver(),
            front_end.placements().get_placement_of_vertex(vertices[x][y]),
            front_end.no_machine_time_steps()
        )

# visualise it in text form (bad but no vis this time)
for time in range(runtime):
    print "at time {}".format(time)
    output = ""
    for y in range(MAX_X_SIZE_OF_FABRIC - 1, 0, -1):
        for x in range(0, MAX_Y_SIZE_OF_FABRIC):
            if recorded_data[(x, y)][time]:
                output += "|X"
            else:
                output += "| "
        output += "\n"
    print output
    print "\n\n"

# clear the machine
front_end.stop()
