/*! \file
 *
 * \brief implementation of the vertex.h interface.
 *
 */

#include "vertex.h"
#include "message_processing.h"
#include "models/vertex_model_page_rank.h"
#include <common/out_spikes.h>
#include <common/maths-util.h>
#include <recording.h>
#include <debug.h>
#include <string.h>
#include <sark.h>

// declare spin1_wfi
void spin1_wfi();

#define SPIKE_RECORDING_CHANNEL 0
#define RANK_RECORDING_CHANNEL 1

//! Array of vertex states
static neuron_pointer_t vertex_array;

//! Global parameters for the vertices
static global_neuron_params_pointer_t global_parameters;

//! The key to be used for this core (will be ORed with vertex id)
static key_t key;

//! A checker that says if this model should be transmitting. If set to false
//! by the data region, then this model should not have a key.
static bool use_key;

//! The number of vertices on the core
static uint32_t n_vertices;

//! The recording flags
static uint32_t recording_flags;

//! storage for vertex state with timestamp
static timed_state_t *ranks;
uint32_t ranks_size;

//! The number of clock ticks to back off before starting the timer, in an attempt to avoid
//!   overloading the network
static uint32_t random_back_off;

//! The number of clock ticks between sending each spike
static uint32_t time_between_spikes;

//! The expected current clock tick of timer_1 when the next spike can be sent
static uint32_t expected_time;

//! The number of recordings outstanding
static uint32_t n_recordings_outstanding = 0;

//! parameters that reside in the vertex_parameter_data_region in human
//! readable form
typedef enum parameters_in_vertex_parameter_data_region {
    RANDOM_BACK_OFF, TIME_BETWEEN_SPIKES, HAS_KEY, TRANSMISSION_KEY,
    N_VERTICES_TO_SIMULATE, INCOMING_SPIKE_BUFFER_SIZE,
    START_OF_GLOBAL_PARAMETERS,
} parameters_in_vertex_parameter_data_region;


//! private method for doing output debug data on the vertices
static inline void _print_vertices() {

//! only if the models are compiled in debug mode will this method contain these lines.
#if LOG_LEVEL >= LOG_DEBUG
    log_debug("-------------------------------------");
    for (index_t n = 0; n < n_vertices; n++) {
        log_debug("### Node %d ###", n);
        vertex_model_print_state_variables(&(vertex_array[n]));
    }
    log_debug("-------------------------------------\n");
#endif // LOG_LEVEL >= LOG_DEBUG
}

//! private method for doing output debug data on the vertices
static inline void _print_vertex_parameters() {

//! only if the models are compiled in debug mode will this method contain these lines.
#if LOG_LEVEL >= LOG_DEBUG
    log_debug("-------------------------------------");
    for (index_t n = 0; n < n_vertices; n++) {
        log_debug("### Node %d ###", n);
        vertex_model_print_parameters(&(vertex_array[n]));
    }
    log_debug("-------------------------------------\n");
#endif // LOG_LEVEL >= LOG_DEBUG
}

//! \brief does the memory copy for the vertex parameters
//! \param[in] address: the address where the vertex parameters are stored
//! in SDRAM
//! \return bool which is true if the mem copy's worked, false otherwise
bool _vertex_load_neuron_parameters(address_t address){
    uint32_t next = START_OF_GLOBAL_PARAMETERS;

    log_info("loading vertex global parameters");
    memcpy(global_parameters, &address[next], sizeof(global_neuron_params_t));
    next += sizeof(global_neuron_params_t) / 4;

    log_info("loading vertex local parameters");
    memcpy(vertex_array, &address[next], n_vertices * sizeof(neuron_t));

    vertex_model_set_global_neuron_params(global_parameters);

    return true;
}

//! \brief interface for reloading vertex parameters as needed
//! \param[in] address: the address where the vertex parameters are stored in SDRAM
//! \return bool which is true if the reload of the vertex parameters was
//! successful or not
bool vertex_reload_neuron_parameters(address_t address) {
    log_info("vertex_reloading_neuron_parameters: starting");
    if (!_vertex_load_neuron_parameters(address)){
        return false;
    }

    // for debug purposes, print the vertex parameters
    _print_vertex_parameters();
    return true;
}

//! \brief Set up the vertex models
//! \param[in] address the absolute address in SDRAM for the start of the NEURON_PARAMS data region
//!            in SDRAM
//! \param[in] recording_flags_param the recordings parameters (contains which regions are active
//!            and how big they are)
//! \param[out] n_vertices_value The number of vertices this model is to emulate
//! \return true if the initialisation was successful, otherwise false
bool vertex_initialise(address_t address, uint32_t recording_flags_param,
        uint32_t *n_vertices_value, uint32_t *incoming_spike_buffer_size) {
    log_info("vertex_initialise: starting");

    random_back_off     = address[RANDOM_BACK_OFF];
    time_between_spikes = address[TIME_BETWEEN_SPIKES] * sv->cpu_clk;
    log_info("\t back off = %u, time between spikes %u", random_back_off, time_between_spikes);

    // Check if there is a key to use
    use_key = address[HAS_KEY];

    // Read the spike key to use
    key = address[TRANSMISSION_KEY];

    // log if this model is expecting to transmit
    if (!use_key) {
        log_info("\tThis model is not expecting to transmit as it has no key");
    } else {
        log_info("\tThis model is expected to transmit with key = %08x", key);
    }

    // Read the vertex details
    n_vertices = address[N_VERTICES_TO_SIMULATE];
    *n_vertices_value = n_vertices;

    // Read the size of the incoming spike buffer to use
    *incoming_spike_buffer_size = address[INCOMING_SPIKE_BUFFER_SIZE];

    // log message for debug purposes
    log_info("\t vertices = %u, spike buffer size = %u, params size = %u",
        n_vertices, *incoming_spike_buffer_size, sizeof(neuron_t));

    // Allocate DTCM for the global parameter details
    if (sizeof(global_neuron_params_t) > 0) {
        global_parameters = (global_neuron_params_t *) spin1_malloc(sizeof(global_neuron_params_t));
        if (global_parameters == NULL) {
            log_error("Unable to allocate global neuron parameters - Out of DTCM");
            return false;
        }
    }

    // Allocate DTCM for vertex array
    if (sizeof(neuron_t) != 0) {
        vertex_array = (neuron_t *) spin1_malloc(n_vertices * sizeof(neuron_t));
        if (vertex_array == NULL) {
            log_error("Unable to allocate vertex array - Out of DTCM");
            return false;
        }
    }

    // Load the data into the allocated DTCM spaces.
    if (!_vertex_load_neuron_parameters(address)){
        return false;
    }

    // Set up the out spikes array
    if (!out_spikes_initialize(n_vertices)) {
        return false;
    }

    recording_flags = recording_flags_param;

    ranks_size = sizeof(uint32_t) + sizeof(state_t) * n_vertices;
    ranks = (timed_state_t *) spin1_malloc(ranks_size);

    _print_vertex_parameters();

    return true;
}


//! \brief stores vertex parameter back into sdram
//! \param[in] address: the address in sdram to start the store
void vertex_store_neuron_parameters(address_t address){

    uint32_t next = START_OF_GLOBAL_PARAMETERS;

    log_info("writing vertex global parameters");
    memcpy(&address[next], global_parameters, sizeof(global_neuron_params_t));
    next += sizeof(global_neuron_params_t) / 4;

    log_info("writing vertex local parameters");
    memcpy(&address[next], vertex_array, n_vertices * sizeof(neuron_t));
}

void recording_done_callback() {
    n_recordings_outstanding -= 1;
}

//! \executes all the updates to neural parameters when a given timer period has occurred.
//! \param[in] time the timer tick  value currently being executed
void vertex_do_timestep_update(timer_t time) {

    log_info("\n\n===== TIME STEP = %u =====", time);

    // Disable interrupts to avoid possible concurrent access
    uint cpsr = spin1_int_disable();

    // Check if all vertices have completed their iteration
    // Note: important to skip first iteration otherwise ranks will be erased
    if (0 < time && sark_app_sema() == 0) {
        // Buffer for incoming packets
        uint32_t iter_no = message_processing_increment_iteration_number();

        log_info("=> Iteration #%u will start.", iter_no);

        // vertex model
        for (index_t vertex_index = 0; vertex_index < n_vertices; vertex_index++) {
            neuron_pointer_t vertex = &vertex_array[vertex_index];
            vertex_model_iteration_did_finish(vertex);
        }

        _print_vertices();
    } else {
        log_info("=> Iteration ongoing (%d).", sark_app_sema());
    }

    // Re-enable interrupts
    spin1_mode_restore(cpsr);

    // Wait a random number of clock cycles
    uint32_t random_back_off_time = tc[T1_COUNT] - random_back_off;
    while (tc[T1_COUNT] > random_back_off_time) {
        // Do Nothing
    }

    // Set the next expected time to wait for between spike sending
    expected_time = tc[T1_COUNT] - time_between_spikes;

    // Wait until recordings have completed, to ensure the recording space can be re-written
    while (n_recordings_outstanding > 0) {
        spin1_wfi();
    }

    // Reset the out spikes before starting
    out_spikes_reset();

    // update each vertex individually
    for (index_t vertex_index = 0; vertex_index < n_vertices; vertex_index++) {
        // Get the parameters for this vertex
        neuron_pointer_t vertex = &vertex_array[vertex_index];

        // Record the rank at the beginning of the iteration
        ranks->states[vertex_index] = vertex_model_get_rank_as_real(vertex);

        if (vertex_model_should_send_pkt(vertex)) {
            // Tell the vertex model
            vertex_model_will_send_pkt(vertex);

            // Get new rank
            payload_t broadcast_rank = vertex_model_get_broadcast_rank(vertex);

            // Record the spike
            out_spikes_set_spike(vertex_index);

            if (use_key) {

                // Wait until the expected time to send
                while (tc[T1_COUNT] > expected_time) {
                    // Do Nothing
                }
                expected_time -= time_between_spikes;

                // Send the spike
                key_t k = key | vertex_index;
                payload_t p = message_processing_payload_format(broadcast_rank);
                log_debug("%16s[t=%04u|#%03d] Sending pkt  0x%08x=%k,0x%08x[sent=%k,0x%08x]",
                         "", time, vertex_index, k, K(broadcast_rank), broadcast_rank, K(p), p);
                while (!spin1_send_mc_packet(k, p, WITH_PAYLOAD)) {
                    log_warning("%16s[t=%04u|#%03d] Sending error...", "", time, vertex_index);
                    spin1_delay_us(1);
                }
            }
        } else {
            log_debug("%16s[t=%04u|#%03d] No spike required.", "", time, vertex_index);
        }
    }

    // Disable interrupts to avoid possible concurrent access
    cpsr = spin1_int_disable();

    // record vertex state (membrane potential) if needed
    if (recording_is_channel_enabled(recording_flags, RANK_RECORDING_CHANNEL)) {
        n_recordings_outstanding += 1;
        ranks->time = time;
        recording_record_and_notify(
            RANK_RECORDING_CHANNEL, ranks, ranks_size, recording_done_callback);
    }

    // do logging stuff if required
    out_spikes_print();

    // Record any spikes this timestep
    if (recording_is_channel_enabled(recording_flags, SPIKE_RECORDING_CHANNEL)) {
        if (!out_spikes_is_empty()) {
            n_recordings_outstanding += 1;
            out_spikes_record(SPIKE_RECORDING_CHANNEL, time, recording_done_callback);
        }
    }

    // Re-enable interrupts
    spin1_mode_restore(cpsr);
}

void update_vertex_payload(uint32_t vertex_index, spike_t payload) {
    neuron_pointer_t vertex = &vertex_array[vertex_index];
    vertex_model_receive_packet(vertex_index, payload, vertex);
}
