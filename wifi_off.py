import gc
import network


ap_if = network.WLAN(network.AP_IF)
ap_if.active(False)
ap_if = None
sta_if = network.WLAN(network.STA_IF)
sta_if.active(False)
sta_if = None

gc.collect()
