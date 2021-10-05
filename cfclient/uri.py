

# Change uris according to your setup
URI_droneA = 'radio://0/60/2M/E6E6E6E6E6'
URI_droneT2 = 'radio://0/80/2M/E7E7E7E7E7'
URI_droneT1 = 'radio://0/80/2M/E7E7E7E7E5' # This is drone 2
# URI2 = 'radio://0/60/2M/E7E7E7E7E7'
# URI3 = 'radio://0/5/2M/E7E7E7E702'
# URI4 = 'radio://0/110/2M/E7E7E7E703'

# (x_meters, y_meters, z_meters, rate-mps, time_seconds)
ROUTE_0 = [
    (0, 0, 1, 1),       # go up
    (0, 0, 1, 2),       # hover
    (0.5, 0, 1, 2),     # go forward
    (-0.5, 0, 1, 2),    # go backwards
    (0, 0, 1, 2),       # hover
    (0, 0.5, 1, 2),     # go left
    (0, -0.5, 1, 2),    # go right
    (0, 0, 1, 2),       # hover
]

ROUTE_1 = [
    (0, 0, .5, 1),       # go up
    (0, 0, .5, 2),       # hover
    (0.5, 0, .5, 2),     # go forward
    (-0.5, 0, .5, 2),    # go backwards
    (0, 0, .5, 2),       # hover
    (0, 0.5, .5, 2),     # go left
    (0, -0.5, .5, 2),    # go right
    (0, 0, .5, 2),       # hover
]

ROUTE_TEST = [
    (0, 0, 1, 1),       # go up
    (0, 0, 1, 1),       # hover 1 sec
    (.5, .5, 1.5, 2),     # Moves foward, left, and up at the same time
    (-.5,-.5, 1, 2),      # Moves Back, right, and down at the same time


]

ROUTE_TEST2 = [
    (0, 0, 0, 3),       # wait
    (0, 0, 1, 1),       # go up
    (0, 0, 1, 2),       # hover
]

# Currently not used
PARAMS_0 = {'route': 0}
PARAMS_1 = {'route': 1}
PARAMS_2 = {'route': 2}
PARAMS_3 = {'route': 3}
PARAMS_4 = {'route': 4}
