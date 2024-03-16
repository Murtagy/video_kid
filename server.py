# import asyncio
# import websockets
# import json

# connected = set()

# async def handler(websocket, path):
#     global connected
#     connected.add(websocket)
#     try:
#         async for message in websocket:
#             data = json.loads(message)
#             # You can add any custom logic for handling different types of messages here
#             print(f"Received message: {data}")
#             # Broadcast the message to all connected clients except the sender
#             for conn in connected:
#                 if conn != websocket:
#                     await conn.send(message)
#     finally:
#         connected.remove(websocket)

# start_server = websockets.serve(handler, "localhost", 8080)

# asyncio.get_event_loop().run_until_complete(start_server)
# asyncio.get_event_loop().run_forever()

import asyncio
import websockets
import json

clients = {}

async def register(websocket):
    clients[websocket] = {"role": None, "peer": None}

async def unregister(websocket):
    clients.pop(websocket, None)
    # Notify the peer if any
    if websocket.peer:
        await inform_peer_disconnect(websocket.peer)

async def set_role(websocket, role):
    clients[websocket]["role"] = role
    await match_peers()

async def inform_peer_disconnect(peer_websocket):
    message = json.dumps({"type": "peerDisconnected"})
    await peer_websocket.send(message)

async def match_peers():
    sender = None
    receiver = None
    for client, info in clients.items():
        if info["role"] == "sender" and not info["peer"]:
            sender = client
        elif info["role"] == "receiver" and not info["peer"]:
            receiver = client
        if sender and receiver:
            clients[sender]["peer"] = receiver
            clients[receiver]["peer"] = sender
            # Notify both peers
            await sender.send(json.dumps({"type": "peerMatched", "role": "sender"}))
            await receiver.send(json.dumps({"type": "peerMatched", "role": "receiver"}))
            break  # Only match one pair for simplicity

async def handler(websocket, path):
    await register(websocket)
    try:
        async for message in websocket:
            data = json.loads(message)
            if data["type"] == "register":
                await set_role(websocket, data["role"])
            elif websocket.peer:  # Forward message to peer if exists
                await clients[websocket]["peer"].send(message)
    finally:
        await unregister(websocket)

start_server = websockets.serve(handler, "localhost", 8080)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()

