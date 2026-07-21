import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from sqlalchemy import create_engine

# Configuração da página
st.set_page_config(page_title="Crypto Bot | Live Monitor", layout="wide")
st.title("🤖 Crypto Bot - Monitoramento em Tempo Real")

# Conexão com o banco de dados (Ajuste a porta se o seu Postgres no Docker expuser outra)
# Como o dashboard rodará localmente fora do docker, usamos localhost
DATABASE_URL = "postgresql://user:password@localhost:5432/cryptobot"

@st.cache_resource
def init_connection():
    return create_engine(DATABASE_URL)

engine = init_connection()

def get_open_trades():
    query = """
    SELECT id, symbol, side, entry_price, quantity, stop_loss, take_profit, entry_time 
    FROM trades 
    WHERE status = 'open'
    """
    return pd.read_sql(query, engine)

def get_latest_price(symbol):
    query = f"""
    SELECT close, timestamp 
    FROM candles 
    WHERE symbol = '{symbol}' 
    ORDER BY timestamp DESC LIMIT 1
    """
    df = pd.read_sql(query, engine)
    if not df.empty:
        return df['close'].iloc[0]
    return 0.0

# --- Lógica de Atualização Automática ---
if st.button("🔄 Atualizar Dados"):
    st.rerun()

st.markdown("---")

trades_df = get_open_trades()

if trades_df.empty:
    st.info("Nenhuma operação aberta no momento.")
else:
    st.subheader(f"Posições Abertas ({len(trades_df)})")
    
    # Criando métricas para cada trade
    for index, row in trades_df.iterrows():
        symbol = row['symbol']
        entry_price = row['entry_price']
        sl = row['stop_loss']
        tp = row['take_profit']
        qty = row['quantity']
        
        current_price = get_latest_price(symbol)
        
        # Cálculo de PnL flutuante
        if row['side'] == 'buy':
            pnl = (current_price - entry_price) * qty
            pnl_pct = ((current_price - entry_price) / entry_price) * 100
        else:
            pnl = (entry_price - current_price) * qty
            pnl_pct = ((entry_price - current_price) / entry_price) * 100

        # Layout em colunas
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Ativo", symbol, f"{row['side'].upper()}")
        col2.metric("Preço Atual", f"${current_price:.2f}")
        col3.metric("PnL Flutuante", f"${pnl:.2f}", f"{pnl_pct:.2f}%")
        col4.metric("Stop Loss (Trailing)", f"${sl:.2f}" if pd.notna(sl) else "N/A")
        col5.metric("Take Profit", f"${tp:.2f}" if pd.notna(tp) else "N/A")

        # --- Gráfico Visual da Posição ---
        fig = go.Figure()

        # Adiciona o preço atual
        fig.add_trace(go.Indicator(
            mode = "number+gauge",
            value = current_price,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text' : "Distância dos Alvos"},
            gauge = {
                'axis': {'range': [sl * 0.98 if pd.notna(sl) else current_price * 0.95, 
                                   tp * 1.02 if pd.notna(tp) else current_price * 1.05]},
                'bar': {'color': "lightgray"},
                'steps': [
                    {'range': [0, sl], 'color': "rgba(255, 99, 132, 0.3)"}, # Zona de Risco (Abaixo do SL)
                    {'range': [sl, entry_price], 'color': "rgba(255, 206, 86, 0.2)"}, # Zona Neutra/Leve Perda
                    {'range': [entry_price, tp], 'color': "rgba(75, 192, 192, 0.2)"} # Zona de Lucro
                ],
                'threshold': {
                    'line': {'color': "blue", 'width': 3},
                    'thickness': 0.75,
                    'value': entry_price
                }
            }
        ))

        st.plotly_chart(fig, use_container_width=True)
        st.markdown("---")

def get_closed_trades():
    query = """
    SELECT symbol, side, entry_price, exit_price, pnl, exit_time 
    FROM trades 
    WHERE status = 'closed'
    ORDER BY exit_time DESC
    """
    return pd.read_sql(query, engine)

st.markdown("---")
st.subheader("📚 Histórico de Operações Fechadas (PnL Realizado)")

closed_trades_df = get_closed_trades()

if closed_trades_df.empty:
    st.info("Nenhuma operação foi fechada ainda.")
else:
    # Calcula o PnL total
    total_pnl = closed_trades_df['pnl'].sum()
    win_rate = (len(closed_trades_df[closed_trades_df['pnl'] > 0]) / len(closed_trades_df)) * 100
    
    # Exibe métricas de performance
    col1, col2, col3 = st.columns(3)
    col1.metric("Resultado Total Acumulado (USDT)", f"${total_pnl:.2f}")
    col2.metric("Total de Trades Finalizados", len(closed_trades_df))
    col3.metric("Taxa de Acerto (Win Rate)", f"{win_rate:.1f}%")
    
    # Formata a tabela para ficar bonita no dashboard
    st.dataframe(
        closed_trades_df.style.format({
            'entry_price': '${:.2f}',
            'exit_price': '${:.2f}',
            'pnl': '${:.2f}'
        }).map(lambda val: 'color: green' if val > 0 else 'color: red', subset=['pnl']),
        use_container_width=True
    )