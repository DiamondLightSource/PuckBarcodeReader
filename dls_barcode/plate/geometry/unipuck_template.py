class UnipuckTemplate:
    """ Defines the layout of a type of sample holder that is a circular puck
    that contains concentric circles (layers) of sample pins.
    """
    NUM_SLOTS = 16
    PUCK_RADIUS = 1
    CENTER_RADIUS = 0.151  # radius of puck center (relative to puck radius)
    SLOT_RADIUS = 0.197  # radius of a pin slot (relative to puck radius)
    LAYERS = 2  # number of concentric layers of pin slots
    N = [5, 11]  # number of pin slots in each concentric layer, starting from center
    LAYER_RADII = [0.371, 0.788]  # distance of center of a pin of a given concentric layer from center of puck
