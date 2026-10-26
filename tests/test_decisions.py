from datetime import date

from tools.decisions import read_decisions, record_decision


def test_record_then_read(tmp_path):
    p = tmp_path / "DECISIONS.md"
    p.write_text("# DECISIONS\n\n## 리밸런싱 제안 기록\n(아직 없음)\n", encoding="utf-8")
    record_decision("장기채 매수 보류", "금리 인하 기다림", on=date(2026, 7, 1), path=p)
    d = read_decisions(p)
    assert d == [{"date": "2026-07-01", "who": "사용자", "decision": "장기채 매수 보류", "reason": "금리 인하 기다림"}]
    assert "(아직 없음)" not in p.read_text(encoding="utf-8")


def test_save_accounts_roundtrip(tmp_path):
    from tools.assets import load_accounts_list, load_pools, save_accounts
    p = tmp_path / "accounts.yaml"
    accounts = [{"id": "a1", "label": "A", "owner": "me", "broker": "mirae", "account_type": "pension_savings",
                 "pocket": "pension", "layer": 3, "api": False, "active": True, "pool": "p1"}]
    pools = {"p1": {"label": "풀1", "strategy": "all_weather", "mode": "buy_only", "accounts": ["a1"]}}
    save_accounts(accounts, pools, path=p)
    assert load_accounts_list(p) == accounts
    got = load_pools(p)
    assert got["p1"]["mode"] == "buy_only" and got["p1"]["accounts"] == ["a1"]
