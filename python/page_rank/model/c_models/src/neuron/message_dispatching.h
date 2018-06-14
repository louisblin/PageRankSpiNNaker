#ifndef _MESSAGE_DISPATCHING_H_
#define _MESSAGE_DISPATCHING_H_

#include <common/neuron-typedefs.h>
#include <neuron/synapse_row.h>
#include <debug.h>

// Get the index of the ring buffer for a given timestep and combined
// synapse type and neuron index (as stored in a synapse row)
static inline index_t message_dispatching_get_ring_buffer_index_combined(
        uint32_t simulation_timestep,
        uint32_t combined_synapse_neuron_index) {
    return (((simulation_timestep & SYNAPSE_DELAY_MASK)
             << SYNAPSE_TYPE_INDEX_BITS)
            | combined_synapse_neuron_index);
}

// Converts a weight stored in a synapse row to an input
static inline input_t message_dispatching_convert_weight_to_input(
        weight_t weight, uint32_t left_shift) {
    union {
        int_k_t input_type;
        s1615 output_type;
    } converter;

    converter.input_type = (int_k_t) (weight) << left_shift;

    return converter.output_type;
}

static inline void message_dispatching_print_weight(weight_t weight, uint32_t left_shift) {
    if (weight != 0) {
        io_printf(IO_BUF, "%12.6k", message_dispatching_convert_weight_to_input(weight, left_shift));
    } else {
        io_printf(IO_BUF, "      ");
    }
}

bool message_dispatching_initialise(address_t synaptic_matrix_address, uint32_t n_neurons_value,
        address_t *indirect_synapses_address);

void message_dispatching_do_timestep_update(timer_t time);

//! \brief process a synaptic row
//! \param[in] row: the synaptic row in question
//! \param[in] payload: the payload to forward
//! \return bool if successful or not
bool message_dispatching_process_synaptic_row_page_rank(synaptic_row_t row, spike_t payload);

//! \brief returns the number of times the message_dispatching have saturated their weights.
//! \return the number of times the message_dispatching have saturated.
uint32_t message_dispatching_get_saturation_count();

//! \brief returns the counters for plastic and fixed pre synaptic events based
//!        on (if the model was compiled with SYNAPSE_BENCHMARK parameter) or
//!        returns 0
//! \return the counter for plastic and fixed pre synaptic events or 0
uint32_t message_dispatching_get_pre_synaptic_events();


#endif // _MESSAGE_DISPATCHING_H_
