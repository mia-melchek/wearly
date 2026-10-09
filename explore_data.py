import pandas as pd


# 1. Load both tables
products = pd.read_parquet("data/products.parquet")
variants = pd.read_parquet("data/variants.parquet")

print("=== TABLE SIZES ===")
print("Products (rows, columns):", products.shape)
print("Variants (rows, columns):", variants.shape)


# 2. Check that the required columns exist
product_columns = [
    "id",
    "title",
    "product_type",
    "price_min_usd",
    "url",
    "featured_image_url",
]

variant_columns = [
    "product_id",
    "sku",
    "price_usd",
    "in_stock",
    "size",
    "color",
]

missing_product_columns = set(product_columns) - set(products.columns)
missing_variant_columns = set(variant_columns) - set(variants.columns)

if missing_product_columns or missing_variant_columns:
    raise ValueError(
        f"Missing product columns: {missing_product_columns}; "
        f"missing variant columns: {missing_variant_columns}"
    )


# 3. Check product identifiers and links between the tables
print("\n=== IDENTIFIERS AND TABLE RELATIONSHIPS ===")

print("Missing product IDs:", products["id"].isna().sum())
print("Duplicate product IDs:", products["id"].duplicated().sum())
print("Missing variant product IDs:", variants["product_id"].isna().sum())

orphan_variants = variants[
    variants["product_id"].notna()
    & ~variants["product_id"].isin(products["id"])
]

print("Variants with an unknown product ID:", len(orphan_variants))

valid_skus = variants["sku"].dropna().astype("string").str.strip()
valid_skus = valid_skus[valid_skus != ""]

print("Duplicate nonempty SKUs:", valid_skus.duplicated().sum())


# 4. Select the product types for the initial catalog
selected_types = [
    "Top",
    "Blouse",
    "Shirt",
    "T-Shirt",
    "Tank Top",
    "Knit Top",
    "Sleeveless Top",
    "Long Sleeve Top",
    "Crop Top",
    "Cami Top",
    "Halter Top",
    "Button-Down Shirt",
    "Button-Up Shirt",
    "Sweater",
    "Sweatshirt",
    "Hoodie",
]

tops = products[
    products["product_type"].isin(selected_types)
].copy()

top_variants = variants[
    variants["product_id"].isin(tops["id"])
].copy()

print("\n=== SELECTED CATALOG ===")
print("Selected products:", len(tops))
print("Selected variants:", len(top_variants))
print(tops["product_type"].value_counts().to_string())

products_without_variants = tops[
    ~tops["id"].isin(top_variants["product_id"])
]

print("Selected products without variants:", len(products_without_variants))


# 5. Check missing values and empty text
print("\n=== MISSING PRODUCT VALUES ===")
print(tops[product_columns].isna().sum().to_string())

print("\n=== MISSING VARIANT VALUES ===")
print(top_variants[variant_columns].isna().sum().to_string())

print("\n=== EMPTY TEXT FIELDS ===")

for column in ["title", "product_type", "url", "featured_image_url"]:
    empty_count = (
        tops[column]
        .astype("string")
        .str.strip()
        .eq("")
        .sum()
    )
    print(f"Empty product {column}: {empty_count}")

for column in ["sku", "size", "color"]:
    empty_count = (
        top_variants[column]
        .astype("string")
        .str.strip()
        .eq("")
        .sum()
    )
    print(f"Empty variant {column}: {empty_count}")


# 6. Check numeric prices
# These new columns leave the original price fields unchanged.
tops["price_checked"] = pd.to_numeric(
    tops["price_min_usd"], errors="coerce"
)

top_variants["price_checked"] = pd.to_numeric(
    top_variants["price_usd"], errors="coerce"
)

print("\n=== PRICE CHECKS ===")

for label, table in [
    ("Products", tops),
    ("Variants", top_variants),
]:
    prices = table["price_checked"]

    print(f"\n{label}:")
    print("Missing or nonnumeric prices:", prices.isna().sum())
    print("Zero or negative prices:", (prices <= 0).sum())
    print(
        "Infinite prices:",
        prices.isin([float("inf"), float("-inf")]).sum(),
    )
    print(prices.describe().to_string())


# 7. Check URL formatting
# This checks the text format, not whether the page actually loads.
print("\n=== URL FORMAT CHECKS ===")

for column in ["url", "featured_image_url"]:
    valid_format = (
        tops[column]
        .astype("string")
        .str.strip()
        .str.match(r"^https?://[^\s/]+(?:/[^\s]*)?$", na=False)
    )
    print(f"Missing or malformed {column}:", (~valid_format).sum())


# 8. Normalize color labels
top_variants["color_normalized"] = (
    top_variants["color"]
    .astype("string")
    .str.strip()
    .str.lower()
    .str.replace(r"\s+", " ", regex=True)
)

print("\n=== COLOR CHECKS ===")
print(
    "Original distinct color labels:",
    top_variants["color"].nunique(),
)
print(
    "Normalized distinct color labels:",
    top_variants["color_normalized"].nunique(),
)

black_variants = top_variants[
    top_variants["color_normalized"].eq("black").fillna(False)
].copy()

print("Variants labeled exactly black:", len(black_variants))
print(
    "Distinct products offered in black:",
    black_variants["product_id"].nunique(),
)


# 9. Check stock values
print("\n=== STOCK CHECKS ===")
print(top_variants["in_stock"].value_counts(dropna=False).to_string())

# Accept only actual boolean True/False values.
valid_stock_value = top_variants["in_stock"].map(
    lambda value: pd.api.types.is_bool(value)
)

print(
    "Missing or nonboolean stock values:",
    (~valid_stock_value).sum(),
)

in_stock_mask = (
    valid_stock_value
    & top_variants["in_stock"].eq(True).fillna(False)
)

available_variants = top_variants[in_stock_mask].copy()

available_black_variants = available_variants[
    available_variants["color_normalized"].eq("black").fillna(False)
].copy()

print("Variants marked in stock:", len(available_variants))
print(
    "Distinct products with an in-stock variant:",
    available_variants["product_id"].nunique(),
)
print(
    "Distinct products with an in-stock black variant:",
    available_black_variants["product_id"].nunique(),
)


# 10. Inspect recorded update dates
# A product's update date is not necessarily a price-check date.
print("\n=== RECORDED PRODUCT UPDATE DATES ===")

if "updated_at" in tops.columns:
    update_dates = pd.to_datetime(
        tops["updated_at"], errors="coerce", utc=True
    )

    print("Missing or unparseable dates:", update_dates.isna().sum())
    print("Oldest recorded update:", update_dates.min())
    print("Newest recorded update:", update_dates.max())
else:
    print("No updated_at column available.")


# 11. Print a repeatable sample for manual inspection
print("\n=== MANUAL IMAGE AND STORE CHECK ===")

sample_products = tops.sample(
    n=min(5, len(tops)),
    random_state=42,
)

for _, product in sample_products.iterrows():
    print("\nProduct ID:", product["id"])
    print("Title:", product["title"])
    print("Type:", product["product_type"])
    print("Catalog minimum price:", product["price_min_usd"])
    print("Image:", product["featured_image_url"])
    print("Store page:", product["url"])


print("\n=== CHECKS FINISHED ===")
print("Image loading and current store prices still require verification.")
print("Variant-to-image color mapping has not yet been established.")

# Save the selected products and their variants
tops.to_parquet("data/selected_products.parquet", index=False)

top_variants.to_parquet(
    "data/selected_variants.parquet",
    index=False,
)

print("\nSelected catalog saved.")