# (x_meters, y_meters, z_meters, time_seconds, rate)
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