#ifndef _IN_MESSAGES_H_
#define _IN_MESSAGES_H_

#include <common/neuron-typedefs.h>
#include <circular_buffer.h>
#include <debug.h>


// IMPORTANT: needs to match ITER_BITS in python_models/tools/simulation.py
//
// Number of bits dedicated to encoding the iteration number in the payload,
//   which are amputated from the 32 bits precisions of the container.
// payload format: UFRACT 0.32 - [...fractional part...[iter_no]{ITER_BITS}]
//
// Note:
//   * encodes ITER_BITS^2 relative iterations steps
//   * no checking if a packet arrives over ITER_BITS^2 iterations in advance
#define ITER_BITS       1
#define ITER_MASK       ((1 << ITER_BITS) - 1)

// Number of iterations to buffer
// Note: latest test shows there is only enough space for 52 of them
#define N_ITER_BUFFERS  (1 << ITER_BITS)

// Circular array of message buffers, indexed by iteration steps
static circular_buffer buffers[N_ITER_BUFFERS];

// Number of the current iteration
static uint32_t curr_iter;

//
// Payload manipulations
//

static inline payload_t in_messages_payload_format(payload_t payload) {
    return (payload_t) ((~ITER_MASK & payload) | (ITER_MASK & curr_iter));
}

static inline uint32_t in_messages_payload_extract_iter(spike_t payload) {
    return (uint32_t) (ITER_MASK & payload);
}

static inline spike_t in_messages_payload_extract_payload(spike_t payload) {
    return (spike_t) (~ITER_MASK & payload);
}

static inline uint32_t _iter_to_buff_idx(uint32_t iter) {
    return iter % N_ITER_BUFFERS;
}

//
// Buffer management
//

static inline circular_buffer _get_buffer_for_iter(uint32_t iter_no) {
    return buffers[_iter_to_buff_idx(iter_no)];
}

// pre-condition: assumes we get a call for each new time step
static inline uint32_t in_messages_increment_iteration_number() {
    circular_buffer buffer = _get_buffer_for_iter(curr_iter);
    log_debug("in_messages_increment_iteration_number [#%u]: enter buff=0x%08x",
              curr_iter, buffer);

    // Purge current buffer, should already be empty
    uint32_t remaining = circular_buffer_size(buffer);
    if (remaining > 0) {
        log_warning("Dropping #%u messages which were not consumed", remaining);
    }
    circular_buffer_clear(buffer);

    // Prepare buffers management parameters for next iteration
    curr_iter++;
    log_debug("in_messages_increment_iteration_number [#%u]: leave buff=0x%08x",
              curr_iter, _get_buffer_for_iter(curr_iter));

    return curr_iter;
}

//
// Using the buffers
//

// initialize_spike_buffer
//
// This function initializes the input spike buffer.
// It configures:
//    buffer:     the buffer to hold the spikes (initialized with size spaces)
//    input:      index for next spike inserted into buffer
//    output:     index for next spike extracted from buffer
//    overflows:  a counter for the number of times the buffer overflows
//    underflows: a counter for the number of times the buffer underflows
//
// If underflows is ever non-zero, then there is a problem with this code.
static inline bool in_messages_initialize_spike_buffer(uint32_t size) {
    // Size account for number of messages, but we store two elements (key and
    //   payload) per message; hence 2x
    uint32_t effective_size = 2 * size;

    // Allocate space for N_ITER_BUFFERS buffers, to buffer packets that arrive
    //   early by up to N_ITER_BUFFERS iterations.
    uint32_t min_size  = 2 * sizeof(spike_t);
    uint32_t last_size = effective_size;

    for (uint32_t i = 0; i < N_ITER_BUFFERS; i++) {
        while (true) {
            buffers[i] = circular_buffer_initialize(last_size);

            if (buffers[i] != 0) {
                log_info("Successfully allocated %u/%u bytes for buffer #%02d: "
                         "0x%08x", last_size, effective_size, i, buffers[i]);
                break; // Leave while loop
            // If we can still allocate a valid buffer but halving its size
            } else if ((last_size >> 1) >= min_size) {
                last_size >>= 1;
                log_error("Unable to allocate buffer #%02d, trying with %u "
                          "bytes", i, last_size);
            } else {
                log_error("Unable to allocate %u bytes for buffer #%02d",
                          last_size, i);
                return false;
            }
        }
    }

    // Set buffers management parameters
    curr_iter = 0;

    return true;
}

static inline bool in_messages_add_key_payload(spike_t key, spike_t _payload) {
    log_debug("in_messages_add_key_payload [#%u]: (%03d[0x%08x] = %k[0x%08x])",
              curr_iter, key, key, _payload, _payload);

    uint32_t iter_no = in_messages_payload_extract_iter(_payload);
    spike_t  payload = in_messages_payload_extract_payload(_payload);
    log_debug("in_messages_add_key_payload [#%u]: iter_no=%d, "
              "payload= 0x%08x=>0x%08x", curr_iter, iter_no, _payload, payload);

    circular_buffer buffer = _get_buffer_for_iter(iter_no);
    log_debug("in_messages_add_key_payload [#%u]: buff=0x%08x for it=%u",
              curr_iter, buffer, iter_no);

    // Add key to buffer
    if(!circular_buffer_add(buffer, key)) {
        return false;
    }

    // Add payload to buffer
    // Note: assuming second add cannot fail from initialization pre condition.
    if (!circular_buffer_add(buffer, payload)) {
        log_error("in_messages_add_key_payload [#%u]: inconsistency - expected "
                  "in_messages items to be addable by pair (%03d[0x%08x] = "
                  "%k[0x%08x]) for it=%u", curr_iter, (0xff & key), key,
                  payload, payload, iter_no);
        return false;
    }

    return true;
}

static inline bool in_messages_get_next_spike(spike_t* spike) {
    circular_buffer buffer = _get_buffer_for_iter(curr_iter);
    log_debug("in_messages_get_next_spike [#%u]: buffer=0x%08x", curr_iter,
              buffer);
    return circular_buffer_get_next(buffer, spike);
}

static inline bool in_messages_is_next_spike_equal(spike_t spike) {
    circular_buffer buffer = _get_buffer_for_iter(curr_iter);
    log_debug("in_messages_is_next_spike_equal [#%u]: buffer=0x%08x", curr_iter,
              buffer);
    return circular_buffer_advance_if_next_equals(buffer, spike);
}

static inline counter_t in_messages_get_n_buffer_overflows() {
    uint32_t acc = 0;
    for (uint32_t i = 0; i < N_ITER_BUFFERS; i++) {
        acc += circular_buffer_get_n_buffer_overflows(buffers[i]);
    }
    return acc;
}

static inline counter_t in_messages_get_n_buffer_underflows() {
    return 0;
}

static inline void in_messages_print_buffer() {
    for (uint32_t i = curr_iter; i < N_ITER_BUFFERS; i++) {
        log_debug("in_messages buffer for iteration #%u", i);
        circular_buffer_print_buffer(buffers[i]);
    }
}

#endif // _IN_MESSAGES_H_
