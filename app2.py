"""
Painel de Monitoramento de Nascimentos - Grande ABC Paulista
Fonte: SINASC 2026 (Ministério da Saúde)
"""

import pandas as pd
import plotly.express as px
import streamlit as st

# ══════════════════════════════════════════════════════════════
# 1. CONFIGURACAO DA PAGINA
# ══════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Nascimentos no Grande ABC",
    page_icon="👶",
    layout="wide",
    initial_sidebar_state="expanded",
)

ARQUIVO = "nascimentos_abc_2026.csv"

AZUL = "#1B3A5C"
AZUL_CLARO = "#2E86AB"
LARANJA = "#E4572E"
ROSA = "#C64191"
CINZA = "#9AA5B1"

CORES_PARTO = {"Vaginal": AZUL_CLARO, "Cesáreo": LARANJA, "Ignorado": CINZA}
CORES_SEXO = {"Masculino": AZUL_CLARO, "Feminino": ROSA, "Ignorado": CINZA}

st.markdown(
    """
    <style>
    .block-container {padding-top: 2.2rem; padding-bottom: 3rem;}
    div[data-testid="stMetric"] {
        background: #F7F9FC;
        border: 1px solid #E3E8EF;
        border-left: 4px solid #2E86AB;
        border-radius: 10px;
        padding: 14px 18px;
    }
    div[data-testid="stMetricValue"] {color: #1B3A5C; font-weight: 700;}
    div[data-testid="stMetricLabel"] {color: #5A6B7B;}
    h1, h2, h3 {color: #1B3A5C;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ══════════════════════════════════════════════════════════════
# 2. DICIONARIOS DE DECODIFICACAO
# ══════════════════════════════════════════════════════════════

MUNICIPIOS = {
    "351380": "Diadema",
    "352940": "Mauá",
    "354330": "Ribeirão Pires",
    "354410": "Rio Grande da Serra",
    "354780": "Santo André",
    "354870": "São Bernardo do Campo",
    "354880": "São Caetano do Sul",
}

MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
         "Jul", "Ago", "Set", "Out", "Nov", "Dez"]

PARTOS = {"1": "Vaginal", "2": "Cesáreo", "9": "Ignorado"}
SEXOS = {"1": "Masculino", "2": "Feminino", "0": "Ignorado"}
GRAVIDEZ = {"1": "Única", "2": "Dupla", "3": "Tripla ou mais", "9": "Ignorado"}
RACAS = {"1": "Branca", "2": "Preta", "3": "Amarela", "4": "Parda", "5": "Indígena"}

GESTACOES = {
    "1": "Menos de 22",
    "2": "22 a 27",
    "3": "28 a 31",
    "4": "32 a 36",
    "5": "37 a 41",
    "6": "42 e mais",
    "9": "Ignorado",
}

CONSULTAS = {
    "1": "Nenhuma",
    "2": "1 a 3",
    "3": "4 a 6",
    "4": "7 e mais",
    "9": "Ignorado",
}

ESCOLARIDADES = {
    "0": "Sem escolaridade",
    "1": "Fund. I incompleto",
    "2": "Fund. I completo",
    "3": "Fund. II incompleto",
    "4": "Fund. II completo",
    "5": "Médio incompleto",
    "6": "Médio completo",
    "7": "Superior incompleto",
    "8": "Superior completo",
    "9": "Ignorado",
    "10": "Fund. I inesp.",
    "11": "Fund. II inesp.",
    "12": "Médio inesp.",
}

ORDEM_GESTACAO = ["Menos de 22", "22 a 27", "28 a 31", "32 a 36",
                  "37 a 41", "42 e mais", "Ignorado"]

ORDEM_CONSULTAS = ["Nenhuma", "1 a 3", "4 a 6", "7 e mais", "Ignorado"]

ORDEM_ESCOLARIDADE = [
    "Sem escolaridade", "Fund. I incompleto", "Fund. I completo",
    "Fund. II incompleto", "Fund. II completo", "Médio incompleto",
    "Médio completo", "Superior incompleto", "Superior completo",
]

FAIXAS_IDADE = ["<15", "15-19", "20-24", "25-29", "30-34", "35-39", "40-49", "50+"]

# ══════════════════════════════════════════════════════════════
# 3. FUNCOES AUXILIARES
# ══════════════════════════════════════════════════════════════


def decodificar(serie, mapa):
    """Traduz codigos numericos em rotulos legiveis."""
    bruto = serie.fillna("").astype(str).str.strip()
    saida = bruto.map(mapa)

    faltante = saida.isna()
    if faltante.any():
        alternativa = bruto[faltante].str.lstrip("0").replace("", "0")
        saida[faltante] = alternativa.map(mapa)

    return saida.fillna("Ignorado")


def estilizar(fig, altura=380, legenda=False):
    """Aplica o padrao visual comum a todos os graficos."""
    fig.update_layout(
        template="plotly_white",
        height=altura,
        margin=dict(l=8, r=8, t=58, b=8),
        title=dict(
            font=dict(size=16, color=AZUL),
            x=0.01,
            xanchor="left",
        ),
        showlegend=legenda,
        legend=dict(orientation="h", y=-0.18, x=0),
        font=dict(family="Segoe UI, Arial, sans-serif", size=12, color="#3A4A5A"),
        hoverlabel=dict(bgcolor="white", font_size=12),
        bargap=0.28,
    )
    fig.update_xaxes(showgrid=False, title=None, linecolor="#DDE3EA")
    fig.update_yaxes(showgrid=True, gridcolor="#EEF1F5", title=None,
                     rangemode="tozero")
    return fig


def barras(dados, coluna, titulo, ordem=None, cores=None, altura=380):
    """Barras verticais com contagem por categoria."""
    contagem = dados[coluna].value_counts()

    if ordem is not None:
        contagem = contagem.reindex([i for i in ordem if i in contagem.index])

    tabela = contagem.rename_axis(coluna).reset_index(name="Nascimentos")

    fig = px.bar(
        tabela,
        x=coluna,
        y="Nascimentos",
        text="Nascimentos",
        color=coluna,
        color_discrete_map=cores,
        title=titulo,
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    return estilizar(fig, altura)


def barras_horizontais(dados, coluna, titulo, altura=380):
    """Barras horizontais ordenadas da maior para a menor."""
    contagem = dados[coluna].value_counts().reset_index()
    contagem.columns = [coluna, "Nascimentos"]

    fig = px.bar(
        contagem,
        x="Nascimentos",
        y=coluna,
        orientation="h",
        text="Nascimentos",
        title=titulo,
    )
    fig.update_traces(
        marker_color=AZUL_CLARO,
        textposition="outside",
        cliponaxis=False,
    )
    fig = estilizar(fig, altura)
    fig.update_yaxes(categoryorder="total ascending", automargin=True)
    fig.update_xaxes(showgrid=True, gridcolor="#EEF1F5")
    return fig


def empilhado(dados, coluna, titulo, ordem=None, altura=420):
    """Barras 100% empilhadas de tipo de parto por categoria."""
    tabela = pd.crosstab(dados[coluna], dados["PARTO_D"], normalize="index") * 100

    if ordem is not None:
        tabela = tabela.reindex([i for i in ordem if i in tabela.index])

    tabela = tabela.reset_index().melt(
        id_vars=coluna,
        var_name="Tipo de parto",
        value_name="Percentual",
    )

    fig = px.bar(
        tabela,
        x=coluna,
        y="Percentual",
        color="Tipo de parto",
        barmode="stack",
        color_discrete_map=CORES_PARTO,
        title=titulo,
    )
    fig.update_layout(yaxis_range=[0, 100], yaxis_ticksuffix="%")

    for trace in fig.data:
        if trace.name == "Cesáreo":
            trace.update(
                text=[f"{v:.1f}%" for v in trace.y],
                textposition="inside",
                insidetextanchor="middle",
                textfont=dict(color="white", size=11),
            )

    return estilizar(fig, altura, legenda=True)


# ══════════════════════════════════════════════════════════════
# 4. CARREGAMENTO E TRATAMENTO DOS DADOS
# ══════════════════════════════════════════════════════════════


@st.cache_data(show_spinner="Carregando a base do SINASC...")
def carregar_dados(caminho):
    """Le o CSV filtrado do ABC e cria as colunas derivadas."""
    df = pd.read_csv(caminho, dtype=str, low_memory=False)

    df["MUNICIPIO"] = df["CODMUNRES"].str.strip().str[:6].map(MUNICIPIOS)
    df["MES"] = pd.to_numeric(df["DTNASC"].str[2:4], errors="coerce")
    df["PESO"] = pd.to_numeric(df["PESO"], errors="coerce")
    df["IDADEMAE"] = pd.to_numeric(df["IDADEMAE"], errors="coerce")

    df["PARTO_D"] = decodificar(df["PARTO"], PARTOS)
    df["SEXO_D"] = decodificar(df["SEXO"], SEXOS)
    df["GRAVIDEZ_D"] = decodificar(df["GRAVIDEZ"], GRAVIDEZ)
    df["RACA_D"] = decodificar(df["RACACOR"], RACAS)
    df["GESTACAO_D"] = decodificar(df["GESTACAO"], GESTACOES)
    df["CONSULTAS_D"] = decodificar(df["CONSULTAS"], CONSULTAS)
    df["ESCOLARIDADE_D"] = decodificar(df["ESCMAEAGR1"], ESCOLARIDADES)

    df["FAIXA_IDADE"] = pd.cut(
        df["IDADEMAE"],
        bins=[-1, 14, 19, 24, 29, 34, 39, 49, 120],
        labels=FAIXAS_IDADE,
    )

    return df


df = carregar_dados(ARQUIVO)

# ══════════════════════════════════════════════════════════════
# 5. BARRA LATERAL DE FILTROS
# ══════════════════════════════════════════════════════════════


def limpar_filtros():
    """Remove os valores salvos no estado da sessao."""
    for chave in ["f_mun", "f_mes", "f_sexo", "f_parto", "f_idade"]:
        st.session_state.pop(chave, None)


st.sidebar.title("Filtros")
st.sidebar.caption("Todos os graficos reagem a selecao abaixo.")

todos_municipios = sorted(df["MUNICIPIO"].dropna().unique())
sel_municipios = st.sidebar.multiselect(
    "Municipio de residencia", todos_municipios,
    default=todos_municipios, key="f_mun",
)

meses_disponiveis = sorted(df["MES"].dropna().unique())
sel_meses = st.sidebar.multiselect(
    "Mes do nascimento", meses_disponiveis, default=meses_disponiveis,
    format_func=lambda m: MESES[int(m) - 1], key="f_mes",
)

sel_sexos = st.sidebar.multiselect(
    "Sexo do recem-nascido", ["Masculino", "Feminino", "Ignorado"],
    default=["Masculino", "Feminino", "Ignorado"], key="f_sexo",
)

sel_partos = st.sidebar.multiselect(
    "Tipo de parto", ["Vaginal", "Cesáreo", "Ignorado"],
    default=["Vaginal", "Cesáreo", "Ignorado"], key="f_parto",
)

if sel_meses:
    extremos = st.sidebar.select_slider(
        "Faixa de idade materna",
        options=FAIXAS_IDADE,
        value=(FAIXAS_IDADE[0], FAIXAS_IDADE[-1]),
        key="f_idade",
    )
    faixa_min = FAIXAS_IDADE.index(extremos[0])
    faixa_max = FAIXAS_IDADE.index(extremos[1])
    idades = FAIXAS_IDADE[faixa_min:faixa_max + 1]
else:
    idades = FAIXAS_IDADE

st.sidebar.button("Limpar filtros", on_click=limpar_filtros, use_container_width=True)
st.sidebar.divider()

# Aplicacao dos filtros
dados = df[
    df["MUNICIPIO"].isin(sel_municipios)
    & df["MES"].isin(sel_meses)
    & df["SEXO_D"].isin(sel_sexos)
    & df["PARTO_D"].isin(sel_partos)
    & df["FAIXA_IDADE"].isin(idades)
]

if dados.empty:
    st.warning("Nenhum registro encontrado com os filtros atuais.")
    st.stop()

validos = dados[dados["PARTO_D"].isin(["Vaginal", "Cesáreo"])]

# ══════════════════════════════════════════════════════════════
# 6. CABECALHO E INDICADORES
# ══════════════════════════════════════════════════════════════

st.title("Nascimentos no Grande ABC")
st.caption(
    "SINASC 2026 - Ministério da Saúde | "
    f"{dados['MUNICIPIO'].nunique()} municipios | "
    "periodo de janeiro a agosto"
)

col1, col2, col3, col4 = st.columns(4)

col1.metric("Nascimentos", f"{len(dados):,}".replace(",", "."))

taxa_cesarea = (validos["PARTO_D"] == "Cesáreo").mean() * 100 if len(validos) else 0
col2.metric("Taxa de cesárea", str(round(taxa_cesarea, 1)).replace(".", ",") + "%")

peso_medio = dados["PESO"].mean()
col3.metric("Peso médio", str(round(peso_medio)).replace(".", ",") + " g" if pd.notna(peso_medio) else "-")

boa_cobertura = (dados["CONSULTAS_D"] == "7 e mais").mean() * 100
col4.metric("Pré-natal 7+ consultas", str(round(boa_cobertura, 1)).replace(".", ",") + "%")

st.divider()

# ══════════════════════════════════════════════════════════════
# 7. ABAS COM OS GRAFICOS
# ══════════════════════════════════════════════════════════════

aba1, aba2, aba3, aba4, aba5 = st.tabs([
    "Visao geral",
    "Parto e gestação",
    "Mãe",
    "Recém-nascido",
    "Dados",
])

with aba1:
    serie = (
        dados.groupby("MES")
        .size()
        .reset_index(name="Nascimentos")
        .sort_values("MES")
    )
    serie["Mes"] = serie["MES"].map(lambda m: MESES[int(m) - 1])

    fig = px.line(serie, x="Mes", y="Nascimentos", markers=True,
                  title="Evolucao mensal dos nascimentos")
    fig.update_traces(
        line=dict(color=AZUL_CLARO, width=3),
        marker=dict(size=9, color=AZUL_CLARO,
                    line=dict(color="white", width=2)),
    )

    ultimo = serie.iloc[-1]
    media_anterior = serie["Nascimentos"].iloc[:-1].mean()
    if len(serie) > 2 and ultimo["Nascimentos"] < media_anterior * 0.7:
        fig.add_annotation(
            x=ultimo["Mes"],
            y=ultimo["Nascimentos"],
            text="mes incompleto",
            showarrow=True,
            arrowhead=2,
            ax=-45,
            ay=-45,
            font=dict(color=LARANJA, size=11),
            bgcolor="white",
            bordercolor=LARANJA,
            borderwidth=1,
        )

    st.plotly_chart(estilizar(fig, altura=400), use_container_width=True)

    st.plotly_chart(
        barras_horizontais(dados, "MUNICIPIO",
                           "Nascimentos por municipio de residencia"),
        use_container_width=True,
    )

with aba2:
    col_a, col_b = st.columns(2)

    with col_a:
        st.plotly_chart(
            barras(dados, "PARTO_D", "Distribuicao por tipo de parto",
                   cores=CORES_PARTO),
            use_container_width=True,
        )

    with col_b:
        st.plotly_chart(
            barras(dados, "GESTACAO_D", "Duracao da gestacao (semanas)",
                   ordem=ORDEM_GESTACAO),
            use_container_width=True,
        )

    st.plotly_chart(
        barras(dados, "GRAVIDEZ_D", "Distribuicao por tipo de gravidez"),
        use_container_width=True,
    )

with aba3:
    col_a, col_b = st.columns(2)

    with col_a:
        if len(validos):
            st.plotly_chart(
                empilhado(validos, "FAIXA_IDADE",
                          "Tipo de parto por faixa de idade materna",
                          ordem=FAIXAS_IDADE),
                use_container_width=True,
            )

    with col_b:
        if len(validos):
            st.plotly_chart(
                empilhado(validos, "ESCOLARIDADE_D",
                          "Tipo de parto por escolaridade materna",
                          ordem=ORDEM_ESCOLARIDADE),
                use_container_width=True,
            )

    st.plotly_chart(
        barras(dados, "CONSULTAS_D", "Consultas de pre-natal",
               ordem=ORDEM_CONSULTAS),
        use_container_width=True,
    )

with aba4:
    col_a, col_b = st.columns(2)

    with col_a:
        peso = dados.dropna(subset=["PESO"])
        if len(peso):
            fig = px.histogram(peso, x="PESO", nbins=50,
                               title="Distribuicao do peso ao nascer")
            fig.update_traces(marker_color=AZUL_CLARO)
            fig.add_vline(
                x=2500, line_dash="dash", line_color=LARANJA, line_width=2,
                annotation_text="2.500 g",
                annotation_position="top",
            )
            fig = estilizar(fig, altura=420)
            fig.update_xaxes(title_text="Peso (g)", showgrid=True,
                             gridcolor="#EEF1F5")
            st.plotly_chart(fig, use_container_width=True)

    with col_b:
        peso = dados.dropna(subset=["PESO"])
        if len(peso):
            fig = px.box(peso, x="SEXO_D", y="PESO", color="SEXO_D",
                         color_discrete_map=CORES_SEXO,
                         title="Peso ao nascer por sexo")
            fig = estilizar(fig, altura=420)
            fig.update_yaxes(title_text="Peso (g)")
            st.plotly_chart(fig, use_container_width=True)

    st.plotly_chart(
        barras(dados, "RACA_D", "Raca/cor do recem-nascido"),
        use_container_width=True,
    )

with aba5:
    st.subheader("Registros filtrados")
    st.caption(f"{len(dados):,} linhas e {dados.shape[1]} colunas".replace(",", "."))

    colunas = [
        "MUNICIPIO", "DTNASC", "PARTO_D", "SEXO_D", "PESO",
        "GESTACAO_D", "CONSULTAS_D", "RACA_D",
        "FAIXA_IDADE", "ESCOLARIDADE_D", "GRAVIDEZ_D",
    ]
    st.dataframe(dados[colunas].head(200), use_container_width=True, height=420)

    st.download_button(
        "Baixar recorte em CSV",
        dados[colunas].to_csv(index=False).encode("utf-8"),
        file_name="nascimentos_filtrados.csv",
        mime="text/csv",
    )
    