#Bloco 1: Importações, Configuração da Página e Curva Epagri
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from streamlit_gsheets import GSheetsConnection

st.set_page_config(
    page_title="Inteligência de Mercado - Bananicultura SC",
    page_icon="🍌",
    layout="wide",
    initial_sidebar_state="expanded"
)

CUSTO_OPERACIONAL_KG = 0.71
CUSTO_OPERACIONAL_CX20 = 14.19

CURVA_EPAGRI = {
    "Caturra": {
        1: 1.24, 2: 1.49, 3: 1.45, 4: 1.15, 5: 0.96, 6: 0.71,
        7: 1.00, 8: 1.50, 9: 2.12, 10: 2.46, 11: 2.06, 12: 1.96
    },
    "Prata": {
        1: 1.95, 2: 2.10, 3: 2.25, 4: 2.35, 5: 2.15, 6: 1.91,
        7: 2.20, 8: 2.48, 9: 2.46, 10: 2.15, 11: 1.90, 12: 1.95
    }
}
#Bloco 2: Conexão e Funções do Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

COLUNAS_VENDAS = (
    "Data", "Produtor_ID", "Variedade", "Entrega", "Qualidade",
    "Ensacamento", "Unidade", "Valor_Informado", "Preco_Liquido_Kg",
    "Volume_Kg", "Canal"
)

def carregar_dados():
    try:
        df = conn.read(worksheet="Vendas", ttl=5)
        df = df.dropna(how="all")
        if df.empty:
            return pd.DataFrame(columns=list(COLUNAS_VENDAS))
        df["Data"] = pd.to_datetime(df["Data"]).dt.date
        df["Preco_Liquido_Kg"] = pd.to_numeric(df["Preco_Liquido_Kg"])
        df["Volume_Kg"] = pd.to_numeric(df["Volume_Kg"])
        return df
    except Exception:
        return pd.DataFrame(columns=list(COLUNAS_VENDAS))

def salvar_registro(novo_registro):
    df = carregar_dados()
    novo_registro["Data"] = str(novo_registro["Data"])
    df_novo = pd.DataFrame((novo_registro,))
    if not df.empty:
        df["Data"] = df["Data"].astype(str)
    df_atualizado = pd.concat((df, df_novo), ignore_index=True)
    conn.update(worksheet="Vendas", data=df_atualizado)

def carregar_referencias():
    try:
        df_ref = conn.read(worksheet="Referencias", ttl=5)
        df_ref = df_ref.dropna(how="all")
        refs = {}
        for _, row in df_ref.iterrows():
            refs[str(row["Variedade"]).strip()] = {
                "cepea_roca": float(row["cepea_roca"]),
                "ceasa_atacado": float(row["ceasa_atacado"])
            }
        refs["ultima_atualizacao"] = str(df_ref.iloc[0]["ultima_atualizacao"])
        return refs
    except Exception:
        return {
            "Caturra": {"cepea_roca": 1.65, "ceasa_atacado": 2.45},
            "Prata": {"cepea_roca": 2.25, "ceasa_atacado": 3.30},
            "ultima_atualizacao": "12/11/2026"
        }

def salvar_referencias(novas_refs):
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")
    df_novo = pd.DataFrame((
        {"Variedade": "Caturra", "cepea_roca": novas_refs["Caturra"]["cepea_roca"], "ceasa_atacado": novas_refs["Caturra"]["ceasa_atacado"], "ultima_atualizacao": agora},
        {"Variedade": "Prata", "cepea_roca": novas_refs["Prata"]["cepea_roca"], "ceasa_atacado": novas_refs["Prata"]["ceasa_atacado"], "ultima_atualizacao": agora}
    ))
    conn.update(worksheet="Referencias", data=df_novo)

REFERENCIAS_EXTERNAS = carregar_referencias()
#Bloco 3: Barra Lateral e Abas Principais
st.sidebar.image("https://flaticon.com", width=60)
st.sidebar.title("Associação de Bananicultores")
st.sidebar.markdown("**Inteligência Comercial & Custos**")

produtor_id = st.sidebar.text_input("Código do Associado (Ex: ASSOC01):", value="ASSOC01").strip().upper()
st.sidebar.caption("🔒 *Sua identidade e o nome do comprador nunca são exibidos no painel público.*")

st.sidebar.divider()
st.sidebar.subheader("📊 Parâmetros Epagri/Cepa")
st.sidebar.metric("Custo Operacional (COT)", f"R$ {CUSTO_OPERACIONAL_CX20:.2f} / cx 20kg", f"R$ {CUSTO_OPERACIONAL_KG:.2f} / kg")
st.sidebar.caption("Base: Propriedade modal 5 ha | Produtividade 35 t/ha (Safra 2025/26).")

st.sidebar.divider()
with st.sidebar.expander("⚙️ Atualizar Índices (Cepea / CEASA)"):
    st.caption(f"Última atualização: {REFERENCIAS_EXTERNAS.get('ultima_atualizacao', 'Hoje')}")
    
    st.markdown("**Banana Caturra (R$/kg)**")
    cat_cepea = st.number_input("Cepea Roça (Caturra):", value=float(REFERENCIAS_EXTERNAS["Caturra"]["cepea_roca"]), step=0.05, format="%.2f")
    cat_ceasa = st.number_input("CEASA Atacado (Caturra):", value=float(REFERENCIAS_EXTERNAS["Caturra"]["ceasa_atacado"]), step=0.05, format="%.2f")
    
    st.markdown("**Banana Prata (R$/kg)**")
    pra_cepea = st.number_input("Cepea Roça (Prata):", value=float(REFERENCIAS_EXTERNAS["Prata"]["cepea_roca"]), step=0.05, format="%.2f")
    pra_ceasa = st.number_input("CEASA Atacado (Prata):", value=float(REFERENCIAS_EXTERNAS["Prata"]["ceasa_atacado"]), step=0.05, format="%.2f")
    
    if st.button("💾 Salvar Novas Cotações", use_container_width=True):
        novas = {
            "Caturra": {"cepea_roca": cat_cepea, "ceasa_atacado": cat_ceasa},
            "Prata": {"cepea_roca": pra_cepea, "ceasa_atacado": pra_ceasa}
        }
        salvar_referencias(novas)
        st.success("Índices salvos no Google Sheets!")
        st.rerun()

st.title("🍌 Painel Inteligente da Bananicultura")
aba_painel, aba_registro, aba_custos = st.tabs((
    "📈 Painel de Preços (Estilo Power BI)",
    "📝 Registrar Venda (20 seg)",
    "🧮 Simulador de Custos (Epagri)"
))

df = carregar_dados()

hoje = datetime.now().date()
limite_15d = hoje - timedelta(days=15)
if not df.empty:
    registros_usuario = df[(df["Produtor_ID"] == produtor_id) & (df["Data"] >= limite_15d)]
    usuario_colaborador = len(registros_usuario) > 0
else:
    usuario_colaborador = False
#Bloco 4: Aba 1 — Painel de Preços
with aba_painel:
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    with col_f1:
        filtro_variedade = st.selectbox("Variedade:", ("Caturra", "Prata"))
    with col_f2:
        filtro_entrega = st.selectbox("Forma de Entrega:", ("Embalada no Galpão", "Cacho na Roça", "Todas"))
    with col_f3:
        filtro_qualidade = st.selectbox("Qualidade:", ("1ª (Extra/Export.)", "2ª (Mercado Interno)", "Todas"))
    with col_f4:
        filtro_dias = st.selectbox("Período de Análise:", (1, 7, 15, 30), index=1, format_func=lambda x: "Hoje (24h)" if x == 1 else f"Últimos {x} dias")

    if df.empty:
        st.info("👋 **Bem-vindo ao Painel da Associação!** O banco de dados na nuvem está pronto. Vá até a aba **'📝 Registrar Venda (20 seg)'** para lançar a primeira cotação e ativar os gráficos!")
    else:
        data_corte = hoje - timedelta(days=filtro_dias - 1)
        df_filtrado = df[(df["Variedade"] == filtro_variedade) & (df["Data"] >= data_corte)]
        
        if filtro_entrega != "Todas":
            df_filtrado = df_filtrado[df_filtrado["Entrega"] == filtro_entrega]
        if filtro_qualidade != "Todas":
            df_filtrado = df_filtrado[df_filtrado["Qualidade"] == filtro_qualidade]

        if df_filtrado.empty:
            st.warning("Ainda não há registros para essa combinação de filtros. Tente ampliar o período ou registre uma venda!")
        else:
            total_kg = df_filtrado["Volume_Kg"].sum()
            preco_medio_kg = (df_filtrado["Preco_Liquido_Kg"] * df_filtrado["Volume_Kg"]).sum() / total_kg
            preco_medio_cx20 = preco_medio_kg * 20
            preco_min_kg = df_filtrado["Preco_Liquido_Kg"].min()
            preco_max_kg = df_filtrado["Preco_Liquido_Kg"].max()
            margem_cx20 = preco_medio_cx20 - CUSTO_OPERACIONAL_CX20

            mes_atual = hoje.month
            ref_epagri_kg = CURVA_EPAGRI[filtro_variedade][mes_atual]

            if preco_medio_kg <= CUSTO_OPERACIONAL_KG * 1.10:
                st.error(f"🔴 **ALERTA DE PREJUÍZO OPERACIONAL:** O preço médio líquido (R$ {preco_medio_kg:.2f}/kg) está abaixo ou muito próximo do Custo Operacional de referência da Epagri (R$ {CUSTO_OPERACIONAL_KG:.2f}/kg).")
            elif preco_medio_kg < ref_epagri_kg * 0.90:
                st.warning(f"🟡 **ATENÇÃO — PRESSÃO DE COMPRADOR:** A cotação na região (R$ {preco_medio_kg:.2f}/kg) está mais de 10% abaixo da referência histórica Epagri para este mês (R$ {ref_epagri_kg:.2f}/kg). Consulte outros canais antes de fechar carga.")
            else:
                st.success(f"🟢 **MERCADO FIRME:** O preço líquido médio (R$ {preco_medio_kg:.2f}/kg) cobre o custo operacional e está alinhado ou acima da referência histórica Epagri (R$ {ref_epagri_kg:.2f}/kg).")

            kpi1, kpi2, kpi3, kpi4 = st.columns(4)
            kpi1.metric("Preço Líquido Médio (Cx 20kg)", f"R$ {preco_medio_cx20:.2f}", f"R$ {preco_medio_kg:.2f} / kg")
            kpi2.metric("Faixa Negociada (Mín - Máx)", f"R$ {preco_min_kg:.2f} a R$ {preco_max_kg:.2f}", f"Diferença de R$ {(preco_max_kg - preco_min_kg)*20:.2f}/cx")
            kpi3.metric("Margem Líquida Estimada", f"R$ {margem_cx20:.2f} / cx", f"{((preco_medio_kg / CUSTO_OPERACIONAL_KG) - 1)*100:.1f}% sobre o custo")
            kpi4.metric("Volume Monitorado", f"{total_kg / 20:,.0f} caixas", f"{len(df_filtrado)} cargas registradas")

            st.divider()

            if not usuario_colaborador:
                st.info("🔒 **Modo Visualização Básica:** Registre pelo menos uma venda na aba **'Registrar Venda'** para desbloquear os gráficos de **Preço por Ensacamento**, **Comparativo por Canal** e **Cotações Externas (Cepea / CEASA)**.")
            else:
                col_g1, col_g2 = st.columns((2, 1))
                with col_g1:
                    st.subheader("📉 Evolução Diária vs. Referências de Mercado")
                    df_diario = df_filtrado.groupby("Data").apply(
                        lambda x: (x["Preco_Liquido_Kg"] * x["Volume_Kg"]).sum() / x["Volume_Kg"].sum()
                    ).reset_index(name="Preco_Associacao")

                    fig_linha = go.Figure()
                    fig_linha.add_trace(go.Scatter(
                        x=df_diario["Data"], y=df_diario["Preco_Associacao"],
                        mode="lines+markers", name="Média Associação (R$/kg)",
                        line=dict(color="#2E7D32", width=4)
                    ))
                    
                    cepea_val = REFERENCIAS_EXTERNAS[filtro_variedade]["cepea_roca"]
                    ceasa_val = REFERENCIAS_EXTERNAS[filtro_variedade]["ceasa_atacado"]
                    
                    fig_linha.add_hline(y=ref_epagri_kg, line_dash="dash", line_color="blue", annotation_text=f"Histórico Epagri (R$ {ref_epagri_kg:.2f})")
                    fig_linha.add_hline(y=cepea_val, line_dash="dot", line_color="orange", annotation_text=f"Cepea Norte SC (R$ {cepea_val:.2f})")
                    fig_linha.add_hline(y=CUSTO_OPERACIONAL_KG, line_dash="solid", line_color="red", annotation_text=f"Custo Epagri (R$ {CUSTO_OPERACIONAL_KG:.2f})")
                    
                    fig_linha.update_layout(height=380, margin=dict(l=20, r=20, t=30, b=20), yaxis_title="R$ / kg líquido")
                    st.plotly_chart(fig_linha, use_container_width=True)

                with col_g2:
                    st.subheader("🌐 Balizadores Externos")
                    st.caption(f"Atualizado em: {REFERENCIAS_EXTERNAS.get('ultima_atualizacao', 'Hoje')}")
                    st.metric("CEASA/SC (Atacado)", f"R$ {ceasa_val:.2f} / kg", f"Margem cadeia: +R$ {(ceasa_val - preco_medio_kg):.2f}/kg")
                    st.metric("HF Brasil / Cepea (Roça SC)", f"R$ {cepea_val:.2f} / kg", f"Dif. local: R$ {(preco_medio_kg - cepea_val):+.2f}/kg")
                    st.metric("Curva Epagri/Cepa (Mês)", f"R$ {ref_epagri_kg:.2f} / kg")
                    
                    st.markdown("**Consultar Boletins Oficiais:**")
                    st.link_button("📄 Cotação Diária CEASA/SC", "https://ceasa.sc.gov.br", use_container_width=True)
                    st.link_button("📊 Estatísticas HF Brasil / Cepea", "https://hfbrasil.org.br", use_container_width=True)
                    st.link_button("🌱 Infoagro / Epagri-Cepa SC", "https://infoagro.sc.gov.br", use_container_width=True)

                col_g3, col_g4 = st.columns(2)
                with col_g3:
                    st.subheader("🛍️ Impacto do Ensacamento no Preço (R$/kg)")
                    df_ensac = df_filtrado.groupby("Ensacamento")["Preco_Liquido_Kg"].mean().reset_index()
                    fig_ensac = px.bar(df_ensac, x="Ensacamento", y="Preco_Liquido_Kg", color="Ensacamento", text_auto=".2f", labels={"Preco_Liquido_Kg": "Preço Médio (R$/kg)", "Ensacamento": "Tipo de Manejo"})
                    fig_ensac.update_layout(showlegend=False, height=320)
                    st.plotly_chart(fig_ensac, use_container_width=True)

                with col_g4:
                    st.subheader("🚚 Preço Médio por Canal de Venda (R$/kg)")
                    df_canal = df_filtrado.groupby("Canal")["Preco_Liquido_Kg"].mean().reset_index()
                    fig_canal = px.bar(df_canal, x="Canal", y="Preco_Liquido_Kg", color="Canal", text_auto=".2f", labels={"Preco_Liquido_Kg": "Preço Médio (R$/kg)", "Canal": "Comprador"})
                    fig_canal.update_layout(showlegend=False, height=320)
                    st.plotly_chart(fig_canal, use_container_width=True)
#Bloco 5: Aba 2 — Formulário de Registro Rápido de Venda
with aba_registro:
    st.subheader("📝 Lançar Nova Venda (Leva 20 segundos)")
    st.markdown("Preencha os dados da sua última carga para alimentar o painel da comunidade e liberar as análises completas.")

    with st.form("form_venda", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            data_venda = st.date_input("1. Data da Venda:", value=hoje)
            variedade = st.radio("2. Variedade:", ("Caturra", "Prata"), horizontal=True)
            entrega = st.radio("3. Forma de Entrega:", ("Embalada no Galpão", "Cacho na Roça"))
        with c2:
            qualidade = st.selectbox("4. Qualidade / Padrão:", ("1ª (Extra/Export.)", "2ª (Mercado Interno)", "Descarte/Indústria"))
            ensacamento = st.selectbox("5. Ensacamento do Cacho:", ("Sem ensacamento", "Plástico", "TNT", "Com Defensivo"))
            unidade = st.selectbox("6. Unidade Negociada:", ("Caixa 20 kg", "Caixa 22 kg", "Por Quilo (kg)"))
        with c3:
            valor_recebido = st.number_input("7. Valor Recebido (R$):", min_value=0.10, max_value=200.00, value=36.00, step=0.50)
            qtd_unidades = st.number_input("8. Quantidade (Caixas ou Kg):", min_value=1, max_value=50000, value=150)
            canal = st.selectbox("9. Canal de Venda:", ("Atravessador", "Cooperativa/Assoc.", "Supermercado/Ceasa"))

        submitted = st.form_submit_button("✅ Salvar Cotação na Nuvem", use_container_width=True)

        if submitted:
            if unidade == "Caixa 20 kg":
                preco_kg_liq = valor_recebido / 20.0
                vol_kg = qtd_unidades * 20
            elif unidade == "Caixa 22 kg":
                preco_kg_liq = valor_recebido / 22.0
                vol_kg = qtd_unidades * 22
            else:
                preco_kg_liq = valor_recebido
                vol_kg = qtd_unidades

            novo_reg = {
                "Data": data_venda,
                "Produtor_ID": produtor_id if produtor_id else "ANONIMO",
                "Variedade": variedade,
                "Entrega": entrega,
                "Qualidade": qualidade,
                "Ensacamento": ensacamento,
                "Unidade": unidade,
                "Valor_Informado": valor_recebido,
                "Preco_Liquido_Kg": round(preco_kg_liq, 4),
                "Volume_Kg": vol_kg,
                "Canal": canal
            }
            salvar_registro(novo_reg)
            st.success(f"Venda salva na nuvem! Preço líquido: **R$ {preco_kg_liq:.2f}/kg** (Equivalente a **R$ {preco_kg_liq*20:.2f}** na caixa de 20 kg).")
            st.rerun()
#Bloco 6: Aba 3 — Simulador de Custos (Matriz Epagri)
with aba_custos:
    st.subheader("🧮 Simulador de Custo de Produção (Matriz Epagri/Cepa)")
    st.markdown("Ajuste a produtividade da sua propriedade e a variação dos insumos para descobrir seu **Preço Mínimo de Equilíbrio**.")

    col_s1, col_s2 = st.columns((1, 1))
    with col_s1:
        area_ha = st.number_input("Área em Produção (hectares):", min_value=0.5, max_value=200.0, value=5.0, step=0.5)
        produtividade_t = st.slider("Sua Produtividade Média (toneladas/ha/ano):", min_value=15.0, max_value=50.0, value=35.0, step=1.0)
        var_insumos = st.slider("Variação no preço dos Adubos/Defensivos (%):", min_value=-30, max_value=50, value=0, step=5)
        var_mao_obra = st.slider("Variação no custo de Mão de Obra (%):", min_value=-20, max_value=50, value=0, step=5)

    custo_base_ha = 24836.81
    parcela_insumos = (custo_base_ha * 0.398) * (1 + var_insumos / 100)
    parcela_mo = (custo_base_ha * 0.325) * (1 + var_mao_obra / 100)
    parcela_outros = custo_base_ha * 0.277

    custo_ajustado_ha = parcela_insumos + parcela_mo + parcela_outros
    producao_kg_ha = produtividade_t * 1000
    custo_kg_produtor = custo_ajustado_ha / producao_kg_ha
    custo_cx20_produtor = custo_kg_produtor * 20

    with col_s2:
        st.info("### Seu Ponto de Equilíbrio Calculado")
        st.metric("Custo por Caixa (20 kg)", f"R$ {custo_cx20_produtor:.2f}", f"Referência Epagri: R$ {CUSTO_OPERACIONAL_CX20:.2f}")
        st.metric("Custo por Quilo (R$/kg)", f"R$ {custo_kg_produtor:.2f}", f"Referência Epagri: R$ {CUSTO_OPERACIONAL_KG:.2f}")
        st.metric("Custo Total Anual da Propriedade", f"R$ {custo_ajustado_ha * area_ha:,.2f}", f"Produção estimada: {produtividade_t * area_ha:,.0f} toneladas/ano")

