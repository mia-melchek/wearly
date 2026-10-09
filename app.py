import html
import io
from pathlib import Path

import pandas as pd
import streamlit as st
from PIL import Image, ImageOps, UnidentifiedImageError
from search_engine import SearchEngine

st.set_page_config(page_title='Wearly — Find your style', page_icon='W', layout='wide')

# Editorial typography, warm neutrals, and generous spacing.
st.markdown('''
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&family=Libre+Caslon+Display&display=swap');
:root {color-scheme: light;}
.stApp {background:#faf9f6; color:#292823; font-family:'DM Sans',sans-serif;}
[data-testid="stHeader"] {background:transparent;}
.block-container {max-width:1280px; padding:2.5rem 3rem 3rem;}
h1,h2,h3 {font-family:'Libre Caslon Display',Georgia,serif!important; font-weight:400!important; color:#292823!important;}
[data-testid="stMarkdownContainer"] p, label {font-family:'DM Sans',sans-serif;}
.wearly-nav {display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #ddd9d0; padding-bottom:22px; margin-bottom:48px;}
.wordmark {font-family:'Libre Caslon Display',Georgia,serif; font-size:clamp(88px,11vw,150px); font-weight:600; color:#201f1b; letter-spacing:-1.7px;}
.nav-note {font-size:10px; letter-spacing:2px; text-transform:uppercase; color:#747267;}
.eyebrow {font-size:10px; letter-spacing:2.2px; text-transform:uppercase; color:#514e45; margin-bottom:20px;}
.hero-title {font-family:'Libre Caslon Display',Georgia,serif; font-size:clamp(72px,8vw,116px); line-height:1.03; letter-spacing:-2px; margin:0 0 24px;}
.hero-copy {max-width:400px; color:#514e45; font-size:16px; line-height:1.8; margin-bottom:24px;}
.hero-foot {font-size:10px; letter-spacing:1.2px; text-transform:uppercase; color:#625c50; margin-top:28px;}
.collage {height:510px; background:#e9e5dc; position:relative; overflow:hidden; margin:0 0 24px;}
.collage img {position:absolute; width:45%; height:78%; object-fit:cover; background:#f1efe9;}
.collage .first {left:7%; top:8%;}
.collage .second {right:6%; top:18%;}
.collage-note {position:absolute; bottom:14px; left:18px; font-size:9px; letter-spacing:1.5px; text-transform:uppercase; color:#5e5b52;}
.section-label {font-size:10px; letter-spacing:2px; text-transform:uppercase; color:#514e45; margin:12px 0 18px;}
.product {margin:0 0 30px;}
.product-image {background:#eeece6; aspect-ratio:3/4; overflow:hidden; margin-bottom:14px;}
.product-image img {width:100%; height:100%; object-fit:contain; transition:transform .3s;}
.product-image:hover img {transform:scale(1.035);}
.product-title {font-size:13px; line-height:1.6; min-height:42px; margin-bottom:8px;}
.product-price {font-size:15px; margin-bottom:9px;}
.product-link {color:#37362f!important; font-size:10px; letter-spacing:1px; text-transform:uppercase; text-decoration:none!important; border-bottom:1px solid #a29a89; padding-bottom:3px;}
.variant-note {font-size:11px; color:#7b766a; margin-bottom:9px;}
.footer {border-top:1px solid #ddd9d0; margin-top:40px; padding-top:20px; display:flex; justify-content:space-between; gap:20px; font-size:10px; color:#8a8579;}
[data-testid="stFileUploader"] {border:1px solid #ded9cf; padding:12px; background:#f5f3ee;}
[data-testid="stFileUploaderDropzone"] {background:#f5f3ee;}
[data-testid="stNumberInput"] input {background:#f5f3ee; color:#292823;}
[data-testid="stSelectbox"] [data-baseweb="select"]>div {background:#f5f3ee; color:#292823;}
[data-testid="stImage"] img {border-radius:0;}
[data-testid="stCaptionContainer"] {color:#625c50;}
hr {border-color:#ddd9d0!important; margin:2rem 0!important;}
@media(max-width:700px) {.block-container{padding:1.5rem 1rem;} .wearly-nav{margin-bottom:30px;} .nav-note{display:none;} .collage{height:290px;} .hero-title{font-size:58px;} .footer{flex-direction:column;}}

html {scroll-behavior:smooth;}
.hero-cta {display:inline-block; background:#302e28; color:#fff!important; padding:17px 30px; text-decoration:none!important; font-size:11px; letter-spacing:1.5px; text-transform:uppercase; margin:6px 0 12px;}
.hero-cta:hover {background:#514c40;}
.scroll-note {text-align:center; font-size:10px; letter-spacing:2px; color:#625c50; padding:35px 0 65px;}
#search-section {scroll-margin-top:50px;}
.hero-title {animation:arrive .85s ease both;}
.collage {animation:arrive 1.1s ease both;}
@keyframes arrive {from {opacity:0; transform:translateY(24px);} to {opacity:1; transform:translateY(0);}}
@supports (animation-timeline: view()) {
 .product {animation:reveal linear both; animation-timeline:view(); animation-range:entry 0% entry 35%;}
 .collage img {animation:drift linear both; animation-timeline:view(); animation-range:exit 0% exit 100%;}
}
@keyframes reveal {from {opacity:0; transform:translateY(30px);} to {opacity:1; transform:translateY(0);}}
@keyframes drift {to {transform:translateY(-35px);}}
@media(prefers-reduced-motion:reduce) {html {scroll-behavior:auto;} .hero-title,.collage,.product,.collage img {animation:none!important;}}
@media(min-width:900px) {.wearly-nav{margin-bottom:65px;} .hero-foot{margin-top:22px;}}

.search-heading {font-family:'Libre Caslon Display',Georgia,serif; font-size:clamp(40px,5vw,64px); color:#24231e; line-height:1.1; margin:8px 0 15px;}
.search-description {font-size:16px; color:#514e45; margin-bottom:24px; line-height:1.7;}
[data-testid="stFileUploader"] {border:2px dashed #aaa18e; padding:24px; background:#eeeae1; border-radius:8px;}
[data-testid="stFileUploaderDropzone"] {min-height:180px; background:#eeeae1;}
[data-testid="stFileUploader"] button {background:#302e28; color:white; padding:12px 24px; border:0;}
[data-testid="stFileUploader"] label p {font-size:19px!important; font-weight:600;}
[data-testid="stButton"] button[kind="primary"] {background:#302e28; border-color:#302e28; min-height:54px; font-size:16px;}
.step-label {font-size:12px; color:#514e45; font-weight:600; margin:20px 0 8px;}
@media(max-width:700px) {.wordmark{font-size:88px;} [data-testid="stFileUploader"]{padding:12px;}}
/* Upload area title */
[data-testid="stFileUploader"] label p {
    font-size: 24px !important;
    font-weight: 600 !important;
}

/* Drag-and-drop instruction */
[data-testid="stFileUploaderDropzone"] span {
    font-size: 22px !important;
}

/* File type and size information */
[data-testid="stFileUploaderDropzone"] small {
    font-size: 15px !important;
}

/* Browse files button */
[data-testid="stFileUploader"] button {
    font-size: 19px !important;
    padding: 16px 30px !important;
}

/* Budget, result count, and color labels */
[data-testid="stNumberInput"] label p,
[data-testid="stSlider"] label p,
[data-testid="stToggle"] label p {
    font-size: 20px !important;
    font-weight: 600 !important;
}
</style>
''', unsafe_allow_html=True)


@st.cache_resource
def load_search_engine():
    """Reuse the existing search engine across control changes."""
    return SearchEngine()


@st.cache_data(show_spinner=False)
def encode_uploaded_image(image_bytes):
    """Encode each uploaded image once."""
    with Image.open(io.BytesIO(image_bytes)) as image:
        query = ImageOps.exif_transpose(image).convert('RGB')
    return load_search_engine().encode_query(query)


@st.cache_data
def read_preview_catalog():
    """Show catalog photography without loading the model on the landing page."""
    catalog = pd.read_parquet(Path(__file__).resolve().parent / 'data' / 'catalog_products.parquet')
    # Prefer understated neutral knitwear for the editorial landing page.
    titles = catalog['title'].fillna('').str.lower()
    neutral = titles.str.contains(r'ivory|cream|beige|taupe|camel|white|black|oatmeal|mocha', regex=True)
    knitwear = titles.str.contains(r'knit|sweater|cardigan', regex=True)
    busy = titles.str.contains(r'flag|graphic|sequin|christmas|halloween|star|leopard|printed|tie.dye', regex=True)
    catalog = catalog.assign(_editorial_score=neutral.astype(int)*3 + knitwear.astype(int)*2 - busy.astype(int)*8)
    return catalog.sort_values('_editorial_score', ascending=False, kind='stable').drop(columns='_editorial_score')


def safe_url(value):
    """Allow only web links and escape them for HTML attributes."""
    value = str(value)
    return html.escape(value, quote=True) if value.startswith(('https://', 'http://')) else ''


def product_card(product, desired_color=None):
    """Render a minimal product card with a real product link."""
    title = html.escape(str(product['title']))
    image_url = safe_url(product['featured_image_url'])
    product_url = safe_url(product['url'])
    note = ''
    if desired_color:
        note = f'<div class="variant-note">Available in {html.escape(desired_color)}</div>'
    link = f'<a class="product-link" href="{product_url}" target="_blank" rel="noopener noreferrer">View piece ↗</a>' if product_url else ''
    st.markdown(f'''<div class="product">
    <div class="product-image"><img src="{image_url}" alt="{title}" loading="lazy"></div>
    <div class="product-title">{title}</div>
    <div class="product-price">From ${float(product['price_min_usd']):.2f}</div>
    {note}{link}</div>''', unsafe_allow_html=True)


st.markdown('<div class="wearly-nav"><span class="wordmark">wearly.</span><span class="nav-note">A little inspiration. A closer match.</span></div>', unsafe_allow_html=True)
left, right = st.columns([1, 1.15], gap='large')
with left:
    st.markdown('''<div class="eyebrow">Discover your next favorite</div>
    <div class="hero-title">Your style.<br>A new find.</div>
    <div class="hero-copy">A look you love, a budget that fits.<br>Upload a photo and discover similar pieces.</div>
    <a class="hero-cta" href="#search-section" target="_self">Find my next favorite ↘</a><div class="hero-foot">Inspired by you · Found with Wearly</div>''', unsafe_allow_html=True)
with right:
    try:
        preview = read_preview_catalog()
        # Use existing catalog photos rather than unrelated decorative imagery.
        preferred = preview[preview['title'].str.contains('knit|sweater|cardigan', case=False, na=False)]
        photos = (preferred if len(preferred) >= 2 else preview).head(2)
        urls = [safe_url(u) for u in photos['featured_image_url']]
        if len(urls) == 2:
            st.markdown(f'''<div class="collage"><img class="first" src="{urls[0]}" alt="A piece from the catalog"><img class="second" src="{urls[1]}" alt="Another catalog style"><span class="collage-note">The Wearly edit / 01</span></div>''', unsafe_allow_html=True)
    except (OSError, ValueError, ImportError):
        st.markdown('<div class="collage"><span class="collage-note">Your next favorite starts here.</span></div>', unsafe_allow_html=True)

st.markdown('<div class="scroll-note">SCROLL TO DISCOVER ↓</div><div id="search-section"></div>', unsafe_allow_html=True)
st.divider()
controls = st.container()
collection = st.container()
with controls:
    st.markdown('<div class="section-label">01 / Your personal style search</div><div class="search-heading">Find something you love.</div><div class="search-description">Upload a clothing photo, set your budget, and discover similar pieces.<br>Turn on color matching when the shade matters too.</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader('1. Upload your inspiration', type=['jpg', 'jpeg', 'png'], help='Choose a clear clothing photo. A close-up of the garment works best.')
    budget_column, count_column, color_column = st.columns(3, gap='large')
    with budget_column:
        max_price = st.number_input('2. Set your budget · USD', min_value=0.0, value=50.0, step=5.0)
    with count_column:
        top_k = st.select_slider('Number of results', options=[3, 6, 9, 12, 15, 18], value=9)
    with color_column:
        prefer_color = st.toggle('3. Prefer a matching color', value=False)
        st.caption('Optional · Focus on the color as well as the style.')
    desired_color = None
    color_weight = 0.0
    start_search = st.button('Find similar pieces →', type='primary', use_container_width=True, disabled=uploaded_file is None)
    if uploaded_file is None:
        st.session_state.pop('wearly_search_image', None)
    elif start_search:
        st.session_state['wearly_search_image'] = uploaded_file.getvalue()

if uploaded_file is None:
    with collection:
        st.markdown('<div class="section-label">The edit / A few pieces to inspire you</div>', unsafe_allow_html=True)
        try:
            preview = read_preview_catalog()
            for column, (_, product) in zip(st.columns(3), preview.head(3).iterrows()):
                with column:
                    product_card(product)
        except (OSError, ValueError, ImportError):
            st.info('Upload a photo to get started. Your catalog needs to be in the data folder.')
elif st.session_state.get('wearly_search_image') == uploaded_file.getvalue():
    try:
        image_bytes = uploaded_file.getvalue()
        with Image.open(io.BytesIO(image_bytes)) as image:
            query_image = ImageOps.exif_transpose(image).convert('RGB')
        with st.spinner('Getting ready to find your style…'):
            engine = load_search_engine()
        with controls:
            if prefer_color:
                options = ['Like my photo']
                if engine.available_colors:
                    options.append('A different color')
                mode = st.radio('Color mood', options)
                if mode == 'A different color':
                    desired_color = st.selectbox('Choose your color', engine.available_colors)
                    st.caption('The main photo may show a different color. Budget uses the starting price.')
                else:
                    color_weight = st.slider('How much should color matter?', 0.0, 0.5, 0.20, 0.05)
            st.markdown('<div class="section-label">Your inspiration</div>', unsafe_allow_html=True)
            st.image(query_image, width=200)
        st.divider()
        with st.spinner('Finding your matches…'):
            results = engine.search(query_image=query_image, max_price=max_price,
                                    top_k=top_k, color_weight=color_weight,
                                    desired_color=desired_color,
                                    query_features=encode_uploaded_image(image_bytes))
        with collection:
            st.markdown('<div class="section-label">Your matches / Selected for you</div>', unsafe_allow_html=True)
            if results.empty:
                st.info('No matches just yet. Try a higher budget or another color.')
            else:
                st.caption(f'{len(results)} pieces inspired by your photo')
                for start in range(0, len(results), 3):
                    for column, (_, product) in zip(st.columns(3), results.iloc[start:start + 3].iterrows()):
                        with column:
                            product_card(product, desired_color)
    except UnidentifiedImageError:
        with collection:
            st.error('Please choose a valid JPG or PNG photo.')
    except (ValueError, OSError) as error:
        with collection:
            st.error(str(error))

st.markdown('''<div class="footer"><span>wearly. / Find your style. Within your budget.</span><span>Sample catalog · Prices and availability may change.</span></div>''', unsafe_allow_html=True)
