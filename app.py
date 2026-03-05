import streamlit as st
import pandas as pd

st.title("📊 Análise Curva ABC - Mercado Livre")

arquivo = st.file_uploader(
    "Suba o relatório do Mercado Livre",
    type=["xlsx"]
)

if arquivo:

    df = pd.read_excel(
        arquivo,
        sheet_name="Relatório",
        header=5
    )

    df = df.rename(columns={
        "ID do anúncio": "item_id",
        "Anúncio": "titulo",
        "Unidades vendidas": "vendas",
        "Vendas brutas (BRL)": "faturamento"
    })

    df["faturamento"] = (
        df["faturamento"]
        .astype(str)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .astype(float)
    )

    df = df.sort_values("faturamento", ascending=False)

    total = df["faturamento"].sum()

    df["percentual"] = df["faturamento"] / total
    df["acumulado"] = df["percentual"].cumsum()

    def curva(x):

        if x <= 0.8:
            return "A"

        elif x <= 0.95:
            return "B"

        else:
            return "C"

    df["curva"] = df["acumulado"].apply(curva)

    st.subheader("Resultado Curva ABC")

    st.dataframe(
        df[
            [
                "titulo",
                "vendas",
                "faturamento",
                "curva"
            ]
        ]
    )
