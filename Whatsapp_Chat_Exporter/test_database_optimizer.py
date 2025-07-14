"""
Tests for database optimization utilities.
"""

import sqlite3

import pytest

from Whatsapp_Chat_Exporter.database_optimizer import (
    BatchQueryExecutor,
    IndexOptimizer,
    QueryOptimizer,
    SQLiteConnectionPool,
    get_connection_pool,
    optimize_database_schema,
    optimized_db_connection,
)


class TestSQLiteConnectionPool:
    """Tests for SQLite connection pool."""

    def test_connection_pool_creation(self, tmp_path):
        """Test connection pool creation and basic operations."""
        db_path = tmp_path / "test.db"

        # Create a test database
        with sqlite3.connect(db_path) as conn:
            conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")
            conn.execute("INSERT INTO test (name) VALUES ('test')")
            conn.commit()

        # Test pool creation
        pool = SQLiteConnectionPool(db_path, pool_size=3)
        assert pool.pool_size == 3

        # Test connection retrieval
        with pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM test")
            result = cursor.fetchone()
            assert result[0] == 1

        # Test pool cleanup
        pool.close_all()

    def test_connection_pool_reuse(self, tmp_path):
        """Test connection reuse in pool."""
        db_path = tmp_path / "test.db"

        with sqlite3.connect(db_path) as conn:
            conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")
            conn.commit()

        pool = SQLiteConnectionPool(db_path, pool_size=2)

        # Get multiple connections
        connections = []
        for _ in range(3):
            with pool.get_connection() as conn:
                connections.append(id(conn))

        # Should reuse connections
        assert len(set(connections)) <= 2

        pool.close_all()

    def test_optimized_db_connection_context_manager(self, tmp_path):
        """Test optimized database connection context manager."""
        db_path = tmp_path / "test.db"

        with sqlite3.connect(db_path) as conn:
            conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, data TEXT)")
            conn.commit()

        # Test context manager
        with optimized_db_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO test (data) VALUES ('test')")
            cursor.execute("SELECT COUNT(*) FROM test")
            result = cursor.fetchone()
            assert result[0] == 1


class TestQueryOptimizer:
    """Tests for query optimization utilities."""

    def test_query_plan_analysis(self, tmp_path):
        """Test query execution plan analysis."""
        db_path = tmp_path / "test.db"

        with sqlite3.connect(db_path) as conn:
            conn.execute(
                "CREATE TABLE messages (id INTEGER PRIMARY KEY, content TEXT, timestamp INTEGER)"
            )
            conn.execute("CREATE INDEX idx_timestamp ON messages (timestamp)")

            # Insert test data
            for i in range(100):
                conn.execute(
                    "INSERT INTO messages (content, timestamp) VALUES (?, ?)",
                    (f"message_{i}", i),
                )
            conn.commit()

            cursor = conn.cursor()

            # Test query plan analysis
            query = "SELECT * FROM messages WHERE timestamp > 50"
            plan = QueryOptimizer.create_query_plan(cursor, query)

            assert isinstance(plan, list)
            assert len(plan) > 0
            assert "detail" in plan[0]

    def test_query_performance_analysis(self, tmp_path):
        """Test query performance analysis."""
        db_path = tmp_path / "test.db"

        with sqlite3.connect(db_path) as conn:
            conn.execute("CREATE TABLE test_table (id INTEGER PRIMARY KEY, data TEXT)")

            # Insert test data
            for i in range(50):
                conn.execute("INSERT INTO test_table (data) VALUES (?)", (f"data_{i}",))
            conn.commit()

            cursor = conn.cursor()

            # Analyze a simple query
            query = "SELECT COUNT(*) FROM test_table"
            analysis = QueryOptimizer.analyze_query_performance(cursor, query)

            assert "execution_time_seconds" in analysis
            assert "row_count" in analysis
            assert "query_plan" in analysis
            assert analysis["execution_time_seconds"] >= 0
            assert analysis["row_count"] >= 0


class TestBatchQueryExecutor:
    """Tests for batch query execution."""

    def test_batch_operations(self, tmp_path):
        """Test batch query execution."""
        db_path = tmp_path / "test.db"

        with sqlite3.connect(db_path) as conn:
            conn.execute("CREATE TABLE batch_test (id INTEGER PRIMARY KEY, value TEXT)")
            conn.commit()

            executor = BatchQueryExecutor(conn, batch_size=5)

            # Add operations to batch
            for i in range(12):
                executor.add_operation(
                    "INSERT INTO batch_test (value) VALUES (?)", (f"value_{i}",)
                )

            # Finalize remaining operations
            remaining = executor.finalize()
            assert remaining == 2  # 12 % 5 = 2 remaining

            # Verify data was inserted
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM batch_test")
            result = cursor.fetchone()
            assert result[0] == 12


class TestIndexOptimizer:
    """Tests for index optimization."""

    def test_create_recommended_indexes(self, tmp_path):
        """Test creation of recommended indexes."""
        db_path = tmp_path / "test.db"

        with sqlite3.connect(db_path) as conn:
            # Create Android-like schema
            conn.execute(
                """
                CREATE TABLE messages (
                    _id INTEGER PRIMARY KEY,
                    key_remote_jid TEXT,
                    timestamp INTEGER,
                    media_wa_type INTEGER
                )
            """
            )
            conn.execute(
                """
                CREATE TABLE jid (
                    _id INTEGER PRIMARY KEY,
                    raw_string TEXT
                )
            """
            )
            conn.commit()

            # Create recommended indexes
            IndexOptimizer.create_recommended_indexes(conn, "android")

            # Verify indexes were created
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND sql IS NOT NULL"
            )
            indexes = [row[0] for row in cursor.fetchall()]

            # Should contain some of our recommended indexes
            expected_indexes = ["messages_timestamp_idx", "jid_raw_string_idx"]
            for idx in expected_indexes:
                assert idx in indexes

    def test_index_usage_analysis(self, tmp_path):
        """Test index usage analysis."""
        db_path = tmp_path / "test.db"

        with sqlite3.connect(db_path) as conn:
            conn.execute("CREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT)")
            conn.execute("CREATE INDEX idx_name ON test_table (name)")
            conn.commit()

            usage_stats = IndexOptimizer.analyze_index_usage(conn)

            assert isinstance(usage_stats, list)
            # Should include our created index
            index_names = [stat["name"] for stat in usage_stats]
            assert "idx_name" in index_names


class TestDatabaseSchemaOptimization:
    """Tests for comprehensive database optimization."""

    def test_optimize_database_schema(self, tmp_path):
        """Test comprehensive database schema optimization."""
        db_path = tmp_path / "test.db"

        with sqlite3.connect(db_path) as conn:
            # Create minimal Android schema
            conn.execute(
                """
                CREATE TABLE messages (
                    _id INTEGER PRIMARY KEY,
                    key_remote_jid TEXT,
                    timestamp INTEGER
                )
            """
            )
            conn.execute(
                """
                CREATE TABLE jid (
                    _id INTEGER PRIMARY KEY,
                    raw_string TEXT
                )
            """
            )
            conn.commit()

            # Apply optimizations
            optimize_database_schema(conn, "android")

            # Verify indexes were created
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND sql IS NOT NULL"
            )
            indexes = cursor.fetchall()

            # Should have created some indexes
            assert len(indexes) > 0

    def test_global_connection_pool(self, tmp_path):
        """Test global connection pool functionality."""
        db_path = tmp_path / "test.db"

        with sqlite3.connect(db_path) as conn:
            conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")
            conn.commit()

        # Get pool through global function
        pool1 = get_connection_pool(db_path, pool_size=3)
        pool2 = get_connection_pool(db_path, pool_size=3)

        # Should return the same pool instance
        assert pool1 is pool2

        # Test connection usage
        with pool1.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1


def test_performance_monitoring_integration(tmp_path):
    """Test that performance monitoring works with optimizations."""
    db_path = tmp_path / "test.db"

    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE perf_test (id INTEGER PRIMARY KEY, data TEXT)")

        # Insert some data
        for i in range(100):
            conn.execute("INSERT INTO perf_test (data) VALUES (?)", (f"data_{i}",))
        conn.commit()

    # Test optimized connection with performance monitoring
    with optimized_db_connection(db_path) as conn:
        cursor = conn.cursor()

        # This should be logged by performance monitoring
        analysis = QueryOptimizer.analyze_query_performance(
            cursor, "SELECT COUNT(*) FROM perf_test"
        )

        assert analysis["execution_time_seconds"] >= 0
        assert analysis["row_count"] == 1  # COUNT returns 1 row


if __name__ == "__main__":
    pytest.main([__file__])
