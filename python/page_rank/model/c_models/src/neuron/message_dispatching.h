#ifndef _MESSAGE_DISPATCHING_H_
#define _MESSAGE_DISPATCHING_H_

#include <common/neuron-typedefs.h>

bool message_dispatching_initialise(address_t synaptic_matrix_address,
        uint32_t n_neurons_value, address_t *indirect_synapses_address);

//! \brief process a synaptic row
//! \param[in] row: the synaptic row in question
//! \param[in] payload: the payload to forward
//! \return bool if successful or not
bool message_dispatching_process_synaptic_row_page_rank(synaptic_row_t row,
        spike_t payload);

//! \brief returns the number of times the message_dispatching have saturated
//!        their weights.
//! \return the number of times the message_dispatching have saturated.
uint32_t message_dispatching_get_saturation_count();

//! \brief returns the counters for plastic and fixed pre synaptic events based
//!        on (if the model was compiled with SYNAPSE_BENCHMARK parameter) or
//!        returns 0
//! \return the counter for plastic and fixed pre synaptic events or 0
uint32_t message_dispatching_get_pre_synaptic_events();


#endif // _MESSAGE_DISPATCHING_H_
