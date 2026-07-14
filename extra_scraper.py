# Web scraping de alguns produtos que compõem a cesta básica, pesquisados no site Extra Mercado, utilizando Selenium.
# O script pesquisa os itens e exporta os resultados para CSV.

import csv
import re
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

# Função para formatar o preço de string para float
def formata_preco(texto_preco):
    try:
        # Remove "R$", remove espaços e troca a vírgula pelo ponto
        preco_limpo = texto_preco.replace("R$", "").replace(" ", "").replace(",", ".")
        return float(preco_limpo)

    except Exception:
        return 0.0   # Retorno de segurança caso venha algo inesperado



driver = webdriver.Chrome() # Seleciona o Google Chrome como navegador
driver.get("https://www.extramercado.com.br") # Acessa a URL do Extra Mercado
wait = WebDriverWait(driver, 10) # Define como padrão 10s para o Explicit Wait

# Aceita os cookies do site
botao_cookie = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//button[text()='Estou ciente']"))
    )
botao_cookie.click()

# Lista de produtos
lista = [
    "leite integral 1l",
    "feijao carioca 1kg",
    "arroz branco 5kg",
    "farinha de mandioca 500g",
    "cafe em po 500g",
    "acucar refinado 1kg",
    "oleo de soja 900ml",
    "margarina cremosa 500g",
    "carne acem",
    "batata inglesa",
    "tomate italiano",
    "pao frances",
    "banana nanica"
]

contador = 0 # Contagem de produtos totais encontrados

resultados = [] # Lista final de resultados

for item in lista:
    print(f"Buscando: {item}")

    # Limpa a barra de pesquisa e seleciona o item a ser pesquisado
    barra_pesquisa = wait.until(
        EC.element_to_be_clickable((By.ID, 'input-search'))
    )
    barra_pesquisa.send_keys(Keys.CONTROL, "a")
    barra_pesquisa.send_keys(Keys.DELETE)

    barra_pesquisa.send_keys(item)
    barra_pesquisa.send_keys(Keys.ENTER)


    # Tenta pegar um elemento antigo caso exista (medida de controle para evitar o erro StaleElement)
    try:
        elemento_antigo = driver.find_elements(By.CSS_SELECTOR, "div[class*='Card-sc']")[0]
    except Exception:
        elemento_antigo = None

    # Caso tenha elemento antigo espera ele ficar obsoleto antes de realizar novas tentativas de identificação
    if elemento_antigo:
        wait.until(EC.staleness_of(elemento_antigo))

    # Espera manual estratégica para ajudar a evitar o erro StaleElement
    sleep(2)

    # Encontra o total de resultados da busca
    total_elementos = wait.until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "p[aria-label*='produtos encontrados']")
        )
    )
    texto = total_elementos.text # X produtos encontrados
    total_produtos = int(re.search(r"\d+", texto).group())
    print(f"Produtos esperados: {total_produtos}")


    # Aguarda todos os resultados da busca aparecerem
    produtos = wait.until(
        EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "div[class*='Card-sc']")
        )
    )

    print(f"Quantidade encontrada: {len(produtos)}")

    tentativas = 0

    # Se não foram carregados todos os produtos, scrolla a página até o final
    while tentativas < 5:

        qtd_ant = len(produtos)

        if total_produtos == qtd_ant:
            break

        print(f"Tentativa nº {tentativas+1}")
        print(f"Produtos carregados: {len(produtos)}")


        # Scrolla até o final da página, metade por vez, depois até o topo, esperando carregar todos os produtos
        driver.execute_script("window.scrollTo(0, 0);")
        metade = driver.execute_script("return document.body.scrollHeight / 2")
        driver.execute_script(f"window.scrollTo(0, {metade});")
        sleep(1)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")


        # Sleep estratégico para evitar erro de carregamento
        sleep(2)

        # Tentativa de pegar todos produtos
        produtos = wait.until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "div[class*='Card-sc']")
            )
        )

        tentativas += 1


    print(f"Quantidade final encontrada: {len(produtos)}")
    contador += len(produtos)

    # Com todos os produtos carregados, salva nome e preço
    for produto in produtos:
        try:
            nome = produto.find_element(
                By.CSS_SELECTOR, "a[title]"
            ).get_attribute("title")

            # Caso o produto esteja sem estoque, coloca o preço como zero
            try:
                preco = produto.find_element(
                    By.CSS_SELECTOR, "p[class*='PriceValue']"
                ).text
            except Exception:
                preco = '0,00'

            # Cria uma lista de listas com os resultados das buscas
            resultados.append(
                [
                    item.upper(),
                    nome.upper(),
                    formata_preco(preco)
                ]
            )

        except Exception:
            continue


# Exporta um arquivo csv com os resultados
with open("cesta_basica_extra.csv", "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)

    # Header
    writer.writerow(["PRODUTO", "NOME", "PREÇO (R$)"])

    for trio in resultados:
      writer.writerow([trio[0], trio[1], trio[2]])


print(f"Total de produtos encontrados: {contador}")

driver.quit()
print("Finalizado")