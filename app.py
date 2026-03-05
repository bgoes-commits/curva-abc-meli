import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Curva ABC Mercado Livre",
    layout="wide"
)

st.title("📊 Analisador Curva ABC - Mercado Livre")

# =========================
# Upload arquivos
# =========================

st.sidebar.header("Upload das planilhas")

file_3m = st.sidebar.file_uploader("Últimos 3 meses", type=["xlsx"])
file_prev = st.sidebar.file_uploader("Mês anterior", type=["xlsx"])
file_current = st.sidebar.file_uploader("Mês atual", type=["xlsx"])

# =========================
# CACHE
# =========================

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

    # corrigir formato monetário brasileiro
    df["faturamento"] = (
        df["faturamento"]
        .astype(str)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .astype(float)
    )

    df["unidades"] = pd.to_numeric(df["unidades"], errors="coerce")

    return df


# =========================
# Curva ABC
# =========================

@st.cache_data
def calcular_curva(df):

    resumo = (
        df.groupby(["id", "anuncio"])
        .agg(
            faturamento=("faturamento", "sum"),
            unidades=("unidades", "sum")
        )
        .reset_index()
    )

    resumo["preco_medio"] = resumo["faturamento"] / resumo["unidades"].replace(0, 1)

    resumo = resumo.sort_values("faturamento", ascending=False)

    resumo["perc"] = resumo["faturamento"] / resumo["faturamento"].sum()

    resumo["perc_acum"] = resumo["perc"].cumsum()

    resumo["curva"] = pd.cut(
        resumo["perc_acum"],
        bins=[0,0.8,0.95,1],
        labels=["A","B","C"]
    )

    return resumo


# =========================
# Comparação de curvas
# =========================

def comparar_curvas(atual, anterior):

    merge = atual.merge(
        anterior,
        on="id",
        how="left",
        suffixes=("_atual", "_anterior")
    )

    merge["curva_anterior"] = merge["curva_anterior"].astype(str).replace("nan","Novo")
    merge["curva_atual"] = merge["curva_atual"].astype(str)

    merge["mudanca"] = merge["curva_anterior"] + " → " + merge["curva_atual"]

    def classificar(row):

        if row["curva_anterior"] == "Novo":
            return "🆕 Novo"

        ordem = {"A":1,"B":2,"C":3}

        if ordem.get(row["curva_atual"],3) < ordem.get(row["curva_anterior"],3):
            return "📈 Subiu"

        if ordem.get(row["curva_atual"],3) > ordem.get(row["curva_anterior"],3):
            return "📉 Caiu"

        return "➡️ Igual"

    merge["movimento"] = merge.apply(classificar, axis=1)

    return merge


# =========================
# EXECUÇÃO
# =========================

if file_3m and file_prev and file_current:

    df3 = load_data(file_3m)
    df_prev = load_data(file_prev)
    df_current = load_data(file_current)

    curva_3m = calcular_curva(df3)
    curva_prev = calcular_curva(df_prev)
    curva_current = calcular_curva(df_current)

    comparacao = comparar_curvas(curva_current, curva_prev)

    # =========================
    # ABAS
    # =========================

    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Dashboard",
        "📈 Curva ABC",
        "🔄 Mudanças de Curva",
        "🔥 Pré-Acordo"
    ])

# =========================
# DASHBOARD
# =========================

    with tab1:

        fat_atual = curva_current["faturamento"].sum()
        fat_anterior = curva_prev["faturamento"].sum()

        crescimento = ((fat_atual - fat_anterior) / fat_anterior) * 100 if fat_anterior != 0 else 0

        c1,c2,c3,c4 = st.columns(4)

        c1.metric("Faturamento Atual", f"R$ {fat_atual:,.2f}")
        c2.metric("Faturamento Anterior", f"R$ {fat_anterior:,.2f}")
        c3.metric("Crescimento", f"{crescimento:.2f}%")
        c4.metric("Anúncios ativos", len(curva_current))

        st.divider()

        col1,col2 = st.columns(2)

        with col1:

            curva_valor = curva_current.groupby("curva")["faturamento"].sum().reset_index()

            fig = px.pie(
                curva_valor,
                names="curva",
                values="faturamento",
                title="Participação Curva ABC"
            )

            st.plotly_chart(fig, use_container_width=True)

        with col2:

            top10 = curva_current.head(10)

            fig2 = px.bar(
                top10,
                x="faturamento",
                y="anuncio",
                orientation="h",
                title="Top 10 anúncios"
            )

            st.plotly_chart(fig2, use_container_width=True)


# =========================
# CURVA ABC
# =========================

    with tab2:

        st.subheader("Curva ABC atual")

        st.dataframe(
            curva_current
            .sort_values("faturamento", ascending=False)
            .style.format({
                "faturamento":"R$ {:,.2f}",
                "preco_medio":"R$ {:,.2f}",
                "perc":"{:.2%}",
                "perc_acum":"{:.2%}"
            }),
            use_container_width=True
        )


# =========================
# MUDANÇAS
# =========================

    with tab3:

        st.subheader("Mudanças de curva")

        mudancas = comparacao[
            comparacao["curva_atual"] != comparacao["curva_anterior"]
        ]

        st.dataframe(
            mudancas[
                [
                    "id",
                    "anuncio_atual",
                    "curva_anterior",
                    "curva_atual",
                    "mudanca",
                    "movimento",
                    "faturamento_atual",
                    "preco_medio_atual"
                ]
            ].style.format({
                "faturamento_atual":"R$ {:,.2f}",
                "preco_medio_atual":"R$ {:,.2f}"
            }),
            use_container_width=True
        )


# =========================
# PRE ACORDO
# =========================

    with tab4:

        st.subheader("Itens que não podem faltar em promoção")

        curvaA = curva_current[curva_current["curva"]=="A"]

        curvaA = curvaA.sort_values("faturamento", ascending=False)

        st.dataframe(
            curvaA.style.format({
                "faturamento":"R$ {:,.2f}",
                "preco_medio":"R$ {:,.2f}",
                "perc":"{:.2%}",
                "perc_acum":"{:.2%}"
            }),
            use_container_width=True
        )

        st.download_button(
            "Baixar lista de pré-acordo",
            curvaA.to_csv(index=False),
            "pre_acordo.csv"
        )

else:

    st.info("⬅️ Faça upload das 3 planilhas para iniciar análise")
