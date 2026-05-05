import pickle
import pandas as pd
import requests
import streamlit as st

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CineMatch",
    page_icon="🎬",
    layout="wide",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;500&display=swap');

/* Global */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #0c0c0f;
    color: #e8e6e0;
}

/* Hide Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 1100px; }

/* Hero title */
.hero-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 4.5rem;
    letter-spacing: 0.08em;
    line-height: 1;
    background: linear-gradient(135deg, #e8e6e0 30%, #c0a060 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.2rem;
}
.hero-sub {
    font-size: 0.95rem;
    color: #7a7870;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 2.5rem;
}

/* Selectbox label */
div[data-testid="stSelectbox"] label {
    font-size: 0.78rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #7a7870;
}

/* Selectbox */
div[data-testid="stSelectbox"] > div {
    background: #17171c !important;
    border: 1px solid #2e2e38 !important;
    border-radius: 10px !important;
    color: #e8e6e0 !important;
}

/* Button */
div[data-testid="stButton"] > button {
    background: #c0a060;
    color: #0c0c0f;
    font-family: 'DM Sans', sans-serif;
    font-weight: 500;
    font-size: 0.88rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    border: none;
    border-radius: 10px;
    padding: 0.65rem 2.5rem;
    cursor: pointer;
    transition: background 0.2s;
    width: 100%;
    margin-top: 0.5rem;
}
div[data-testid="stButton"] > button:hover {
    background: #d4b478;
}

/* Movie card */
.movie-card {
    background: #17171c;
    border-radius: 14px;
    overflow: hidden;
    border: 1px solid #2e2e38;
    transition: transform 0.25s, border-color 0.25s;
    height: 100%;
}
.movie-card:hover {
    transform: translateY(-6px);
    border-color: #c0a060;
}
.movie-card img {
    width: 100%;
    display: block;
    aspect-ratio: 2/3;
    object-fit: cover;
}
.movie-card-body {
    padding: 0.75rem 0.85rem 1rem;
}
.movie-card-title {
    font-size: 0.88rem;
    font-weight: 500;
    color: #e8e6e0;
    line-height: 1.3;
    margin: 0;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}
.match-badge {
    display: inline-block;
    background: rgba(192,160,96,0.15);
    color: #c0a060;
    font-size: 0.7rem;
    letter-spacing: 0.08em;
    padding: 2px 8px;
    border-radius: 20px;
    margin-top: 0.4rem;
}

/* Divider */
.gold-divider {
    height: 1px;
    background: linear-gradient(to right, transparent, #c0a060, transparent);
    margin: 2rem 0;
}

/* Selected movie banner */
.selected-banner {
    background: #17171c;
    border: 1px solid #2e2e38;
    border-left: 4px solid #c0a060;
    border-radius: 10px;
    padding: 0.8rem 1.2rem;
    margin-bottom: 1.5rem;
    font-size: 0.85rem;
    color: #7a7870;
    letter-spacing: 0.06em;
}
.selected-banner span {
    color: #e8e6e0;
    font-weight: 500;
}
</style>
""", unsafe_allow_html=True)


# ── Data loading ──────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    movies_dict = pickle.load(open('movie_dict.pkl', 'rb'))
    movies = pd.DataFrame(movies_dict)
    with gzip.open('similarity.pkl', 'rb') as f:
        similarity = pickle.load(f)
    return movies, similarity

movies, similarity = load_data()


# ── TMDB poster fetcher ───────────────────────────────────────────────────────
TMDB_API_KEY = "8265bd1679663a7ea12ac168da84d2e8"   # replace with your key
PLACEHOLDER  = "https://via.placeholder.com/300x450/17171c/c0a060?text=No+Poster"

@st.cache_data(show_spinner=False)
def fetch_poster(movie_id):
    try:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}"
        data = requests.get(url, timeout=5).json()
        path = data.get("poster_path")
        if path:
            return f"https://image.tmdb.org/t/p/w500{path}"
    except Exception:
        pass
    return PLACEHOLDER


# ── Recommender logic ─────────────────────────────────────────────────────────
def recommend(movie):
    idx = movies[movies['title'] == movie].index[0]
    distances = similarity[idx]
    top = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]
    names, posters, scores = [], [], []
    for i, score in top:
        mid = movies.iloc[i].movie_id
        names.append(movies.iloc[i].title)
        posters.append(fetch_poster(mid))
        scores.append(round(score * 100, 1))
    return names, posters, scores


# ── UI Layout ─────────────────────────────────────────────────────────────────
st.markdown('<div class="hero-title">CineMatch</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">Content-based movie recommendations</div>', unsafe_allow_html=True)

col_select, col_btn = st.columns([4, 1], gap="medium")

with col_select:
    selected_movie = st.selectbox(
        "Choose a movie you love",
        movies['title'].values,
        index=0,
        label_visibility="visible"
    )

with col_btn:
    st.markdown("<br>", unsafe_allow_html=True)
    recommend_btn = st.button("Recommend →")

# ── Results ───────────────────────────────────────────────────────────────────
if recommend_btn:
    st.markdown('<div class="gold-divider"></div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="selected-banner">Showing recommendations for <span>{selected_movie}</span></div>',
        unsafe_allow_html=True
    )

    with st.spinner("Finding your next watch..."):
        names, posters, scores = recommend(selected_movie)

    cols = st.columns(5, gap="medium")
    for col, name, poster, score in zip(cols, names, posters, scores):
        with col:
            st.markdown(f"""
            <div class="movie-card">
                <img src="{poster}" alt="{name}" onerror="this.src='{PLACEHOLDER}'"/>
                <div class="movie-card-body">
                    <p class="movie-card-title">{name}</p>
                    <span class="match-badge">{score}% match</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
