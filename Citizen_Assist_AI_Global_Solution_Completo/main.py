"""Citizen Assist AI — Central do Cidadão de Aurora (Terminal)."""
import os
from base_conhecimento import BaseConhecimento
from assistente import Assistente

PASTA = os.path.dirname(os.path.abspath(__file__))


def main():
    base = BaseConhecimento(os.path.join(PASTA, "data", "base_conhecimento.json"))
    if not base.carregar():
        print(f"Erro: {base.erro}")
        print("Corrija o arquivo data/base_conhecimento.json e rode novamente.")
        return

    assistente = Assistente("Citizen Assist AI - Aurora", base,
                            os.path.join(PASTA, "data", "historico.json"),
                            os.path.join(PASTA, "data", "atendimentos.csv"))

    print(f"=== {assistente.nome} ===")
    print("Orientação sobre documentos pessoais (Central do Cidadão de Aurora).")
    print("Aviso: NÃO digite CPF, RG, telefone ou e-mail. Este assistente NÃO é um canal oficial.")

    try:
        while True:
            print("\n=== Menu Principal ===")
            print("1. Fazer uma pergunta (texto livre)")
            print("2. Navegar por categorias")
            print("3. Ver indicadores de atendimento")
            print("4. Exportar relatório CSV")
            print("0. Sair")
            opcao = input("Escolha: ").strip()
            if opcao == "1":
                assistente.perguntar()
            elif opcao == "2":
                assistente.navegar()
            elif opcao == "3":
                assistente.exibir_indicadores()
            elif opcao == "4":
                assistente.exportar_csv()
            elif opcao == "0":
                assistente.encerrar()
                break
            else:
                print("Opção inválida. Digite de 0 a 4.")
    except (KeyboardInterrupt, EOFError):
        print("\nEncerrando...")
        assistente.exportar_csv()


if __name__ == "__main__":
    main()
