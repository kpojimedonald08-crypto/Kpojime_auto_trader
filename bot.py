import asyncio
import json
import websockets

API_TOKEN = "pat_442f41c718647d66e4b5cee3471ebe5aa1e99b6a9223afc514efd8a84c30a0ef"
APP_ID = 1089
WS_URL = f"wss://ws.derivws.com/websockets/v3?app_id={APP_ID}"

SYMBOLS = {
    "EURUSD": "frxEURUSD",
    "GOLD": "frxXAUUSD"
}
TRADE_AMOUNT = 1

async def send(ws, data):
    await ws.send(json.dumps(data))
    return json.loads(await ws.recv())

async def run_bot():
    while True:
        try:
            async with websockets.connect(WS_URL) as ws:
                auth = await send(ws, {"authorize": API_TOKEN})
                print("Authorized:", auth.get("authorize", {}).get("loginid"))

                while True:
                    for name, symbol in SYMBOLS.items():
                        candles_resp = await send(ws, {
                            "ticks_history": symbol,
                            "count": 10,
                            "end": "latest",
                            "style": "candles",
                            "granularity": 60
                        })
                        candles = candles_resp.get("candles", [])
                        if len(candles) < 5:
                            continue
                        highs = [c["high"] for c in candles]
                        lows = [c["low"] for c in candles]
                        last_close = candles[-1]["close"]
                        prev_high = max(highs[-5:-1])
                        prev_low = min(lows[-5:-1])

                        if last_close > prev_high:
                            direction = "CALL"
                        elif last_close < prev_low:
                            direction = "PUT"
                        else:
                            print(f"No signal on {name}")
                            continue

                        print(f"BOS detected on {name}: {direction}")
                        proposal = await send(ws, {
                            "proposal": 1,
                            "amount": TRADE_AMOUNT,
                            "basis": "stake",
                            "contract_type": direction,
                            "currency": "USD",
                            "duration": 5,
                            "duration_unit": "m",
                            "symbol": symbol
                        })
                        pid = proposal.get("proposal", {}).get("id")
                        if pid:
                            result = await send(ws, {"buy": pid, "price": 100})
                            print(f"Trade placed: {result}")

                    await asyncio.sleep(60)

        except Exception as e:
            print(f"Error: {e}, reconnecting in 10s...")
            await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(run_bot())
