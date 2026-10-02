import time

# Starting coordinates
lat = 36.508472
lon = -6.281327

# Increment per second. 
# 1 degree is approx 111 km. 0.00001 degrees is roughly 1 meter.
step_lat = 0.00001  # Changes latitude (North/South)
step_lon = 0.00001  # Changes longitude (East/West)

print("Starting independent walking simulation...")
print("Press Ctrl+C in the console to stop the script.\n")

try:
    while True:
        # Display the current position
        print(f"Current position -> Latitude: {lat:.6f} | Longitude: {lon:.6f}")
        
        # Simulate movement by adding the step
        lat += step_lat
        lon += step_lon

        # Write the new position to a file
        with open("gps_data.txt", "w") as file:
            file.write(f"{lat},{lon}")
        
        # Wait 1 second before calculating the next step
        time.sleep(1)
        
except KeyboardInterrupt:
    print("\nSimulation stopped by the user.")