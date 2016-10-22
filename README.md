# Multicast communication
Use these scripts to broadcast unencrypted data across your network. Originally intended for use with power-monitoring so multiple devices could handle on-battery events from an uninterrupted power supply.  

Multiple senders can send data to the same group/port, which will be received by all listeners.  

## Setup
Copy config.ini.template to config.ini, and create a shared key for use by all your senders and receivers.  

## Use
Pipe or provide data to `send.py` as a parameter.  

`receive.py` will print out the data provided to `send.py` encased between start and end tags:  
```
### Start message a51214ef0 ###
Stuff!
### End message a51214ef0 ###
```

## Notes
The data transmitted across the wire is unencrypted, so it can be read by any multicast client on your network. However, I have taken steps to allow "trusted" use, where you rely on the information even though it may be read openly.

Through the use of a shared key, as well as run-time generated random data and a transmission counter, receivers should be relatively well protected against in-flight data corruption (unintentional or otherwise) as well as duplicate transmission.

Corrupted data, or data received multiple times will be silently dropped unless the `receive.py` debug flag is activated.
