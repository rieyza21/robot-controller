import serial
import time
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from scipy.ndimage import zoom

from smbus2 import SMBus

# Define constants
AMG8833_ADDRESS = 0x69  # Example I2C address for the AMG8833, confirm this address
BLOCK_SIZE = 32

# Function to read thermal data
def read_thermal_data(bus, address, register, length):
    data = []
    num_full_blocks = length // BLOCK_SIZE
    remaining_bytes = length % BLOCK_SIZE

    for i in range(num_full_blocks):
        start_byte = i * BLOCK_SIZE
        block = bus.read_i2c_block_data(address, register + start_byte, BLOCK_SIZE)
        data.extend(block)

    if remaining_bytes:
        start_byte = num_full_blocks * BLOCK_SIZE
        block = bus.read_i2c_block_data(address, register + start_byte, remaining_bytes)
        data.extend(block)

    return data

# Initialize plot
fig, ax = plt.subplots()
data = np.zeros((8, 8))
interpolated_data = zoom(data, 16)  # Interpolates 8x8 to 128x128
im = ax.imshow(interpolated_data, cmap='inferno', vmin=20, vmax=40)

def update(frame):
    global data
    try:
        with SMBus(1) as bus:
            raw_data = read_thermal_data(bus, AMG8833_ADDRESS, 0x80, 128)
            data = np.array(raw_data).reshape((8, 8))
            interpolated_data = zoom(data, 16)  # Interpolate to 128x128
            im.set_array(interpolated_data)
    except Exception as e:
        print(f"Error: {e}")

    return [im]

ani = FuncAnimation(fig, update, interval=1000, blit=True)
plt.colorbar(im)
plt.show()
