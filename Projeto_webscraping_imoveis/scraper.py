from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re
import json
import datetime

BASE_URL = "https://www.chavesnamao.com.br"

def fetch_html(url: str) -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            locale="pt-BR",
            viewport={"width": 1280, "height": 800}
        )
        page = context.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        html = page.content()
        browser.close()
        return html

def parse_listing(html: str) -> list:
    soup = BeautifulSoup(html, 'html.parser')
    links = soup.find_all('a', href=re.compile(r'/imovel/'))
    urls = list({BASE_URL + a['href'] for a in links if '/imovel/' in a['href']})
    return urls

def parse_imovel(html: str, url: str) -> dict:
    soup = BeautifulSoup(html, 'html.parser')

    id_match = re.search(r'id-(\d+)', url)
    imovel_id = id_match.group(1) if id_match else None

    dados = {}
    for tag in soup.find_all('script', type='application/ld+json'):
        try:
            obj = json.loads(tag.string)
            graph = obj.get('@graph', [obj])
            for item in graph:
                if item.get('@type') == 'RealEstateListing':
                    dados = item
                    break
        except:
            continue

    about    = dados.get('about', {})
    oferta   = about.get('offers', {})
    imovel   = oferta.get('itemOffered', {})

    tipo_negocio = 'Aluguel' if 'para-alugar' in url or 'temporada' in url.lower() else 'Venda'

    tipo_map = {
        'Apartment': 'Apartamento', 'House': 'Casa',
        'SingleFamilyResidence': 'Casa', 'CommercialProperty': 'Comercial'
    }
    tipo_imovel = tipo_map.get(imovel.get('@type', ''), imovel.get('@type'))

    address = imovel.get('address', {})
    bairro  = address.get('addressLocality', '').split(',')[0].strip()

    # --- CORREÇÃO DA ÁREA M2 ---
    floor_size = imovel.get('floorSize', {})
    raw_area = floor_size.get('value')
    area = None

    if raw_area:
        try:
            if isinstance(raw_area, str):
                raw_area_clean = raw_area.replace('.', '').replace(',', '.')
                area = int(float(raw_area_clean))
            else:
                area = int(raw_area)
        except:
            area = None

    # --- REFINAMENTO DO PREÇO ---
    raw_preco = oferta.get('price')
    preco = None
    if raw_preco:
        try:
            if isinstance(raw_preco, str):
                preco = float(raw_preco.replace('.', '').replace(',', '.'))
            else:
                preco = float(raw_preco)
        except:
            preco = None

    # Filtro de segurança (opcional, setando como None se a área for irreal)
    if area and area <= 5:
        pass

    preco_m2 = round(preco / area, 2) if preco and area and area > 0 else None

    quartos   = imovel.get('numberOfBedrooms') or imovel.get('numberOfRooms')
    banheiros = imovel.get('numberOfBathroomsTotal')
    quartos   = int(quartos)   if quartos   else None
    banheiros = int(banheiros) if banheiros else None

    garagem_tag = soup.find('p', attrs={'aria-label': 'Garagens'})
    garagens = None
    if garagem_tag:
        b_tag = garagem_tag.find('b')
        if b_tag:
            try:
                garagens = int(b_tag.get_text(strip=True))
            except:
                pass

    def extrair_valor_label(label: str):
        for p in soup.find_all('p', class_=re.compile('text-body-sm')):
            if label.lower() in p.get_text().lower():
                next_p = p.find_next_sibling('p')
                if next_p:
                    texto_limpo = next_p.get_text().replace('.', '').replace(',', '.')
                    match = re.search(r'[\d.]+', texto_limpo)
                    if match:
                        return float(match.group())
        return None

    condominio = extrair_valor_label('Condomínio')
    iptu       = extrair_valor_label('IPTU')
    titulo     = dados.get('name') or about.get('name')


    # ==========================================
    # --- CAPTURA DA URL DA FOTO DE CAPA ---
    # Colocamos o bloco exatamente aqui!
    # ==========================================
    url_foto = None
    # Tentativa 1: Buscar no JSON estruturado (campo image)
    raw_image = imovel.get('image') or dados.get('image')
    if raw_image:
        if isinstance(raw_image, list) and len(raw_image) > 0:
            url_foto = raw_image[0]
        elif isinstance(raw_image, dict):
            url_foto = raw_image.get('url')
        else:
            url_foto = raw_image

    # Tentativa 2: Se não achou no JSON, busca na Meta Tag 'og:image' do HTML
    if not url_foto:
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            url_foto = og_image['content']
    # ==========================================
# Define a cidade dinamicamente lendo a URL do portal
    cidade_nome = "Lauro de Freitas" if "lauro-de-freitas" in url else "Salvador"
    
    return {
        "id":           imovel_id,
        "titulo":       titulo,
        "url_foto":     url_foto,  # <--- E AQUI ela é enviada para o banco!
        "url":          url,
        "tipo_negocio": tipo_negocio,
        "tipo_imovel":  tipo_imovel,
        "bairro":       bairro,
        "cidade":       cidade_nome,
        "estado":       "BA",
        "area_m2":      area,
        "quartos":      quartos,
        "banheiros":    banheiros,
        "garagens":     garagens,
        "preco_atual":  preco,
        "preco_m2":     preco_m2,
        "condominio":   condominio,
        "iptu":         iptu,
        "data_coleta":  datetime.date.today().isoformat()
    }