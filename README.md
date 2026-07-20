Atue como um Arquiteto de Sistemas Quantitativos, Desenvolvedor Python Sênior, Engenheiro de Dados e Especialista em Trading Algorítmico.

Objetivo:

Desenvolver um bot de trade automatizado para criptomoedas com arquitetura profissional, foco em segurança, backtesting, paper trading e posterior operação em produção.

Requisitos do Projeto

1. Stack Tecnológica

Python 3.11+

CCXT para integração com exchanges

Pandas e NumPy para processamento de dados

ta ou pandas-ta para indicadores técnicos

Backtesting.py ou vectorbt para backtests

PostgreSQL para armazenamento de dados

Docker para conteinerização

Telegram Bot API para alertas

2. Estrutura do Projeto

crypto_bot/
├── app/
│   ├── strategies/
│   ├── risk_management/
│   ├── execution/
│   ├── data/
│   ├── notifications/
│   └── config/
├── tests/
├── docker/
├── docs/
├── requirements.txt
└── README.md

3. Funcionalidades Mínimas (MVP)

Coleta de Dados

OHLCV de BTC/USDT, ETH/USDT e SOL/USDT

Timeframes: 1m, 5m, 15m e 1h

Persistência em banco de dados

Estratégia Inicial

Implementar uma estratégia de trend following utilizando:

EMA 20

EMA 50

RSI

Filtro de tendência pela EMA 200

Regras:

Compra: EMA20 > EMA50 e RSI > 55

Venda: EMA20 < EMA50 ou RSI < 45

Gestão de Risco

Risco máximo de 1% do capital por operação

Stop Loss configurável

Take Profit configurável

Limite de operações simultâneas

Backtesting

Gerar relatório com:

Win Rate

Profit Factor

Sharpe Ratio

Drawdown Máximo

Retorno acumulado

Paper Trading

Modo simulado sem envio de ordens reais

Registro de todas as operações

Monitoramento

Enviar alertas para Telegram:

Entrada em operação

Saída da operação

Erro crítico

Resumo diário

4. Requisitos de Segurança

Não expor chaves de API no código

Usar variáveis de ambiente

Implementar logs estruturados

Tratar exceções de rede e API

Adicionar retry automático para falhas temporárias

5. Entregáveis

Forneça:

Arquitetura completa do sistema

Código-fonte modularizado

Arquivo requirements.txt

Dockerfile

docker-compose.yml

Exemplo de arquivo .env

Testes unitários básicos

Documentação de instalação e uso

Exemplo de backtest

Guia para implantação em AWS EC2

6. Boas Práticas

Utilizar tipagem com type hints

Aplicar princípios SOLID

Separar claramente estratégia, execução e risco

Adicionar logs detalhados

Escrever código pronto para expansão futura

7. Expansões Futuras

Deixe pontos de extensão para:

Machine Learning

Análise de sentimento

Múltiplas estratégias

Arbitragem

Grid Trading

Dashboard web

8. Formato da Resposta

Apresente a solução em etapas:

Visão geral da arquitetura

Estrutura de pastas

Implementação dos módulos principais

Configuração do ambiente

Execução do backtest

Execução em paper trading

Deploy em produção

Seja detalhado e forneça código executável sempre que possível.
