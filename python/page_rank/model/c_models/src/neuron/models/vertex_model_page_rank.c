#include "vertex_model_page_rank.h"

#include <common/maths-util.h>
#include <debug.h>
#include <sark.h>

static global_neuron_params_pointer_t global_params;

// Checkpoints
#define READY         0  // When neuron is ready for iteration
#define SENT_PACKET   1  // When the page rank packet was sent
#define RECEIVED_ALL  2  // When all expected ranks were received
#define FINISHED      3  // When neuron notified it had finished

// Checkpoints API
#define CHECKPOINT_RESET(N)    (N->iter_state = READY)
#define CHECKPOINT_SAVE(N, E)  (N->iter_state |= (1 << E))
#define CHECKPOINT_HAS(N, E)   (N->iter_state & (1 << E))


void vertex_model_set_global_neuron_params(global_neuron_params_pointer_t params) {
    global_params = params;
}


inline void _finish(neuron_pointer_t neuron) {
    // Lowers a semaphore associated with the AppID running on this core.
    sark_app_lower();
    CHECKPOINT_SAVE(neuron, FINISHED);
    log_debug("[idx=   ] vertex_model_state_update: iteration completed (%k)",
        K(neuron->curr_rank_acc));
}

inline void _has_sent_packet(neuron_pointer_t neuron) {
    // Raises a semaphore associated with the AppID running on this core.
    sark_app_raise();
    CHECKPOINT_SAVE(neuron, SENT_PACKET);

    if (!CHECKPOINT_HAS(neuron, FINISHED) && CHECKPOINT_HAS(neuron, RECEIVED_ALL)) {
        _finish(neuron);
    }
}

inline void _has_received_all(neuron_pointer_t neuron) {
    CHECKPOINT_SAVE(neuron, RECEIVED_ALL);

    if (!CHECKPOINT_HAS(neuron, FINISHED) && CHECKPOINT_HAS(neuron, SENT_PACKET)) {
        _finish(neuron);
    }
}

// Triggered when a packet is received
void vertex_model_receive_packet(input_t key, spike_t payload, neuron_pointer_t neuron) {

    // Decode key / payload
    index_t idx = (index_t) key;
    union payloadDeserializer {
        spike_t asSpikeT;
        UFRACT asFract;
    };
    union payloadDeserializer contrib = { payload };

    // User signals a packet has arrived
    UFRACT prev_rank_acc = neuron->curr_rank_acc;
    uint32_t prev_rank_count = neuron->curr_rank_count;

    // Saved
    neuron->curr_rank_acc   += contrib.asFract;
    neuron->curr_rank_count += 1;

    log_debug("[idx=%03u] vertex_model_state_update: %k/%d + %k = %k/%d [exp=%d]", idx,
        K(prev_rank_acc), prev_rank_count, K(contrib.asFract), K(neuron->curr_rank_acc),
        neuron->curr_rank_count, neuron->incoming_edges_count);

    if (neuron->curr_rank_count >= neuron->incoming_edges_count) {
        _has_received_all(neuron);
    }
}

payload_t vertex_model_get_broadcast_rank(neuron_pointer_t neuron) {
    union payloadSerializer {
        UFRACT asFract;
        payload_t asPayloadT;
    };
    union payloadSerializer rank = { neuron->rank };

    // Check we don't divide by 0
    if (neuron->outgoing_edges_count > 0) {
        rank.asFract /= neuron->outgoing_edges_count;
    }
    return rank.asPayloadT;
}

REAL vertex_model_get_rank_as_real(neuron_pointer_t neuron) {
    union payloadSerializer {
        UFRACT asFract;
        REAL asReal;
    };
    union payloadSerializer rank = { neuron->rank };
    return rank.asReal;
}

bool vertex_model_should_send_pkt(neuron_pointer_t neuron) {
    return !CHECKPOINT_HAS(neuron, FINISHED) && !CHECKPOINT_HAS(neuron, SENT_PACKET);
}

// Perform operations required to reset the state after a spike
void vertex_model_will_send_pkt(neuron_pointer_t neuron) {
    if (neuron->incoming_edges_count > 0) {
        _has_sent_packet(neuron);
    } else {
        // Else, not expected to receive any packets so iteration is finished for the node
        CHECKPOINT_SAVE(neuron, FINISHED);
    }
}

void vertex_model_iteration_did_finish(neuron_pointer_t neuron) {
    neuron->rank = global_params->damping_sum
                 + global_params->damping_factor * neuron->curr_rank_acc;
    neuron->curr_rank_acc = 0;
    neuron->curr_rank_count = 0;
    CHECKPOINT_RESET(neuron);
}

void vertex_model_print_state_variables(restrict neuron_pointer_t neuron) {
    log_debug("rank            = %k", K(neuron->rank));
    log_debug("curr_rank_acc   = %k", K(neuron->curr_rank_acc));
    log_debug("curr_rank_count = %d", neuron->curr_rank_count);
    log_debug("iter_state      = 0x%04x", neuron->iter_state);
}

void vertex_model_print_parameters(restrict neuron_pointer_t neuron) {
    log_debug("incoming_edges_count = %d", neuron->incoming_edges_count);
    log_debug("outgoing_edges_count = %d", neuron->outgoing_edges_count);
}
