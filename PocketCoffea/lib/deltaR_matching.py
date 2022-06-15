from collections.abc import Iterable
import numpy as np
import awkward as ak
import numba

@numba.jit
def get_matching_pairs_indices(idx_quark, idx_jets, builder, builder2):
    for ev_q, ev_j in zip(idx_quark, idx_jets):
        builder.begin_list()
        builder2.begin_list()
        q_done = []
        j_done = []
        for i, (q,j) in enumerate(zip(ev_q, ev_j)):
            if q not in q_done:
                if j not in j_done:
                    builder.append(i)
                    q_done.append(q)
                    j_done.append(j)
                else: 
                    builder2.append(i)
        builder.end_list()
        builder2.end_list()
    return builder, builder2

# This function takes as arguments the indices of two collections of objects that have been
# previously matched and ordered by pt, and return the indices padded with None values where
# no match has been found. In the implementation, the assumption is that the number of
# un-matched obj (gen-jets) is less or equal than the number of un-matched obj2 (jets).
@numba.jit
def get_matching_objects_indices_padnone(idx_matched_obj, idx_matched_obj2, num_jets, deltaR, builder, builder2, builder3):
    for ev1_match, ev2_match, nj, dr in zip(idx_matched_obj, idx_matched_obj2, num_jets, deltaR):
        #print(ev1_match, ev2_match)
        builder.begin_list()
        builder2.begin_list()
        builder3.begin_list()
        row1_length = len(ev1_match)
        row2_length = nj
        missed = 0
        for i in range(row2_length):
            if i in ev2_match:
                #print(i, row1_length)
                builder2.append(i)
                if i-missed < row1_length:
                    builder.append(ev1_match[i-missed])
                    builder3.append(dr[i-missed])
            else:
                builder.append(None)
                builder2.append(None)
                builder3.append(None)
                missed += 1
        builder.end_list()
        builder2.end_list()
        builder3.end_list()
    return builder, builder2, builder3

def metric_pt(obj, obj2):
    return abs(obj.pt - obj2.pt)

def object_matching(obj, obj2, dr_min, dpt_max=None):
    # Compute deltaR(quark, jet) and save the nearest jet (deltaR matching)
    deltaR = ak.flatten(obj.metric_table(obj2), axis=2)
    # Keeping only the pairs with a deltaR min
    maskDR = deltaR < dr_min
    if dpt_max is not None:
        deltaPt_table = obj.metric_table(obj2, metric=metric_pt)
        # Check if the pt cut is an iterable or a scalar
        if isinstance(dpt_max, Iterable):
            # Broadcast and flatten pt_min array in order to match the shape of the metric_table()
            dpt_max_broadcast = ak.broadcast_arrays(dpt_max[:,np.newaxis], deltaPt_table)[0]
            dpt_max  = ak.flatten(dpt_max_broadcast, axis=2)
        deltaPt = ak.flatten(deltaPt_table, axis=2)
        maskPt = deltaPt < dpt_max
        maskDR = maskDR & maskPt
    idx_pairs_sorted = ak.argsort(deltaR, axis=1)
    pairs = ak.argcartesian([obj, obj2])
    pairs_sorted  = pairs[idx_pairs_sorted]
    deltaR_sorted = deltaR[idx_pairs_sorted]
    maskDR_sorted = maskDR[idx_pairs_sorted]
    idx_obj, idx_obj2 = ak.unzip(pairs_sorted)
    
    _idx_matched_pairs, _idx_missed_pairs = get_matching_pairs_indices(idx_obj, idx_obj2, ak.ArrayBuilder(), ak.ArrayBuilder())
    idx_matched_pairs = _idx_matched_pairs.snapshot()
    idx_missed_pairs  = _idx_missed_pairs.snapshot()
    # The indices related to the invalid jet matches are skipped
    idx_matched_obj  = idx_obj[idx_matched_pairs]
    idx_matched_obj2 = idx_obj2[idx_matched_pairs]
    deltaR_matched = deltaR_sorted[idx_matched_pairs]
    maskDR_matched = maskDR_sorted[idx_matched_pairs]
    # In order to keep track of the invalid jet matches, the indices of the second collection
    # are sorted, and the order of the first collection of indices is reshuffled accordingly
    obj2_order = ak.argsort(idx_matched_obj2)
    idx_obj_obj2sorted  = idx_matched_obj[obj2_order]
    idx_obj2_obj2sorted = idx_matched_obj2[obj2_order]
    deltaR_obj2sorted = deltaR_matched[obj2_order]
    maskDR_obj2sorted = maskDR_matched[obj2_order]
    # Here we apply the deltaR + pT requirements on the objects and on deltaR
    idx_obj_obj2sorted_masked  = idx_obj_obj2sorted[maskDR_obj2sorted]
    idx_obj2_obj2sorted_masked = idx_obj2_obj2sorted[maskDR_obj2sorted]
    deltaR_final = deltaR_obj2sorted[maskDR_obj2sorted]
    # The indices and deltaR are padded with None values where there is no match
    _idx_obj_sorted_padnone, _idx_obj2_sorted_padnone, _deltaR_final_padnone = get_matching_objects_indices_padnone(idx_obj_obj2sorted_masked, 
                                                                                             idx_obj2_obj2sorted_masked, 
                                                                                             ak.num(obj2), deltaR_final,
                                                                                             ak.ArrayBuilder(), ak.ArrayBuilder(), ak.ArrayBuilder())
    idx_obj_sorted_padnone  = _idx_obj_sorted_padnone.snapshot()
    idx_obj2_sorted_padnone = _idx_obj2_sorted_padnone.snapshot()
    deltaR_final_padnone    = _deltaR_final_padnone.snapshot()
    # Finally the objects are sliced through the padded indices
    # In this way, to a None entry in the indices will correspond a None entry in the object
    matched_obj  = obj[idx_obj_sorted_padnone]
    matched_obj2 = obj2[idx_obj2_sorted_padnone]

    return matched_obj, matched_obj2, deltaR_final_padnone