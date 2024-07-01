import serial

serial_port = serial.Serial('COM3', 9600, timeout=1)

command_a = "A,255,1\n"
while True:
    print(f"Sending command A: {command_a}")
    serial_port.write(command_a.encode())
    #serial_port.write(command_b.encode())