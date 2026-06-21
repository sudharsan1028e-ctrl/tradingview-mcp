#!/usr/bin/env python3
"""
TradingView MCP Server
Provides live market data via tradingview-ta library
"""

import json
import asyncio
from typing import Any
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from tradingview_ta import TA_Handler, Interval, Exchange

app = Server("tradingview-mcp")

INTERVAL_MAP = {
    "1m": Interval.INTERVAL_1_MINUTE,
    "5m": Interval.INTERVAL_5_MINUTES,
    "15m": Interval.INTERVAL_15_MINUTES,
    "30m": Interval.INTERVAL_30_MINUTES,
    "1h": Interval.INTERVAL_1_HOUR,
    "2h": Interval.INTERVAL_2_HOURS,
    "4h": Interval.INTERVAL_4_HOURS,
    "1d": Interval.INTERVAL_1_DAY,
    "1W": Interval.INTERVAL_1_WEEK,
    "1M": Interval.INTERVAL_1_MONTH,
}


def get_analysis(symbol: str, exchange: str, screener: str, interval: str) -> dict:
    handler = TA_Handler(
        symbol=symbol.upper(),
        exchange=exchange.upper(),
        screener=screener.lower(),
        interval=INTERVAL_MAP.get(interval, Interval.INTERVAL_1_HOUR),
        timeout=10,
    )
    analysis = handler.get_analysis()
    return {
        "symbol": symbol.upper(),
        "interval": interval,
        "summary": {
            "recommendation": analysis.summary["RECOMMENDATION"],
            "buy": analysis.summary["BUY"],
            "sell": analysis.summary["SELL"],
            "neutral": analysis.summary["NEUTRAL"],
        },
        "oscillators": {
            "recommendation": analysis.oscillators["RECOMMENDATION"],
            "buy": analysis.oscillators["BUY"],
            "sell": analysis.oscillators["SELL"],
            "neutral": analysis.oscillators["NEUTRAL"],
        },
        "moving_averages": {
            "recommendation": analysis.moving_averages["RECOMMENDATION"],
            "buy": analysis.moving_averages["BUY"],
            "sell": analysis.moving_averages["SELL"],
            "neutral": analysis.moving_averages["NEUTRAL"],
        },
        "indicators": {
            "close": analysis.indicators.get("close"),
            "open": analysis.indicators.get("open"),
            "high": analysis.indicators.get("high"),
            "low": analysis.indicators.get("low"),
            "volume": analysis.indicators.get("volume"),
            "RSI": analysis.indicators.get("RSI"),
            "MACD_macd": analysis.indicators.get("MACD.macd"),
            "MACD_signal": analysis.indicators.get("MACD.signal"),
            "EMA_20": analysis.indicators.get("EMA20"),
            "EMA_50": analysis.indicators.get("EMA50"),
            "EMA_200": analysis.indicators.get("EMA200"),
            "BB_upper": analysis.indicators.get("BB.upper"),
            "BB_lower": analysis.indicators.get("BB.lower"),
            "Stoch_K": analysis.indicators.get("Stoch.K"),
            "Stoch_D": analysis.indicators.get("Stoch.D"),
            "ADX": analysis.indicators.get("ADX"),
            "ATR": analysis.indicators.get("ATR"),
            "CCI20": analysis.indicators.get("CCI20"),
        },
    }


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_quote",
            description="Get live price and technical analysis for any symbol (e.g. XAUUSD, EURUSD, BTCUSD, AAPL)",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Trading symbol e.g. XAUUSD, EURUSD, BTCUSD, AAPL, TSLA"
                    },
                    "exchange": {
                        "type": "string",
                        "description": "Exchange e.g. OANDA, BINANCE, NASDAQ, NYSE, FX_IDC",
                        "default": "OANDA"
                    },
                    "screener": {
                        "type": "string",
                        "description": "Screener: forex, crypto, america, europe, etc.",
                        "default": "forex"
                    },
                    "interval": {
                        "type": "string",
                        "description": "Timeframe: 1m, 5m, 15m, 30m, 1h, 2h, 4h, 1d, 1W, 1M",
                        "default": "1h"
                    }
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="get_multi_timeframe",
            description="Get analysis for a symbol across multiple timeframes at once",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Trading symbol e.g. XAUUSD"},
                    "exchange": {"type": "string", "default": "OANDA"},
                    "screener": {"type": "string", "default": "forex"},
                    "intervals": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of intervals e.g. ['15m','1h','4h','1d']",
                        "default": ["15m", "1h", "4h", "1d"]
                    }
                },
                "required": ["symbol"]
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    try:
        if name == "get_quote":
            symbol = arguments["symbol"]
            exchange = arguments.get("exchange", "OANDA")
            screener = arguments.get("screener", "forex")
            interval = arguments.get("interval", "1h")

            result = get_analysis(symbol, exchange, screener, interval)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_multi_timeframe":
            symbol = arguments["symbol"]
            exchange = arguments.get("exchange", "OANDA")
            screener = arguments.get("screener", "forex")
            intervals = arguments.get("intervals", ["15m", "1h", "4h", "1d"])

            results = {}
            for interval in intervals:
                try:
                    results[interval] = get_analysis(symbol, exchange, screener, interval)
                except Exception as e:
                    results[interval] = {"error": str(e)}

            return [TextContent(type="text", text=json.dumps(results, indent=2))]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
