import serial
import websocket
import threading
import json
import time

# Replace '/dev/ttyUSB0' with your serial port and adjust the baud rate as needed
serial_port = serial.Serial('COM3', 9600, timeout=1)

def on_message(ws, message):
    data = json.loads(message)
    if data.get('type') == 'ping':
        command_a = f"A,0,0\n"
        command_b = f"B,0,0\n"
        print(f"Sending command A: {command_a}")
        print(f"Sending command B: {command_b}")
        
        time.sleep(0.1)
        serial_port.write(command_a.encode())
        serial_port.write(command_b.encode())
        return

    message_data = data.get('message', {})
    if isinstance(message_data, dict):
        direction_x = message_data.get('directionx', 0)
        direction_y = message_data.get('directiony', 0)
        print(f"Received direction_x: {direction_x}, direction_y: {direction_y}")

        # Basic speed and direction calculations
        base_speed = 0  # Min speed remains 0 to prevent immediate start
        max_speed = 255  # Max speed
        # Calculate dynamic speed based on direction_y
        dynamic_speed = max(base_speed, min(abs(direction_y) * max_speed, max_speed))
        speed_a = dynamic_speed
        speed_b = dynamic_speed
        direction_a = 0 if direction_y >= 0 else 1  # 0 for forward, 1 for backward
        direction_b = 0 if direction_y >= 0 else 1

        # Adjust speeds for turning
        if direction_x > 0:  # Turn right
            speed_b = max(base_speed, dynamic_speed - abs(direction_x) * (max_speed - dynamic_speed))  # Decrease speed of motor B
        elif direction_x < 0:  # Turn left
            speed_a = max(base_speed, dynamic_speed - abs(direction_x) * (max_speed - dynamic_speed))  # Decrease speed of motor A

        last_send_time = 0  # Initialize the last send time to 0

        # Inside your loop or function where commands are sent
        current_time = time.time()  # Get the current time
        if current_time - last_send_time >= 0.5:  # Check if 500ms have elapsed
            command_a = f"A,{speed_a},{direction_a}\n"
            command_b = f"B,{speed_b},{direction_b}\n"
            print(f"Sending command A: {command_a}")
            print(f"Sending command B: {command_b}")

            serial_port.write(command_a.encode())
            serial_port.write(command_b.encode())

            last_send_time = current_time  # Update the last send time to the current time
        else:
            # It hasn't been 500ms yet, do nothing or handle accordingly
            pass
    else:
        print("message_data is not a dictionary.", message_data)

    # Optionally, send data to the serial port
    # serial_port.write(f"{direction_x},{direction_y}\n".encode())

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

if __name__ == "__main__":
    websocket.enableTrace(False)
    ws = websocket.WebSocketApp("wss://mastion-backend-e2bbfddfbd53.herokuapp.com/api/v1/connect",
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    ws.on_open = on_open
    ws.run_forever()