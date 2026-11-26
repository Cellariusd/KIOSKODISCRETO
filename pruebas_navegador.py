"""Prueba opcional de extremo a extremo del HTML local (Playwright + Chromium)."""
import os
import re
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

with sync_playwright() as w:
    navegador = w.chromium.launch(executable_path=os.environ.get('CHROME_BIN') or None)
    p = navegador.new_page(viewport={'width': 390, 'height': 844})
    errores = []
    p.on('pageerror', lambda e: errores.append(str(e)))
    p.goto(Path(__file__).with_name('index.html').resolve().as_uri())
    def tab(t):
        if not p.locator('#tabs').is_visible(): p.locator('#menuMovil').click()
        grupo=p.locator('#tabs details').filter(has=p.locator(f'[data-tab="{t}"]'))
        if not grupo.evaluate('e=>e.open'): grupo.locator('summary').click()
        p.locator(f'[data-tab="{t}"]').click()
    def click(id): p.locator('#'+id).click()
    assert p.evaluate('document.documentElement.scrollWidth <= innerWidth')
    assert p.locator('#botonesMonedas button').count() == 3
    click('abrirQR'); expect(p.locator('#dialogQR')).to_be_visible()
    expect(p.locator('#vistaQR img')).to_be_visible()
    assert p.locator('#vistaQR img').evaluate('img => img.complete && img.naturalWidth > 0')
    expect(p.locator('#dialogQR .qrLink')).to_have_attribute('href', 'https://cellariusd.github.io/KIOSKODISCRETO/')
    p.keyboard.press('Escape'); expect(p.locator('#dialogQR')).to_be_hidden()
    corazon = p.locator('[data-like]').first
    formulario = 'https://docs.google.com/forms/d/e/1FAIpQLScVBRp-DVsvGOZj_CEmmAUU-Ad5p1rhXZtmrtdB_t57Xa5k5A/viewform'
    # Comprobar navegación sin enviar votos ni depender de Google en la prueba.
    p.context.route(formulario, lambda r: r.fulfill(status=200, content_type='text/html', body='<h1>Formulario de prueba</h1>'))
    aperturas = []
    p.context.on('page', lambda pagina: aperturas.append(pagina))
    def activar_corazon(boton):
        with p.context.expect_page() as nueva:
            boton.click()
        registro = nueva.value
        registro.wait_for_url(formulario)
        assert registro.evaluate('window.opener === null')
        registro.close()
        expect(boton).to_have_attribute('aria-pressed', 'true')
    activar_corazon(corazon)
    expect(corazon).to_contain_text('Te gusta')
    p.reload(); expect(corazon).to_have_attribute('aria-pressed', 'true')
    corazon.click(); expect(corazon).to_have_attribute('aria-pressed', 'false')
    assert len(aperturas) == 1, 'Recargar o quitar el corazón no debe abrir el registro'
    for ancho in (320, 390, 760, 1280):
        p.set_viewport_size({'width': ancho, 'height': 844})
        assert p.evaluate('document.documentElement.scrollWidth <= innerWidth'), ancho
        click('abrirQR')
        assert p.locator('#dialogQR').evaluate('e => e.scrollWidth <= e.clientWidth'), ancho
        click('cerrarQR')
    p.set_viewport_size({'width': 390, 'height': 844})
    assert p.locator('#qrCont, #btnQR, #enlaceForm').count() == 0
    # Pedido de dos unidades. Una devolución no despacha nada; el vuelto no paga la unidad siguiente.
    p.locator('#pedido summary').click()
    p.locator('[data-producto="chocolate"]').click(); click('ticketAdd')
    p.locator('[data-producto="galletas"]').click(); click('ticketAdd')
    expect(p.locator('#ticketTotal')).to_contain_text('S/ 12'); click('ticketPagar')
    monedas=p.locator('#botonesMonedas button'); monedas.last.click(); click('btnCancelar')
    expect(p.locator('#ticketLista li')).to_have_count(2)
    monedas.last.click(); monedas.nth(1).click()
    expect(p.locator('#dspBandeja')).to_contain_text('Chocolate. Vuelto: S/ 1'); expect(p.locator('#txtProducto')).to_have_text('Galletas')
    p.select_option('#tipoDiagrama','mealy'); expect(p.locator('#svgContenedor svg')).to_be_visible()
    assert p.evaluate('document.documentElement.scrollWidth <= innerWidth')
    monedas.last.click(); monedas.first.click(); expect(p.locator('#ticketEstado')).to_contain_text('2 entregados · S/ 12')
    p.select_option('#tipoDiagrama','moore'); click('btnReiniciar')
    for producto, sprite, nombre in [('gaseosa','gaseosa','Gaseosa'), ('chocolate','chocolate','Chocolate'), ('galletas','galletas','Galletas'), ('energia','bebida',p.evaluate('cfg.producto'))]:
        click('btnReiniciar')
        p.locator('[data-producto="'+producto+'"]').click()
        expect(p.locator('#txtProducto')).to_have_text(nombre)
        expect(p.locator('#productoExhibido')).to_have_attribute('href', '#'+sprite)
        p.locator('#botonesMonedas button').first.click()
        for boton in p.locator('[data-producto]').all(): expect(boton).to_be_disabled()
        p.locator('#botonesMonedas button').last.click()
        expect(p.locator('#dspBandeja')).to_contain_text('Producto entregado: '+nombre)
        expect(p.locator('#spritePremio')).to_have_attribute('href', '#'+sprite)
        vuelto = 6 - p.evaluate('precio()')
        assert p.locator('#monedasVuelto [data-valor]').evaluate_all('(es) => es.reduce((s,e)=>s+Number(e.dataset.valor),0)') == vuelto
        expect(p.locator('#catalogo button').first).to_be_enabled()
    # Cambiar la siguiente selección no cambia el producto ya entregado.
    p.locator('[data-producto="chocolate"]').click()
    expect(p.locator('#spritePremio')).to_have_attribute('href', '#bebida')
    click('btnReiniciar')
    p.locator('#botonesMonedas button').nth(1).click(); click('btnCancelar')
    expect(p.locator('#vueltoResumen')).to_have_text('Devuelto: S/ 2')
    expect(p.locator('#monedasVuelto [data-valor]')).to_have_attribute('data-valor', '2')
    p.emulate_media(reduced_motion='reduce')
    assert p.locator('.monedaSalida').evaluate('e => getComputedStyle(e).animationName') == 'none'
    p.emulate_media(reduced_motion='no-preference')
    click('btnReiniciar'); assert p.locator('#monedasVuelto [data-valor]').count() == 0
    p.locator('[data-producto="energia"]').click()
    for _ in range(p.evaluate('precio()')): p.locator('#botonesMonedas button').first.click()
    expect(p.locator('#dspEstado')).to_contain_text('D_0')
    assert p.locator('#monedasVuelto [data-valor]').count() == 0
    click('btnReiniciar')
    p.locator('#botonesMonedas button').first.click(); click('btnCancelar')
    expect(p.locator('#dspEstado')).to_contain_text('S_0')
    expect(p.locator('#tblHistorial tbody tr').first).to_contain_text('Devuelve S/ 1')
    click('btnEjemplo'); expect(p.locator('#modo')).to_have_value('hoja'); expect(p.locator('#btnEjemplo')).to_be_enabled(timeout=26000)
    assert p.locator('#botonesMonedas button').count() == 2
    # Diagrama Moore ↔ Mealy (en la pestaña Máquina, donde vive el selector).
    p.select_option('#tipoDiagrama', 'mealy')
    svg = p.locator('#svgContenedor')
    txt_mealy = svg.text_content() or ''
    assert svg.locator('rect').count() == 0, 'Mealy no debe dibujar estados D_v'
    assert svg.locator('circle').count() == p.evaluate('precio()'), 'Mealy dibuja un círculo por cada S_i'
    assert 'D_' not in txt_mealy and '—' in txt_mealy, txt_mealy
    assert 'Mealy' in (p.locator('#microDiagrama').text_content() or '')
    expect(p.locator('#ultimoPaso')).to_contain_text('S_4 → S_0')
    expect(svg).to_have_attribute('aria-label', re.compile('Estado actual: S_0'))
    p.select_option('#filtroMoneda','2')
    assert '+2 / V0' in svg.text_content() and '+1 /' not in svg.text_content()
    assert p.evaluate('document.documentElement.scrollWidth <= innerWidth')
    p.select_option('#tipoDiagrama', 'moore')
    assert 'D_' in (svg.text_content() or ''), 'Moore restaura los estados de despacho'
    assert 'Moore' in (p.locator('#microDiagrama').text_content() or '')
    tab('tablas'); assert p.locator('#tblMoore th').count() == 4
    tab('sorpresa'); p.locator('#sorSecuencia').fill('10');click('btnRevelar');expect(p.locator('#sorMsg')).to_contain_text('modo activo')
    p.locator('#sorSecuencia').fill('1');click('btnRevelar');expect(p.locator('#sorTraza')).to_be_empty()
    p.locator('#sorEstado').fill('S_1');p.locator('#sorVuelto').fill('0');click('btnRevelar');expect(p.locator('#sorMsg')).to_contain_text('✅')
    tab('recurrencia');click('btnVerRec'); p.locator('#recLista button').last.click();expect(p.locator('#btnEjemplo')).to_be_enabled(timeout=8000)
    expect(p.locator('#dspEstado')).to_contain_text('D_0');p.locator('#botonesMonedas button').first.click()
    expect(p.locator('#svgContenedor')).to_contain_text('D_0 → (+1) → S_1')
    tab('numeracion');click('btnVerNum'); n=2026+p.evaluate('cfg.K');expect(p.locator('#binTitulo')).to_contain_text(format(n,'b')+'₂');expect(p.locator('#hexTitulo')).to_contain_text(format(n,'X')+'₁₆')
    tab('megusta');expect(p.locator('#formLike')).to_be_hidden()
    activar_corazon(p.locator('#tab-megusta [data-like]'))
    assert len(aperturas) == 2
    # La tienda mantiene cesta y recorrido al cambiar de modelo, también después de un rechazo.
    tab('tienda'); add=p.locator('[data-merc="agregar"]').first; add.click()
    p.locator('[data-merc="quitar"]').click(); expect(p.locator('#mercTotal')).to_have_text('Total simulado: S/ 0')
    add.click(); add.click(); expect(p.locator('#mercTotal')).to_have_text('Total simulado: S/ 16')
    def comprar(a): p.locator(f'[data-merc="{a}"]').click()
    comprar('revisar'); p.select_option('#mercPerfil','vencida'); comprar('tarjeta')
    expect(add).to_be_disabled(); expect(p.locator('#mercIndicacion')).to_contain_text('tarjeta vencida')
    pasos=p.locator('#mercTraza li').count(); p.select_option('#mercModelo','mealy'); assert p.locator('#mercTraza li').count()==pasos
    expect(p.locator('#mercUltimo')).to_contain_text('Tarjeta vencida / Mostrar rechazo')
    comprar('reintentar'); p.select_option('#mercPerfil','basica'); comprar('tarjeta'); comprar('importe')
    expect(p.locator('#mercIndicacion')).to_contain_text('saldo insuficiente')
    comprar('reintentar'); p.select_option('#mercPerfil','campus')
    for a in ('tarjeta','importe','enviar','recibir'): comprar(a)
    expect(p.locator('#mercFlujo [aria-current]')).to_have_text('Entregado'); expect(p.locator('#mercTotal')).to_contain_text('16')
    p.set_viewport_size({'width':320,'height':700}); assert p.evaluate('document.documentElement.scrollWidth <= innerWidth')
    p.locator('[data-merc="nuevo"]').click(); expect(p.locator('#mercFlujo [aria-current]')).to_have_text('Catálogo')
    tab('config'); expect(p.locator('.bitacora li')).to_have_count(3)
    p.emulate_media(media='print'); expect(p.locator('.bitacora')).to_be_visible(); expect(p.locator('#imprimirBitacora')).to_be_hidden(); expect(p.locator('header')).to_be_hidden()
    assert not errores, errores
    navegador.close(); print('Web móvil: compra, devolución, ejemplo, tablas, predicción, recurrencia, numeración y votación estática OK.')
