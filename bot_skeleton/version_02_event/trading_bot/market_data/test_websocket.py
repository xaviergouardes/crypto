import asyncio
import aiohttp

async def test_ws():
    symbol = "ethusdc"  # changer ici si nécessaire
    url = f"wss://stream.binance.com:9443/ws/{symbol}@depth10@100ms"
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(url) as ws:
            async for msg in ws:
                print("TYPE:", msg.type)
                print("==> msg = ", msg)
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = msg.json()
                    if asyncio.iscoroutine(data):
                        data = await data
                    print("Bids:", data.get("bids"))
                    print("Asks:", data.get("asks"))

asyncio.run(test_ws())
