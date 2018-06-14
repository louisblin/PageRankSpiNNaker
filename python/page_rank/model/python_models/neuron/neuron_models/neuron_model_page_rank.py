from data_specification.enums import DataType
from enum import Enum
from pacman.executor.injection_decorator import inject_items
from pacman.model.decorators.overrides import overrides
from spynnaker.pyNN.models.abstract_models import AbstractContainsUnits
from spynnaker.pyNN.models.neural_properties import NeuronParameter
from spynnaker.pyNN.models.neuron.neuron_models import AbstractNeuronModel
from spynnaker.pyNN.utilities import utility_calls


class _Parameters(Enum):
    def __new__(cls, value, data_type, unit):
        obj = object.__new__(cls)
        # Ordering of parameters matters, iteration order is based in _value_
        obj._value_ = value
        obj._data_type = data_type
        obj._unit = unit
        return obj

    @property
    def data_type(self):
        return self._data_type

    @property
    def unit(self):
        return self._unit


class _GlobalParameters(_Parameters):
    """
    Needs to match the C code `global_neuron_params_t' in neuron/models/*.h
    """
    DAMPING_FACTOR = (1, DataType.U032, 'proba')
    DAMPING_SUM = (2, DataType.U032, 'rk')
    MACHINE_TIME_STEP = (3, DataType.UINT32, 'steps')


class _NeuralParameters(_Parameters):
    """
    Needs to match the C code `neuron_t' in neuron/models/*.h
    """
    INCOMING_EDGES_COUNT = (1, DataType.UINT32, 'count')
    OUTGOING_EDGES_COUNT = (2, DataType.UINT32, 'count')
    RANK_INIT = (3, DataType.U032, 'rk')
    CURR_RANK_ACC_INIT = (4, DataType.U032, 'rk')
    CURR_RANK_COUNT_INIT = (5, DataType.UINT32, 'count')
    ITER_STATE_INIT = (6, DataType.UINT32, 'state')


class NeuronModelPageRank(AbstractNeuronModel, AbstractContainsUnits):

    def __init__(self, n_neurons,
                 damping_factor, damping_sum,
                 incoming_edges_count, outgoing_edges_count,
                 rank_init, curr_rank_acc_init, curr_rank_count_init,
                 iter_state_init):
        AbstractNeuronModel.__init__(self)
        AbstractContainsUnits.__init__(self)

        self._n_neurons = n_neurons

        # Global parameters (fixed value throughout simulation)
        self._damping_factor = damping_factor
        self._damping_sum = damping_sum

        # Store any neural parameters (fixed value throughout simulation)
        self._incoming_edges_count = self._var_init(incoming_edges_count)
        self._outgoing_edges_count = self._var_init(outgoing_edges_count)

        # Store any neural state variables (value is expected to change)
        self._initialise_state_vars([
            ('rank_init', rank_init),
            ('curr_rank_acc_init', curr_rank_acc_init),
            ('curr_rank_count_init', curr_rank_count_init),
            ('iter_state_init', iter_state_init),
        ])

    #
    # Initialisers for variables
    #

    def _initialise_state_vars(self, state_vars):
        """
        Custom initialiser for state variables.

        sPyNNaker allows for an initial value for be assigned to each state
        variables. For state var `my_var' in C, a python field `my_var_init'
        should be defined as well as an initialising method `initialise_my_var'

        :param state_vars: the state variables
        :return:
        """
        def _mk_initialize(state_var):
            def initialize(self, v):
                self[state_var] = self._var_init(v)

            return initialize

        for name, val in state_vars:
            _state_var = '_{}'.format(name)
            initialize_name = 'initialize_{}'.format(name[:-5])

            # Save variable to self._<var name>_init
            setattr(self, _state_var, self._var_init(val))
            # Set an init method to self.initialize_<var name>
            setattr(self, initialize_name, _mk_initialize(_state_var))

    def _var_init(self, state_var):
        return utility_calls.convert_param_to_numpy(state_var, self._n_neurons)

    #
    # Getters and setters for the parameters
    #

    @property
    def damping_factor(self):
        return self._damping_factor

    @damping_factor.setter
    def damping_factor(self, damping_factor):
        self._damping_factor = damping_factor

    @property
    def damping_sum(self):
        return self._damping_sum

    @damping_sum.setter
    def damping_sum(self, damping_sum):
        self._damping_sum = damping_sum

    @property
    def incoming_edges_count(self):
        return self._incoming_edges_count

    @incoming_edges_count.setter
    def incoming_edges_count(self, incoming_edges_count):
        self._incoming_edges_count = self._var_init(incoming_edges_count)

    @property
    def outgoing_edges_count(self):
        return self._outgoing_edges_count

    @outgoing_edges_count.setter
    def outgoing_edges_count(self, outgoing_edges_count):
        self._outgoing_edges_count = self._var_init(outgoing_edges_count)

    #
    # Mapping per-neuron parameters (`neuron_t' in C code)
    #

    @overrides(AbstractNeuronModel.get_n_neural_parameters)
    def get_n_neural_parameters(self):
        return len(_NeuralParameters)

    @overrides(AbstractNeuronModel.get_neural_parameters)
    def get_neural_parameters(self):
        def _get_var(item):
            return getattr(self, '_' + item.name.lower())

        # Note: must match the order of parameters in `neuron_t' in C
        return [
            NeuronParameter(_get_var(item), item.data_type)
            for item in _NeuralParameters
        ]

    @overrides(AbstractNeuronModel.get_neural_parameter_types)
    def get_neural_parameter_types(self):
        return [item.data_type for item in _NeuralParameters]

    #
    # Mapping population-wide parameters (`global_neuron_t' in C code)
    #

    @overrides(AbstractNeuronModel.get_n_global_parameters)
    def get_n_global_parameters(self):
        return len(_GlobalParameters)

    # noinspection PyMethodOverriding
    @inject_items({"machine_time_step": "MachineTimeStep"})
    @overrides(
        AbstractNeuronModel.get_global_parameters,
        additional_arguments={"machine_time_step"}
    )
    def get_global_parameters(self, machine_time_step):
        def _get_var(item):
            name = item.name.lower()
            if name == 'machine_time_step':
                return machine_time_step
            return getattr(self, '_' + name)

        # Note: must match the order of parameters in `global_neuron_t' in C
        return [
            NeuronParameter(_get_var(item), item.data_type)
            for item in _GlobalParameters
        ]

    @overrides(AbstractNeuronModel.get_global_parameter_types)
    def get_global_parameter_types(self):
        return [item.data_type for item in _GlobalParameters]

    #
    # Utilities
    #

    @overrides(AbstractNeuronModel.get_n_cpu_cycles_per_neuron)
    def get_n_cpu_cycles_per_neuron(self):
        # Number of CPU cycles taken by neuron_model functions in main loop
        # Note: This can be a guess
        return 40

    @overrides(AbstractContainsUnits.get_units)
    def get_units(self, variable):
        return _NeuralParameters[variable.upper()].unit
