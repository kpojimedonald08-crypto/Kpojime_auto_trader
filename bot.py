import asyncio
import json
from deriv_api import DerivAPI

# Configuration
API_TOKEN = "pat_442f41c718647d66e4b5cee3471ebe5aa1e99b6a9223afc514efd8a84c30a0ef"
APP_ID = 1089

# Trading settings
SYMBOLS = {
    "EURUSD": "frxEURUSD",
    "GOLD": "frxXAUUSD"
}
TRADE_AMOUNT = 1
DURATION = 5
DURATION_UNIT = "m"

async def get_candles(api, symbol, count=10):
    response = await api.ticks_history({
        "ticks_history": symbol,
        "count": count,
        "end": "latest",
        "style": "candles",
        "granularity": 60
    })
    return response.get("candles", [])

def detect_bos(candles):
    if len(candles) < 5:
        return None
    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]
    last_close = candles[-1]["close"]
    prev_high = max(highs[-5:-1])
    prev_low = min(lows[-5:-1])
    if last_close > prev_high:
        return "CALL"
    elif last_close < prev_low:
        return "PUT"
    return None

async def place_trade(api, symbol, direction):
    proposal = await api.proposal({
        "proposal": 1,
        "amount": TRADE_AMOUNT,
        "basis": "stake",
        "contract_type": direction,
        "currency": "USD",
        "duration": DURATION,
        "duration_unit": DURATION_UNIT,
        "symbol": symbol
    })
    proposal_id = proposal["proposal"]["id"]
    buy = await api.buy({"buy": proposal_id, "price": 100})
    print(f"Trade placed: {direction} on {symbol}")
    return buy

async def run_bot():
    api = DerivAPI(app_id=APP_ID)
    await api.authorize({"authorize": API_TOKEN})
    print("Bot authorized and running...")
    
    while True:
        for name, symbol in SYMBOLS.items():
            candles = await get_candles(api, symbol)
            signal = detect_bos(candles)
            if signal:
                print(f"BOS detected on {name}: {signal}")
                await place_trade(api, symbol, signal)
            else:
                print(f"No signal on {name}")
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(run_bot())
