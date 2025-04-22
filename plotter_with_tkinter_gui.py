import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import serial
import time
import numpy as np

# Serial port configuration
SERIAL_PORT = 'COM3'  # Change to '/dev/ttyUSB0' on Linux
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

# Tkinter GUI setup
root = tk.Tk()
root.title("Real-Time Serial Data Plotter")
root.geometry("1000x600")

# Create a frame for buttons (left) and plot (right)
button_frame = ttk.Frame(root)
button_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

# Create a frame for the plot
plot_frame = ttk.Frame(root)
plot_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

# Figure and plot setup
fig, ax = plt.subplots(figsize=(8, 5))
ax.set_xlabel('Time (s)')
ax.set_ylabel('Value')
ax.set_xlim(0, 10)
ax.set_ylim(-10, 10)  # Initial range for safety
ax.legend()
ax.grid(True)

# Embed the plot in Tkinter
canvas = FigureCanvasTkAgg(fig, master=plot_frame)
canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

# Function to toggle plotting for a sensor
def toggle_plot(sensor_name):
    sensor_data[sensor_name]['active'] = not sensor_data[sensor_name]['active']
    print(f"Plotting {sensor_name}: {sensor_data[sensor_name]['active']}")
    sensor_data[sensor_name]['line'].set_visible(sensor_data[sensor_name]['active'])
    ax.legend()
    canvas.draw()

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
    
    # Create a toggle button for the sensor in the button frame
    button = ttk.Button(button_frame, text=f"{sensor_name} (ON)", command=lambda: toggle_button(sensor_name))
    button.pack(fill=tk.X, pady=2)
    sensor_data[sensor_name]['button'] = button
    
    print(f"Added sensor: {sensor_name}")
    ax.legend()
    canvas.draw()

# Function to toggle button text and plot state
def toggle_button(sensor_name):
    toggle_plot(sensor_name)
    state = "ON" if sensor_data[sensor_name]['active'] else "OFF"
    sensor_data[sensor_name]['button'].config(text=f"{sensor_name} ({state})")

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

    # Update the canvas
    canvas.draw()

    # Return lines that need to be updated
    lines = [s_data['line'] for s_data in sensor_data.values() if s_data['active']]
    return lines

# Animation
ani = FuncAnimation(fig, update, interval=50, blit=False)

# Start the Tkinter main loop
root.mainloop()

# Close serial port when done
ser.close()