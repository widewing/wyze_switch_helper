# wyze_switch_helper
A simple script to help update Wyze switch status in near realtime in Home Assistant

## How does it work
When a switch is pressed, it will send some message to Wyze cloud. We don't care what's in the message, we just need this event to tell Home Assistant to udpate corresponding device.
Internally it uses tcpdump to capture network traffic on Wyze Switch devices, and convert MAC addresses to entity_id, and call update_entity API in Home Assistant.
