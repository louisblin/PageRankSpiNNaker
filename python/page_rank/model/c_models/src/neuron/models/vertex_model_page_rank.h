#ifndef _VERTEX_MODEL_PAGE_RANK_H_
#define _VERTEX_MODEL_PAGE_RANK_H_

#include <neuron/models/neuron_model.h>
#include <common/maths-util.h>

#define K(n) (n >> 17)

typedef struct neuron_t {

    // Number of edges inbound / leaving that neuron
    uint32_t incoming_edges_count;
    uint32_t outgoing_edges_count;

    // The current rank of the neuron
    UFRACT rank;

    // Pending neuron update: the accumulated / count of ranks received.
    UFRACT curr_rank_acc;
    uint32_t curr_rank_count;
    uint32_t iter_state;

} neuron_t;

typedef struct global_neuron_params_t {
    // Probability user click to the next page: d
    UFRACT damping_factor;

    // Rank from probability user stays on the page: (1-d) / N
    UFRACT damping_sum;

    // Time steps since beginning of simulation
    uint32_t machine_time_step;

} global_neuron_params_t;

void vertex_model_set_global_neuron_params(global_neuron_params_pointer_t p);

void vertex_model_receive_packet(input_t key, spike_t payload,
    neuron_pointer_t neuron);

uint32_t vertex_model_get_incoming_edges(neuron_pointer_t neuron);
REAL vertex_model_get_rank_as_real(neuron_pointer_t neuron);
payload_t vertex_model_get_broadcast_rank(neuron_pointer_t neuron);

bool vertex_model_should_send_pkt(neuron_pointer_t neuron);
void vertex_model_will_send_pkt(neuron_pointer_t neuron);

void vertex_model_iteration_did_finish(neuron_pointer_t neuron);


#endif // _VERTEX_MODEL_PAGE_RANK_H_

