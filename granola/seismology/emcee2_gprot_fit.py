from __future__ import print_function
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import h5py

import os
import math

from emcee2_GProt import calc_p_init, mcmc_fit


def make_lists(xb, yb, yerrb, l):
    nlists = int(math.ceil((xb[-1] - xb[0]) / l))
    xlist, ylist, yerrlist= [], [], []
    masks = np.arange(nlists + 1) * l
    for i in range(nlists):
        m = (masks[i] < xb) * (xb < masks[i+1])
        xlist.append(xb[m])
        ylist.append(yb[m])
        yerrlist.append(yerrb[m])
    return xlist, ylist, yerrlist


def make_gaps(x, y, yerr, points_per_day):
    nkeep = points_per_day * (x[-1] - x[0])
    m = np.zeros(len(x), dtype=bool)
    l = np.random.choice(np.arange(len(x)), nkeep)
    for i in l:
        m[i] = True
    inds = np.argsort(x[m])
    return x[m][inds], y[m][inds], yerr[m][inds]


def moving_average(y, window_size):
    window = np.ones(int(window_size))/float(window_size)
    return np.convolve(y, window, "same")


def sigma_clip(x, y, yerr, nsigma):
    med = moving_average(y, 20)
    std = (sum((med - y)**2)/float(len(y)))**.5
    print(std)
    m = np.abs(y - med) > (nsigma * std)
    return x[~m], y[~m], yerr[~m]


def gp_fit(x, y, yerr, sid, RESULTS_DIR, burnin=1000, nwalkers=16, nruns=5,
           full_run=1000, nsets=2, p_max=None, nsigma=3):

    # sigma clip
    x, y, yerr = sigma_clip(x, y, yerr, nsigma)

    ppd = 4  # cut off at 200 days, 4 points per day
    xb, yb, yerrb = make_gaps(x, y, yerr, ppd)

    # make data into a list of lists, 200 days each
    xb, yb, yerrb = make_lists(xb, yb, yerrb, 200)

    # find p_init
    acf_period, a_err, pgram_period, p_err = calc_p_init(x, y, yerr, sid,
                                                         RESULTS_DIR,
                                                         clobber=False)

    # set initial period
    p_init = pgram_period
    if not p_max:
        p_max = np.log((xb[0][-1] - xb[0][0]) / 2.)
    if p_init > np.exp(p_max):
        p_init = 40
    elif p_init < .5:
        p_init = 10
    burnin, nwalkers, nruns, full_run = 1000, 16, 5, 1000

    assert p_init < np.exp(p_max), "p_init > p_max"
    # fast settings
#     burnin, nwalkers, nruns, full_run = 2, 12, 2, 50
#     xb[0], yb[0], yerrb[0] = xb[0][::100], yb[0][::100], yerrb[0][::100]

    trths = [None, None, None, None, None]
    mcmc_fit(xb[:2], yb[:2], yerrb[:2], p_init, p_max, sid, RESULTS_DIR,
             truths=trths, burnin=burnin, nwalkers=nwalkers, nruns=nruns,
             full_run=full_run, diff_threshold=.5, n_independent=1000)

if __name__ == "__main__":
    import random
    x = np.arange(0, 100, .1)
    y = np.sin(2*np.pi*x*1./10)
    err = .1
    yerr = np.ones_like(y) * err
    y += np.random.randn(len(x)) * err
    for i in range(50):
        y[np.random.choice(range(len(y)))] += .5
    for i in range(50):
        y[np.random.choice(range(len(y)))] -= .5
    plt.clf()
    plt.plot(x, y, "r.")
    x2, y2, yerr2, med = sigma_clip(x, y, yerr, 2)
    plt.plot(x2, y2, "k.")
    print(len(x) - len(x2))
    plt.plot(x, med)
    plt.savefig("test")
