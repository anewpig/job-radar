"""Persistent ANN-style vector index for assistant corpus search."""

from __future__ import annotations

from array import array
import json
import random
import sqlite3
from pathlib import Path
from typing import Any, Callable

from ..models import JobListing, MarketSnapshot
from ..sqlite_utils import connect_sqlite
from ..storage import load_snapshot, now_iso
from ..utils import ensure_directory
from .chunks import build_chunks
from .models import KnowledgeChunk
from .retrieval import cosine_similarity, prepare_embedding_text, stable_hash


EmbedTexts = Callable[[list[str]], dict[str, list[float]]]

RUNTIME_SOURCE_REF = "runtime:current_snapshot"
MARKET_HISTORY_SOURCE_REF = "market_history:job_posts"
DEFAULT_BAND_COUNT = 8
DEFAULT_BITS_PER_BAND = 6


def _is_locked_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return "database is locked" in message or "database schema is locked" in message


def _encode_vector(vector: list[float]) -> bytes:
    return array("f", [float(value) for value in vector]).tobytes()


def _decode_vector(blob: bytes) -> list[float]:
    values = array("f")
    values.frombytes(blob)
    return list(values)


def _chunk_key(*, embedding_model: str, source_ref: str, chunk: KnowledgeChunk) -> str:
    return stable_hash(
        {
            "embedding_model": embedding_model,
            "source_ref": source_ref,
            "chunk_id": chunk.chunk_id,
            "source_type": chunk.source_type,
            "label": chunk.label,
            "text": chunk.text,
            "url": chunk.url,
            "metadata": chunk.metadata_items(),
        }
    )


def _source_ref_for_path(path: Path) -> str:
    return f"snapshot_file:{path.resolve()}"


def _snapshot_content_hash(snapshot: MarketSnapshot) -> str:
    return stable_hash(snapshot.to_dict())


def _history_content_hash(rows: list[sqlite3.Row]) -> str:
    payload = [
        (
            str(row["job_url"]),
            str(row["last_seen_at"]),
            int(row["last_crawl_run_id"]),
        )
        for row in rows
    ]
    return stable_hash({"job_posts": payload})


def _indexable_chunks(snapshot: MarketSnapshot) -> list[KnowledgeChunk]:
    return [
        chunk
        for chunk in build_chunks(snapshot=snapshot, resume_profile=None)
        if chunk.source_type != "resume-summary" and not chunk.source_type.startswith("market-")
    ]


class PersistentANNIndex:
    """SQLite-backed persistent vector corpus with random-projection band search."""

    def __init__(
        self,
        *,
        db_path: Path,
        embedding_model: str,
        band_count: int = DEFAULT_BAND_COUNT,
        bits_per_band: int = DEFAULT_BITS_PER_BAND,
    ) -> None:
        self.db_path = db_path
        self.embedding_model = embedding_model
        self.band_count = int(band_count)
        self.bits_per_band = int(bits_per_band)
        ensure_directory(db_path.parent)
        self._planes_cache: dict[int, list[list[list[float]]]] = {}
        self._initialize()

    def sync_runtime_snapshot(
        self,
        *,
        snapshot: MarketSnapshot,
        embed_texts: EmbedTexts,
    ) -> int:
        return self._sync_chunks(
            source_ref=RUNTIME_SOURCE_REF,
            source_kind="runtime_snapshot",
            content_hash=_snapshot_content_hash(snapshot),
            chunks=_indexable_chunks(snapshot),
            embed_texts=embed_texts,
            snapshot_generated_at=snapshot.generated_at,
            query_signature="",
        )

    def sync_snapshot_file(
        self,
        *,
        snapshot_path: Path,
        embed_texts: EmbedTexts,
    ) -> int:
        if not snapshot_path.exists():
            return 0
        snapshot = load_snapshot(snapshot_path)
        if snapshot is None:
            return 0
        return self._sync_chunks(
            source_ref=_source_ref_for_path(snapshot_path),
            source_kind="snapshot_file",
            content_hash=_snapshot_content_hash(snapshot),
            chunks=_indexable_chunks(snapshot),
            embed_texts=embed_texts,
            snapshot_generated_at=snapshot.generated_at,
            query_signature="",
        )

    def sync_snapshot_store(
        self,
        *,
        snapshot_store_dir: Path,
        embed_texts: EmbedTexts,
        max_snapshots: int | None = None,
    ) -> int:
        if not snapshot_store_dir.exists():
            return 0
        indexed = 0
        snapshot_paths = sorted(
            snapshot_store_dir.glob("*.json"),
            key=lambda path: path.stat().st_mtime if path.exists() else 0.0,
            reverse=True,
        )
        if max_snapshots is not None and max_snapshots > 0:
            snapshot_paths = snapshot_paths[: int(max_snapshots)]
        for snapshot_path in snapshot_paths:
            indexed += self.sync_snapshot_file(
                snapshot_path=snapshot_path,
                embed_texts=embed_texts,
            )
        return indexed

    def sync_market_history(
        self,
        *,
        history_db_path: Path,
        embed_texts: EmbedTexts,
        max_rows: int | None = None,
    ) -> int:
        if not history_db_path.exists():
            return 0

        with connect_sqlite(history_db_path, row_factory=sqlite3.Row) as connection:
            table_exists = connection.execute(
                """
                SELECT 1
                FROM sqlite_master
                WHERE type = 'table' AND name = 'job_posts'
                """
            ).fetchone()
            if table_exists is None:
                return 0
            rows = connection.execute(
                """
                SELECT
                    job_url,
                    latest_payload_json,
                    last_seen_at,
                    last_crawl_run_id
                FROM job_posts
                ORDER BY last_seen_at DESC, job_url ASC
                LIMIT ?
                """
                ,
                (int(max_rows) if max_rows is not None and max_rows > 0 else -1,),
            ).fetchall()

        if not rows:
            return 0

        jobs: list[JobListing] = []
        latest_seen_at = ""
        for row in rows:
            payload = json.loads(str(row["latest_payload_json"] or "{}"))
            if not payload:
                continue
            jobs.append(JobListing(**payload))
            latest_seen_at = max(latest_seen_at, str(row["last_seen_at"] or ""))
        if not jobs:
            return 0

        snapshot = MarketSnapshot(
            generated_at=latest_seen_at or now_iso(),
            queries=["market_history_job_posts"],
            role_targets=[],
            jobs=jobs,
            skills=[],
            task_insights=[],
            errors=[],
        )
        return self._sync_chunks(
            source_ref=MARKET_HISTORY_SOURCE_REF,
            source_kind="market_history",
            content_hash=_history_content_hash(rows),
            chunks=_indexable_chunks(snapshot),
            embed_texts=embed_texts,
            snapshot_generated_at=snapshot.generated_at,
            query_signature="market_history",
        )

    def search(
        self,
        *,
        question: str,
        embed_texts: EmbedTexts,
        top_k: int,
        exclude_source_refs: set[str] | None = None,
    ) -> list[KnowledgeChunk]:
        prepared_question = prepare_embedding_text(question)
        if not prepared_question:
            return []
        embeddings = embed_texts([prepared_question])
        query_vector = embeddings.get(prepared_question, [])
        if not query_vector:
            return []
        self._ensure_dimension(len(query_vector))

        candidate_limit = max(top_k * 3, 24)
        band_matches = self._band_hashes(query_vector)
        exclude_source_refs = exclude_source_refs or set()

        try:
            with connect_sqlite(self.db_path, row_factory=sqlite3.Row) as connection:
                if not self._has_chunks(connection):
                    return []
                rows = self._load_candidate_rows(
                    connection=connection,
                    band_matches=band_matches,
                    limit=candidate_limit,
                    exclude_source_refs=exclude_source_refs,
                )
        except sqlite3.OperationalError as exc:
            if _is_locked_error(exc):
                return []
            raise

        scored: list[tuple[float, KnowledgeChunk]] = []
        for row in rows:
            chunk = self._row_to_chunk(row)
            vector = _decode_vector(bytes(row["embedding_blob"]))
            band_hits = int(row["hit_count"] or 0)
            score = cosine_similarity(query_vector, vector) + min(0.12, band_hits * 0.02)
            scored.append((score, chunk))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [chunk for _, chunk in scored[:top_k]]

    def _sync_chunks(
        self,
        *,
        source_ref: str,
        source_kind: str,
        content_hash: str,
        chunks: list[KnowledgeChunk],
        embed_texts: EmbedTexts,
        snapshot_generated_at: str,
        query_signature: str,
    ) -> int:
        try:
            with connect_sqlite(self.db_path, row_factory=sqlite3.Row) as connection:
                current_row = connection.execute(
                    """
                    SELECT content_hash
                    FROM ann_sources
                    WHERE source_ref = ?
                    """,
                    (source_ref,),
                ).fetchone()
                if current_row is not None and str(current_row["content_hash"] or "") == content_hash:
                    return 0
        except sqlite3.OperationalError as exc:
            if _is_locked_error(exc):
                return 0
            raise

        prepared_by_chunk: dict[str, str] = {
            chunk.chunk_id: prepare_embedding_text(chunk.text)
            for chunk in chunks
            if prepare_embedding_text(chunk.text)
        }
        if not prepared_by_chunk:
            self._delete_source(source_ref)
            return 0

        unique_texts: list[str] = []
        seen_texts: set[str] = set()
        for text in prepared_by_chunk.values():
            if text in seen_texts:
                continue
            seen_texts.add(text)
            unique_texts.append(text)
        embeddings = embed_texts(unique_texts)
        if not embeddings:
            return 0

        vector_dimension = len(next(iter(embeddings.values())))
        self._ensure_dimension(vector_dimension)

        try:
            with connect_sqlite(self.db_path) as connection:
                self._delete_source(source_ref, connection=connection)
                for chunk in chunks:
                    prepared_text = prepared_by_chunk.get(chunk.chunk_id)
                    if not prepared_text:
                        continue
                    vector = embeddings.get(prepared_text)
                    if not vector:
                        continue
                    chunk_key = _chunk_key(
                        embedding_model=self.embedding_model,
                        source_ref=source_ref,
                        chunk=chunk,
                    )
                    connection.execute(
                        """
                        INSERT INTO ann_chunks (
                            chunk_key,
                            source_ref,
                            embedding_model,
                            source_type,
                            label,
                            text,
                            url,
                            metadata_json,
                            embedding_blob,
                            snapshot_generated_at,
                            query_signature,
                            created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            chunk_key,
                            source_ref,
                            self.embedding_model,
                            chunk.source_type,
                            chunk.label,
                            chunk.text,
                            chunk.url,
                            json.dumps(chunk.metadata_items(), ensure_ascii=False),
                            sqlite3.Binary(_encode_vector(vector)),
                            snapshot_generated_at,
                            query_signature,
                            now_iso(),
                        ),
                    )
                    for band_index, band_hash in enumerate(self._band_hashes(vector)):
                        connection.execute(
                            """
                            INSERT INTO ann_lsh_bands (
                                chunk_key,
                                band_index,
                                band_hash
                            ) VALUES (?, ?, ?)
                            """,
                            (chunk_key, int(band_index), band_hash),
                        )
                connection.execute(
                    """
                    INSERT INTO ann_sources (
                        source_ref,
                        source_kind,
                        content_hash,
                        updated_at
                    ) VALUES (?, ?, ?, ?)
                    ON CONFLICT(source_ref) DO UPDATE SET
                        source_kind = excluded.source_kind,
                        content_hash = excluded.content_hash,
                        updated_at = excluded.updated_at
                    """,
                    (source_ref, source_kind, content_hash, now_iso()),
                )
                connection.commit()
        except sqlite3.OperationalError as exc:
            if _is_locked_error(exc):
                return 0
            raise
        return len(chunks)

    def _delete_source(
        self,
        source_ref: str,
        *,
        connection: sqlite3.Connection | None = None,
    ) -> None:
        owns_connection = connection is None
        if connection is None:
            connection = connect_sqlite(self.db_path)
        try:
            chunk_rows = connection.execute(
                """
                SELECT chunk_key
                FROM ann_chunks
                WHERE source_ref = ?
                """,
                (source_ref,),
            ).fetchall()
            chunk_keys = [str(row[0]) for row in chunk_rows]
            if chunk_keys:
                placeholders = ",".join("?" for _ in chunk_keys)
                connection.execute(
                    f"DELETE FROM ann_lsh_bands WHERE chunk_key IN ({placeholders})",
                    chunk_keys,
                )
                connection.execute(
                    f"DELETE FROM ann_chunks WHERE chunk_key IN ({placeholders})",
                    chunk_keys,
                )
            connection.execute("DELETE FROM ann_sources WHERE source_ref = ?", (source_ref,))
            if owns_connection:
                connection.commit()
        finally:
            if owns_connection:
                connection.close()

    def _has_chunks(self, connection: sqlite3.Connection) -> bool:
        row = connection.execute("SELECT 1 FROM ann_chunks LIMIT 1").fetchone()
        return row is not None

    def _load_candidate_rows(
        self,
        *,
        connection: sqlite3.Connection,
        band_matches: list[str],
        limit: int,
        exclude_source_refs: set[str],
    ) -> list[sqlite3.Row]:
        band_predicates: list[str] = []
        band_params: list[Any] = []
        for band_index, band_hash in enumerate(band_matches):
            band_predicates.append("(band_index = ? AND band_hash = ?)")
            band_params.extend([int(band_index), band_hash])

        exclude_sql = ""
        exclude_params: list[Any] = []
        if exclude_source_refs:
            placeholders = ",".join("?" for _ in exclude_source_refs)
            exclude_sql = f"AND c.source_ref NOT IN ({placeholders})"
            exclude_params.extend(sorted(exclude_source_refs))

        query = f"""
            WITH band_hits AS (
                SELECT chunk_key, COUNT(*) AS hit_count
                FROM ann_lsh_bands
                WHERE {" OR ".join(band_predicates)}
                GROUP BY chunk_key
            )
            SELECT
                c.chunk_key,
                c.source_type,
                c.label,
                c.text,
                c.url,
                c.metadata_json,
                c.embedding_blob,
                c.snapshot_generated_at,
                COALESCE(b.hit_count, 0) AS hit_count
            FROM ann_chunks c
            LEFT JOIN band_hits b ON b.chunk_key = c.chunk_key
            WHERE c.embedding_model = ?
            {exclude_sql}
            ORDER BY
                hit_count DESC,
                c.snapshot_generated_at DESC,
                c.chunk_key ASC
            LIMIT ?
        """
        return connection.execute(
            query,
            [*band_params, self.embedding_model, *exclude_params, int(limit)],
        ).fetchall()

    def _row_to_chunk(self, row: sqlite3.Row) -> KnowledgeChunk:
        return KnowledgeChunk(
            chunk_id=str(row["chunk_key"]),
            source_type=str(row["source_type"]),
            label=str(row["label"]),
            text=str(row["text"]),
            url=str(row["url"] or ""),
            metadata=json.loads(str(row["metadata_json"] or "{}")),
        )

    def _band_hashes(self, vector: list[float]) -> list[str]:
        planes = self._planes_for_dimension(len(vector))
        hashes: list[str] = []
        for band in planes:
            value = 0
            for plane in band:
                dot_product = sum(left * right for left, right in zip(vector, plane))
                value = (value << 1) | int(dot_product >= 0.0)
            hashes.append(f"{value:0{self.bits_per_band // 4 + 1}x}")
        return hashes

    def _planes_for_dimension(self, dimension: int) -> list[list[list[float]]]:
        cached = self._planes_cache.get(dimension)
        if cached is not None:
            return cached

        seed = 20_260_409 + dimension * 31 + self.band_count * 17 + self.bits_per_band
        rng = random.Random(seed)
        planes: list[list[list[float]]] = []
        for _ in range(self.band_count):
            band_planes: list[list[float]] = []
            for _ in range(self.bits_per_band):
                band_planes.append([rng.uniform(-1.0, 1.0) for _ in range(dimension)])
            planes.append(band_planes)
        self._planes_cache[dimension] = planes
        return planes

    def _ensure_dimension(self, dimension: int) -> None:
        try:
            with connect_sqlite(self.db_path, row_factory=sqlite3.Row) as connection:
                row = connection.execute(
                    """
                    SELECT value
                    FROM ann_metadata
                    WHERE key = 'embedding_dimension'
                    """
                ).fetchone()
                if row is None:
                    connection.execute(
                        """
                        INSERT INTO ann_metadata(key, value)
                        VALUES('embedding_dimension', ?)
                        """,
                        (str(int(dimension)),),
                    )
                    connection.commit()
                    return
                existing_dimension = int(str(row["value"] or "0"))
                if existing_dimension != int(dimension):
                    self._reset_dimension(connection=connection, dimension=dimension)
        except sqlite3.OperationalError as exc:
            if _is_locked_error(exc):
                return
            raise

    def _reset_dimension(
        self,
        *,
        connection: sqlite3.Connection,
        dimension: int,
    ) -> None:
        connection.execute("DELETE FROM ann_lsh_bands")
        connection.execute("DELETE FROM ann_chunks")
        connection.execute("DELETE FROM ann_sources")
        connection.execute("DELETE FROM ann_metadata WHERE key = 'embedding_dimension'")
        connection.execute(
            """
            INSERT INTO ann_metadata(key, value)
            VALUES('embedding_dimension', ?)
            """,
            (str(int(dimension)),),
        )
        connection.commit()

    def _initialize(self) -> None:
        with connect_sqlite(self.db_path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS ann_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL DEFAULT ''
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS ann_sources (
                    source_ref TEXT PRIMARY KEY,
                    source_kind TEXT NOT NULL DEFAULT '',
                    content_hash TEXT NOT NULL DEFAULT '',
                    updated_at TEXT NOT NULL DEFAULT ''
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS ann_chunks (
                    chunk_key TEXT PRIMARY KEY,
                    source_ref TEXT NOT NULL,
                    embedding_model TEXT NOT NULL,
                    source_type TEXT NOT NULL DEFAULT '',
                    label TEXT NOT NULL DEFAULT '',
                    text TEXT NOT NULL DEFAULT '',
                    url TEXT NOT NULL DEFAULT '',
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    embedding_blob BLOB NOT NULL,
                    snapshot_generated_at TEXT NOT NULL DEFAULT '',
                    query_signature TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT ''
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS ann_lsh_bands (
                    chunk_key TEXT NOT NULL,
                    band_index INTEGER NOT NULL,
                    band_hash TEXT NOT NULL DEFAULT '',
                    PRIMARY KEY (chunk_key, band_index),
                    FOREIGN KEY (chunk_key) REFERENCES ann_chunks(chunk_key) ON DELETE CASCADE
                )
                """
            )
            for statement in (
                """
                CREATE INDEX IF NOT EXISTS idx_ann_chunks_source_ref
                ON ann_chunks(source_ref, snapshot_generated_at DESC, chunk_key)
                """,
                """
                CREATE INDEX IF NOT EXISTS idx_ann_chunks_model_generated_at
                ON ann_chunks(embedding_model, snapshot_generated_at DESC, chunk_key)
                """,
                """
                CREATE INDEX IF NOT EXISTS idx_ann_lsh_band_hash
                ON ann_lsh_bands(band_index, band_hash, chunk_key)
                """,
            ):
                connection.execute(statement)
            connection.commit()
