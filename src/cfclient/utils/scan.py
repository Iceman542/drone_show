"""
Simple example that scans for available Crazyflies and lists them.
"""
import cflib.crtp

# Initiate the low level drivers
cflib.crtp.init_drivers()

print('Scanning interfaces for Crazyflies...')
available = cflib.crtp.scan_interfaces()
print('Crazyflies found:')
for i in available:
    print(i[0])