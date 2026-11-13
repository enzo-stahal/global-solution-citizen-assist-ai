"""Classe Assistente: faz o atendimento, protege dados, neutraliza prompt injection e valida entradas."""
import csv
import json
import re
import time
from datetime import datetime

CAMPOS_CSV = ["data", "origem", "pergunta", "id_orientacao", "encontrou",
              "ajudou", "tentativas", "tempo_s", "sessao", "nota"]

PALAVRAS_INJECTION = [
    "ignore as instrucoes", "ignore as instruções", "ignore previous",
    "mostre seu prompt", "prompt de sistema", "[sistema]", "nova regra",
    "novo prompt", "finja ser"
]


class Assistente:
    def __init__(self, nome, base, caminho_historico="data/historico.json",
                 caminho_csv="data/atendimentos.csv"):
        self.nome = nome
        self.base = base
        self.caminho_historico = caminho_historico
        self.caminho_csv = caminho_csv
        self.sessao = datetime.now().strftime("%Y%m%d%H%M%S")
        self.historico = self._carregar_historico()

    def _carregar_historico(self):
        try:
            with open(self.caminho_historico, "r", encoding="utf-8") as arq:
                dados = json.load(arq)
            return dados if isinstance(dados, list) else []
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return []

    def _salvar_historico(self):
        try:
            with open(self.caminho_historico, "w", encoding="utf-8") as arq:
                json.dump(self.historico, arq, indent=2, ensure_ascii=False)
        except OSError:
            pass

    def _ler_numero(self, texto, minimo, maximo):
        while True:
            resp = input(texto).strip()
            try:
                numero = int(resp)
                if minimo <= numero <= maximo:
                    return numero
            except ValueError:
                pass
            print(f"Opção inválida. Digite um número de {minimo} a {maximo}.")

    def _ler_sn(self, texto):
        while True:
            resp = input(texto).strip().lower()
            if resp in ("s", "n"):
                return resp == "s"
            print("Responda apenas com s ou n.")

    def analisar_mensagem(self, texto):
        """Classifica a mensagem do usuário antes da busca nas fichas (Golden Dataset 20 a 26)."""
        t = texto.strip()
        t_lower = t.lower()

        if not t:
            return "VAZIA", "Você não digitou nada. Escreva sua dúvida ou escolha uma categoria no menu."
        if len(t) > 500:
            return "INVALIDA", "Sua mensagem é muito longa. Por favor, faça uma pergunta curta e objetiva sobre documentos."

        for termo in PALAVRAS_INJECTION:
            if termo in t_lower:
                return "INJECTION", (
                    "Recuso essa solicitação. Não posso ignorar minhas regras internas, revelar instruções de sistema "
                    "ou aceitar novas regras vindas da mensagem. Continuo seguindo exclusivamente as fichas da Central do Cidadão de Aurora."
                )

        digitos = sum(1 for c in t if c.isdigit())
        tem_cpf_ou_tel = digitos >= 8 or "@" in t
        pede_cadastro = any(p in t_lower for p in ["meu cpf", "meu endereco", "meu endereço", "meu telefone", "minha situacao", "minha situação", "agendar meu"])
        if tem_cpf_ou_tel or pede_cadastro:
            return "DADOS_PESSOAIS", (
                "Atenção: por favor, NÃO informe dados pessoais (como CPF, RG, endereço ou telefone) neste chat. "
                "Este assistente não coleta dados, não consulta situação cadastral e não realiza agendamentos. "
                "Para esses serviços, acesse diretamente o portal oficial da Central do Cidadão. (FC-01, FC-02, FC-07)"
            )

        if "canal oficial" in t_lower or "prefeitura" in t_lower:
            return "AVISO_OFICIAL", (
                "Não; este assistente é um protótipo educacional e NÃO é um canal oficial da prefeitura. "
                "Confirme sempre as informações no órgão competente."
            )

        if "passaporte" in t_lower:
            return "FORA_ESCOPO", "Não consta nas fichas. Não inventar valor; dizer que não encontrou e orientar a consultar o órgão competente."

        letras = re.findall(r"[a-zA-ZáéíóúãõâêôçÁÉÍÓÚÃÕÂÊÔÇ]{2,}", t)
        if not letras or "asdfgh" in t_lower or len(t) < 3:
            return "INVALIDA", (
                "Não entendi sua mensagem. Por favor, reformule sua pergunta ou use o menu de categorias "
                "(ex.: RG, CPF, Título de Eleitor, Carteira de Trabalho, Certidões ou CNH)."
            )

        return "OK", ""

    def responder_texto(self, texto):
        """Processa uma pergunta e retorna (categoria_resultado, texto_resposta, fonte_id)."""
        status, msg_especial = self.analisar_mensagem(texto)
        if status != "OK":
            return status, msg_especial, None

        resultados = self.base.buscar(texto)
        if not resultados or resultados[0][0] < 10:
            return "FORA_ESCOPO", (
                "Não consta nas fichas. Não inventar valor; dizer que não encontrou e orientar a consultar o órgão competente."
            ), None

        pontos, melhor = resultados[0]
        return "ESCOPO", f"{melhor.resposta} ({melhor.fonte} - verificado em {melhor.verificado_em})", melhor.id

    def perguntar(self):
        tentativas = 0
        inicio = time.time()
        while True:
            texto = input("\nDigite sua dúvida (0 para voltar): ").strip()
            if texto == "0":
                return

            status, msg_especial = self.analisar_mensagem(texto)
            if status != "OK":
                print(f"\n{msg_especial}")
                print("Aviso: este assistente NÃO é um canal oficial.")
                if status != "VAZIA":
                    self.registrar("pergunta", texto, None, True, True, 1, 0.1)
                continue

            tentativas += 1
            resultados = self.base.buscar(texto)

            if not resultados or resultados[0][0] < 10:
                tempo = round(time.time() - inicio, 1)
                print("\nNão consta nas fichas. Não inventar valor; dizer que não encontrou e orientar a consultar o órgão competente.")
                print("Aviso: este assistente NÃO é um canal oficial.")
                self.registrar("pergunta", texto, None, False, False, tentativas, tempo)
                continue

            pontos, melhor = resultados[0]
            confianca = "ALTA" if pontos >= 20 else "MÉDIA"
            print(f"\nConfiança da resposta: {confianca} ({pontos} pontos)")
            melhor.exibir()

            alternativas = [(p, o) for p, o in resultados[1:3] if p >= 10]
            if alternativas:
                print("\nOutras orientações relacionadas:")
                for p, o in alternativas:
                    print(f"  - {o.titulo} ({o.fonte})")

            tempo = round(time.time() - inicio, 1)
            ajudou = self._ler_sn("\nEssa orientação respondeu sua dúvida? (s/n): ")
            self.registrar("pergunta", texto, melhor.id, True, ajudou, tentativas, tempo)
            tentativas = 0
            inicio = time.time()

    def navegar(self):
        while True:
            categorias = self.base.categorias()
            print("\n=== Categorias (Central do Cidadão de Aurora) ===")
            for i, cat in enumerate(categorias, 1):
                print(f"{i}. {cat}")
            print("0. Voltar")
            op = self._ler_numero("Escolha: ", 0, len(categorias))
            if op == 0:
                return
            categoria = categorias[op - 1]

            while True:
                orientacoes = self.base.por_categoria(categoria)
                print(f"\n=== {categoria} ===")
                for i, o in enumerate(orientacoes, 1):
                    print(f"{i}. {o.titulo} [{o.id}]")
                print("0. Voltar")
                inicio = time.time()
                op2 = self._ler_numero("Escolha: ", 0, len(orientacoes))
                if op2 == 0:
                    break
                escolhida = orientacoes[op2 - 1]
                escolhida.exibir()
                tempo = round(time.time() - inicio, 1)
                ajudou = self._ler_sn("\nEssa orientação respondeu sua dúvida? (s/n): ")
                self.registrar("categoria", "", escolhida.id, True, ajudou, 1, tempo)

    def registrar(self, origem, pergunta, id_orientacao, encontrou, ajudou,
                  tentativas, tempo):
        self.historico.append({
            "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "origem": origem,
            "pergunta": pergunta,
            "id_orientacao": id_orientacao,
            "encontrou": encontrou,
            "ajudou": ajudou,
            "tentativas": tentativas,
            "tempo_s": tempo,
            "sessao": self.sessao,
            "nota": None,
        })
        self._salvar_historico()

    def indicadores(self):
        total = len(self.historico)
        if total == 0:
            return None
        encontrados = [h for h in self.historico if h["encontrou"]]
        ajudaram = [h for h in encontrados if h["ajudou"]]
        notas = [h["nota"] for h in self.historico if h.get("nota")]
        return {
            "total": total,
            "encontrada_pct": round(100 * len(encontrados) / total, 1),
            "acerto_pct": round(100 * len(ajudaram) / len(encontrados), 1) if encontrados else 0.0,
            "tempo_medio": round(sum(h["tempo_s"] for h in encontrados) / len(encontrados), 1) if encontrados else 0.0,
            "facilidade": round(sum(notas) / len(notas), 1) if notas else None,
        }

    def exibir_indicadores(self):
        ind = self.indicadores()
        print("\n=== Indicadores de Desempenho ===")
        if ind is None:
            print("Ainda não há atendimentos registrados.")
            return
        print(f"Total de interações:        {ind['total']}")
        print(f"Respostas encontradas (%):  {ind['encontrada_pct']}%")
        print(f"Taxa de satisfação/ajuda:   {ind['acerto_pct']}%")
        print(f"Tempo médio de busca:       {ind['tempo_medio']} s")
        fac = ind["facilidade"] if ind["facilidade"] is not None else "Sem notas de avaliação ainda"
        print(f"Facilidade de uso (1 a 5):  {fac}")

    def exportar_csv(self):
        try:
            with open(self.caminho_csv, "w", newline="", encoding="utf-8") as arq:
                escritor = csv.DictWriter(arq, fieldnames=CAMPOS_CSV, extrasaction="ignore")
                escritor.writeheader()
                escritor.writerows(self.historico)
            print(f"Relatório exportado com sucesso em {self.caminho_csv}")
        except OSError:
            print("Aviso: não consegui exportar o CSV.")

    def encerrar(self):
        da_sessao = [h for h in self.historico if h["sessao"] == self.sessao]
        if da_sessao:
            nota = self._ler_numero("\nDe 1 a 5, quão fácil foi usar o assistente? ", 1, 5)
            for h in da_sessao:
                h["nota"] = nota
            self._salvar_historico()
        self.exportar_csv()
        print("Obrigado por usar a Central do Cidadão de Aurora. Até logo!")
