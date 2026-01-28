import asyncio
import aiohttp
import sys

async def test_ws(url):
    print(f"Testing {url}...", flush=True)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(url) as ws:
                print("Connected!", flush=True)
                await ws.close()
                print("Closed.", flush=True)
    except Exception as e:
        print(f"Failed: {e}", flush=True)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = "ws://localhost:8010/twilio/stream"
    
    asyncio.run(test_ws(url))
