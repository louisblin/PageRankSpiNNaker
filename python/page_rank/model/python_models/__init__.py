import os

from spynnaker.pyNN.abstract_spinnaker_common import AbstractSpiNNakerCommon

from page_rank.model.python_models import model_binaries

# This adds the model binaries path to the paths searched by sPyNNaker
AbstractSpiNNakerCommon.register_binary_search_path(
    os.path.dirname(model_binaries.__file__))
