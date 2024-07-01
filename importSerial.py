import serial
import websocket
import threading
import json
import time
import psycopg2

# Database connection settings
db_config = {
    'dbname': 'your_dbname',
    'user': 'your_username',
    'password': 'your_password',
    'host': 'localhost'
}

# Replace '/dev/ttyUSB0' with your serial port and adjust the baud rate as needed
serial_port = serial.Serial('COM3', 9600, timeout=1)

# Initialize the last send time
last_send_time = 0
is_recording = False
recorded_commands = []

def store_command_locally(direction_x, direction_y):
    recorded_commands.append((direction_x, direction_y))

def store_commands_in_db():
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()
    cursor.executemany("INSERT INTO commands (direction_x, direction_y) VALUES (%s, %s)", recorded_commands)
    conn.commit()
    conn.close()

def playback_commands():
    for command in recorded_commands:
        direction_x, direction_y = command
        
        # Logic to calculate motor speeds and directions (as per the active file excerpt)
        if direction_y < 0:  # Forward
            motor_a_speed = motor_b_speed = abs(direction_y)
        elif direction_y > 0:  # Backward
            motor_a_speed = motor_b_speed = -abs(direction_y)
        else:  # Stop
            motor_a_speed = motor_b_speed = 0

        if direction_x > 0:  # Turning right
            motor_b_speed -= direction_x
            motor_a_speed = min(255, motor_a_speed + abs(direction_x))
        elif direction_x < 0:  # Turning left
            motor_a_speed -= abs(direction_x)
            motor_b_speed = min(255, motor_b_speed + abs(direction_x))

        motor_a_speed = max(-255, min(255, motor_a_speed))
        motor_b_speed = max(-255, min(255, motor_b_speed))

        motor_a_direction = '1' if motor_a_speed >= 0 else '0'
        motor_b_direction = '1' if motor_b_speed >= 0 else '0'

        motor_a_speed_abs = abs(motor_a_speed)
        motor_b_speed_abs = abs(motor_b_speed)

        # Construct commands as per the active file excerpt
        command_a = f"A,{motor_a_speed_abs},{motor_a_direction}\n"
        command_b = f"B,{motor_b_speed_abs},{motor_b_direction}\n"

        # Write commands to serial port
        serial_port.write(command_a.encode())
        serial_port.write(command_b.encode())

def on_message(ws, message):

    global last_send_time
    current_time = time.time()

    # Checks if 2 seconds have passed since last send
    if current_time - last_send_time <0:
        return #Less thatn 2 seconds have passed, don't send data

    last_send_time = current_time

    data = json.loads(message)
    if data.get('type') == 'ping':
        return

    message_data = data.get('message', {})
    if isinstance(message_data, dict):
        direction_x = message_data.get('directionx', 0)
        direction_y = message_data.get('directiony', 0)
        #print(f"Received direction_x: {direction_x}, direction_y: {direction_y}")

        # Adjust motor speeds based on direction_y and direction_x
        if direction_y < 0:  # Forward
            motor_a_speed = motor_b_speed = abs(direction_y)
        elif direction_y > 0:  # Backward
            motor_a_speed = motor_b_speed = -abs(direction_y)
        else:  # Stop
            motor_a_speed = motor_b_speed = 0

        # Adjust for turning
        if direction_x > 0:  # Turning right
            motor_b_speed -= direction_x
            motor_a_speed = min(255, motor_a_speed + abs(direction_x))
        elif direction_x < 0:  # Turning left
            motor_a_speed -= abs(direction_x)
            motor_b_speed = min(255, motor_b_speed + abs(direction_x))

        # Ensure motor speeds are within -255 to 255 range
        motor_a_speed = max(-255, min(255, motor_a_speed))
        motor_b_speed = max(-255, min(255, motor_b_speed))

        # Determine directions based on speed signs
        motor_a_direction = '1' if motor_a_speed >= 0 else '0'
        motor_b_direction = '1' if motor_b_speed >= 0 else '0'

        # Convert speeds to absolute values for the command
        motor_a_speed_abs = abs(motor_a_speed)
        motor_b_speed_abs = abs(motor_b_speed)

        # Construct and send commands
        command_a = f"A,{motor_a_speed_abs},{motor_a_direction}\n"
        command_b = f"B,{motor_b_speed_abs},{motor_b_direction}\n"
        #print(f"Sending command for motor A: {command_a}")
        #print(f"Sending command for motor B: {command_b}")
        serial_port.write(command_a.encode())
        serial_port.write(command_b.encode())
    else:
        print("message_data is not a dictionary.", message_data)

    # Optionally, send data to the serial port
    #print(f"Sending command for motor A: {command_a}")
    #print(f"Sending command for motor B: {command_b}")

def on_error(ws, error):
    print(error)

def on_close(ws):
    print("### closed ###")

def on_open(ws):
    def run(*args):
        # Subscribe to the channel, adjust the subscription message as needed
        ws.send(json.dumps({"command": "subscribe", "identifier": json.dumps({"channel": "Api::V1::ChatRoomsChannel", "chat_room_id": 1})}))
    thread = threading.Thread(target=run)
    thread.start()
    print("### connected ###")

if __name__ == "__main__":
    websocket.enableTrace(False)
    ws = websocket.WebSocketApp("wss://mastion-backend-e2bbfddfbd53.herokuapp.com/api/v1/connect",
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    ws.on_open = on_open
    ws.run_forever()