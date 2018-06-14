from spinn_utilities.overrides import overrides

from spynnaker.pyNN.models.abstract_models import AbstractContainsUnits
from spynnaker.pyNN.models.neuron.synapse_types import AbstractSynapseType


class SynapseTypeNoOp(AbstractSynapseType, AbstractContainsUnits):

    def get_n_synapse_type_bits(self):
        return 0

    def get_n_synapse_types(self):
        # Workaround `spynnaker/pyNN/models/neuron/synaptic_manager.py' that
        # needs at least one synapse_type, although this Page Rank
        # implementation does not need any.
        return 1

    def get_synapse_id_by_target(self, target):
        return 0

    def get_synapse_targets(self):
        return "noop"

    def get_n_synapse_type_parameters(self):
        return 0

    def get_synapse_type_parameters(self):
        return []

    def get_synapse_type_parameter_types(self):
        return []

    def get_n_cpu_cycles_per_neuron(self):
        return 0

    @overrides(AbstractContainsUnits.get_units)
    def get_units(self, variable):
        return None
