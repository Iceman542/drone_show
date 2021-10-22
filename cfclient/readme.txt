uri_local.py
------------

g_unity  = ("192.168.1.100", 9999)
g_uris   = {uri.URI_droneA}
g_routes = {uri.URI_droneA: uri.ROUTE_0}
g_params = {uri.URI_droneA: {'index': 0, "start_pos": (-2, 0, 0)}}
g_lights = {uri.URI_droneA: uri.LIGHTS_1,
            uri.URI_droneT1: uri.LIGHTS_2}

Information
-----------
ISSUE1: y=z / z=y
ISSUE2: -40 is upstage y=-y
ISSUE3: 20:1 location factor

STAGE:
            +40
    -80             +80
            -40

start_pos - this is in unity coordinates (must account for xfactor)
red = Vehicle0
blue = Vehicle1