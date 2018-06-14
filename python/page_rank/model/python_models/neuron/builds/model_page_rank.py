# All models should inherit from this main interface to use spynnaker tools
from spynnaker.pyNN.models.neuron import AbstractPopulationVertex
from spynnaker.pyNN.models.neuron.input_types import InputTypeCurrent

from page_rank.model.python_models.neuron.neuron_models.neuron_model_page_rank \
    import NeuronModelPageRank
from page_rank.model.python_models.neuron.synapse_types.synapse_type_noop \
    import SynapseTypeNoOp
from page_rank.model.python_models.neuron.threshold_types.threshold_type_noop \
    import ThresholdTypeNoOp


class PageRankBase(AbstractPopulationVertex):
    """Base class defining what the Page Rank neural model"""

    # Maximum number of atoms per core that can be supported.
    # Note: a higher number would overflow the 8-bit semaphores used.
    _model_based_max_atoms_per_core = 255

    # All default parameters need to be defined
    default_parameters = {}

    # Default parameters for this build, used when end user has not entered any
    none_pynn_default_parameters = {
        'curr_rank_acc_init': 0,
        'curr_rank_count_init': 0,
        'iter_state_init': 0,
    }

    def __init__(
            self, n_neurons, spikes_per_second=AbstractPopulationVertex.
                none_pynn_default_parameters['spikes_per_second'],
            ring_buffer_sigma=AbstractPopulationVertex.
                none_pynn_default_parameters['ring_buffer_sigma'],
            incoming_spike_buffer_size=AbstractPopulationVertex.
                none_pynn_default_parameters['incoming_spike_buffer_size'],
            constraints=AbstractPopulationVertex.none_pynn_default_parameters[
                'constraints'],
            label=AbstractPopulationVertex.none_pynn_default_parameters[
                'label'],

            # [default] Global model parameters
            damping_factor=None,  # required
            damping_sum=None,  # required

            # [default] Model parameters
            incoming_edges_count=None,  # required
            outgoing_edges_count=None,  # required

            # [none pynn] Initial values for the state variables
            rank_init=None,  # required
            curr_rank_acc_init=none_pynn_default_parameters[
                'curr_rank_acc_init'],
            curr_rank_count_init=none_pynn_default_parameters[
                'curr_rank_count_init'],
            iter_state_init=none_pynn_default_parameters['iter_state_init']):
        neuron_model = NeuronModelPageRank(
            n_neurons,
            damping_factor, damping_sum,
            incoming_edges_count, outgoing_edges_count,
            rank_init, curr_rank_acc_init, curr_rank_count_init, iter_state_init
        )

        input_type = InputTypeCurrent()  # Used as a NoOp
        synapse_type = SynapseTypeNoOp()
        threshold_type = ThresholdTypeNoOp()

        # instantiate sPyNNaker by initialising the AbstractPopulationVertex
        AbstractPopulationVertex.__init__(
            # standard inputs, do not need to change.
            self, n_neurons=n_neurons, label=label,
            spikes_per_second=spikes_per_second,
            ring_buffer_sigma=ring_buffer_sigma,
            incoming_spike_buffer_size=incoming_spike_buffer_size,
            max_atoms_per_core=PageRankBase._model_based_max_atoms_per_core,

            # These are the various model types
            neuron_model=neuron_model, input_type=input_type,
            synapse_type=synapse_type, threshold_type=threshold_type,
            model_name="PageRank",  # name shown in reports
            binary="page_rank.aplx"  # C binary, defined in neuron/builds/<name>
        )

    @staticmethod
    def get_max_atoms_per_core():
        return PageRankBase._model_based_max_atoms_per_core

    @staticmethod
    def set_max_atoms_per_core(new_value):
        PageRankBase._model_based_max_atoms_per_core = new_value
