import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import uuid
import os
import logging
from pathlib import Path
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Infer project root dynamically (assuming script is in PROJECT/utils)
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent  # Move up one level from utils to project root
OUTPUT_DIR = PROJECT_ROOT / "data"
OUTPUT_PATH = OUTPUT_DIR / "sales_data.csv"

# Seed for reproducibility
np.random.seed(42)
random.seed(42)

# Configuration dictionary for scalability
CONFIG = {
    "num_records": 1000,
    "start_date": datetime(2024, 1, 1),
    "end_date": datetime(2025, 12, 31),
    "products": [
        {"name": "Laptop Pro", "category": "Electronics", "base_price": 1200.00},
        {"name": "Smartphone X", "category": "Electronics", "base_price": 800.00},
        {
            "name": "Wireless Headphones",
            "category": "Electronics",
            "base_price": 150.00,
        },
        {"name": "Office Chair", "category": "Furniture", "base_price": 200.00},
        {"name": "Desk Lamp", "category": "Furniture", "base_price": 50.00},
        {"name": "Coffee Maker", "category": "Appliances", "base_price": 100.00},
        {"name": "Blender", "category": "Appliances", "base_price": 80.00},
    ],
    "regions": ["North America", "Europe", "Asia", "South America", "Africa"],
    "chunk_size": 10000,  # For large datasets, write in chunks
}


def generate_date_range(start_date: datetime, end_date: datetime) -> List[datetime]:
    """Generate a list of dates between start_date and end_date."""
    return [start_date + timedelta(days=x) for x in range((end_date - start_date).days)]


def generate_sales_data(config: Dict[str, Any]) -> pd.DataFrame:
    """Generate a DataFrame with synthetic sales data."""
    try:
        num_records = config["num_records"]
        date_range = generate_date_range(config["start_date"], config["end_date"])

        data = {
            "order_id": [str(uuid.uuid4()) for _ in range(num_records)],
            "order_date": [
                random.choice(date_range).strftime("%Y-%m-%d")
                for _ in range(num_records)
            ],
            "product": [],
            "category": [],
            "quantity": [random.randint(1, 10) for _ in range(num_records)],
            "unit_price": [],
            "total_price": [],
            "customer_region": [
                random.choice(config["regions"]) for _ in range(num_records)
            ],
        }

        for i in range(num_records):
            product = random.choice(config["products"])
            data["product"].append(product["name"])
            data["category"].append(product["category"])
            price_variation = product["base_price"] * random.uniform(0.9, 1.1)
            data["unit_price"].append(round(price_variation, 2))
            data["total_price"].append(
                round(data["unit_price"][-1] * data["quantity"][i], 2)
            )

        df = pd.DataFrame(data).astype(
            {
                "order_id": str,
                "order_date": str,
                "product": str,
                "category": str,
                "quantity": int,
                "unit_price": float,
                "total_price": float,
                "customer_region": str,
            }
        )

        logger.info(f"Generated {num_records} sales records")
        return df

    except Exception as e:
        logger.error(f"Error generating sales data: {str(e)}")
        raise


def save_to_csv(df: pd.DataFrame, output_path: Path, chunk_size: int) -> None:
    """Save DataFrame to CSV, creating output directory if needed."""
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if len(df) > chunk_size:
            logger.info(f"Writing large dataset in chunks of {chunk_size}")
            df.to_csv(output_path, index=False, chunksize=chunk_size)
        else:
            df.to_csv(output_path, index=False)
        logger.info(f"Sales data saved to {output_path}")

    except Exception as e:
        logger.error(f"Error saving CSV: {str(e)}")
        raise


def main() -> None:
    """Main function to generate and save sales data."""
    try:
        sales_df = generate_sales_data(CONFIG)
        save_to_csv(sales_df, OUTPUT_PATH, CONFIG["chunk_size"])
        logger.info(f"Generated CSV with columns: {list(sales_df.columns)}")

    except Exception as e:
        logger.error(f"Script execution failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()
