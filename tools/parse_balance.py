"""parse_balance — 보유 내역 입력. (1) CSV 읽기 (2) 앱 캡처 이미지 → 표 (Claude 비전, Agent SDK).

캡처 파싱은 처음 등록할 때와 수량이 바뀔 때만 쓴다. 매번의 현재가는 tools.market.fetch_prices.
검사 칸은 종목명·수량·현재가 세 개 (docs/AGENT_DESIGN.md 완료 기준 2).
"""
from __future__ import annotations

import asyncio
from pathlib import Path

import pandas as pd

HOLDING_COLUMNS = ["account_id", "ticker_name", "ticker", "qty", "price"]

CAPTURE_SCHEMA = {
    "type": "object",
    "properties": {
        "account_label": {"type": "string", "description": "화면 상단 계좌 이름, 예: 연금저축계좌(신)"},
        "screen_total_value": {"type": "integer", "description": "화면에 보이는 평가금액 합계(원). 없으면 0"},
        "rows": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "ticker_name": {"type": "string"},
                    "qty": {"type": "integer", "description": "보유수량"},
                    "price": {"type": "integer", "description": "현재가(원)"},
                    "value": {"type": "integer", "description": "평가금액(원)"},
                    "buy_value": {"type": "integer", "description": "매입금액(원), 없으면 0"},
                },
                "required": ["ticker_name", "qty", "price", "value", "buy_value"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["account_label", "screen_total_value", "rows"],
    "additionalProperties": False,
}


def load_holdings_csv(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8-sig", dtype={"ticker": str})
    missing = [c for c in HOLDING_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"CSV에 없는 열: {missing}")
    df["qty"] = df["qty"].astype(int)
    df["price"] = df["price"].astype(int)
    return df


def reconcile(rows: pd.DataFrame, screen_total: int, tolerance: int = 5_000) -> tuple[bool, int]:
    """파싱한 행의 합계와 화면 합계를 대조. 불일치면 사용자가 표를 고쳐 확정한다."""
    total = int((rows["qty"] * rows["price"]).sum()) if "value" not in rows else int(rows["value"].sum())
    diff = total - int(screen_total)
    return abs(diff) <= tolerance, diff


async def _parse_capture_async(image_paths: list[Path]) -> dict:
    from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

    files = "\n".join(f"- {p.resolve()}" for p in image_paths)
    prompt = (
        "다음 증권사 앱 잔고 캡처 이미지를 Read 도구로 읽고, 보이는 종목 전부를 표로 옮겨라. "
        "같은 종목이 여러 이미지에 중복으로 보이면 한 번만 넣어라. 숫자는 쉼표를 빼고 정수로. "
        "계산하거나 추정하지 말고 화면에 보이는 값만 옮겨라. 화면 합계(평가금액)도 보이면 적어라.\n" + files
    )
    options = ClaudeAgentOptions(
        allowed_tools=["Read"],
        permission_mode="dontAsk",
        max_turns=12,
        output_format={"type": "json_schema", "schema": CAPTURE_SCHEMA},
        system_prompt="너는 표 전사 도구다. 보이는 값만 옮긴다. 분류·판단·계산을 하지 않는다.",
    )
    result = None
    async for msg in query(prompt=prompt, options=options):
        if isinstance(msg, ResultMessage):
            result = msg
    if result is None or result.structured_output is None:
        raise RuntimeError(f"캡처 파싱 실패: {getattr(result, 'result', None)}")
    return result.structured_output


def parse_capture(image_paths: list[str | Path], account_id: str) -> tuple[pd.DataFrame, dict]:
    """캡처 이미지들 → holdings DataFrame. 두 번째 반환값은 {account_label, screen_total_value, reconciled, diff}."""
    paths = [Path(p) for p in image_paths]
    data = asyncio.run(_parse_capture_async(paths))
    df = pd.DataFrame(data["rows"])
    df.insert(0, "account_id", account_id)
    df["ticker"] = None
    ok, diff = reconcile(df, data["screen_total_value"]) if data["screen_total_value"] else (True, 0)
    meta = {"account_label": data["account_label"], "screen_total_value": data["screen_total_value"],
            "reconciled": ok, "diff": diff}
    return df[HOLDING_COLUMNS + ["value", "buy_value"]], meta
