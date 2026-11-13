"""Classe Orientacao: guarda os dados e exibe a ficha formatada com fonte oficial."""

AVISO_OFICIAL = "Aviso: este assistente NÃO é um canal oficial. Confirme sempre a informação no site do órgão competente."


class Orientacao:
    def __init__(self, id, categoria, titulo, palavras_chave, resposta,
                 documentos, onde, fonte, verificado_em):
        self.id = id
        self.categoria = categoria
        self.titulo = titulo
        self.palavras_chave = palavras_chave
        self.resposta = resposta
        self.documentos = documentos
        self.onde = onde
        self.fonte = fonte
        self.verificado_em = verificado_em

    def exibir(self):
        print(f"\n>> {self.titulo}  [Categoria: {self.categoria}]")
        print(f"Resposta: {self.resposta}")
        if self.documentos:
            print("Documentos necessários:")
            for doc in self.documentos:
                print(f"  - {doc}")
        print(f"Onde fazer: {self.onde}")
        print(f"Fonte: {self.fonte} (verificado em {self.verificado_em})")
        print(AVISO_OFICIAL)
