#ifndef _MESSAGE_PROCESSING_H_
#define _MESSAGE_PROCESSING_H_

#include <common/neuron-typedefs.h>

bool message_processing_initialise(size_t row_max_n_bytes,
    uint32_t mc_pkt_callback_priority, uint32_t user_event_priority,
    uint32_t incoming_spike_buffer_size);

//! \brief returns the number of times the input buffer has overflowed
//! \return the number of times the input buffer has overflowed
uint32_t message_processing_get_buffer_overflows();

payload_t message_processing_payload_format(payload_t payload);
uint32_t message_processing_increment_iteration_number(void);

#endif // _MESSAGE_PROCESSING_H_
