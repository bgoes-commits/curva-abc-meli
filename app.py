import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Curva ABC Mercado Livre", layout="wide")

st.title("📊 Analisador Curva ABC - Mercado Livre")

# -------------------------
# Upload arquivos
# -------------------------

st.sidebar.header("Upload das planilhas")

file_3m = st.sidebar.file_uploader("Últimos 3 meses", type=["xlsx"])
file_prev = st.sidebar.file_uploader("Mês anterior", type=["xlsx"])
file_current = st.sidebar.file_uploader("Mês atual", type=["xlsx"])


# -------------------------
# Função carregar planilha
# -------------------------

def load_data(file):

    df = pd.read_excel(file)

    df.columns = df.columns.str.lower().str.strip()

    return df


# -------------------------
# Detectar colunas automaticamente
# -------------------------

def detectar_colunas(df):

    col_anuncio = None
    col_vendas = None
    col_faturamento = None
    col_preco = None
    col_data = None

    for col in df.columns:

        if "titulo" in col or "anuncio" in col or "publicacao" in col:
            col_anuncio = col

        if "vend" in col:
            col_vendas = col

        if "faturamento" in col or "receita" in col:
            col_faturamento = col

        if "preco" in col or "preço" in col:
            col_preco = col

        if "data" in col:
            col_data = col

    return col_anuncio, col_vendas, col_faturamento, col_preco, col_data


# -------------------------
# Curva ABC
# -------------------------

def calcular_curva(df):

    anuncio, vendas, faturamento, preco, data = detectar_colunas(df)

    resumo = df.groupby(anuncio).agg({
        faturamento:"sum",
        vendas:"sum",
        preco:"mean"
    }).reset_index()

    resumo = resumo.sort_values(faturamento, ascending=False)

    resumo["perc"] = resumo[faturamento] / resumo[faturamento].sum()

    resumo["perc_acum"] = resumo["perc"].cumsum()

    def curva(x):

        if x <= 0.80:
            return "A"

        elif x <= 0.95:
            return "B"

        else:
            return "C"

    resumo["curva"] = resumo["perc_acum"].apply(curva)

    resumo.columns = ["anuncio","faturamento","vendas","preco","perc","perc_acum","curva"]

    return resumo


# -------------------------
# Comparar curvas
# -------------------------

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


# -------------------------
# Executar app
# -------------------------

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

        st.header("📊 Dashboard")

        fat_atual = df_current.select_dtypes(include=np.number).sum().max()
        fat_anterior = df_prev.select_dtypes(include=np.number).sum().max()

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
            title="Participação Curva ABC"
        )

        st.plotly_chart(fig, use_container_width=True)

# -------------------------
# CURVA ABC
# -------------------------

    if menu == "Curva ABC":

        st.header("📈 Curva ABC")

        st.dataframe(curva_current)

# -------------------------
# MUDANÇAS
# -------------------------

    if menu == "Mudanças de Curva":

        st.header("🔄 Mudanças de Curva")

        mudancas = comparacao[
            comparacao["curva_atual"] != comparacao["curva_anterior"]
        ]

        st.dataframe(mudancas)

# -------------------------
# PERFORMANCE DIARIA
# -------------------------

    if menu == "Performance Diária":

        st.header("📅 Performance diária")

        anuncio = st.selectbox(
            "Escolha anúncio",
            df_current.iloc[:,0].unique()
        )

        filtro = df_current[df_current.iloc[:,0] == anuncio]

        fig = px.line(
            filtro,
            x=filtro.columns[1],
            y=filtro.columns[2],
            title="Vendas por dia"
        )

        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(filtro)

# -------------------------
# PRE ACORDO
# -------------------------

    if menu == "Pré-Acordo":

        st.header("🔥 Itens que não podem faltar em promoção")

        curvaA = curva_current[curva_current["curva"]=="A"]

        curvaA = curvaA.sort_values("faturamento", ascending=False)

        st.dataframe(curvaA)

        st.download_button(
            "Baixar lista",
            curvaA.to_csv(index=False),
            "pre_acordo.csv"
        )

else:

    st.info("⬅️ Faça upload das 3 planilhas para iniciar análise")
