import logging
from sqlalchemy import inspect, text
from app.config.settings import settings
from app.data.models import engine, SessionLocal, Trade

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def validate_and_migrate_db():
    logger.info(f"Inspecionando o banco de dados: {settings.DATABASE_URL}")
    
    # Inspeciona a estrutura atual do banco de dados conectado
    inspector = inspect(engine)
    
    if "trades" not in inspector.get_table_names():
        logger.warning("Tabela 'trades' não encontrada. Execute o init_db() no main.py primeiro.")
        return False

    # Extrai o nome de todas as colunas existentes na tabela trades
    columns = [col['name'] for col in inspector.get_columns("trades")]
    
    migrated = False
    with engine.connect() as conn:
        try:
            if "stop_loss" not in columns:
                logger.info("🔧 Adicionando coluna 'stop_loss' na tabela trades...")
                conn.execute(text("ALTER TABLE trades ADD COLUMN stop_loss FLOAT;"))
                migrated = True
                
            if "take_profit" not in columns:
                logger.info("🔧 Adicionando coluna 'take_profit' na tabela trades...")
                conn.execute(text("ALTER TABLE trades ADD COLUMN take_profit FLOAT;"))
                migrated = True
                
            if migrated:
                conn.commit()
                logger.info("✅ Migração estrutural concluída com sucesso!")
            else:
                logger.info("✅ Estrutura OK: As colunas de risco já existem no banco de dados.")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao tentar alterar a estrutura da tabela: {e}")
            conn.rollback()
            return False

def test_trailing_stop_persistence():
    """Valida se o ORM consegue gravar, ler e atualizar as novas colunas."""
    logger.info("Iniciando teste de persistência do Trailing Stop...")
    db = SessionLocal()
    try:
        # 1. Cria um trade simulado com SL e TP iniciais
        dummy_trade = Trade(
            symbol="TEST_TS/USDT",
            side="buy",
            entry_price=50000.0,
            quantity=0.1,
            status="open",
            stop_loss=49000.0,
            take_profit=52000.0
        )
        db.add(dummy_trade)
        db.commit()
        logger.info(f"Trade de teste criado com ID {dummy_trade.id} | SL Inicial: {dummy_trade.stop_loss}")
        
        # 2. Simula o Trailing Stop movendo o SL para cima
        novo_sl = 49500.0
        dummy_trade.stop_loss = novo_sl
        db.commit()
        
        # 3. Verifica a persistência forçando uma releitura do banco
        db.refresh(dummy_trade)
        assert dummy_trade.stop_loss == novo_sl, "Falha: O banco não salvou a atualização do Trailing Stop."
        logger.info(f"✅ Atualização do Trailing Stop validada! Novo SL persistido: {dummy_trade.stop_loss}")
        
        # 4. Limpa a sujeira do teste
        db.delete(dummy_trade)
        db.commit()
        logger.info("🗑️ Trade de teste removido da base de dados.")
        
    except Exception as e:
        logger.error(f"❌ Falha no teste de persistência: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    if validate_and_migrate_db():
        test_trailing_stop_persistence()