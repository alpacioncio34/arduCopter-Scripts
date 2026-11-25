# Delay's effect and viability study
This documentation aims to predict with the best certainty the effects that the several layers (frontend-backend-onboard) will have on the final performance of the comunication protocol, the test will be mainly focused on 
manual control, since it is the feature that requires the most efficient implementation, in order to simulate this, I will use a small WebSocket server that takes the requests from an esp32, the esp32 will have 8 buttons 
( the same buttons as the manual control: 4 directional arrows, 2 yaw rate spin and 2 altitude arrows), attached to the buttons, there will be an LED that means that the button is PRESSED, same to the manual service, it
will handle on press and on release logic, right now just the exact same way **manual_control.py** handles it, it will have more reliability and security layers in the future.

**esp32-board-foto**

After implementing this, we are measuring a median of ~35 ms (//TODO: Check this measures statisfically using the csv of delays), the esp32 connects though a network (In this case, my mobile phone's network), and sends via
websockets the messages, the computer is also connected to the network and reads the inputs from the buttons, the pins send HIGH to the buttons, so the button sends LOW, and HIGH again when presses (review a more
technical circuit explanation), since the button has the same ONPRESS ONRELEASE logic, I copied the same functions from **manual_control.py** and pasted them here as actions.

## Takeaways
The good thing, is that if we manage to achieve a decent manual control, the rest of the funcionality have much more margin when it comes to time per request, but also manual control this way is much more usefull for 
testing rather than a feature itself, because delay will grow with distance, therefore if we wanted to implement our own efficient manual control without a controller we would need to study more protocols and change our
approach, it still is useefull for a low-range mobile phone manual control if limits are set correctly (perhaps using correspondend mavinit scripts based on mode, and restricting a lot GEOFENCE with manual control)

## Next steps:
- Start adding delay manually in the esp32 code in order to test how much margin we have, based on the margin we can spend more or less time during each request.
- Try MQTT or other protocols that could be faster or more efficient, at least not depending on a network.
