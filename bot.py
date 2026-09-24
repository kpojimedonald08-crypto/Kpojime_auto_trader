import asyncio
import json
import websockets

API_TOKEN = "pat_442f41c718647d66e4b5cee3471ebe5aa1e99b6a9223afc514efd8a84c30a0ef"

SYMBOLS = {
    "EURUSD": "frxEURUSD",
    "GOLD": "frxXAUUSD"
}
TRADE_AMOUNT = 1

async def run_bot():
    uri = "wss://ws.derivws.com/websockets/v3?app_id=1089"
    while True:
        try:
            async with websockets.connect(
                uri,
                ping_interval=20,
                ping_timeout=10,
                extra_headers={"Origin": "https://app.deriv.com"}
            ) as ws:
                auth = await ws.send(json.dumps({"authorize": API_TOKEN}))
                resp = json.loads(await ws.recv())
                print("Auth:", resp.get("authorize", {}).get("loginid", "Failed"))

                while True:
                    for name, symbol in SYMBOLS.items():
                        await ws.send(json.dumps({
                            "ticks_history": symbol,
                            "count": 10,
                            "end": "latest",
                            "style": "candles",
                            "granularity": 60
                        }))
                        data = json.loads(await ws.recv())
                        candles = data.get("candles", [])
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
                        print(f"Signal: {direction} on {name}")
                        await ws.send(json.dumps({
                            "proposal": 1,
                            "amount": TRADE_AMOUNT,
                            "basis": "stake",
                            "contract_type": direction,
                            "currency": "USD",
                            "duration": 5,
                            "duration_unit": "m",
                            "symbol": symbol
                        }))
                        proposal = json.loads(await ws.recv())
                        pid = proposal.get("proposal", {}).get("id")
                        if pid:
                            await ws.send(json.dumps({"buy": pid, "price": 100}))
                            result = json.loads(await ws.recv())
                            print(f"Trade placed: {result}")
                    await asyncio.sleep(60)
        except Exception as e:
            print(f"Error: {e}, retrying in 10s...")
            await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(run_bot())
