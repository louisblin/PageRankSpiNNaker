from spynnaker.pyNN.models.neuron.threshold_types import AbstractThresholdType


class ThresholdTypeNoOp(AbstractThresholdType):
    """ A threshold type class that does nothing"""

    def get_n_threshold_parameters(self):
        return 0

    def get_threshold_parameters(self):
        return []

    def get_threshold_parameter_types(self):
        return []

    def get_n_cpu_cycles_per_neuron(self):
        return 0
