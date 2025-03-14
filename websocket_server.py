import asyncio
import websockets
import json

connected_clients = {}  # Store connected clients (device_id: websocket)

async def handle_client(websocket, path):
    client_id = None
    try:
        async for message in websocket:
            print(f"Server received message: {message}")
            try:
                message_data = json.loads(message)
                message_type = message_data.get('type')

                if message_type == 'register':
                    client_id = message_data.get('client_id')
                    client_type = message_data.get('client_type')
                    if client_id and client_type:
                        connected_clients[client_id] = websocket
                        print(f"Client registered: ID={client_id}, Type={client_type}")
                        await websocket.send(json.dumps({"type": "registration_ack", "message": "Registration successful"})) # Acknowledge registration

                    else:
                        print("Registration failed: client_id or client_type missing")
                        await websocket.send(json.dumps({"type": "registration_nack", "message": "Registration failed: missing info"}))

                elif message_type == 'message': # Example message type - you can add more logic here
                    target_client_id = message_data.get('target_client_id')
                    payload = message_data.get('payload')
                    if target_client_id and payload:
                        target_websocket = connected_clients.get(target_client_id)
                        if target_websocket:
                            await target_websocket.send(json.dumps({"type": "relayed_message", "from_client_id": client_id, "payload": payload})) # Relay message
                            print(f"Relayed message from {client_id} to {target_client_id}")
                        else:
                            print(f"Target client {target_client_id} not found.")
                            await websocket.send(json.dumps({"type": "error", "message": f"Target client {target_client_id} not found."}))
                    else:
                        print("Message relay failed: target_client_id or payload missing")
                        await websocket.send(json.dumps({"type": "error", "message": "Message relay failed: missing info"}))

                else:
                    print(f"Unknown message type: {message_type}")
                    await websocket.send(json.dumps({"type": "error", "message": "Unknown message type"}))


            except json.JSONDecodeError:
                print("Received non-JSON message:", message)
                await websocket.send(json.dumps({"type": "error", "message": "Invalid JSON message"}))
            except Exception as e:
                print(f"Error processing message: {e}")
                await websocket.send(json.dumps({"type": "error", "message": f"Server error: {e}"}))


    except websockets.exceptions.ConnectionClosedError as e:
        print(f"Connection closed unexpectedly: {e}")
    except websockets.exceptions.ConnectionClosedOK:
        print("Connection closed normally by client.")
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        if client_id:
            if client_id in connected_clients:
                del connected_clients[client_id] # Remove client on disconnection
                print(f"Client disconnected: ID={client_id}")
            else:
                print(f"Client disconnected (ID={client_id}), but was not in connected_clients.") # Should not happen, but for safety

        print("WebSocket connection finished.")


async def main():
    server = await websockets.serve(handle_client, "0.0.0.0", 8765) # Listen on all interfaces, port 8765
    print("WebSocket server started, listening on port 8765")
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
