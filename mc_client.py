import websocket
import threading
import time
import json

class machina_client:
    def __init__(self, url):
        self.ws = websocket.WebSocketApp(
            url,
            on_open=self.on_open,
            on_message=self.on_message
        )
        self.last_command = None

        # Start WebSocket in a background thread
        self.thread = threading.Thread(target=self.ws.run_forever)
        self.thread.start()

    def send_command(self, command):
        self.last_command = command
        if self.ws.sock and self.ws.sock.connected:
            self.ws.send(command)
        else:
            print("WebSocket is not connected. Command not sent.")


    def on_open(self, ws):
        print("Connected to MachinaBridge")

    def on_message(self, ws, message):
        try:
            data = json.loads(message)
            event_type = data.get("event")

            if event_type == "action-executed":
                pending = int(data.get("pendTot", 0))
                if pending < 1 and self.last_command:
                    time.sleep(0.5)
                    ws.send(self.last_command)

            print(event_type)
        except Exception as e:
            print("Error processing message:", e)

# Run the program
if __name__ == "__main__":
    url = "ws://127.0.0.1:6999/Bridge"
    machina_client(url)

    # Keep the main thread alive
    while True:
        time.sleep(1)
