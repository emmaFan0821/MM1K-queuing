#!/usr/bin/env python
# -*- coding: utf-8 -*-
##
# @file     mm1.py
# @author   Kyeong Soo (Joseph) Kim <kyeongsoo.kim@gmail.com>
# @date     2016-09-27
#
# @brief    Simulate M/M/1 queueing system
#
# @remarks  Copyright (C) 2016 Kyeong Soo (Joseph) Kim. All rights reserved.
#
# @remarks  This software is written and distributed under the GNU General
#           Public License Version 2 (http://www.gnu.org/licenses/gpl-2.0.html).
#           You must not remove this notice, or any other, from this software.
#

import argparse
import numpy as np
import random
import simpy
import sys
import matplotlib.pyplot as plt


def source(env, mean_ia_time, mean_srv_time, server, wait_times, system_capacity, waiting, loss, number, trace):
    """Generates packets with exponential interarrival time."""
    for i in range(number):
        ia_time = random.expovariate(1.0 / mean_ia_time)
        srv_time = random.expovariate(1.0 / mean_srv_time)
        pkt = packet(env, 'Packet-%d' % i, server, srv_time, wait_times, system_capacity, waiting, loss, trace)
        env.process(pkt)
        yield env.timeout(ia_time)


def packet(env, name, server, service_time, wait_times, system_capacity, waiting, loss, trace):
    """Requests a server, is served for a given service_time, and leaves the server."""
    arrv_time = env.now
    waiting.append(1)  # new customer come, waiting number +1
    if trace:
        # print('t=%.4Es: %s arrived, %d' % (arrv_time, name, len(waiting)))
        if len(waiting) > system_capacity:
            waiting.pop()  # new customer has to leave, waiting number -1
            loss.append(1)  # server lose a customer, loss number +1
            # print('t=%.4Es: %s left, %d' % (arrv_time, name, len(waiting)))
        else:
            with server.request() as request:
                yield request  # wait til there is no customer in front of you
                wait_time = env.now - arrv_time
                wait_times.append(wait_time)
                # if trace:
                    # print('t=%.4Es: %s waited for %.4Es' % (env.now, name, wait_time))
                yield env.timeout(service_time)
                if trace:
                    waiting.pop()  # after service, customer leave
                    # print('t=%.4Es: %s served for %.4Es and left, %d' % (env.now, name, service_time, len(waiting)))


def run_simulation(mean_ia_time, mean_srv_time, system_capacity, num_packets=1000, random_seed=1234, trace=True):
    """Runs a simulation and returns statistics."""
    random.seed(random_seed)
    env = simpy.Environment()
    # start processes and run
    server = simpy.Resource(env, capacity=1)
    wait_times = []
    waiting = []
    loss = []
    env.process(source(env, mean_ia_time,mean_srv_time, server, wait_times, system_capacity, waiting, loss, number=num_packets, trace=trace))
    env.run()
    # return statistics (i.e., mean waiting time)
    return np.mean(wait_times), len(loss)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-A",
        "--mean_ia_time",
        help="mean packet interarrival time [s]; default is 1.0",
        default=0.0105,
        type=float)
    parser.add_argument(
        "-S",
        "--mean_srv_time",
        help="mean packet service time [s]; default is 0.1",
        default=0.01,
        type=float)
    parser.add_argument(
        "-N",
        "--num_packets",
        help="number of packets to generate; default is 1000",
        default=1000,
        type=int)
    parser.add_argument(
        "-R",
        "--random_seed",
        help="seed for random number generation; default is 1234",
        default=1234,
        type=int)
    parser.add_argument(
        "-K",
        "--system_capacity",
        help="System capacity / The maximum number of people the system can queue",
        default=10,
        type=int)
    parser.add_argument('--trace', dest='trace', action='store_true')
    parser.add_argument('--no-trace', dest='trace', action='store_false')
    parser.set_defaults(trace=True)
    args = parser.parse_args()

    # set variables using command-line arguments
    mean_ia_time = args.mean_ia_time
    mean_srv_time = args.mean_srv_time
    num_packets = args.num_packets
    random_seed = args.random_seed
    system_capacity = args.system_capacity
    trace = args.trace

    # run a simulation
    PB_the_matrix = []
    PB_sim_matrix = []
    lmd_list = []
    lmd = 0
    miu = 100
    k_list = [10, 20, 50]
    for n in range(19):
        lmd += 5
        lmd_list.append(lmd)  # arrival rate

    for k in k_list:
        PB_the_list = []
        for lmd in lmd_list:
            # print statistics from the simulation
            '''Compute Theoretical Blocking Probability'''
            rho = lmd / miu
            p0 = (1 - rho) / (1-rho**(k+1))
            pn_sum = 0
            for j in range(k):
                pn = (rho ** j) * p0
                pn_sum = pn_sum + pn
            pk = (rho ** k) * p0
            PB_the = pk / pn_sum
            PB_the_list.append(PB_the)
            print("Arrival rate=%d, K=%d, Theoretical block probability = %f" % (lmd, k, PB_the))
        PB_the_matrix.append(PB_the_list)

    for k in k_list:
        PB_sim_list = []
        for lmd in lmd_list:
            mean_ia_time = 1/lmd
            mean_srv_time = 1/miu
            system_capacity = k
            mean_waiting_time, loss_times = run_simulation(mean_ia_time, mean_srv_time, system_capacity, num_packets, random_seed, trace)
            PB_sim = loss_times / num_packets
            PB_sim_list.append(PB_sim)
            print("Arrival rate=%d, K=%d, Simulation block probability = %f, Average waiting time = %.4Es" % (lmd, k, PB_sim, mean_waiting_time))
        PB_sim_matrix.append(PB_sim_list)

    """plot """
    for m in range(3):
        plt.ylim(0, 0.1)
        plt.plot(lmd_list, PB_the_matrix[m], 'r', label='Theory')
        plt.plot(lmd_list, PB_sim_matrix[m], 'b', label='Simulation')
        plt.legend(loc='upper left')
        plt.xlabel("Arrival rate")
        plt.ylabel("Blocking probability")
        if m == 0:
            plt.title("K = 10")
        elif m == 1:
            plt.title("K = 20")
        elif m == 2:
            plt.title("K = 50")
        plt.show()


