import os
from dotenv import load_dotenv
from pinecone import Pinecone
import logging
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def clear_pinecone_index(confirm=False):
    """
    Delete all vectors from the Pinecone index specified in the environment variables.
    
    Args:
        confirm (bool): If True, skip confirmation prompt
    """
    try:
        # Load environment variables
        load_dotenv()
        
        # Get environment variables
        api_key = os.getenv("PINECONE_API_KEY")
        index_name = os.getenv("PINECONE_INDEX_NAME", "dev-portal-chatbot")
        
        if not api_key:
            raise ValueError("PINECONE_API_KEY environment variable is required")
            
        # Initialize Pinecone
        pc = Pinecone(api_key=api_key)
        
        # Get the index
        index = pc.Index(index_name)
        
        # Get current stats
        stats = index.describe_index_stats()
        vector_count = stats.total_vector_count
        
        if vector_count == 0:
            logger.info("Index is already empty. No vectors to delete.")
            return
            
        # Confirm deletion if not auto-confirmed
        if not confirm:
            response = input(f"Are you sure you want to delete all {vector_count} vectors from index '{index_name}'? (y/N): ")
            if response.lower() != 'y':
                logger.info("Operation cancelled.")
                return
        
        # Delete all vectors
        logger.info(f"Deleting all vectors from index '{index_name}'...")
        index.delete(delete_all=True)
        
        # Verify deletion
        new_stats = index.describe_index_stats()
        if new_stats.total_vector_count == 0:
            logger.info("Successfully deleted all vectors from the index.")
        else:
            logger.warning(f"Some vectors may remain. Current count: {new_stats.total_vector_count}")
            
    except Exception as e:
        logger.error(f"Error clearing Pinecone index: {e}")
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clear all vectors from a Pinecone index")
    parser.add_argument("--force", "-f", action="store_true", help="Skip confirmation prompt")
    args = parser.parse_args()
    
    clear_pinecone_index(confirm=args.force) 