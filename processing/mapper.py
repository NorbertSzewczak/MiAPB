from collections import defaultdict


def build_transition_map(log_list):
    """
    Tworzy słownik przejść między aktywnościami wraz z liczbą ich wystąpień.

    Args:
        log_list (list[list[str]]): lista ścieżek (traces), np. [['a', 'b', 'c'], ['a', 'c']]

    Returns:
        dict: mapa przejść {(source, target): count}
    """
    transition_map = defaultdict(int)

    for trace in log_list:
        for i in range(len(trace) - 1):
            src = trace[i]
            dst = trace[i + 1]
            transition_map[(src, dst)] += 1

    return dict(transition_map)
