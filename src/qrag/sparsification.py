"""Matched unordered-edge budgets with an explicit full-objective error bound."""
from dataclasses import replace
from time import perf_counter
import numpy as np


def sparsify(problem,complementarity,rule='evidence',fraction=.5,seed=42):
    started=perf_counter()
    if rule not in {'evidence','absolute','random','degree'} or not np.isfinite(fraction) or not 0<=fraction<=1:
        raise ValueError('Unknown rule or invalid edge fraction')
    comp=np.asarray(complementarity)
    if comp.shape!=problem.pairs.shape or not np.isfinite(comp).all() or np.any(comp<0):
        raise ValueError('Invalid evidence priorities')
    edges=[(int(i),int(j)) for i,j in zip(*np.nonzero(problem.pairs))]
    budget=int(np.floor(fraction*len(edges)))
    magnitude=lambda edge:abs(problem.pairs[edge])
    absolute=sorted(edges,key=lambda e:(-magnitude(e),*e))
    protected=[]
    if rule=='absolute':
        ordered=absolute
    elif rule=='random':
        order=np.random.default_rng(seed).permutation(len(edges))
        ordered=[edges[int(i)] for i in order]
    elif rule=='degree':
        ranks={}
        for node in range(len(problem.linear)):
            neighbors=sorted([e for e in edges if node in e],key=lambda e:(-magnitude(e),*e))
            for rank,edge in enumerate(neighbors):
                ranks[edge]=min(ranks.get(edge,rank),rank)
        ordered=sorted(edges,key=lambda e:(ranks[e],-magnitude(e),*e))
    else:
        # Reserve at most half the hard budget for potential evidence bridges;
        # when protected candidates exceed this quota, rank them explicitly.
        candidates=sorted([e for e in edges if comp[e]>0],key=lambda e:(-comp[e]*np.sqrt(magnitude(e)),-magnitude(e),*e))
        protected=candidates[:min(budget,int(np.ceil(budget/2)))]
        ordered=protected+[e for e in absolute if e not in set(protected)]
    retained=set(ordered[:budget])
    pairs=np.zeros_like(problem.pairs)
    for edge in retained:
        pairs[edge]=problem.pairs[edge]
    delta=float(np.abs(problem.pairs-pairs).sum())
    result=replace(problem,pairs=pairs)
    return result,{'rule':rule,'edge_fraction':fraction,'seed':seed,'available_edges':len(edges),
                   'retained_edges':len(retained),'protected_edges':len(protected),
                   'retained_indices':[list(e) for e in sorted(retained)],'removed_l1':delta,
                   'full_gap_bound_for_exact_sparse_solution':2*delta,
                   'seconds':perf_counter()-started,'degree_symmetry':'minimum endpoint neighbor rank; exact unordered-edge budget'}
