from pathlib import Path

import pandas as pd

from io import BytesIO

import requests
from PIL import Image


# Resolve paths relative to this script, regardless of the terminal location.
PROJECT_DIR = Path(__file__).resolve().parent
PRODUCTS_PATH = PROJECT_DIR / "data" / "selected_products.parquet"
IMAGES_DIR = PROJECT_DIR / "data" / "images"

def download_image(product_id, image_url):
    """Download and validate one image, then save it as JPEG."""
    image_path = IMAGES_DIR / f"{product_id}.jpg"

    # Skip an existing file only if it can be fully opened.
    if image_path.exists():
        try:
            with Image.open(image_path) as image:
                image.load()
            print(f"Already downloaded: {product_id}")
            return True
        except OSError:
            # Replace the invalid file by downloading the image again.
            pass

    try:
        # Raise an error for failed HTTP responses, such as 404.
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()

        # Decode the downloaded bytes and save a consistent image format.
        with Image.open(BytesIO(response.content)) as image:
            image.load()
            rgb_image = image.convert("RGB")
            rgb_image.save(image_path, format="JPEG", quality=95)

        print(f"Downloaded: {product_id}")
        return True

    except (requests.RequestException, OSError, ValueError) as error:
        # Report the failure without stopping the remaining downloads.
        print(f"Failed: {product_id} — {error}")
        return False
    
def main():
    """Load the selected catalog and inspect a small image-download sample."""
    products = pd.read_parquet(PRODUCTS_PATH)

    # Select all products for the full download.
    sample = products[["id", "title", "featured_image_url"]]

    print(f"Total products: {len(products)}")
    print(f"Products selected for testing: {len(sample)}")
    print(sample.to_string(index=False))

    # Create the images folder if it does not exist.
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    successful = 0

    # Iterate over products; each row provides its ID and image URL.
    for row in sample.itertuples(index=False):
        if download_image(row.id, row.featured_image_url):
            successful += 1

    print(f"\nReady images: {successful}/{len(sample)}")


# Run main only when this file is executed directly.
if __name__ == "__main__":
    main()