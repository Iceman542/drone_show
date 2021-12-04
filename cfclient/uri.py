

# Change uris according to your setup
URI_droneA0 = 'radio://0/60/2M/E6E6E6E6E6'
URI_droneA1 = 'radio://0/60/2M/E6E6E6E6E7'
URI_droneA2 = 'radio://0/60/2M/E6E6E6E6E8'
URI_droneT2 = 'radio://0/80/2M/E7E7E7E7E7'
URI_droneT1 = 'radio://0/80/2M/E7E7E7E7E5' # This is drone 2
# URI2 = 'radio://0/60/2M/E7E7E7E7E7'
# URI3 = 'radio://0/5/2M/E7E7E7E702'
# URI4 = 'radio://0/110/2M/E7E7E7E703'

# (x_meters, y_meters, z_meters, time_seconds)
ROUTE_0 = [
    (0, 0, 1, 1),       # go up
    (0, 0, 1, 2),       # hover
    (1, 0, 0.5, 2),     # go forward and down
    (0, 0, 0.5, 3),     # hover
    (0, 0.5, 1, 2),     # go left
    (0, -1, 1, 2),      # go right
    (0, 0, 1, 2),       # hover
    (1, 0, 1, 4),       # foward
    (0, -0.5, 1.5, 2),  # go right and up
    (-1, 0, 1.5, 3),    # Back and up
    (0.5, 0.5, 1.5, 2), # go left and foward
    (0, 0, 1, 2),       # back to takeoff spot
]

ROUTE_1 = [
    (0, 0, 1, 1),       # go up
    (0, 0, .5, 2),       # hover
    (-1, 0, 1.7, 3),       # Back and up
    (0, 0, 1.7, 2),       # hover
    (0, -0.5, 1, 2),  # go right and up
    (0, 0.5, 1.5, 2),     # go left
    (0, 0, 1, 2),       # hover
    (1, 0, 1, 4),       # foward
    (0, -0.5, 1.5, 2),  # go right and up
    (-1, 0, 1.5, 3),       # Back
    (0.5, 0.5, 1.5, 2),     # go left and foward
]

ROUTE_2 = [
    (0, 0, 1, 1),       # go up
    (0, 0, .5, 2),       # hover
    (-1, 0, 1.7, 3),       # Back and up
    (0, 0, 1.7, 2),       # hover
    (0, -0.5, 1, 2),  # go right and up
    (0, 0.5, 1.5, 2),     # go left
    (0, 0, 1, 2),       # hover
    (1, 0, 1, 4),       # foward
    (0, -0.5, 1.5, 2),  # go right and up
    (-1, 0, 1.5, 3),       # Back
    (0.5, 0.5, 1.5, 2),     # go left and foward
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

# (time, (r,g,b))
LIGHTS_0 = [
    (5, (100, 0, 0)),
    (5, (0, 100, 0)),
    (5, (0, 0, 100)),
    (5, (0, 100, 0)),
    (5, (100, 0, 0)),
    (1000, (0, 0, 0))
]

LIGHTS_1 = [
    (5, (0, 100, 0)),
    (5, (0, 0, 100)),
    (5, (100, 0, 0)),
    (5, (0, 0, 100)),
    (5, (0, 100, 0)),
    (1000, (0, 0, 0))
]

LIGHTS_2 = [
    (5, (0, 0, 255)),
    (5, (0, 255, 0)),
    (5, (255, 0, 0)),
    (5, (0, 255, 255)),
    (5, (255, 255, 255)),
    (1000, (0, 0, 0))
]

PARAMS_0 = {'index': 0, "start_pos": (0, -2, 0)}
PARAMS_1 = {'index': 1, "start_pos": (0, 0, 0)}
PARAMS_2 = {'index': 2, "start_pos": (0, 2, 0)}
