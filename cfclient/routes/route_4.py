# (x_meters, y_meters, z_meters, time_seconds, {clockwise, counterclockwise)
ROUTE_4 = [
    (0, 0, 1, 3),                   # go up
    (1, 0, 1, 3),                   # hover
    (1, 0, 1, 5, {"type": "circle", "rotation": "counterclockwise", "radius": 0.5, "lift": 0.5, "start": 3}),  # circle
    (1, 0, 1, 3)                    # hover
]
