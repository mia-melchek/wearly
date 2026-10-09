from pathlib import Path
from collections import deque
import numpy as np
import pandas as pd
import torch
import open_clip

MODEL_ID = 'hf-hub:Marqo/marqo-fashionSigLIP'


def color_descriptor(image):
    """Match the color preprocessing used in the Colab notebook."""
    rgb = np.asarray(image.convert('RGB').resize((96, 96)), dtype=np.float32) / 255.0
    near_white = (rgb.min(axis=2) > 0.92) & (np.ptp(rgb, axis=2) < 0.04)
    height, width = near_white.shape
    background = np.zeros_like(near_white, dtype=bool)
    queue = deque()
    borders = ([(0, x) for x in range(width)]
               + [(height - 1, x) for x in range(width)]
               + [(y, 0) for y in range(height)]
               + [(y, width - 1) for y in range(height)])
    for y, x in borders:
        if near_white[y, x] and not background[y, x]:
            background[y, x] = True
            queue.append((y, x))
    while queue:
        y, x = queue.popleft()
        for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
            if (0 <= ny < height and 0 <= nx < width
                    and near_white[ny, nx] and not background[ny, nx]):
                background[ny, nx] = True
                queue.append((ny, nx))
    pixels = rgb[~background]
    if len(pixels) < 100:
        pixels = rgb.reshape(-1, 3)
    histogram, _ = np.histogramdd(pixels, bins=(8, 8, 8),
                                range=((0, 1), (0, 1), (0, 1)))
    histogram = histogram.ravel()
    histogram /= histogram.sum()
    return np.sqrt(histogram).astype(np.float32)


class SearchEngine:
    """Search the saved FashionSigLIP catalog with optional color preferences."""

    def __init__(self):
        data_dir = Path(__file__).resolve().parent / 'data'
        # These three files were exported together in catalog row order.
        self.catalog_products = pd.read_parquet(data_dir / 'catalog_products.parquet')
        self.catalog_products['id'] = self.catalog_products['id'].astype(str)
        self.catalog_embeddings = torch.load(
            data_dir / 'catalog_embeddings.pt', map_location='cpu', weights_only=True
        ).float()
        self.catalog_colors = np.load(data_dir / 'catalog_colors.npy', allow_pickle=False)
        products = self.catalog_products
        required = {'id', 'title', 'price_min_usd', 'url', 'featured_image_url'}
        if not required.issubset(products.columns) or not products['id'].is_unique:
            raise ValueError('Invalid catalog columns or duplicate product IDs.')
        if self.catalog_embeddings.shape != (len(products), 768):
            raise ValueError('Expected FashionSigLIP embeddings with shape (products, 768).')
        if self.catalog_colors.shape != (len(products), 512):
            raise ValueError('Color descriptors do not match the catalog.')
        if not torch.isfinite(self.catalog_embeddings).all() or not np.isfinite(self.catalog_colors).all():
            raise ValueError('Invalid embedding or color values.')
        if not torch.allclose(self.catalog_embeddings.norm(dim=1),
                              torch.ones(len(products)), atol=1e-4):
            raise ValueError('Embeddings must be normalized.')
        products['price_min_usd'] = pd.to_numeric(products['price_min_usd'], errors='raise')
        prices = products['price_min_usd'].to_numpy()
        if not np.isfinite(prices).all() or (prices <= 0).any():
            raise ValueError('Invalid catalog prices.')

        # Optional variant data enables explicit color selection.
        self.variant_colors = None
        variants_path = data_dir / 'selected_variants.parquet'
        if variants_path.exists():
            variants = pd.read_parquet(variants_path)
            if not {'product_id', 'color'}.issubset(variants.columns):
                raise ValueError('Variants require product_id and color columns.')
            variants = variants.dropna(subset=['product_id', 'color']).copy()
            variants['product_id'] = variants['product_id'].astype(str)
            variants['color_key'] = variants['color'].astype(str).str.strip().str.casefold()
            variants = variants[variants['color_key'].ne('') & variants['product_id'].isin(products['id'])]
            self.variant_colors = variants
        self.device = 'cpu'
        self.model, _, self.preprocess = open_clip.create_model_and_transforms(
            MODEL_ID, device=self.device
        )
        self.model.eval()

    @property
    def available_colors(self):
        """Return actual variant color labels, with case differences merged."""
        if self.variant_colors is None:
            return []
        return sorted(self.variant_colors['color_key'].unique().tolist())

    def encode_query(self, query_image):
        """Encode once so changing controls does not rerun the model."""
        tensor = self.preprocess(query_image.convert('RGB')).unsqueeze(0).to(self.device)
        with torch.inference_mode():
            embedding = self.model.encode_image(tensor, normalize=True).cpu().float().squeeze(0)
        return embedding, color_descriptor(query_image)

    def search(self, query_image, max_price, top_k=10, exclude_product_id=None,
               color_weight=0.0, desired_color=None, candidate_k=50, query_features=None):
        """Rank visually similar items, optionally reranking or filtering by color."""
        if not np.isfinite(max_price) or max_price < 0:
            raise ValueError('Budget must be finite and nonnegative.')
        if isinstance(top_k, bool) or not isinstance(top_k, int) or top_k < 1:
            raise ValueError('top_k must be a positive integer.')
        if not np.isfinite(color_weight) or not 0 <= color_weight <= 1:
            raise ValueError('Color weight must be between zero and one.')
        if isinstance(candidate_k, bool) or not isinstance(candidate_k, int) or candidate_k < 1:
            raise ValueError('candidate_k must be a positive integer.')
        eligible = self.catalog_products['price_min_usd'] <= max_price
        if exclude_product_id is not None:
            eligible &= self.catalog_products['id'] != str(exclude_product_id)
        if desired_color is not None:
            if self.variant_colors is None:
                raise ValueError('Add data/selected_variants.parquet to select a specific color.')
            key = desired_color.strip().casefold()
            ids = self.variant_colors.loc[self.variant_colors['color_key'].eq(key), 'product_id']
            eligible &= self.catalog_products['id'].isin(ids)
        indices = torch.tensor(np.flatnonzero(eligible.to_numpy()), dtype=torch.long)
        if indices.numel() == 0:
            results = self.catalog_products.iloc[:0].copy()
            for name in ('similarity', 'color_similarity', 'final_score'):
                results[name] = pd.Series(dtype=float)
            return results
        embedding, colors = query_features if query_features is not None else self.encode_query(query_image)
        visual = self.catalog_embeddings[indices] @ embedding
        count = min(max(candidate_k, top_k), len(indices))
        scores, positions = torch.topk(visual, k=count)
        candidates = indices[positions].numpy()
        visual = scores.numpy()
        color_scores = np.clip(self.catalog_colors[candidates] @ colors, 0, 1)
        # A specific color filters variants; it does not favor the source image color.
        weight = 0.0 if desired_color is not None else color_weight
        final = (1 - weight) * np.clip((visual + 1) / 2, 0, 1) + weight * color_scores
        order = np.argsort(-final, kind='stable')[:top_k]
        results = self.catalog_products.iloc[candidates[order]].copy()
        results['similarity'] = visual[order]
        results['color_similarity'] = color_scores[order]
        results['final_score'] = final[order]
        return results.reset_index(drop=True)


if __name__ == '__main__':
    engine = SearchEngine()
    print('Search engine is ready. Loaded products:', len(engine.catalog_products))
