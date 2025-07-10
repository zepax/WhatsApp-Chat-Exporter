"""
Database optimization utilities for WhatsApp Chat Exporter.
Provides connection pooling, query optimization, and performance monitoring.
"""

import sqlite3
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from queue import Queue, Empty
import logging

from .logging_config import get_logger, get_performance_logger

logger = get_logger(__name__)
perf_logger = get_performance_logger()


class SQLiteConnectionPool:
    """Thread-safe connection pool for SQLite databases."""
    
    def __init__(self, database_path: Union[str, Path], pool_size: int = 5):
        """
        Initialize the connection pool.
        
        Args:
            database_path: Path to the SQLite database
            pool_size: Maximum number of connections in the pool
        """
        self.database_path = str(database_path)
        self.pool_size = pool_size
        self._pool = Queue(maxsize=pool_size)
        self._lock = threading.Lock()
        self._created_connections = 0
        
        # Pre-populate pool with connections
        self._initialize_pool()
        
        logger.info(f"Initialized SQLite connection pool for {database_path} with {pool_size} connections")
    
    def _initialize_pool(self) -> None:
        """Initialize the connection pool with optimized connections."""
        for _ in range(self.pool_size):
            conn = self._create_optimized_connection()
            self._pool.put(conn)
            self._created_connections += 1
    
    def _create_optimized_connection(self) -> sqlite3.Connection:
        """Create an optimized SQLite connection."""
        conn = sqlite3.connect(
            self.database_path,
            check_same_thread=False,
            isolation_level=None  # Autocommit mode for better performance
        )
        conn.row_factory = sqlite3.Row  # Enable column access by name
        
        # Apply SQLite performance optimizations
        cursor = conn.cursor()
        
        # Enable WAL mode for better concurrent access
        cursor.execute("PRAGMA journal_mode=WAL")
        
        # Optimize cache and memory settings
        cursor.execute("PRAGMA cache_size=10000")  # 10MB cache
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.execute("PRAGMA mmap_size=268435456")  # 256MB memory mapping
        
        # Optimize synchronization for performance
        cursor.execute("PRAGMA synchronous=NORMAL")
        
        # Enable query planner optimization
        cursor.execute("PRAGMA optimize")
        
        cursor.close()
        return conn
    
    @contextmanager
    def get_connection(self):
        """
        Get a connection from the pool using context manager.
        
        Yields:
            sqlite3.Connection: Database connection
        """
        start_time = time.time()
        conn = None
        
        try:
            # Try to get a connection from the pool
            try:
                conn = self._pool.get_nowait()
            except Empty:
                # Pool is empty, create a new connection if under limit
                with self._lock:
                    if self._created_connections < self.pool_size * 2:  # Allow overflow
                        conn = self._create_optimized_connection()
                        self._created_connections += 1
                    else:
                        # Wait for a connection to become available
                        conn = self._pool.get(timeout=30)
            
            # Test connection health
            try:
                conn.execute("SELECT 1")
            except sqlite3.Error:
                # Connection is stale, create a new one
                conn.close()
                conn = self._create_optimized_connection()
            
            acquisition_time = time.time() - start_time
            perf_logger.debug(
                "Database connection acquired",
                extra={
                    "acquisition_time_seconds": acquisition_time,
                    "pool_size": self._pool.qsize(),
                    "database": self.database_path
                }
            )
            
            yield conn
            
        except Exception as e:
            logger.error(f"Error with database connection: {e}")
            if conn:
                conn.close()
                conn = None
            raise
        finally:
            # Return connection to pool
            if conn:
                try:
                    # Return to pool if space available
                    self._pool.put_nowait(conn)
                except:
                    # Pool is full, close the connection
                    conn.close()
                    with self._lock:
                        self._created_connections -= 1
    
    def close_all(self) -> None:
        """Close all connections in the pool."""
        while not self._pool.empty():
            try:
                conn = self._pool.get_nowait()
                conn.close()
            except Empty:
                break
        
        logger.info(f"Closed all connections in pool for {self.database_path}")


class QueryOptimizer:
    """Query optimization utilities and batch operations."""
    
    @staticmethod
    def create_query_plan(cursor: sqlite3.Cursor, query: str) -> List[Dict[str, Any]]:
        """
        Get the query execution plan for optimization analysis.
        
        Args:
            cursor: Database cursor
            query: SQL query to analyze
            
        Returns:
            List of query plan steps
        """
        explain_query = f"EXPLAIN QUERY PLAN {query}"
        cursor.execute(explain_query)
        
        plan = []
        for row in cursor.fetchall():
            plan.append({
                'selectid': row[0],
                'order': row[1], 
                'from': row[2],
                'detail': row[3]
            })
        
        return plan
    
    @staticmethod
    def analyze_query_performance(cursor: sqlite3.Cursor, query: str, 
                                params: Optional[Tuple] = None) -> Dict[str, Any]:
        """
        Analyze query performance and provide optimization suggestions.
        
        Args:
            cursor: Database cursor
            query: SQL query to analyze
            params: Query parameters
            
        Returns:
            Performance analysis results
        """
        start_time = time.time()
        
        # Get query plan
        plan = QueryOptimizer.create_query_plan(cursor, query)
        
        # Execute query and measure time
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        execution_time = time.time() - start_time
        row_count = len(cursor.fetchall())
        
        # Analyze plan for potential issues
        issues = []
        suggestions = []
        
        for step in plan:
            detail = step['detail'].upper()
            
            # Check for table scans
            if 'SCAN TABLE' in detail:
                issues.append(f"Full table scan detected: {step['detail']}")
                suggestions.append("Consider adding appropriate indexes")
            
            # Check for temporary tables
            if 'USE TEMP B-TREE' in detail:
                issues.append(f"Temporary B-tree created: {step['detail']}")
                suggestions.append("Consider optimizing ORDER BY or GROUP BY clauses")
        
        analysis = {
            'execution_time_seconds': execution_time,
            'row_count': row_count,
            'query_plan': plan,
            'performance_issues': issues,
            'optimization_suggestions': suggestions,
            'rows_per_second': row_count / execution_time if execution_time > 0 else 0
        }
        
        perf_logger.info(
            "Query performance analysis completed",
            extra={
                'query_hash': hash(query),
                'execution_time': execution_time,
                'row_count': row_count,
                'issues_found': len(issues)
            }
        )
        
        return analysis


class BatchQueryExecutor:
    """Efficient batch query execution for bulk operations."""
    
    def __init__(self, connection: sqlite3.Connection, batch_size: int = 1000):
        """
        Initialize batch executor.
        
        Args:
            connection: Database connection
            batch_size: Number of operations per batch
        """
        self.connection = connection
        self.batch_size = batch_size
        self.pending_operations = []
        
    def add_operation(self, query: str, params: Tuple) -> None:
        """
        Add an operation to the batch.
        
        Args:
            query: SQL query
            params: Query parameters
        """
        self.pending_operations.append((query, params))
        
        if len(self.pending_operations) >= self.batch_size:
            self.execute_batch()
    
    def execute_batch(self) -> int:
        """
        Execute all pending operations in a batch.
        
        Returns:
            Number of operations executed
        """
        if not self.pending_operations:
            return 0
        
        start_time = time.time()
        operations_count = len(self.pending_operations)
        
        try:
            cursor = self.connection.cursor()
            
            # Group operations by query type for efficiency
            query_groups = {}
            for query, params in self.pending_operations:
                if query not in query_groups:
                    query_groups[query] = []
                query_groups[query].append(params)
            
            # Execute each group as a batch
            for query, param_list in query_groups.items():
                cursor.executemany(query, param_list)
            
            self.connection.commit()
            
            execution_time = time.time() - start_time
            
            perf_logger.info(
                "Batch operations executed",
                extra={
                    'operations_count': operations_count,
                    'execution_time_seconds': execution_time,
                    'operations_per_second': operations_count / execution_time,
                    'query_types': len(query_groups)
                }
            )
            
            # Clear pending operations
            self.pending_operations.clear()
            
            return operations_count
            
        except Exception as e:
            logger.error(f"Batch execution failed: {e}")
            self.connection.rollback()
            raise
    
    def finalize(self) -> int:
        """
        Execute any remaining operations.
        
        Returns:
            Number of operations executed
        """
        return self.execute_batch()


class IndexOptimizer:
    """Utilities for creating and managing database indexes for optimal performance."""
    
    RECOMMENDED_INDEXES = {
        # Android database indexes
        'android': {
            'messages_timestamp_idx': 'CREATE INDEX IF NOT EXISTS messages_timestamp_idx ON messages (timestamp)',
            'messages_jid_timestamp_idx': 'CREATE INDEX IF NOT EXISTS messages_jid_timestamp_idx ON messages (key_remote_jid, timestamp)',
            'messages_media_type_idx': 'CREATE INDEX IF NOT EXISTS messages_media_type_idx ON messages (media_wa_type) WHERE media_wa_type IS NOT NULL',
            'jid_raw_string_idx': 'CREATE INDEX IF NOT EXISTS jid_raw_string_idx ON jid (raw_string)',
            'receipt_user_message_idx': 'CREATE INDEX IF NOT EXISTS receipt_user_message_idx ON receipt_user (message_row_id)',
        },
        
        # iOS database indexes  
        'ios': {
            'message_timestamp_idx': 'CREATE INDEX IF NOT EXISTS message_timestamp_idx ON ZWAMESSAGE (ZMESSAGEDATE)',
            'message_chat_idx': 'CREATE INDEX IF NOT EXISTS message_chat_idx ON ZWAMESSAGE (ZCHATSESSION)',
            'chat_contact_idx': 'CREATE INDEX IF NOT EXISTS chat_contact_idx ON ZWACHATSESSION (ZCONTACTJID)',
            'message_media_idx': 'CREATE INDEX IF NOT EXISTS message_media_idx ON ZWAMESSAGE (ZMEDIAITEM) WHERE ZMEDIAITEM IS NOT NULL',
        }
    }
    
    @staticmethod
    def create_recommended_indexes(connection: sqlite3.Connection, platform: str) -> None:
        """
        Create recommended indexes for the specified platform.
        
        Args:
            connection: Database connection
            platform: 'android' or 'ios'
        """
        if platform not in IndexOptimizer.RECOMMENDED_INDEXES:
            logger.warning(f"No recommended indexes for platform: {platform}")
            return
        
        cursor = connection.cursor()
        indexes = IndexOptimizer.RECOMMENDED_INDEXES[platform]
        
        created_count = 0
        
        for index_name, create_sql in indexes.items():
            try:
                start_time = time.time()
                cursor.execute(create_sql)
                creation_time = time.time() - start_time
                
                logger.info(f"Created index {index_name} in {creation_time:.2f}s")
                created_count += 1
                
            except sqlite3.Error as e:
                if "already exists" not in str(e).lower():
                    logger.warning(f"Failed to create index {index_name}: {e}")
        
        connection.commit()
        logger.info(f"Created {created_count} indexes for {platform} platform")
    
    @staticmethod
    def analyze_index_usage(connection: sqlite3.Connection) -> List[Dict[str, Any]]:
        """
        Analyze which indexes are being used effectively.
        
        Args:
            connection: Database connection
            
        Returns:
            List of index usage statistics
        """
        cursor = connection.cursor()
        
        # Get index list
        cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL")
        indexes = cursor.fetchall()
        
        usage_stats = []
        
        for index_name, index_sql in indexes:
            try:
                # Get index info
                cursor.execute(f"PRAGMA index_info({index_name})")
                columns = [row[2] for row in cursor.fetchall()]
                
                # Estimate index effectiveness (simplified heuristic)
                cursor.execute(f"PRAGMA index_list({index_name.split('.')[-1] if '.' in index_name else index_name})")
                
                usage_stats.append({
                    'name': index_name,
                    'columns': columns,
                    'sql': index_sql
                })
                
            except sqlite3.Error as e:
                logger.debug(f"Could not analyze index {index_name}: {e}")
        
        return usage_stats


# Global connection pools
_connection_pools: Dict[str, SQLiteConnectionPool] = {}
_pool_lock = threading.Lock()


def get_connection_pool(database_path: Union[str, Path], pool_size: int = 5) -> SQLiteConnectionPool:
    """
    Get or create a connection pool for the specified database.
    
    Args:
        database_path: Path to the SQLite database
        pool_size: Maximum number of connections in the pool
        
    Returns:
        Connection pool instance
    """
    db_path_str = str(database_path)
    
    with _pool_lock:
        if db_path_str not in _connection_pools:
            _connection_pools[db_path_str] = SQLiteConnectionPool(database_path, pool_size)
        
        return _connection_pools[db_path_str]


def close_all_pools() -> None:
    """Close all connection pools."""
    with _pool_lock:
        for pool in _connection_pools.values():
            pool.close_all()
        _connection_pools.clear()


@contextmanager
def optimized_db_connection(database_path: Union[str, Path]):
    """
    Context manager for getting an optimized database connection.
    
    Args:
        database_path: Path to the SQLite database
        
    Yields:
        sqlite3.Connection: Optimized database connection
    """
    pool = get_connection_pool(database_path)
    with pool.get_connection() as conn:
        yield conn


def optimize_database_schema(connection: sqlite3.Connection, platform: str) -> None:
    """
    Apply comprehensive database optimizations.
    
    Args:
        connection: Database connection
        platform: 'android' or 'ios'
    """
    logger.info(f"Optimizing database schema for {platform} platform")
    
    # Create recommended indexes
    IndexOptimizer.create_recommended_indexes(connection, platform)
    
    # Update table statistics
    cursor = connection.cursor()
    cursor.execute("ANALYZE")
    
    # Optimize database structure
    cursor.execute("PRAGMA optimize")
    
    connection.commit()
    logger.info("Database optimization completed")