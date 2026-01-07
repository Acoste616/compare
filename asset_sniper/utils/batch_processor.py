"""
Batch Processor for Large CSV Files

Handles 100k+ records by processing in chunks to avoid memory issues.

Features:
- Chunked CSV reading (pandas)
- Progress tracking
- Error handling
- Memory-efficient processing

Based on: BIBLE v1.0
Author: BigDInc Team
"""

import pandas as pd
from pathlib import Path
from typing import Callable, Dict
import logging

logger = logging.getLogger(__name__)


class BatchProcessor:
    """
    Batch processor for large CSV files.

    Processes CSV in chunks to handle 100k+ rows without memory issues.

    Usage:
        processor = BatchProcessor(chunk_size=10000)
        stats = processor.process_large_csv(
            'input.csv',
            'output.csv',
            processor_func=lambda df: my_processing_function(df)
        )
    """

    def __init__(self, chunk_size: int = 10000):
        """
        Initialize batch processor.

        Args:
            chunk_size: Number of rows per chunk (default: 10,000)
        """
        self.chunk_size = chunk_size
        logger.info(f"[BATCH] Initialized with chunk_size={chunk_size}")

    def process_large_csv(
        self,
        input_path: str,
        output_path: str,
        processor_func: Callable[[pd.DataFrame], pd.DataFrame]
    ) -> Dict:
        """
        Process large CSV file in chunks.

        Args:
            input_path: Path to input CSV file
            output_path: Path to output CSV file
            processor_func: Function that processes DataFrame chunk
                           Must accept DataFrame and return processed DataFrame

        Returns:
            Statistics dictionary:
            {
                'total_rows': int,
                'processed_rows': int,
                'chunks_processed': int,
                'errors': list
            }
        """
        logger.info(f"[BATCH] Processing {input_path} -> {output_path}")
        logger.info(f"[BATCH] Chunk size: {self.chunk_size} rows")

        stats = {
            'total_rows': 0,
            'processed_rows': 0,
            'chunks_processed': 0,
            'errors': []
        }

        # Process in chunks
        first_chunk = True

        try:
            for chunk_df in pd.read_csv(input_path, chunksize=self.chunk_size):
                stats['total_rows'] += len(chunk_df)
                stats['chunks_processed'] += 1

                chunk_num = stats['chunks_processed']
                logger.info(f"[BATCH] Processing chunk {chunk_num} ({len(chunk_df)} rows)...")

                try:
                    # Process chunk
                    processed_df = processor_func(chunk_df)
                    stats['processed_rows'] += len(processed_df)

                    # Save chunk (append mode after first chunk)
                    mode = 'w' if first_chunk else 'a'
                    header = first_chunk
                    processed_df.to_csv(output_path, mode=mode, header=header, index=False)

                    first_chunk = False

                    logger.info(f"[BATCH] ✓ Chunk {chunk_num} complete: {len(processed_df)} rows processed")

                except Exception as e:
                    error_msg = f"Error in chunk {chunk_num}: {e}"
                    stats['errors'].append(error_msg)
                    logger.error(f"[BATCH] ❌ {error_msg}")

            # Summary
            logger.info("")
            logger.info("=== BATCH PROCESSING COMPLETE ===")
            logger.info(f"Total rows read: {stats['total_rows']}")
            logger.info(f"Rows processed: {stats['processed_rows']}")
            logger.info(f"Chunks processed: {stats['chunks_processed']}")
            logger.info(f"Errors: {len(stats['errors'])}")

            if stats['errors']:
                logger.warning("Errors encountered:")
                for error in stats['errors']:
                    logger.warning(f"  - {error}")

            return stats

        except Exception as e:
            logger.error(f"[BATCH] Fatal error: {e}")
            raise


# === CLI TEST ===

if __name__ == "__main__":
    import tempfile
    import os

    print("=== Batch Processor Test ===\n")

    # Create test CSV with 25k rows
    test_data = {
        'name': [f'Company_{i}' for i in range(25000)],
        'value': list(range(25000))
    }
    df_test = pd.DataFrame(test_data)

    # Save to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        input_path = f.name
        df_test.to_csv(input_path, index=False)

    output_path = input_path.replace('.csv', '_output.csv')

    # Define processor function
    def process_chunk(df):
        """Simple processing: double the value."""
        df['value'] = df['value'] * 2
        return df

    # Process in batches
    processor = BatchProcessor(chunk_size=10000)
    stats = processor.process_large_csv(input_path, output_path, process_chunk)

    print("\nProcessing Statistics:")
    print(f"  Total rows: {stats['total_rows']}")
    print(f"  Processed rows: {stats['processed_rows']}")
    print(f"  Chunks: {stats['chunks_processed']}")
    print(f"  Errors: {len(stats['errors'])}")

    # Verify output
    df_output = pd.read_csv(output_path)
    print(f"\nOutput file rows: {len(df_output)}")
    print(f"Sample values (first 5): {df_output['value'].head().tolist()}")

    # Cleanup
    os.unlink(input_path)
    os.unlink(output_path)

    print("\n✅ Batch Processor Test Complete!")
