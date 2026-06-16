from scraper import fetch_html, parse_listing, parse_imovel
from database import salvar_imovel

# ============================================================
# CONFIGURAÇÕES — VENDA (Alto Padrão)
# ============================================================
VENDA = {
    "locais": [
        # Salvador
        ("ba-salvador", "corredor-da-vitoria"),
        ("ba-salvador", "jaguaribe"),
        ("ba-salvador", "patamares"),
        ("ba-salvador", "graca"),
        ("ba-salvador", "imbui"),
        ("ba-salvador", "alphaville-i"),
        ("ba-salvador", "alphaville-ii"),
        ("ba-salvador", "cidade-jardim"),
        ("ba-salvador", "jardim-apipema"),
        ("ba-salvador", "ondina"),
        ("ba-salvador", "pituba"),
        ("ba-salvador", "barra"),
        ("ba-salvador", "itaigara"),
        ("ba-salvador", "horto-florestal"),
        
        # Lauro de Freitas
        ("ba-lauro-de-freitas", "vilas-do-atlantico"),
        ("ba-lauro-de-freitas", "buraquinho"),
        ("ba-lauro-de-freitas", "ipitanga"),
    ],
    "url_base": "https://www.chavesnamao.com.br/imoveis-a-venda/{cidade}/{bairro}/",
    "preco_min": 400000,
    "preco_max": 20000000,
}

# ============================================================
# CONFIGURAÇÕES — ALUGUEL (Alto Padrão)
# ============================================================
ALUGUEL = {
    "locais": [
        # Salvador
        ("ba-salvador", "patamares"),
        ("ba-salvador", "jaguaribe"),
        ("ba-salvador", "pituba"),
        ("ba-salvador", "barra"),
        ("ba-salvador", "itaigara"),
        ("ba-salvador", "horto-florestal"),
        ("ba-salvador", "graca"),
        ("ba-salvador", "corredor-da-vitoria"),
        ("ba-salvador", "campo-grande"),
        ("ba-salvador", "vila-Laura"),
        ("ba-salvador", "ondina"),
        ("ba-salvador", "rio-vermelho"),
        ("ba-salvador", "alphaville-i"),
        ("ba-salvador", "alphaville-ii"),

        # Lauro de Freitas
        ("ba-lauro-de-freitas", "vilas-do-atlantico"),
        ("ba-lauro-de-freitas", "buraquinho"),
        ("ba-lauro-de-freitas", "ipitanga"),
    ],
    "url_base": "https://www.chavesnamao.com.br/imoveis-para-alugar/{cidade}/{bairro}/",
    "preco_min": 2000,
    "preco_max": 35000,
}

PAGINAS = 4

def coletar(config: dict, tipo: str):
    total_salvos  = 0
    total_erros   = 0
    total_pulados = 0

    # Desempacotando a tupla (cidade_url, bairro) no loop
    for cidade_url, bairro in config["locais"]:
        print(f"\n{'='*50}")
        print(f"{tipo.upper()} | Cidade: {cidade_url.upper()} | Bairro: {bairro.upper()}")
        print(f"{'='*50}")

        for pg in range(1, PAGINAS + 1):
            url_lista = (
                config["url_base"].format(cidade=cidade_url, bairro=bairro)
                + f"?priceMin={config['preco_min']}&priceMax={config['preco_max']}&pg={pg}"
            )
            print(f"  Página {pg}...")

            try:
                html_lista   = fetch_html(url_lista)
                urls_imoveis = parse_listing(html_lista)

                if not urls_imoveis:
                    print(f"  Sem imóveis. Pulando...")
                    break

                for url in urls_imoveis:
                    try:
                        html_imovel = fetch_html(url)
                        imovel      = parse_imovel(html_imovel, url)

                        if not imovel['id']:
                            total_pulados += 1
                            continue

                        salvar_imovel(imovel)
                        total_salvos += 1
                        print(f"    ✓ {imovel['id']} | {imovel['bairro']} | R$ {imovel['preco_atual']}")

                    except Exception as e:
                        total_erros += 1
                        print(f"    ✗ Erro em {url}: {e}")

            except Exception as e:
                print(f"  Erro na listagem: {e}")

    return total_salvos, total_erros, total_pulados


def run():
    print("\n🏠 INICIANDO COLETA — ALTO PADRÃO BA\n")

    s1, e1, p1 = coletar(VENDA,   "VENDA")
    s2, e2, p2 = coletar(ALUGUEL, "ALUGUEL")

    print(f"\n{'='*50}")
    print(f"RESUMO FINAL")
    print(f"  Venda   — Salvos: {s1} | Erros: {e1} | Pulados: {p1}")
    print(f"  Aluguel — Salvos: {s2} | Erros: {e2} | Pulados: {p2}")
    print(f"  Total   — Salvos: {s1+s2}")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    run()