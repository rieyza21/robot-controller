import serial
import websocket
import threading
import json
import time

# Replace '/dev/ttyUSB0' with your serial port and adjust the baud rate as needed
serial_port = serial.Serial('COM3', 9600, timeout=1)

movement_history = []
is_recording = False

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
            motor_a_speed = abs(direction_y)  # Use the base speed or another logic for speed calculation
            motor_b_speed = -abs(direction_y)  # Reverse direction for opposite motor
        elif direction_x < 0:  # Turning left
            motor_a_speed = -abs(direction_y)  # Reverse direction for opposite motor
            motor_b_speed = abs(direction_y)  # Use the base speed or another logic for speed calculation

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

        # Record the movement
        if is_recording:
            movement_record = {"command_a": command_a, "command_b": command_b, "timestamp": time.time()}
            movement_history.append(movement_record)
        
        serial_port.write(command_a.encode())
        serial_port.write(command_b.encode())
    else:
        print("message_data is not a dictionary.", message_data)


def replay_path():
    if not movement_history:
        print("No path recorded.")
        return

    last_timestamp = None
    for record in movement_history:
        # If using timestamps, calculate the delay needed
        if last_timestamp is not None:
            time.sleep(record["timestamp"] - last_timestamp)
        
        # Send the recorded commands
        serial_port.write(record["command_a"].encode())
        serial_port.write(record["command_b"].encode())
        
        # Update last_timestamp if using timestamps
        last_timestamp = record["timestamp"]

    print("Path replay finished.")

def start_recording():
    global is_recording_enabled
    is_recording_enabled = True
    print("Recording started.")

def stop_recording():
    global is_recording_enabled
    is_recording_enabled = False
    print("Recording stopped.")


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
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("wss://ex.api-mastion-backend.kesug.com/api/v1/connect",
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    ws.on_open = on_open
    ws.run_forever()
