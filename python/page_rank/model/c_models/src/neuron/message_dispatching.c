#include "message_dispatching.h"
#include "vertex.h"
#include <debug.h>
#include <spin1_api.h>
#include <string.h>

// Globals required for synapse benchmarking to work.
uint32_t  num_fixed_pre_synaptic_events = 0;

// The number of neurons
static uint32_t n_neurons;

// Count of the number of times the ring buffers have saturated
static uint32_t saturation_count = 0;


/* PRIVATE FUNCTIONS */

static inline void _print_synaptic_row(synaptic_row_t synaptic_row) {
#if LOG_LEVEL >= LOG_DEBUG
    log_debug("Synaptic row, at address %08x Num plastic words:%u\n",
              (uint32_t )synaptic_row, synapse_row_plastic_size(synaptic_row));
    if (synaptic_row == NULL) {
        return;
    }
    log_info("----------------------------------------\n");

    // Get details of fixed region
    address_t fixed_region_address = synapse_row_fixed_region(synaptic_row);
    address_t fixed_synapses = synapse_row_fixed_weight_controls(fixed_region_address);
    size_t n_fixed_synapses = synapse_row_num_fixed_synapses(fixed_region_address);
    log_debug("Fixed region %u fixed synapses (%u plastic control words):\n",
              n_fixed_synapses, synapse_row_num_plastic_controls(fixed_region_address));

    for (uint32_t i = 0; i < n_fixed_synapses; i++) {
        uint32_t synapse = fixed_synapses[i];

        log_debug("%08x [%3d: (w: %5u d: %2u, n = %3u)] - {%08x %08x}\n",
            synapse, i, synapse_row_sparse_weight(synapse),
            synapse_row_sparse_delay(synapse),
            synapse_row_sparse_index(synapse),
            SYNAPSE_DELAY_MASK, SYNAPSE_TYPE_INDEX_BITS);
    }
#else
    use(synaptic_row);
#endif // LOG_LEVEL >= LOG_DEBUG
}


/* INTERFACE FUNCTIONS */
bool message_dispatching_initialise(
        address_t synaptic_matrix_address,
        uint32_t n_neurons_value,
        address_t *indirect_synapses_address) {

//    log_info("message_dispatching_initialise: starting");

    n_neurons = n_neurons_value;

    // Work out the positions of the direct and indirect synaptic matrices and copy the direct
    // matrix to DTCM
    *indirect_synapses_address = &(synaptic_matrix_address[1]);

    log_info("message_dispatching_initialise: completed successfully");

    return true;
}

inline void message_dispatching_do_timestep_update(timer_t time) {
    use(time);
}


//! \brief processes incoming packets by forwarding them to their neuron.
//!        Each event could cause up to 256 distinct neuron update
bool message_dispatching_process_synaptic_row_page_rank(synaptic_row_t row, spike_t payload) {

    _print_synaptic_row(row);

    // Get address of non-plastic region from row
    address_t fixed_region_address = synapse_row_fixed_region(row);

    register uint32_t *synaptic_words = synapse_row_fixed_weight_controls(fixed_region_address);
    register uint32_t fixed_synapse = synapse_row_num_fixed_synapses(fixed_region_address);

    num_fixed_pre_synaptic_events += fixed_synapse;

    for (; fixed_synapse > 0; fixed_synapse--) {

        // Get the next 32 bit word from the synaptic_row
        // (should auto increment pointer in single instruction)
        uint32_t synaptic_word = *synaptic_words++;

        // Extract components from this word
        uint32_t combined_synapse_neuron_index = synapse_row_sparse_type_index(synaptic_word);

        // TODO: handle underflow
        log_debug("Neuron idx=%d receives payload = 0x%08x", combined_synapse_neuron_index, payload);
        update_vertex_payload(combined_synapse_neuron_index, payload);
    }
    return true;
}

//! \brief returns the number of times the message_dispatching have saturated their weights.
//! \return the number of times the message_dispatching have saturated.
uint32_t message_dispatching_get_saturation_count() {
    return saturation_count;
}

//! \brief returns the counters for plastic and fixed pre synaptic events
//!        based on (if the model was compiled with SYNAPSE_BENCHMARK parameter) or returns 0
//! \return the counter for plastic and fixed pre synaptic events or 0
uint32_t message_dispatching_get_pre_synaptic_events() {
    return num_fixed_pre_synaptic_events;
}
