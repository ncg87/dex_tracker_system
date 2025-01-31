from typing import List
from datetime import datetime, timedelta

class PostgresSchema:
    @staticmethod
    def get_schema_queries() -> List[str]:
        return [
            # Extensions
            "CREATE EXTENSION IF NOT EXISTS btree_gist",
            
            # Swaps table with range partitioning
            '''
            CREATE TABLE IF NOT EXISTS swaps (
                id TEXT NOT NULL,
                parent_transaction JSONB NOT NULL,
                timestamp INTEGER NOT NULL,
                dex_id TEXT NOT NULL,
                token0_symbol TEXT NOT NULL,
                token1_symbol TEXT NOT NULL,
                token0_id TEXT NOT NULL,
                token1_id TEXT NOT NULL,
                token0_name TEXT NOT NULL,
                token1_name TEXT NOT NULL,
                amount0 TEXT NOT NULL,
                amount1 TEXT NOT NULL,
                amount_usd TEXT NOT NULL,
                sender TEXT NOT NULL,
                recipient TEXT NOT NULL,
                origin TEXT,
                fee_tier INTEGER,
                liquidity TEXT,
                PRIMARY KEY (timestamp, id)
            ) PARTITION BY RANGE (timestamp)
            ''',
            
            # Mints table with range partitioning
            '''
            CREATE TABLE IF NOT EXISTS mints (
                id TEXT NOT NULL,
                parent_transaction JSONB NOT NULL,
                timestamp INTEGER NOT NULL,
                dex_id TEXT NOT NULL,
                token0_symbol TEXT NOT NULL,
                token1_symbol TEXT NOT NULL,
                token0_id TEXT NOT NULL,
                token1_id TEXT NOT NULL,
                token0_name TEXT NOT NULL,
                token1_name TEXT NOT NULL,
                amount0 TEXT NOT NULL,
                amount1 TEXT NOT NULL,
                amount_usd TEXT NOT NULL,
                owner TEXT NOT NULL,
                origin TEXT,
                fee_tier INTEGER,
                liquidity TEXT,
                PRIMARY KEY (timestamp, id)
            ) PARTITION BY RANGE (timestamp)
            ''',
            
            # Burns table with range partitioning
            '''
            CREATE TABLE IF NOT EXISTS burns (
                id TEXT NOT NULL,
                parent_transaction JSONB NOT NULL,
                timestamp INTEGER NOT NULL,
                dex_id TEXT NOT NULL,
                token0_symbol TEXT NOT NULL,
                token1_symbol TEXT NOT NULL,
                token0_id TEXT NOT NULL,
                token1_id TEXT NOT NULL,
                token0_name TEXT NOT NULL,
                token1_name TEXT NOT NULL,
                amount0 TEXT NOT NULL,
                amount1 TEXT NOT NULL,
                amount_usd TEXT NOT NULL,
                owner TEXT NOT NULL,
                origin TEXT,
                fee_tier INTEGER,
                liquidity TEXT,
                PRIMARY KEY (timestamp, id)
            ) PARTITION BY RANGE (timestamp)
            ''',
            # Collects table
            
            
            # Flashed table
            
            # Tokens Metadata table

            '''
            CREATE TABLE IF NOT EXISTS token_metadata (
                id TEXT PRIMARY KEY,          -- Contract address
                symbol TEXT NOT NULL,         -- Token symbol
                name TEXT NOT NULL,           -- Token name
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            '''
            ,
            
            # Create optimized indexes
            '''
            CREATE INDEX IF NOT EXISTS idx_swaps_tokens ON swaps (token0_symbol, token1_symbol);
            CREATE INDEX IF NOT EXISTS idx_swaps_dex ON swaps (dex_id);
            CREATE INDEX IF NOT EXISTS idx_swaps_parent_tx ON swaps USING GIN (parent_transaction);
            CREATE INDEX IF NOT EXISTS idx_swaps_timestamp ON swaps (timestamp DESC);
            CREATE INDEX IF NOT EXISTS idx_swaps_sender ON swaps (sender);
            CREATE INDEX IF NOT EXISTS idx_swaps_recipient ON swaps (recipient);
            
            CREATE INDEX IF NOT EXISTS idx_mints_tokens ON mints (token0_symbol, token1_symbol);
            CREATE INDEX IF NOT EXISTS idx_mints_dex ON mints (dex_id);
            CREATE INDEX IF NOT EXISTS idx_mints_parent_tx ON mints USING GIN (parent_transaction);
            CREATE INDEX IF NOT EXISTS idx_mints_timestamp ON mints (timestamp DESC);
            CREATE INDEX IF NOT EXISTS idx_mints_owner ON mints (owner);
            
            CREATE INDEX IF NOT EXISTS idx_burns_tokens ON burns (token0_symbol, token1_symbol);
            CREATE INDEX IF NOT EXISTS idx_burns_dex ON burns (dex_id);
            CREATE INDEX IF NOT EXISTS idx_burns_parent_tx ON burns USING GIN (parent_transaction);
            CREATE INDEX IF NOT EXISTS idx_burns_timestamp ON burns (timestamp DESC);
            CREATE INDEX IF NOT EXISTS idx_burns_owner ON burns (owner);
            '''
        ]

    @staticmethod
    def get_partition_queries(start_date: datetime, end_date: datetime, interval: timedelta) -> List[str]:
        """Generate partition creation queries for a date range"""
        queries = []
        
        # Round start_date down to the start of its month
        start_date = datetime(start_date.year, start_date.month, 1)
        
        # Round end_date up to the end of its month
        if end_date.month == 12:
            end_date = datetime(end_date.year + 1, 1, 1)
        else:
            end_date = datetime(end_date.year, end_date.month + 1, 1)
        
        current_date = start_date
        
        while current_date < end_date:
            # Calculate next month's start
            if current_date.month == 12:
                next_date = datetime(current_date.year + 1, 1, 1)
            else:
                next_date = datetime(current_date.year, current_date.month + 1, 1)
            
            partition_start = int(current_date.timestamp())
            partition_end = int(next_date.timestamp())
            
            # Create partition names with YYYY_MM format
            partition_suffix = current_date.strftime('%Y_%m')
            
            # Create partitions for each table
            for table in ['swaps', 'mints', 'burns']:
                partition_name = f"{table}_p{partition_suffix}"
                query = f'''
                DO $$ 
                BEGIN 
                    IF NOT EXISTS (
                        SELECT 1
                        FROM pg_class c
                        JOIN pg_namespace n ON n.oid = c.relnamespace
                        WHERE c.relname = '{partition_name}'
                    ) THEN
                        CREATE TABLE {partition_name}
                        PARTITION OF {table}
                        FOR VALUES FROM ({partition_start}) TO ({partition_end});
                    END IF;
                END $$;
                '''
                queries.append(query)
            
            current_date = next_date
        
        return queries