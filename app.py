import streamlit as st
import pandas as pd

st.set_page_config(page_title="Sistema de Análise de Produtos", layout="wide")

st.title("📊 Sistema de Análise de Marketplaces")

st.markdown("Faça upload das planilhas para iniciar a análise.")

st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    produtos_file = st.file_uploader("📦 Planilha de Produtos Base", type=["xlsx"])

with col2:
    anuncios_file = st.file_uploader("🛒 Planilha de Títulos de Anúncios", type=["xlsx"])

with col3:
    mercado_file = st.file_uploader("📈 Planilha de Dados de Mercado", type=["xlsx"])


if produtos_file and anuncios_file and mercado_file:

    st.success("Planilhas carregadas com sucesso!")

    produtos = pd.read_excel(produtos_file)
    anuncios = pd.read_excel(anuncios_file)
    mercado = pd.read_excel(mercado_file)

    st.subheader("🔎 Dados carregados")

    colA, colB, colC = st.columns(3)

    with colA:
        st.write("Produtos")
        st.dataframe(produtos)

    with colB:
        st.write("Anúncios")
        st.dataframe(anuncios)

    with colC:
        st.write("Mercado")
        st.dataframe(mercado)

    st.divider()

    st.subheader("⚙️ Processamento")

    if st.button("Rodar análise"):

        produtos_lista = produtos.iloc[:,0].tolist()

        resultados = []

        for titulo in anuncios.iloc[:,0]:
            for produto in produtos_lista:
                if produto.lower() in titulo.lower():
                    resultados.append({
                        "Produto": produto,
                        "Título do anúncio": titulo
                    })

        resultado_df = pd.DataFrame(resultados)

        st.subheader("📊 Resultado da análise")

        st.dataframe(resultado_df)

        csv = resultado_df.to_csv(index=False).encode("utf-8")

        st.download_button(
            "📥 Baixar resultado",
            csv,
            "resultado.csv",
            "text/csv"
        )

else:
    st.info("Envie as três planilhas para começar.")
