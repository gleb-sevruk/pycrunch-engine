def unload_candidates(new_modules : set):
    reload_this = set()
    for x in new_modules:
        if is_candidate_for_reload(x):
            reload_this.add(x)

    return reload_this

def is_candidate_for_reload(x):
    return not(x.startswith('_pytest') or x.startswith('py.'))