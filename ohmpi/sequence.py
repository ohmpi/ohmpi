import numpy as np
import pandas as pd
import os

def create_sequence(nelec, params=[('dpdp', 1, 8)], include_reciprocal=False, ip_optimization=False):
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
    ip_optimization: bool, optional
        If True, will optimize for induced polarization measurement (i.e. will
        try to put as much time possible between injection and measurement at
        the same electrode).
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
    if ip_optimization:
        print('NOT IMPLEMENTED YET')

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
    elec = np.arange(nelec) + 11
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

# for i in np.array(range(0,len(a))):
#     n_ = np.array(range(0, n[i]))+1
#     s_ = np.array(range(0, s[i]))+1
#     for j in np.array(range(0, len(n_))):
#         for k in np.array(range(0, len(s_))):
#             A = elec_id
#             B = A + s_[k] + 2
#             M = A + n_[j] * a[i]
#             N = M + a[i]
#             abmn.append(np.vstack([A, B, M, N]).T)


# test code
# x1 = dpdp1(24, 2, 8)
# x3 = wenner_alpha(24, 1)
# x6 = schlum1(24, 1, 10)
# x8 = multigrad(24, 1, 10, 2)



#%% show pseudoSection
#import matplotlib.pyplot as plt    
#
#N = 24
#elecpos = np.linspace(0, 8, N)
#quad = pd.concat([wenner_alpha(N, 1), wenner_alpha(N, 2)]).values
#array = np.sort(quad, axis=1)
#
#cmiddle = np.min([elecpos[array[:,0]-1], elecpos[array[:,1]-1]], axis=0) \
#    + np.abs(elecpos[array[:,0]-1]-elecpos[array[:,1]-1])/2
#pmiddle = np.min([elecpos[array[:,2]-1], elecpos[array[:,3]-1]], axis=0) \
#    + np.abs(elecpos[array[:,2]-1]-elecpos[array[:,3]-1])/2
#xpos = np.min([cmiddle, pmiddle], axis=0) + np.abs(cmiddle-pmiddle)/2
#ypos = - np.sqrt(2)/2*np.abs(cmiddle-pmiddle)
#
#
#fig, ax = plt.subplots()
#cax = ax.plot(xpos, ypos, 'o')
#ax.set_title('Pseudo Section')
#fig.show()
