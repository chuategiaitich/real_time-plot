# import matplotlib.pyplot as plt
# from matplotlib.animation import FuncAnimation
# import serial
# import time
# import numpy as np

# # Serial port configuration
# SERIAL_PORT = 'COM3'
# BAUD_RATE = 115200
# TIMEOUT = 0.1

# # Data storage
# t = []
# data = []
# start_time = time.time()

# # Initialize Serial
# try:
#     ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=TIMEOUT)
#     ser.flushInput()
#     print(f"Connected to {SERIAL_PORT}")
# except serial.SerialException as e:
#     print(f"Error opening serial port: {e}")
#     exit(1)

# # Figure and plot setup
# fig, ax = plt.subplots()
# line, = ax.plot([], [], 'b-', label='Serial Data')
# ax.set_xlabel('Time (s)')
# ax.set_ylabel('Value')
# ax.set_xlim(0, 10)
# ax.legend()
# ax.grid(True)

# def update(frame):
#     global t, data
#     try:
#         while ser.in_waiting > 0:
#             line_data = ser.readline().decode('utf-8').strip()
#             try:
#                 value = float(line_data)
#                 current_time = time.time() - start_time
#                 # print(f"Time: {data}")  # Debug dữ liệu
                
#                 # Append data
#                 t.append(current_time)
#                 data.append(value)
                
#                 # Remove old data outside the 10-second window
#                 while t and t[0] < current_time - 10:
#                     t.pop(0)
#                     data.pop(0)
                
#                 # Update plot data
#                 line.set_data(t, data)
                
#                 # Always show the last 10 seconds on the x-axis
#                 ax.set_xlim(max(0, current_time - 10), current_time)
                
#                 # Dynamically adjust y-axis based on data
#                 if data:  # Ensure data is not empty
#                     y_min = min(data)
#                     y_max = max(data)
#                     ax.set_ylim(y_min, y_max)
                
#             except ValueError:
#                 print(f"Invalid data received: {line_data}")
#     except serial.SerialException as e:
#         print(f"Serial error: {e}")

#     return line,

# # Animation
# ani = FuncAnimation(fig, update, interval=50, blit=False)
# plt.title('Real-Time Serial Data Plot')
# plt.show()

# # Close serial port when done
# ser.close()



import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Button
import serial
import time
import numpy as np

# Serial port configuration
SERIAL_PORT = 'COM3'
BAUD_RATE = 115200
TIMEOUT = 0.1

# Data storage for sensors
sensor_data = {}  # Dictionary to store data for each sensor
start_time = time.time()

# List of colors for different sensors
colors = ['b-', 'r-', 'g-', 'c-', 'm-', 'y-', 'k-']  # Add more if needed
color_index = 0

# Initialize Serial
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=TIMEOUT)
    ser.flushInput()
    print(f"Connected to {SERIAL_PORT}")
except serial.SerialException as e:
    print(f"Error opening serial port: {e}")
    exit(1)

# Figure and plot setup
fig, ax = plt.subplots()
ax.set_xlabel('Time (s)')
ax.set_ylabel('Value')
ax.set_xlim(0, 10)
ax.set_ylim(-10, 10)  # Initial range for safety
ax.legend()
ax.grid(True)

# Function to toggle plotting for a sensor
def toggle_plot(sensor_name):
    def toggle(event):
        sensor_data[sensor_name]['active'] = not sensor_data[sensor_name]['active']
        print(f"Plotting {sensor_name}: {sensor_data[sensor_name]['active']}")
        sensor_data[sensor_name]['line'].set_visible(sensor_data[sensor_name]['active'])
        ax.legend()
        fig.canvas.draw()
    return toggle

# Function to add a new sensor to the plot
def add_sensor(sensor_name):
    global color_index
    # Initialize data for the new sensor
    sensor_data[sensor_name] = {
        't': [],  # Time data
        'data': [],  # Sensor values
        'active': True,  # Plotting state
        'line': None,  # Plot line object
        'button': None  # Toggle button
    }
    
    # Create a new plot line for the sensor
    color = colors[color_index % len(colors)]  # Cycle through colors
    line, = ax.plot([], [], color, label=sensor_name)
    sensor_data[sensor_name]['line'] = line
    line.set_visible(True)  # Initially visible
    color_index += 1
    
    # Create a toggle button for the sensor
    button_pos = [0.1 + 0.1 * len(sensor_data), 0.01, 0.1, 0.05]  # Position buttons dynamically
    ax_button = plt.axes(button_pos)
    button = Button(ax_button, sensor_name, color='lightgray', hovercolor='gray')
    button.on_clicked(toggle_plot(sensor_name))
    sensor_data[sensor_name]['button'] = button
    
    print(f"Added sensor: {sensor_name}")
    ax.legend()
    fig.canvas.draw()

def update(frame):
    try:
        while ser.in_waiting > 0:
            line_data = ser.readline().decode('utf-8').strip()
            try:
                # Process data in format ">sensor: value"
                if line_data.startswith('>') and ': ' in line_data:
                    parts = line_data.split('>')
                    if len(parts) < 2:
                        continue
                    sensor_part = parts[1].split(': ')
                    if len(sensor_part) < 2:
                        continue
                    sensor_name = sensor_part[0].lower()  # e.g., "temperature"
                    value_str = sensor_part[1]  # e.g., "25.5"
                    value = float(value_str)

                    # Add sensor if it's new
                    if sensor_name not in sensor_data:
                        add_sensor(sensor_name)

                    current_time = time.time() - start_time

                    # Store data for the sensor
                    sensor_data[sensor_name]['t'].append(current_time)
                    sensor_data[sensor_name]['data'].append(value)

                    # Remove old data outside the 10-second window
                    while sensor_data[sensor_name]['t'] and sensor_data[sensor_name]['t'][0] < current_time - 10:
                        sensor_data[sensor_name]['t'].pop(0)
                        sensor_data[sensor_name]['data'].pop(0)

                    # Update plot if active
                    if sensor_data[sensor_name]['active']:
                        sensor_data[sensor_name]['line'].set_data(
                            sensor_data[sensor_name]['t'],
                            sensor_data[sensor_name]['data']
                        )

                    # Always show the last 10 seconds on the x-axis
                    ax.set_xlim(max(0, current_time - 10), current_time)

                    # Dynamically adjust y-axis based on visible data
                    all_data = []
                    for s_name, s_data in sensor_data.items():
                        if s_data['active'] and s_data['data']:
                            all_data.extend(s_data['data'])
                    if all_data:  # Ensure data is not empty
                        y_min = min(all_data)
                        y_max = max(all_data)
                        padding = (y_max - y_min) * 0.1
                        ax.set_ylim(y_min - padding, y_max + padding)

            except ValueError:
                print(f"Invalid data received: {line_data}")
    except serial.SerialException as e:
        print(f"Serial error: {e}")

    # Return lines that need to be updated
    lines = [s_data['line'] for s_data in sensor_data.values() if s_data['active']]
    return lines

# Animation
ani = FuncAnimation(fig, update, interval=50, blit=False)
plt.title('Real-Time Serial Data Plot')
plt.show()

# Close serial port when done
ser.close()