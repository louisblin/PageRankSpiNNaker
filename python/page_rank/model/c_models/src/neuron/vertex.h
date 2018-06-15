/*! \file
 *
 *  \brief interface for vertices
 *
 *  The API contains:
 *    - vertex_initialise(address, recording_flags, n_vertices_value):
 *         translate the data stored in the NEURON_PARAMS data region in SDRAM
 *         and converts it into c based objects for use.
 *    - vertex_set_input_buffers(input_buffers_value):
 *         setter for the internal input buffers
 *    - vertex_do_timestep_update(time):
 *         executes all the updates to neural parameters when a given timer
 *         period has occurred.
 */

#ifndef _VERTEX_H_
#define _VERTEX_H_

#include <common/neuron-typedefs.h>
#include <recording.h>

//! \brief translate the data stored in the NEURON_PARAMS data region in SDRAM
//!        and convert it into c based objects for use.
//! \param[in] address the absolute address in SDRAM for the start of the
//!            NEURON_PARAMS data region in SDRAM
//! \param[in] recording_flags_param the recordings parameters
//!            (contains which regions are active and how big they are)
//! \param[out] n_vertices_value The number of vertices this model is to emulate
//! \return boolean which is True is the translation was successful
//!         otherwise False
bool vertex_initialise(address_t address, uint32_t recording_flags,
    uint32_t *n_vertices_value);

//! \brief executes all the updates to neural parameters when a given timer
//!        period has occurred.
//! \param[in] time the timer tick value currently being executed
//! \return nothing
void vertex_do_timestep_update(uint32_t time);

//! \brief interface for reloading vertex parameters as needed
//! \param[in] address: the address where the vertex parameters are stored
//! in SDRAM
//! \return bool which is true if the reload of the vertex parameters was
//! successful or not
bool vertex_reload_neuron_parameters(address_t address);

//! \brief interface for rewriting the vertex parameters back into sdram
//! \param[in] address the absolute address in SDRAM for the start of the
//!            NEURON_PARAMS data region in SDRAM
void vertex_store_neuron_parameters(address_t address);

//! \brief triggered when a spike is received (MCPL)
//! \param[in] key the key received in the MC packet
//! \param[in] payload the payload received in the MC packet
//! \return nothing
void update_vertex_payload(uint32_t key, spike_t payload);


#endif // _VERTEX_H_
