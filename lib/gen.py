def shuffled_list(start: int, stop: int, step: int = 1):
    """Get shuffled range() list"""
    from random import shuffle
    shuffled_list = list(range(start, stop, step))
    shuffle(shuffled_list)
    return shuffled_list
