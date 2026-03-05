import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Analisador Curva ABC Meli", layout="wide")

st.title("📊 Analisador de Curva ABC - Mercado Livre")

st.sidebar.title("Upload de Planilhas")

file_3m = st.sidebar.file_uploader("Últimos 3 meses", type=["xlsx"])
file_prev = st.sidebar.file_uploader("Mês anterior", type=["xlsx"])
file_current = st.sidebar.file_uploader("Mês atual", type=["xlsx"])


def load_data(file):
    df = pd.read_excel(file)

    df.columns = df.columns.str.lower()

    return df


def calcular_curva(df):

    resumo = df.groupby("anuncio").agg({
        "faturamento":"sum",
        "vendas":"sum",
        "preco":"mean"
    }).reset_index()

    resumo = resumo.sort_values("faturamento", ascending=False)

    resumo["perc"] = resumo["faturamento"] / resumo["faturamento"].sum()

    resumo["perc_acum"] = resumo["perc"].cumsum()

    def curva(x):

        if x <= 0.80:
            return "A"

        elif x <= 0.95:
            return "B"

        else:
            return "C"

    resumo["curva"] = resumo["perc_acum"].apply(curva)

    return resumo


def comparar_curvas(atual, anterior):

    merge = atual.merge(
        anterior,
        on="anuncio",
        how="left",
        suffixes=("_atual","_anterior")
    )

    merge["mudanca"] = merge["curva_anterior"] + " → " + merge["curva_atual"]

    merge["analise_preco"] = np.where(
        merge["preco_atual"] < merge["preco_anterior"],
        "Preço caiu",
        "Preço subiu"
    )

    return merge


if file_3m and file_prev and file_current:

    df3 = load_data(file_3m)
    df_prev = load_data(file_prev)
    df_current = load_data(file_current)

    curva_3m = calcular_curva(df3)
    curva_prev = calcular_curva(df_prev)
    curva_current = calcular_curva(df_current)

    comparacao = comparar_curvas(curva_current, curva_prev)

    menu = st.sidebar.radio(
        "Menu",
        [
            "Dashboard",
            "Curva ABC",
            "Mudanças de Curva",
            "Performance Diária",
            "Pré-Acordo"
        ]
    )

# -------------------------
# DASHBOARD
# -------------------------

    if menu == "Dashboard":

        st.header("Dashboard Geral")

        fat_atual = df_current["faturamento"].sum()
        fat_anterior = df_prev["faturamento"].sum()

        crescimento = ((fat_atual - fat_anterior) / fat_anterior) * 100

        c1,c2,c3 = st.columns(3)

        c1.metric("Faturamento Atual", f"R$ {fat_atual:,.0f}")
        c2.metric("Faturamento Anterior", f"R$ {fat_anterior:,.0f}")
        c3.metric("Crescimento", f"{crescimento:.2f}%")

        curva_valor = curva_current.groupby("curva")["faturamento"].sum().reset_index()

        fig = px.pie(
            curva_valor,
            names="curva",
            values="faturamento",
            title="Participação por Curva"
        )

        st.plotly_chart(fig, use_container_width=True)

# -------------------------
# CURVA ABC
# -------------------------

    if menu == "Curva ABC":

        st.header("Curva ABC - Mês Atual")

        st.dataframe(curva_current)

# -------------------------
# MUDANÇAS
# -------------------------

    if menu == "Mudanças de Curva":

        st.header("Mudanças de Curva")

        mudancas = comparacao[
            comparacao["curva_atual"] != comparacao["curva_anterior"]
        ]

        st.dataframe(mudancas)

# -------------------------
# PERFORMANCE DIARIA
# -------------------------

    if menu == "Performance Diária":

        st.header("Performance Diária")

        anuncio = st.selectbox(
            "Selecione anúncio",
            df_current["anuncio"].unique()
        )

        filtro = df_current[df_current["anuncio"] == anuncio]

        fig = px.line(
            filtro,
            x="data",
            y="vendas",
            title="Vendas por dia"
        )

        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(filtro)

# -------------------------
# PRE ACORDO
# -------------------------

    if menu == "Pré-Acordo":

        st.header("Itens que não podem faltar em promoção")

        curvaA = curva_current[curva_current["curva"]=="A"]

        curvaA = curvaA.sort_values("faturamento", ascending=False)

        st.dataframe(curvaA)

        st.download_button(
            "Baixar lista",
            curvaA.to_csv(index=False),
            "pre_acordo.csv"
        )

else:

    st.info("Faça upload das 3 planilhas para iniciar análise")
