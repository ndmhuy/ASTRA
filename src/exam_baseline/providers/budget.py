"""Persistent application cost guard, independent of provider account billing limits."""

import json
import sqlite3
from decimal import ROUND_CEILING, ROUND_FLOOR, Decimal
from pathlib import Path
from uuid import uuid4

from exam_baseline.core.contracts import ProviderError

MICRO_USD = 1_000_000


class SpendLedger:
    """Atomically reserve estimated worst-case cost across processes and retries.

    A UTF-8/JSON byte bound plus 2048 tokens of overhead conservatively estimates
    input; output reserves max_tokens. Unknown/timeout calls retain the reservation.
    This is a local estimate guard, not an Anthropic invoice/account-level cap.
    """

    def __init__(self, settings):
        self.path = Path(settings.spend_ledger)
        self.budget_id = settings.spend_budget_id
        self.limit = int(
            (Decimal(str(settings.spend_limit_usd)) * MICRO_USD).to_integral_value(
                rounding=ROUND_FLOOR
            )
        )
        self.in_price = Decimal(str(settings.input_price_per_million))
        self.out_price = Decimal(str(settings.output_price_per_million))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS provider_spend "
                "(id TEXT PRIMARY KEY, budget_id TEXT NOT NULL, micro_usd INTEGER NOT NULL, "
                "state TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP)"
            )

    def connect(self):
        return sqlite3.connect(self.path, timeout=15)

    def amount(self, incoming, outgoing):
        # USD per million tokens numerically equals micro-USD per token.
        return int(
            (incoming * self.in_price + outgoing * self.out_price).to_integral_value(
                rounding=ROUND_CEILING
            )
        )

    def reserve(self, payload, max_output_tokens):
        incoming = len(json.dumps(payload, ensure_ascii=True).encode("utf-8")) + 2048
        amount = self.amount(incoming, max_output_tokens)
        reservation = uuid4().hex
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            used = db.execute(
                "SELECT COALESCE(SUM(micro_usd),0) FROM provider_spend WHERE budget_id=?",
                (self.budget_id,),
            ).fetchone()[0]
            if used + amount > self.limit:
                raise ProviderError(
                    "spend_limit_exceeded",
                    "ASTRA không gửi thêm request: ngân sách còn lại không đủ cho "
                    f"ước tính tối đa của lượt gọi (trần {self.limit / MICRO_USD:g} USD).",
                )
            db.execute(
                "INSERT INTO provider_spend (id,budget_id,micro_usd,state) VALUES (?,?,?,?)",
                (reservation, self.budget_id, amount, "reserved"),
            )
        return reservation

    def settle(self, reservation, usage=None, *, unbilled=False):
        if unbilled:
            amount, state = 0, "unbilled"
        elif (
            usage is not None and usage.input_tokens is not None and usage.output_tokens is not None
        ):
            amount, state = self.amount(usage.input_tokens, usage.output_tokens), "reported"
        else:
            with self.connect() as db:
                db.execute(
                    "UPDATE provider_spend SET state='unknown' "
                    "WHERE id=? AND budget_id=? AND state='reserved'",
                    (reservation, self.budget_id),
                )
            return
        with self.connect() as db:
            db.execute(
                "UPDATE provider_spend SET micro_usd=?,state=?"
                " WHERE id=? AND budget_id=? AND state='reserved'",
                (amount, state, reservation, self.budget_id),
            )

    def snapshot(self):
        with self.connect() as db:
            rows = db.execute(
                "SELECT state, COALESCE(SUM(micro_usd),0) FROM provider_spend "
                "WHERE budget_id=? GROUP BY state",
                (self.budget_id,),
            ).fetchall()
        totals = dict(rows)
        used = sum(totals.values())
        return {
            "budgetId": self.budget_id,
            "limitUsd": self.limit / MICRO_USD,
            "reportedUsd": totals.get("reported", 0) / MICRO_USD,
            "reservedUsd": (totals.get("reserved", 0) + totals.get("unknown", 0)) / MICRO_USD,
            "unknownUsd": totals.get("unknown", 0) / MICRO_USD,
            "remainingUsd": max(0, self.limit - used) / MICRO_USD,
        }
