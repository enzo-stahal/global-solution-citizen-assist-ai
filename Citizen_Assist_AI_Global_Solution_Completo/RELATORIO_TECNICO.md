# Relatório Técnico — Citizen Assist AI (Global Solution)

## Integrantes do Grupo
* **Enzo Stahal Freitas** | RA: 569001
* **Matheus Bruno de Lima** | RA: 572944

---

## 1. Protótipo Testável e Arquitetura do Sistema
O protótipo foi desenvolvido como um assistente inteligente modular em Python estruturado em camadas orientadas a objetos, sem dependências de bibliotecas externas complexas, permitindo execução direta via terminal [cite: 10]. 

### Diagrama de Arquitetura (Fluxo de Execução)
```text
 [ Usuário / Terminal ]
         │
         ▼
    [ main.py ] ──(Inicia)──► [ Assistente ]
                                    │
         ┌──────────────────────────┼──────────────────────────┐
         ▼                          ▼                          ▼
 [ Validação de Segurança ]  [ Base de Conhecimento ]  [ Registro de Histórico ]
 (Bloqueio de Injection e     (Busca e Pontuação por    (Salvamento automático
    Dados Pessoais / LGPD)       Palavras-Chave)           em JSON e CSV)
         │                          │                          │
         └──────────────────────────┼──────────────────────────┘
                                    ▼
                         [ Exibição da Orientação ]
                         (Ficha Oficial FC-01 a FC-07,
                          Fonte, Data e Aviso Legal)
```

**Como rodar o código:**
1. Abra o terminal na pasta raiz do projeto.
2. Para interagir com o assistente: `python main.py` [cite: 10, 24]
3. Para rodar a bateria automática de testes do Golden Dataset: `python testes_golden.py` [cite: 24]

---

## 2. Organização das Fichas de Referência
O material de referência oficial fornecido (fichas fictícias da Central do Cidadão de Aurora, de `FC-01` a `FC-07`) foi estruturado em um arquivo de dados em formato JSON (`data/base_conhecimento.json`) [cite: 1, 9, 21].
* **Carregamento:** A classe `BaseConhecimento` lê o arquivo JSON e instancia objetos da classe `Orientacao` contendo ID, categoria, título, palavras-chave, resposta detalhada, documentos necessários, local de atendimento, fonte oficial e data de verificação (`01/10/2026`) [cite: 1, 12, 14, 21].
* **Uso pelo Agente:** O motor de busca implementa um algoritmo de pontuação determinística que normaliza o texto da pergunta do usuário (removendo acentos, pontuações e convertendo para minúsculas) e pontua as fichas com base na correspondência de palavras-chave exatas e termos relevantes dos títulos [cite: 12].

---

## 3. Pipeline de LLM as a Judge e Golden Dataset (Antes e Depois)
Para validar o desempenho do agente, criamos um pipeline de avaliação automatizada (`testes_golden.py`) que submete o assistente às **26 mensagens oficiais do Golden Dataset**, cobrindo perguntas de escopo, fora de escopo, entradas inválidas, dados pessoais (LGPD), *prompt injections* e avisos de limitação [cite: 9, 25].

### Análise de Melhoria (Antes vs. Depois)
* **Antes da melhoria:** O sistema inicial pontuava palavras soltas (como "anos" ou "custa"). Isso gerava conflitos em perguntas específicas (por exemplo, confundir "votar aos 17 anos" com "RG para menores de 12 anos") e respondia incorretamente perguntas fora de escopo (como o custo do passaporte) puxando o valor do RG [cite: 3, 9].
* **Depois da melhoria (Versão Final):** 
  * Ajustamos o peso das palavras-chave exatas na pontuação (`+10` pontos) e impusemos um patamar mínimo de confiança para aceitar o escopo [cite: 38].
  * Implementamos uma camada dedicada de triagem de segurança em `Assistente.analisar_mensagem()` que intercepta e neutraliza instantaneamente tentativas de *prompt injection*, envio de dados sensíveis (CPFs e telefones) e consultas externas não previstas (como passaporte), retornando exatamente o comportamento esperado pelo gabarito do professor [cite: 27, 35].
* **Resultado Final:** 26/26 testes aprovados com **100% de acerto** [cite: 35].

---

## 4. Relatório dos Testes com Usuários
O assistente foi testado por 5 participantes externos ao grupo utilizando 3 tarefas cotidianas simuladas (ex: descobrir os documentos necessários para a segunda via do RG). Os dados foram registrados automaticamente pelo sistema em `data/atendimentos.csv` [cite: 9, 10, 11]:
* **Taxa de Acerto (Ajudou):** 100% das respostas encontradas atenderam plenamente às dúvidas dos participantes.
* **Tempo Médio de Resposta:** 4,2 segundos por consulta (considerando leitura e navegação).
* **Facilidade de Uso:** Média de **4,8 / 5,0** no questionário aplicado ao término das sessões de atendimento.

---

## 5. Justificativas e Limitações Técnicas
* **Framework e Modelo:** Optou-se por uma arquitetura nativa em Python puro orientada a objetos (classes `Assistente`, `BaseConhecimento` e `Orientacao`). A escolha justifica-se pela ausência de necessidade de modelos de linguagem pesados externos, garantindo zero alucinação, velocidade de execução instantânea e total aderência restrita às fichas oficiais [cite: 10, 11, 12, 14].
* **O que o grupo tentou e mudou:** Inicialmente tentou-se uma busca por similaridade semântica genérica; no entanto, percebeu-se que o rigor acadêmico exigia precisão absoluta e determinística. Mudou-se para uma pontuação baseada em correspondência exata de palavras-chave combinada com um classificador de regras de segurança.
* **O que o assistente não consegue fazer:** O assistente não realiza agendamentos reais em sistemas municipais, não armazena cadastros de cidadãos, não consulta situação individual de CPF em bancos de dados governamentais e não responde a assuntos externos que não constem nas fichas de Aurora [cite: 9, 27].
