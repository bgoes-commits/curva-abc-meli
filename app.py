import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(
    page_title="BI Mercado Livre",
    layout="wide"
)

st.title("📊 BI Comercial - Mercado Livre")

# ---------------------------------------
# Upload
# ---------------------------------------

st.sidebar.header("Upload de Dados")

file_prev = st.sidebar.file_uploader(
    "Mês anterior",
    type=["xlsx"]
)

file_current = st.sidebar.file_uploader(
    "Mês atual",
    type=["xlsx"]
)

# ---------------------------------------
# Função leitura
# ---------------------------------------

def load_data(file):

    df = pd.read_excel(file)

    df = df[[
        "ID do anúncio",
        "Anúncio",
        "Unidades vendidas",
        "Vendas Brutas (BRL)"
    ]]

    df["Vendas Brutas (BRL)"] = (
        df["Vendas Brutas (BRL)"]
        .astype(str)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .astype(float)
    )

    return df

# ---------------------------------------
# Curva ABC
# ---------------------------------------

def curva_abc(df):

    resumo = df.groupby(
        ["ID do anúncio","Anúncio"]
    ).agg({
        "Unidades vendidas":"sum",
        "Vendas Brutas (BRL)":"sum"
    }).reset_index()

    resumo["preco_medio"] = (
        resumo["Vendas Brutas (BRL)"] /
        resumo["Unidades vendidas"]
    )

    resumo = resumo.sort_values(
        "Vendas Brutas (BRL)",
        ascending=False
    )

    resumo["perc"] = (
        resumo["Vendas Brutas (BRL)"] /
        resumo["Vendas Brutas (BRL)"].sum()
    )

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

# ---------------------------------------
# Comparação
# ---------------------------------------

def comparar(atual, anterior):

    df = atual.merge(
        anterior,
        on="ID do anúncio",
        how="left",
        suffixes=("_atual","_anterior")
    )

    df["mudanca_curva"] = (
        df["curva_anterior"] + " → " +
        df["curva_atual"]
    )

    df["variacao_faturamento"] = (
        (df["Vendas Brutas (BRL)_atual"] -
        df["Vendas Brutas (BRL)_anterior"])
        /
        df["Vendas Brutas (BRL)_anterior"]
    ) * 100

    df["variacao_preco"] = (
        (df["preco_medio_atual"] -
        df["preco_medio_anterior"])
        /
        df["preco_medio_anterior"]
    ) * 100

    return df

# ---------------------------------------
# Execução
# ---------------------------------------

if file_prev and file_current:

    df_prev = load_data(file_prev)
    df_current = load_data(file_current)

    curva_prev = curva_abc(df_prev)
    curva_current = curva_abc(df_current)

    comparacao = comparar(curva_current, curva_prev)

    # ---------------------------------------
    # Abas
    # ---------------------------------------

    tab1,tab2,tab3,tab4,tab5,tab6 = st.tabs([

        "Dashboard",
        "Curva ABC",
        "Mudanças",
        "Oportunidades",
        "Pré-Acordo",
        "Ranking"

    ])

# ---------------------------------------
# DASHBOARD
# ---------------------------------------

    with tab1:

        fat_atual = df_current["Vendas Brutas (BRL)"].sum()
        fat_anterior = df_prev["Vendas Brutas (BRL)"].sum()

        crescimento = (
            (fat_atual-fat_anterior)/fat_anterior
        )*100

        unidades = df_current["Unidades vendidas"].sum()

        ticket = fat_atual/unidades

        anuncios = df_current["ID do anúncio"].nunique()

        c1,c2,c3,c4,c5 = st.columns(5)

        c1.metric("Faturamento Atual",f"R$ {fat_atual:,.0f}")
        c2.metric("Faturamento Anterior",f"R$ {fat_anterior:,.0f}")
        c3.metric("Crescimento",f"{crescimento:.2f}%")
        c4.metric("Unidades Vendidas",f"{unidades:,.0f}")
        c5.metric("Anúncios Ativos",anuncios)

        curva_valor = curva_current.groupby(
            "curva"
        )["Vendas Brutas (BRL)"].sum().reset_index()

        fig = px.pie(
            curva_valor,
            names="curva",
            values="Vendas Brutas (BRL)",
            title="Participação Curva ABC"
        )

        st.plotly_chart(fig,use_container_width=True)

# ---------------------------------------
# CURVA ABC
# ---------------------------------------

    with tab2:

        st.subheader("Curva ABC")

        st.dataframe(
            curva_current,
            use_container_width=True
        )

# ---------------------------------------
# MUDANÇAS
# ---------------------------------------

    with tab3:

        st.subheader("Mudanças de Curva")

        mudancas = comparacao[
            comparacao["curva_atual"]!=
            comparacao["curva_anterior"]
        ]

        st.dataframe(mudancas)

# ---------------------------------------
# OPORTUNIDADES
# ---------------------------------------

    with tab4:

        st.subheader("Radar de Oportunidades")

        oportunidade = comparacao[
            (comparacao["variacao_preco"] < 0) &
            (comparacao["variacao_faturamento"] > 0)
        ]

        st.write("🚀 Produtos que podem subir preço")

        st.dataframe(oportunidade)

# ---------------------------------------
# PRE ACORDO
# ---------------------------------------

    with tab5:

        st.subheader("Produtos para Pré-Acordo")

        curvaA = curva_current[
            curva_current["curva"]=="A"
        ]

        curvaA = curvaA.sort_values(
            "Vendas Brutas (BRL)",
            ascending=False
        )

        st.dataframe(curvaA)

# ---------------------------------------
# RANKING
# ---------------------------------------

    with tab6:

        st.subheader("Top Faturamento")

        top = curva_current.sort_values(
            "Vendas Brutas (BRL)",
            ascending=False
        ).head(20)

        fig = px.bar(
            top,
            x="Anúncio",
            y="Vendas Brutas (BRL)"
        )

        st.plotly_chart(fig,use_container_width=True)

else:

    st.info("Faça upload das planilhas para iniciar análise")
