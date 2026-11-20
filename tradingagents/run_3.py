# TradingAgents 试跑脚本：只跑 3 只验证（A股、港股、美股各一支）
# 用法（key 由调用方从环境传入，不要把 key 写进文件）：
#   GOOGLE_API_KEY=<key> ~/workspace/pro-analysis/.venv/bin/python ~/workspace/pro-analysis/run_3.py
# 输出：每只的 decision（Buy/Overweight/Hold/Underweight/Sell + 最终决策全文和
#       各分析师报告）打印到 stdout，并写入 run_3_results.json；
#       2026-11-20 17:20 修：之前只存了 decision 一个词，理由全丢了——
#       现在把 final_state 里的 final_trade_decision 和四份报告也存进 JSON。
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "TradingAgents"))

from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.graph.trading_graph import TradingAgentsGraph

TICKERS = [
    ("600519.SS", "贵州茅台"),
    ("0700.HK", "腾讯控股"),
    ("NVDA", "英伟达"),
]
ANALYSIS_DATE = "2026-11-19"  # 用已收盘的完整交易日，避免盘中数据不完整

config = DEFAULT_CONFIG.copy()
config["llm_provider"] = os.environ.get("TRADINGAGENTS_LLM_PROVIDER", "google")
config["deep_think_llm"] = os.environ.get("TRADINGAGENTS_DEEP_THINK_LLM", "gemini-3.6-flash")
config["quick_think_llm"] = os.environ.get("TRADINGAGENTS_QUICK_THINK_LLM", "gemini-3.5-flash-lite")
config["output_language"] = "Chinese"  # 给用户的最终报告用中文；内部辩论仍用英文
config["max_debate_rounds"] = 1
config["max_risk_discuss_rounds"] = 1

def main():
    if not os.environ.get("GOOGLE_API_KEY"):
        print("ERROR: 未设置 GOOGLE_API_KEY，无法调用 Gemini。", file=sys.stderr)
        sys.exit(2)
    ta = TradingAgentsGraph(debug=False, config=config)
    results = {}
    for ticker, name in TICKERS:
        print(f"\n===== {name} ({ticker}) @ {ANALYSIS_DATE} =====", flush=True)
        try:
            final_state, decision = ta.propagate(ticker, ANALYSIS_DATE)
            results[ticker] = {
                "name": name,
                "decision": decision,
                "final_trade_decision": final_state.get("final_trade_decision"),
                "market_report": final_state.get("market_report"),
                "sentiment_report": final_state.get("sentiment_report"),
                "news_report": final_state.get("news_report"),
                "fundamentals_report": final_state.get("fundamentals_report"),
                "trader_investment_plan": final_state.get("trader_investment_plan"),
                "investment_plan": final_state.get("investment_plan"),
            }
            print(f"--- {ticker} decision ---\n{decision}\n", flush=True)
            print(f"--- {ticker} final_trade_decision ---\n{final_state.get('final_trade_decision')}\n", flush=True)
        except Exception as e:
            results[ticker] = {"name": name, "error": f"{type(e).__name__}: {e}"}
            print(f"--- {ticker} FAILED: {e} ---\n", flush=True)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "run_3_results.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"results written to {out}")

if __name__ == "__main__":
    main()
