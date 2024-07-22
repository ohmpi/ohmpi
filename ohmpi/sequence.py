import numpy as np
import pandas as pd
import os
from joblib import Parallel, delayed
import matplotlib.pyplot as plt

def create_sequence(nelec, params=[('dpdp', 1, 8)], include_reciprocal=False,
    opt_ip=False, opt_param={}, opt_plot=False):
    """Creates a sequence of quadrupole.Several type of
    sequence or sequence with different parameters can be combined together.

    Parameters
    ----------
    nelec : int
        Number of electrodes.
    params : list of tuple, optional
        Each tuple is the form (<array_name>, param1, param2, ...)
        Dipole spacing is specified in terms of "number of electrode spacing".
        Dipole spacing is often referred to 'a'. Number of levels is a multiplier
        of 'a', often referred to 'n'. For multigradient array, an additional parameter
        's' is needed.
        Types of sequences available are :
        - ('wenner', a)
        - ('dpdp', a, n)
        - ('schlum', a, n)
        - ('multigrad', a, n, s)
        By default, if an integer is provided for a, n and s, the parameter
        will be considered varying from 1 to this value. For instance, for
        ('wenner', 3), the sequence will be generated for a = 1, a = 2 and a = 3.
        If only some levels are desired, the user can use a list instead of an int.
        For instance ('wenner', [3]) will only generate quadrupole for a = 3.
    include_reciprocal : bool, optional
        If True, will add reciprocal quadrupoles (so MNAB) to the sequence.
    opt_ip : bool, optional
        If True, will optimize for induced polarization measurement (i.e. will
        try to put as much time possible between injection and measurement at
        the same electrode). Optimization can take a few seconds.
    opt_param : dic, optional
        Dictionary of parameters to be passed to optimize_ip(). Possible values are
        'niter' (int): number of iterations during optimization
        'nchains' (int): number of chain to run in parallel (each chain is run niter times)
        'pad' (int): how far from its position move the quad with the largest cost in the sequence
    opt_plot : bool, optional
        Plot cost decay of ip optimization.
    """
    # dictionary of function to create sequence
    fdico = {
        'dpdp': dpdp,
        'wenner': wenner,
        'schlum': schlum,
        'multigrad': multigrad,
    }
    
    # check parameters (all int and > 0)
    for param in params:
        for i, p in enumerate(param[1:]):
            if isinstance(p, float) or isinstance(p, int):
                if p <= 0:
                    raise ValueError('parameters of sequence (a, n or s) needs to be > 0')
            else:
                for pp in p:
                    if pp <= 0:
                        raise ValueError('parameters of sequence (a, n or s) needs to be > 0')

    # create sequence
    dfs = []
    for param in params:
        dfs.append(fdico[param[0]](nelec, *param[1:]))
    dfseq = pd.concat(dfs, axis=0)

    # add reciprocal
    if include_reciprocal:
        dfseqr = dfseq.copy().rename(columns={'a': 'm', 'b': 'n', 'm': 'a', 'n': 'b'})
        dfseqr = dfseqr.sort_values(['a', 'b', 'm', 'n'])
        dfseq = pd.concat([dfseq, dfseqr]).reset_index(drop=True)

    # optimize for IP
    if opt_ip:
        dfseq = dfseq.sort_values(['m', 'n', 'a', 'b'])
        nchains = opt_param['nchains'] if 'nchains' in opt_param else 4
        outs = Parallel(n_jobs=-1, backend='loky')(delayed(optimize_ip)(dfseq.values) for i in range(nchains))

        # best order
        cost = np.inf
        order = None
        for out in outs:
            if out[1][-1] < cost:
                order = out[0]
                cost = out[1][-1]
        print('Best cost is {:.2f}'.format(cost))
        dfseq.loc[:, :] = dfseq.values[order, :]

    if opt_plot:
        fig, ax = plt.subplots()
        for out in outs:
            ax.plot(out[1])
        ax.set_xlabel('Number of iterations')
        ax.set_ylabel(r'$\sum (1/d_i)$')
        fig.show()
            
    # stats
    print('{:d} quadrupoles generated.'.format(dfseq.shape[0]))
    return dfseq

def dpdp(nelec, a, n):
    ''' Generates quadrupole matrix for dipole-dipole survey.
    
    Parameters
    ----------
    nelec : int
        Number of electrodes
    a : int or list of int
        Spacing between AB (current) and MN (voltage) pairs in electrode spacing
        (a = 1 is the same as skip 0).
    n : int or list of int
        Quadrupole separation in electrode spacing.
    '''
    # check parameters
    if isinstance(a, int):
        a = np.arange(a) + 1
    if isinstance(n, int):
        n = np.arange(n) + 1
    
    elec = np.arange(nelec) + 1
    abmn = []
    for aa in a:
        if aa < 1:
            raise ValueError('a must be >= 1, it is the electrode spacing between AB and MN pairs (a = 1 is the same as skip 0)')
        for nn in n:
            if nn < 1:
                raise ValueError('n must be >= 1, it is the number of level between AB and MN')
            A = elec
            B = A + aa
            M = B + nn * aa
            N = M + aa
            abmn.append(np.vstack([A, B, M, N]).T)
    abmn = np.vstack(abmn)
    abmn = abmn[(abmn <= nelec).all(1), :]
    df = pd.DataFrame(abmn, columns=['a', 'b', 'm', 'n'])
    df = df.sort_values(['a', 'b', 'm', 'n']).reset_index(drop=True)
    return df

def wenner(nelec, a):
    '''Generates quadrupole matrix for Wenner alpha survey.
    
    Parameters
    ----------
    nelec : int
        Number of electrodes
    a : int or list of int
        Spacing between electrodes (in electrode spacing).
   '''
    if isinstance(a, int):
        a = np.arange(a) + 1
    elec = np.arange(nelec) + 1
    abmn = []
    for aa in a:
        A = elec
        M = A + aa
        N = M + aa
        B = N + aa
        abmn.append(np.vstack([A, B, M, N]).T)
    abmn = np.vstack(abmn)
    abmn = abmn[(abmn <= nelec).all(1), :]
    df = pd.DataFrame(abmn, columns=['a', 'b', 'm', 'n'])
    df = df.sort_values(['a', 'b', 'm', 'n']).reset_index(drop=True)
    return df
    

def schlum(nelec, a, n):
    ''' Generates quadrupole matrix for Schlumberger survey.
    Parameters
    ----------
    nelec : int
        Number of electrodes
    a : int or list of int
        Spacing between electrodes (in electrode spacing).
    n : int or list of int
        Quadrupole separation in electrode spacing.   
    '''
    # check parameters
    if isinstance(a, int):
        a = np.arange(a) + 1
    if isinstance(n, int):
        n = np.arange(n) + 1
    
    elec = np.arange(nelec) + 1
    abmn = []
    for aa in a:
        for nn in n:
            if nn >= aa-1: #minus 1 here to permit measurements on level 2 of pseudosection
                A = elec
                M = A + nn
                N = M + aa
                B = N + nn
                abmn.append(np.vstack([A, B, M, N]).T)
    abmn = np.vstack(abmn)
    abmn = abmn[(abmn <= nelec).all(1), :]
    df = pd.DataFrame(abmn, columns=['a', 'b', 'm', 'n'])
    df = df.sort_values(['a', 'b', 'm', 'n']).reset_index(drop=True)
    return df
    
def multigrad(nelec, a, n, s):
    ''' Generate measurement matrix for multigradient array.
    
    Parameters
    ----------
    nelec : int
        Number of electrodes
    a : int or list of int
        Spacing between potential electrodes (in electrode spacing).
    n : int or list of int
        Multiplier for `a` to determine spacing from A to M.
    s : int or list of int
        Separation factor for current electrodes, should be the intermediate
        numbers.
    '''
    # check parameters
    if isinstance(a, int):
        a = np.arange(a) + 1
    if isinstance(n, int):
        n = np.arange(n) + 1
    if isinstance(s, int):
        s = np.arange(s) + 1
    elec = np.arange(nelec) + 1
    abmn = []
    for ss in s:
        for nn in n:  # sometimes n will make M or N go beyond B
            for aa in a:
                A = elec
                B = A + (ss + 2) * aa
                M = A + nn * aa
                N = M + aa
                abmn.append(np.vstack([A, B, M, N]).T)
    abmn = np.vstack(abmn)
    abmn = abmn[(abmn <= nelec).all(1), :]
    abmn = abmn[(abmn[:, 2] < abmn[:, 1]) & (abmn[:, 3] < abmn[:, 1])]
    df = pd.DataFrame(abmn, columns=['a', 'b', 'm', 'n'])
    df = df.sort_values(['a', 'b', 'm', 'n']).reset_index(drop=True)
    return df 

#%% function for ip optimization
def computeCost(quad):
    # compute d (smallest distance between injecting and next time the electrode is used for MN)
    d = []
    for i in range(quad.shape[0]):
        a = quad[i, 0]
        b = quad[i, 1]
        ie1 = (quad[i+1:, 2:] == a).any(1)
        ie2 = (quad[i+1:, 2:] == b).any(1)
        ie = ie1 | ie2
        if ie.sum() > 0:
            d.append(i + np.min(np.where(ie)[0])+1)  # index 1 is first row after i
        else:
            d.append(-1)  # flag it to set it to 0 in the cost function later
    d = np.array(d)
    
    # cost function
    dinv = 1/d
    dinv[d < 0] = 0
    cost = np.sum(dinv)
    return cost, d


def optimize_ip(seq, niter=1000, pad=2):
    """Optimize a sequence to maximize the distance between
    a quadrupole used for injection and for potential readings.
    Tried to follow the Quenched method of Wilkinson et al. (2012)
    https://doi.org/10.1111/j.1365-246X.2012.05372.x. This function is
    relatively fast but can be stuck in local minima.

    Parameters
    ----------
    seq : array_like
        Sequence with 4 columns as A, B, M and N.
    niter : int, optional
        Number of iterations.
    pad : int, optional
        How far away from the position of the quadrupole with the largest
        cost can we move this quadrupole with the largest cost.

    Returns
    -------
    order : array of int
        Array of index showing the best order of quad to minimize the cost.
    costs : array of float
        Costs for each iteration.
    """
    seq = seq.copy()
    order = np.arange(seq.shape[0])
    order_old = order.copy()
    cost_old = np.inf
    costs = np.zeros(niter) * np.nan
    for iteration in range(niter):
        quad = seq[order, :]
        cost, d = computeCost(quad)
    
        if (d != -1).sum() == 0:
            break

        # only accept order that bring down the cost
        if cost > cost_old:
            order = order_old  # go back to previous order
            costs[iteration] = cost_old
        else:
            costs[iteration] = cost
            cost_old = cost
            order_old = order
        
        # update order by moving the smallest d to another random position
        imin = np.where(d == np.min(d[d != -1]))[0][0]
        ipos = np.random.choice(np.r_[np.arange(0, imin-pad),
                                np.arange(imin+pad, len(order))], 1)[0]
        order = np.insert(np.delete(order, imin), ipos, order[imin])

    return order, costs


# if True:
#     plt.ion()
#     seq = create_sequence(24, params=[('wenner', 4)], opt_ip=True, opt_plot=True)
#     print(seq)
#     plt.show(block=True)