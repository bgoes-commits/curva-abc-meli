import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Curva ABC Inteligente",
    layout="wide"
)

st.title("📊 Curva ABC Inteligente - Mercado Livre")

# ========================
# Upload
# ========================

st.sidebar.header("Upload das planilhas")

file_prev = st.sidebar.file_uploader("Mês anterior", type=["xlsx"])
file_current = st.sidebar.file_uploader("Mês atual", type=["xlsx"])


# ========================
# LOAD DATA
# ========================

@st.cache_data
def load_data(file):

    df = pd.read_excel(file, header=5)

    df = df[
        [
            "ID do anúncio",
            "Anúncio",
            "Unidades vendidas",
            "Vendas brutas (BRL)"
        ]
    ]

    df.columns = [
        "id",
        "anuncio",
        "unidades",
        "faturamento"
    ]

    df["faturamento"] = (
        df["faturamento"]
        .astype(str)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .astype(float)
    )

    df["unidades"] = pd.to_numeric(df["unidades"], errors="coerce").fillna(0).astype(int)

    return df


# ========================
# CURVA ABC
# ========================

@st.cache_data
def calcular_curva(df):

    resumo = (
        df.groupby(["id","anuncio"])
        .agg(
            faturamento=("faturamento","sum"),
            unidades=("unidades","sum")
        )
        .reset_index()
    )

    resumo["preco_medio"] = resumo["faturamento"] / resumo["unidades"].replace(0,1)

    resumo = resumo.sort_values("faturamento", ascending=False)

    resumo["perc"] = resumo["faturamento"] / resumo["faturamento"].sum()

    resumo["perc_acum"] = resumo["perc"].cumsum()

    resumo["curva"] = pd.cut(
        resumo["perc_acum"],
        bins=[0,0.8,0.95,1],
        labels=["A","B","C"]
    )

    return resumo


# ========================
# COMPARAÇÃO
# ========================

def comparar(atual, anterior):

    df = atual.merge(
        anterior,
        on="id",
        how="left",
        suffixes=("_atual","_anterior")
    )

    ordem = {"A":1,"B":2,"C":3}

    df["curva_anterior"] = df["curva_anterior"].astype(str).replace("nan","Novo")
    df["curva_atual"] = df["curva_atual"].astype(str)

    # Movimento

    def movimento(row):

        if row["curva_anterior"] == "Novo":
            return "🆕 Novo"

        atual = ordem.get(row["curva_atual"],99)
        anterior = ordem.get(row["curva_anterior"],99)

        if atual < anterior:
            return "📈 Subiu"

        if atual > anterior:
            return "📉 Caiu"

        return "➡️ Igual"

    df["movimento"] = df.apply(movimento, axis=1)

    # Variações

    df["var_faturamento"] = df["faturamento_atual"] - df["faturamento_anterior"]

    df["var_faturamento_perc"] = (
        df["var_faturamento"] /
        df["faturamento_anterior"].replace(0,1)
    )

    df["var_unidades"] = df["unidades_atual"] - df["unidades_anterior"]

    df["var_preco"] = df["preco_medio_atual"] - df["preco_medio_anterior"]

    # ALERTA INTELIGENTE

    def alerta(row):

        if row["movimento"] == "📉 Caiu" and row["var_preco"] > 0:
            return "⚠️ Preço subiu e perdeu competitividade"

        if row["movimento"] == "📉 Caiu" and row["var_unidades"] < 0:
            return "📉 Perda de demanda"

        if row["movimento"] == "📈 Subiu":
            return "🚀 Ganhando relevância"

        return ""

    df["alerta"] = df.apply(alerta, axis=1)

    return df


# ========================
# EXECUÇÃO
# ========================

if file_prev and file_current:

    df_prev = load_data(file_prev)
    df_current = load_data(file_current)

    curva_prev = calcular_curva(df_prev)
    curva_current = calcular_curva(df_current)

    comparacao = comparar(curva_current, curva_prev)


# ========================
# TABS
# ========================

    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Dashboard",
        "📈 Curva ABC",
        "🔍 Diagnóstico",
        "🚀 Oportunidades"
    ])


# ========================
# DASHBOARD
# ========================

    with tab1:

        fat_atual = curva_current["faturamento"].sum()
        fat_anterior = curva_prev["faturamento"].sum()

        crescimento = ((fat_atual-fat_anterior)/fat_anterior)*100

        c1,c2,c3,c4 = st.columns(4)

        c1.metric("Faturamento Atual", f"R$ {fat_atual:,.2f}")
        c2.metric("Faturamento Anterior", f"R$ {fat_anterior:,.2f}")
        c3.metric("Crescimento", f"{crescimento:.2f}%")
        c4.metric("Anúncios ativos", len(curva_current))

        st.divider()

        curva_valor = curva_current.groupby("curva")["faturamento"].sum().reset_index()

        fig = px.pie(
            curva_valor,
            names="curva",
            values="faturamento",
            title="Participação Curva ABC"
        )

        st.plotly_chart(fig, use_container_width=True)


# ========================
# CURVA ABC
# ========================

    with tab2:

        filtro_curva = st.multiselect(
            "Filtrar curva",
            ["A","B","C"],
            default=["A","B","C"]
        )

        df_curva = curva_current[curva_current["curva"].isin(filtro_curva)]

        st.dataframe(
            df_curva
            .sort_values("faturamento", ascending=False)
            .style.format({
                "faturamento":"R$ {:,.2f}",
                "preco_medio":"R$ {:,.2f}",
                "perc":"{:.2%}",
                "perc_acum":"{:.2%}"
            }),
            use_container_width=True
        )


# ========================
# DIAGNÓSTICO
# ========================

    with tab3:

        st.subheader("Produtos com queda relevante")

        queda = st.slider("Queda mínima (%)",0,100,20)

        df_diag = comparacao[
            comparacao["var_faturamento_perc"] < -(queda/100)
        ]

        st.dataframe(
            df_diag[
                [
                    "id",
                    "anuncio_atual",
                    "curva_anterior",
                    "curva_atual",
                    "movimento",
                    "alerta",
                    "faturamento_anterior",
                    "faturamento_atual",
                    "var_faturamento_perc",
                    "unidades_anterior",
                    "unidades_atual",
                    "preco_medio_anterior",
                    "preco_medio_atual"
                ]
            ].style.format({

                "faturamento_anterior":"R$ {:,.2f}",
                "faturamento_atual":"R$ {:,.2f}",
                "preco_medio_anterior":"R$ {:,.2f}",
                "preco_medio_atual":"R$ {:,.2f}",
                "var_faturamento_perc":"{:.2%}"

            }),

            use_container_width=True
        )


# ========================
# OPORTUNIDADES
# ========================

    with tab4:

        st.subheader("Produtos próximos da Curva A")

        candidatos = curva_current[
            (curva_current["curva"]=="B") &
            (curva_current["perc_acum"] < 0.85)
        ]

        st.dataframe(

            candidatos
            .sort_values("faturamento", ascending=False)
            .style.format({

                "faturamento":"R$ {:,.2f}",
                "preco_medio":"R$ {:,.2f}"

            }),

            use_container_width=True
        )

else:

    st.info("⬅️ Faça upload das duas planilhas")
