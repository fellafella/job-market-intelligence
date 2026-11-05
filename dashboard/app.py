"""Dashboard Streamlit : lit les marts dbt dans PostgreSQL."""

import os

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

st.set_page_config(page_title="Job Market Intelligence", page_icon="📊", layout="wide")


@st.cache_resource
def get_engine():
    url = URL.create(
        "postgresql+psycopg2",
        username=os.getenv("WAREHOUSE_USER", "jobs"),
        password=os.getenv("WAREHOUSE_PASSWORD", "jobs"),
        host=os.getenv("WAREHOUSE_HOST", "localhost"),
        port=int(os.getenv("WAREHOUSE_PORT", "5432")),
        database=os.getenv("WAREHOUSE_DB", "warehouse"),
    )
    return create_engine(url)


@st.cache_data(ttl=300)
def query(sql: str) -> pd.DataFrame:
    with get_engine().connect() as conn:
        return pd.read_sql(text(sql), conn)


st.title("📊 Job Market Intelligence")
st.caption("Offres d'emploi data : compétences, salaires et tendances (Airflow + dbt + PostgreSQL)")

try:
    postings = query(
        """
        select f.*, c.company_name
        from marts.fct_job_postings f
        join marts.dim_company c using (company_id)
        """
    )
    skills = query("select * from marts.mart_skill_demand")
    salaries = query("select * from marts.mart_salary_summary")
    trend = query("select * from marts.mart_postings_trend")
except Exception:
    st.warning(
        "Les tables ne sont pas encore prêtes. Lancez le DAG `job_market_pipeline` "
        "dans Airflow (http://localhost:8080), puis rechargez cette page."
    )
    st.stop()

if postings.empty:
    st.info("Aucune offre pour le moment : lancez le pipeline.")
    st.stop()

# --- Filtres -----------------------------------------------------------------
roles = sorted(postings["role_family"].unique())
selected_roles = st.sidebar.multiselect("Famille de métier", roles, default=roles)
filtered = postings[postings["role_family"].isin(selected_roles)]

if filtered.empty:
    st.info("Sélectionnez au moins une famille de métier.")
    st.stop()

# --- Indicateurs -------------------------------------------------------------
with_salary = filtered["salary_mid"].notna().mean() * 100
usd = filtered[filtered["salary_currency"] == "USD"]["salary_mid"]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Offres", f"{len(filtered):,}")
c2.metric("Entreprises", f"{filtered['company_id'].nunique():,}")
c3.metric("Avec salaire affiché", f"{with_salary:.0f} %")
c4.metric("Salaire médian (USD)", f"{usd.median():,.0f}" if not usd.empty else "n/a")

tab_skills, tab_salary, tab_trend, tab_jobs = st.tabs(
    ["Compétences", "Salaires", "Tendances", "Offres"]
)

# --- Compétences -------------------------------------------------------------
with tab_skills:
    demand = (
        skills[skills["role_family"].isin(selected_roles)]
        .groupby(["skill_name", "skill_category"], as_index=False)["postings_with_skill"]
        .sum()
    )
    demand["pct"] = (100 * demand["postings_with_skill"] / len(filtered)).round(1)
    top = demand.sort_values("pct", ascending=False).head(15)
    fig = px.bar(
        top.sort_values("pct"),
        x="pct",
        y="skill_name",
        color="skill_category",
        orientation="h",
        labels={"pct": "% des offres", "skill_name": "", "skill_category": "Catégorie"},
        title="Top 15 des compétences les plus demandées",
    )
    st.plotly_chart(fig, use_container_width=True)

# --- Salaires ----------------------------------------------------------------
with tab_salary:
    currencies = sorted(salaries["salary_currency"].unique())
    if not currencies:
        st.info("Aucun salaire affiché dans les offres collectées.")
    else:
        currency = st.selectbox("Devise", currencies, index=0)
        sal = salaries[
            (salaries["salary_currency"] == currency) & salaries["role_family"].isin(selected_roles)
        ]
        fig = px.bar(
            sal,
            x="role_family",
            y="median_salary",
            color="seniority",
            barmode="group",
            labels={"role_family": "", "median_salary": f"Salaire médian ({currency})"},
            title="Salaire médian annoncé par métier et séniorité",
        )
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(sal, hide_index=True, use_container_width=True)

# --- Tendances ---------------------------------------------------------------
with tab_trend:
    tr = trend[trend["role_family"].isin(selected_roles)]
    fig = px.bar(
        tr,
        x="published_date",
        y="postings_count",
        color="role_family",
        labels={"published_date": "", "postings_count": "Offres", "role_family": "Métier"},
        title="Offres publiées par jour",
    )
    st.plotly_chart(fig, use_container_width=True)

# --- Offres ------------------------------------------------------------------
with tab_jobs:
    cols = [
        "published_date", "title", "company_name", "role_family", "seniority",
        "location", "salary_min", "salary_max", "salary_currency", "skills_count", "job_url",
    ]
    st.dataframe(
        filtered.sort_values("published_date", ascending=False)[cols],
        hide_index=True,
        use_container_width=True,
        column_config={"job_url": st.column_config.LinkColumn("Lien", display_text="Ouvrir")},
    )
