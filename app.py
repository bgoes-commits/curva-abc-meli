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

    df = pd.read_excel(file, header=5)

    df.columns = df.columns.str.lower().str.strip()

    df = df.rename(columns={
        "anúncio":"anuncio",
        "anuncio":"anuncio",
        "quantidade de vendas":"vendas",
        "unidades vendidas":"vendas",
        "vendas brutas (brl)":"faturamento"
    })

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

        nome = col.lower()

        if "anuncio" in nome:
            col_anuncio = col

        if "vend" in nome:
            col_vendas = col

        if "faturamento" in nome or "brutas" in nome:
            col_faturamento = col

        if "preco" in nome or "preço" in nome:
            col_preco = col

        if "data" in nome:
            col_data = col

    return col_anuncio, col_vendas, col_faturamento, col_preco, col_data


# -------------------------
# Curva ABC
# -------------------------

def calcular_curva(df):

    anuncio, vendas, faturamento, preco, data = detectar_colunas(df)

    if anuncio is None or faturamento is None:

        st.error("Não foi possível identificar as colunas necessárias.")
        st.write("Colunas encontradas:")
        st.write(df.columns)
        st.stop()

    agg_dict = {
        faturamento:"sum"
    }

    if vendas:
        agg_dict[vendas] = "sum"

    if preco:
        agg_dict[preco] = "mean"

    resumo = df.groupby(anuncio).agg(agg_dict).reset_index()

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

    resumo = resumo.rename(columns={
        faturamento:"faturamento",
        vendas:"vendas",
        preco:"preco"
    })

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

    if "curva_anterior" in merge.columns:

        merge["mudanca"] = merge["curva_anterior"] + " → " + merge["curva_atual"]

    else:

        merge["mudanca"] = "Novo"

    if "preco_atual" in merge.columns and "preco_anterior" in merge.columns:

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
            "Pré-Acordo"
        ]
    )

# -------------------------
# DASHBOARD
# -------------------------

    if menu == "Dashboard":

        st.header("📊 Dashboard")

        fat_atual = curva_current["faturamento"].sum()
        fat_anterior = curva_prev["faturamento"].sum()

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
