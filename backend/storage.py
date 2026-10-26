"""Local single-household ledger. Tests inject a temporary database path."""
from contextlib import contextmanager
from datetime import date, datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import Annotated, Literal
from uuid import UUID

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, model_validator

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "local" / "retire-together.sqlite3"
Money = Annotated[int, Field(strict=True, ge=0, le=1_000_000_000_000_000)]

class InputModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

class Person(InputModel):
    name: Annotated[str, Field(min_length=1, max_length=40)]
    age: Annotated[int, Field(strict=True, ge=18, le=110)]
    gender: Literal["female", "male", "unspecified"]
    role: Literal["wife", "husband", "partner"]

class FamilyInput(InputModel):
    me: Person
    partner: Person | None = None
    retirement_age: Annotated[int, Field(strict=True, ge=18, le=100)]
    target_amount: Annotated[int, Field(strict=True, ge=1, le=1_000_000_000_000_000)]
    version: Annotated[int, Field(strict=True, ge=0)]

class AssetInput(InputModel):
    name: Annotated[str, Field(min_length=1, max_length=100)]
    account: Annotated[str, Field(min_length=1, max_length=100)]
    owner: Literal["me", "partner"]
    pocket: Literal["retirement", "cash", "property", "debt"]
    assetClass: Literal["stock", "long_bond", "mid_bond", "gold", "commodity", "cash", "property", "mixed", "debt"]
    amount: Money
    as_of: date

    @model_validator(mode="after")
    def consistent_class(self):
        if self.pocket in ("property", "debt"):
            if self.assetClass != self.pocket:
                raise ValueError("부동산·대출의 분류가 일치해야 합니다")
        elif self.assetClass in ("property", "debt"):
            raise ValueError("금융 주머니에 부동산·대출을 넣을 수 없습니다")
        if self.as_of > date.today():
            raise ValueError("기준일은 미래일 수 없습니다")
        return self

class AssetCreate(AssetInput):
    request_id: UUID

class AssetUpdate(AssetInput):
    version: Annotated[int, Field(strict=True, ge=1)]

def now():
    return datetime.now(timezone.utc).isoformat()

@contextmanager
def connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    conn = sqlite3.connect(DB_PATH, timeout=5)
    DB_PATH.chmod(0o600)
    conn.row_factory = sqlite3.Row
    try:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS family (id INTEGER PRIMARY KEY CHECK(id=1), payload TEXT NOT NULL, version INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS assets (id TEXT PRIMARY KEY, request_id TEXT UNIQUE NOT NULL, payload TEXT NOT NULL, version INTEGER NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS asset_history (event_id INTEGER PRIMARY KEY AUTOINCREMENT, asset_id TEXT NOT NULL, operation TEXT NOT NULL, payload TEXT NOT NULL, version INTEGER NOT NULL, created_at TEXT NOT NULL);
        """)
        with conn:
            yield conn
    finally:
        conn.close()

def family_from(conn):
    row = conn.execute("SELECT payload, version FROM family WHERE id=1").fetchone()
    return {**json.loads(row["payload"]), "version": row["version"]} if row else None

def require_person(conn, owner):
    family = family_from(conn)
    if not family or not family.get(owner):
        raise HTTPException(422, "먼저 해당 소유자의 기본 정보를 등록해 주세요.")

def asset_from(row):
    return {**json.loads(row["payload"]), "id": row["id"], "version": row["version"], "updated_at": row["updated_at"]}

def get_family():
    with connection() as conn:
        return family_from(conn)

def save_family(data: FamilyInput):
    with connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        current = family_from(conn)
        if (current["version"] if current else 0) != data.version:
            raise HTTPException(409, "다른 화면에서 정보가 바뀌었습니다. 새로고침 후 다시 확인해 주세요.")
        if data.partner is None and any(json.loads(row[0])["owner"] == "partner" for row in conn.execute("SELECT payload FROM assets")):
            raise HTTPException(409, "배우자 자산이 있어 배우자 정보를 지울 수 없습니다.")
        payload = data.model_dump(exclude={"version"})
        payload["updated_at"] = now()
        conn.execute("INSERT INTO family VALUES (1, ?, ?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload, version=excluded.version", (json.dumps(payload, ensure_ascii=False), data.version + 1))
        return {**payload, "version": data.version + 1}

def list_assets():
    with connection() as conn:
        return [asset_from(row) for row in conn.execute("SELECT * FROM assets ORDER BY created_at, id")]

def create_asset(data: AssetCreate):
    from uuid import uuid4
    payload = data.model_dump(mode="json", exclude={"request_id"})
    text = json.dumps(payload, ensure_ascii=False)
    with connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        require_person(conn, data.owner)
        existing = conn.execute("SELECT * FROM assets WHERE request_id=?", (str(data.request_id),)).fetchone()
        if existing:
            if json.loads(existing["payload"]) != payload:
                raise HTTPException(409, "이미 사용된 등록 요청입니다. 화면을 다시 열어 주세요.")
            return asset_from(existing)
        asset_id, timestamp = str(uuid4()), now()
        conn.execute("INSERT INTO assets VALUES (?, ?, ?, 1, ?, ?)", (asset_id, str(data.request_id), text, timestamp, timestamp))
        conn.execute("INSERT INTO asset_history(asset_id, operation, payload, version, created_at) VALUES (?, 'create', ?, 1, ?)", (asset_id, text, timestamp))
        return {**payload, "id": asset_id, "version": 1, "updated_at": timestamp}

def update_asset(asset_id: UUID, data: AssetUpdate):
    payload = data.model_dump(mode="json", exclude={"version"})
    text = json.dumps(payload, ensure_ascii=False)
    with connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        require_person(conn, data.owner)
        existing = conn.execute("SELECT version FROM assets WHERE id=?", (str(asset_id),)).fetchone()
        if not existing:
            raise HTTPException(404, "등록된 자산을 찾을 수 없습니다.")
        if existing["version"] != data.version:
            raise HTTPException(409, "다른 화면에서 자산이 바뀌었습니다. 새로고침 후 다시 확인해 주세요.")
        timestamp = now()
        conn.execute("UPDATE assets SET payload=?, version=version+1, updated_at=? WHERE id=?", (text, timestamp, str(asset_id)))
        conn.execute("INSERT INTO asset_history(asset_id, operation, payload, version, created_at) VALUES (?, 'update', ?, ?, ?)", (str(asset_id), text, data.version + 1, timestamp))
        return {**payload, "id": str(asset_id), "version": data.version + 1, "updated_at": timestamp}

def delete_asset(asset_id: UUID, version: int):
    with connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        existing = conn.execute("SELECT * FROM assets WHERE id=?", (str(asset_id),)).fetchone()
        if not existing:
            raise HTTPException(404, "등록된 자산을 찾을 수 없습니다.")
        if existing["version"] != version:
            raise HTTPException(409, "다른 화면에서 자산이 바뀌었습니다. 새로고침 후 다시 확인해 주세요.")
        conn.execute("INSERT INTO asset_history(asset_id, operation, payload, version, created_at) VALUES (?, 'delete', ?, ?, ?)", (str(asset_id), existing["payload"], version, now()))
        conn.execute("DELETE FROM assets WHERE id=?", (str(asset_id),))

def dashboard(owner: Literal["together", "me", "partner"]):
    all_assets = list_assets()
    scoped = [a for a in all_assets if owner == "together" or a["owner"] == owner]
    assets = [a for a in scoped if a["pocket"] != "debt"]
    total = sum(a["amount"] for a in assets)
    debt = sum(a["amount"] for a in scoped if a["pocket"] == "debt")
    retirement = sum(a["amount"] for a in assets if a["pocket"] == "retirement")
    cash = sum(a["amount"] for a in assets if a["pocket"] == "cash")
    return {"assets": assets, "debts": [a for a in scoped if a["pocket"] == "debt"], "total": total, "debt": debt, "net": total - debt, "retirement": retirement, "cash": cash, "financial": retirement + cash, "property": sum(a["amount"] for a in assets if a["pocket"] == "property"), "count": len(scoped), "unclassified": sum(a["amount"] for a in assets if a["assetClass"] == "mixed"), "as_of": min((a["as_of"] for a in scoped), default=None)}
