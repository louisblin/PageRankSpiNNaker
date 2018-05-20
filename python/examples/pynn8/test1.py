import spynnaker8 as p
import pyNN.utility.plotting as plot
import matplotlib.pyplot as plt

p.setup(timestep=1.0)
p.set_number_of_neurons_per_core(p.IF_curr_exp, 100)

pop_1 = p.Population(1, p.IF_curr_exp(), label="pop_1")
input = p.Population(1, p.SpikeSourceArray(spike_times=[0]), label="input")
input_proj = p.Projection(input, pop_1, p.OneToOneConnector(), synapse_type=p.StaticSynapse(weight=5, delay=1))

pop_1.record(["spikes", "v"])
simtime = 10000000
p.run(simtime)

neo = pop_1.get_data(variables=["spikes", "v"])
spikes = neo.segments[0].spiketrains
print('spikes', spikes)
v = neo.segments[0].filter(name='v')[0]
print('v', v)
p.end()

plot.Figure(
    # plot voltage for first ([0]) neuron
    plot.Panel(v, ylabel="Membrane potential (mV)", data_labels=[pop_1.label], yticks=True, xlim=(0, simtime)),
    # plot spikes (or in this case spike)
    plot.Panel(spikes, yticks=True, markersize=5, xlim=(0, simtime)),
        title="Simple Example", annotations="Simulated with {}".format(p.name())
)
plt.show()


### Notes
#
# Data exchange between cores done by:
# - MCP: MultiCast Packet
# - SDP: SpiNNaker Datagram Packet
# - DMA to exchange between memory spaces
#
# spin1 framework does allow for MC packets to takek a 32bit payload
#
# Looks like the current sPyNNaker framework does not allow for payloads
## https://github.com/SpiNNakerManchester/sPyNNaker/blob/5add8ddd983a0349cd710f8ea4848c078560e7b3/neural_modelling/src/neuron/neuron.c#L628
