#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
GoLismero 2.0 - The web knife - Copyright (C) 2011-2014

Golismero project site: https://github.com/golismero
Golismero project mail: contact@golismero-project.com

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""

# Fix the module load path.
if __name__ == "__main__":
    import os, sys
    from os import path
    root = path.split(path.abspath(__file__))[0]
    if not root:  # if it fails use cwd instead
        root = path.abspath(os.getcwd())
    root = path.abspath(path.join(root, ".."))
    thirdparty_libs = path.join(root, "thirdparty_libs")
    if path.exists(thirdparty_libs):
        sys.path.insert(0, thirdparty_libs)
        sys.path.insert(0, root)


url = [
"http://entretenimiento.terra.es/vuelve-alvaro-el-superman-de-gran-hermano-14,e676a7215295d310VgnVCM3000009acceb0aRCRD.html",
"http://deportes.terra.es/equipos/seleccion",
"http://noticias.terra.es/mundo/renuncia-y-sucesor-de-benedicto-xvi/la-eleccion-del-papa-con-terra-desde-dentro-y-al-minuto,e4657913b045d310VgnVCM5000009ccceb0aRCRD.html",
"http://www.terra.es/chat/",
"http://deportes.terra.es/equipos/real-madrid",
"http://vidayestilo.terra.es/casa/",
"http://www.recetasderechupete.com",
"http://entretenimiento.terra.es/corazon/carmen-martinez-bordiu-condenada-a-pagar-70-trajes,84e9aa4bca85d310VgnVCM20000099cceb0aRCRD.html",
"http://noticias.terra.es/margallo-no-tiene-ni-la-menor-idea-de-si-corinna-tuvo-escolta,833107f71255d310VgnCLD2000000dc6eb0aRCRD.html",
"http://www.invertia.com/noticias/economia-grecia-contrajo-recesion-2828154.htm",
"http://vidayestilo.terra.es/salud/cuerpo-de-diosa/blog",
"http://www.invertia.com/noticias/Encuestas/portada.asp",
"http://deportes.terra.es/equipos/levante",
"http://noticias.terra.es/mundo/",
"http://www.terra.es/portada/comercial",
"http://deportes.terra.es/equipos/celta-de-vigo",
"http://www.terra.es/movil/",
"http://noticias.terra.es/oscar-lopez-pone-su-cargo-a-disposicion-del-psoe,9ef589d8b795d310VgnVCM20000099cceb0aRCRD.html",
"http://deportes.terra.es/elbanquilloderivero/blog/2013/03/08/la-sonrisa-de-mou-en-manchester/",
"http://terra.tv/default.aspxplay=1&cid=458898",
"http://vidayestilo.terra.es/salud/nutricion/dieta-depurativa-desintoxica-tu-cuerpo-para-la-primavera,083b0259d804d310VgnVCM3000009acceb0aRCRD.html",
"http://deportes.terra.es/futbol/futbol-internacional/argentina/primera-division/nicolas-blandi-el-salvador-de-boca-en-rafaela,25cc9d45cc85d310VgnVCM5000009ccceb0aRCRD.html",
"http://entretenimiento.terra.es/cine/",
"http://noticias.terra.es/contra-la-pornografia-infantil,8afb8c2adb4a8310VgnVCM3000009acceb0aRCRD.html",
"http://vidayestilo.terra.es/living-in-barcelona/blog",
"http://vidayestilo.terra.es/living-in-paris/blog",
"http://entretenimiento.terra.es/cine/es-cine-mama/blog/2013/03/06/la-alargada-sombra-de-oz/",
"http://noticias.terra.es/yo-invertio/blog/",
"http://vidayestilo.terra.es/moda/oportunidades-retro-en-la-feria-moda-vintage,c22891026994d310VgnVCM5000009ccceb0aRCRD.html",
"http://vidayestilo.terra.es/el-estilista/blog",
"http://deportes.terra.es/jogo-bonito/blog/2013/03/05/dorlan-pabon-y-carlos-vela-brillantes-y-decisivos-en-espana/",
"http://www.terra.es/aviso-legal/aviso-legal.htm",
"http://vidayestilo.terra.es/living-in/paris/blog/2013/03/07/de-compras-y-a-cenar-en-casa-de-ralph-lauren/",
"http://vidayestilo.terra.es/salud/",
"http://deportes.terra.es/elcuentaquilometros/blog",
"http://vidayestilo.terra.es/parque-cerrado/blog",
"http://deportes.terra.es/futbol/champions-league/",
"http://www.terra.es",
"http://noticias.terra.es/tecnologia/espana-el-mayor-cliente-del-nuevo-sitio-de-kim-dotcom,572207f71255d310VgnCLD2000000dc6eb0aRCRD.html",
"http://deportes.terra.es/equipos/real-betis",
"http://www.protegeles.com",
"http://deportes.terra.es/automovilismo/formula1",
"http://vidayestilo.terra.es/xtreme/blog/2013/03/08/audi-r8-e-tron-el-nuevo-coche-de-iron-man/",
"http://tienda.terra.es",
"http://vidayestilo.terra.es/fotos/",
"http://noticias.terra.es/kiosko-global/blog/",
"http://www.terra.tv",
"http://noticias.terra.es/los-pq-de-romanillos/blog/2013/03/10/%C2%BFpor-que-las-mujeres-tienen-mas-cultura-y-menos-salario/",
"http://entretenimiento.terra.es/corazon/jose-m-aznar-y-ana-botella-abuelos-por-quinta-vez,f42b7064b885d310VgnVCM20000099cceb0aRCRD.html",
"http://astrocentro.terra.es/terra//",
"http://deportes.terra.es/elbanquilloderivero/blog",
"http://www.autopista.es/novedades/todas-las-novedades/articulo/koenigsegg-agera-s-hundra",
"http://entretenimiento.terra.es/corazon/natalia-verbeke-tiene-un-nuevo-amor,ebe71c55e485d310VgnVCM20000099cceb0aRCRD.html",
"http://vidayestilo.terra.es",
"http://deportes.terra.es/equipos/rayo-vallecano",
"http://entretenimiento.terra.es/corazon/el-discreto-corazon-de-britney-spears,57ad61950095d310VgnVCM20000099cceb0aRCRD.html",
"http://deportes.terra.es/patada-a-seguir/blog/2013/03/06/a-n-other/",
"http://entretenimiento.terra.es/corazon/videos/",
"http://deportes.terra.es/equipos/zaragoza",
"http://noticias.terra.es/mundo/oriente-proximo/la-isaf-confirma-la-muerte-de-dos-militares-estadoundienses-por-disparos-de-fuerzas-afganas,e9b407f71255d310VgnCLD2000000dc6eb0aRCRD.html",
"http://vidayestilo.terra.es/living-in/new-york/blog/2013/03/06/nyc-es-una-ciudad-wifi/",
"http://deportes.terra.es/patada-a-seguir/blog",
"http://www.terra.es/indice/",
"http://entretenimiento.terra.es/cultura/",
"http://deportes.terra.es/automovilismo/formula1/red-bull-no-forzara-a-vettel-para-que-se-quede,1ab207f71255d310VgnCLD2000000dc6eb0aRCRD.html",
"http://vidayestilo.terra.es/living-in/sao-paulo/blog",
"http://kedin.es/madrid/que-hacer/concierto-de-fangoria-en-el-teatro-circo-price-de-madrid.html",
"http://noticias.terra.es/yo-invertio/blog/2013/02/18/los-recortes-se-imponen-en-las-remuneraciones-en-la-banca/",
"http://deportes.terra.es/real-madrid/luka-modric-objetivo-del-manchester-united,91df28bc8c85d310VgnVCM3000009acceb0aRCRD.html",
"http://entretenimiento.terra.es",
"http://noticias.terra.es/mundo/europa/corte-internacional-levanta-caso-contra-keniano,e3b407f71255d310VgnCLD2000000dc6eb0aRCRD.html",
"http://entretenimiento.terra.es/corazon/las-celebrities-y-su-operacion-bikini,2b68630f0e94d310VgnVCM4000009bcceb0aRCRD.html",
"http://www.terra.tv/Noticias/Actualidad/7213-458932/Hilarante-asi-serian-los-grandes-videojuegos-con-sexo.htm",
"http://www.terra.tv/Noticias/Actualidad/Especiales/Renuncia-de-Benedicto-XVI/10931-458893/Asi-vive-Roma-a-la-espera-del-conclave.htm",
"http://www.invertia.com/noticias/millan-alvarez-miranda-adveo-companias-tiene-potencial-revalorizacion-2828097.htm",
"http://deportes.terra.es/equipos/malaga",
"http://vidayestilo.terra.es/living-in-londres/blog",
"http://www.terra.tv/Noticias/Actualidad/7213-458931/Graban-raras-imagenes-de-un-leopardo-de-las-nieves.htm",
"http://entretenimiento.terra.es/corazon/baby-herederos-los-futuros-reyes-de-europa,3b6ca49ca2a4d310VgnVCM3000009acceb0aRCRD.html",
"http://deportes.terra.es/equipos/valladolid",
"http://deportes.terra.es/tenis/djokovic-cede-set-ante-fognini-pero-avanza-en-indian-wells,d0c88382f375d310VgnCLD2000009acceb0aRCRD.html",
"http://noticias.terra.es/cospedal-luchamos-contra-los-comportamientos-ilicitos,ab5f7064b885d310VgnVCM20000099cceb0aRCRD.html",
"http://entretenimiento.terra.es/corazon/realeza-off/esperanza-aguirre-se-convierte-en-la-duquesa-de-bornos,2c6107f71255d310VgnCLD2000000dc6eb0aRCRD.html",
"http://noticias.terra.es/espana/ejecutiva-del-psoe-rechaza-la-dimision-de-oscar-lopez-por-el-caso-ponferrada,55b407f71255d310VgnCLD2000000dc6eb0aRCRD.html",
"http://deportes.terra.es/equipos/granada",
"http://noticias.terra.es/mundo/fallece-la-princesa-lilian-de-suecia-a-los-97-anos,1117e3d98165d310VgnVCM5000009ccceb0aRCRD.html",
"http://www.terra.es/portada/fotos/",
"http://deportes.terra.es/confesionesdesdemilan/blog",
"http://vidayestilo.terra.es/moda/apuntes-moda/tenemos-chica-nueva-en-la-oficina-cinco-dias-cinco-looks,8271beca6255d310VgnVCM5000009ccceb0aRCRD.html",
"http://entretenimiento.terra.es/musica/justin-bieber-cancela-uno-de-sus-conciertos-en-portugal,251207f71255d310VgnCLD2000000dc6eb0aRCRD.html",
"http://deportes.terra.es/jogo-bonito/blog",
"http://vidayestilo.terra.es/living-in-new-york/blog",
"http://www.terra.tv/Vida-y-Estilo/Moda/El-estilista/10847-458566/El-exito-de-las-tachuelas.htm",
"http://www.terra.tv/Entretenimiento/Musica/9031-458972/Cuatro-mil-bailarines-compiten-por-ser-el-rey-del-hip-hop.htm",
"http://entretenimiento.terra.es/corazon/harper-seven-la-fan-numero-1-de-david-beckham,fbae25377385d310VgnVCM20000099cceb0aRCRD.html",
"http://entretenimiento.terra.es/corazon/noelia-lopez-sufre-un-accidente-de-trafico,cbca0b2a8595d310VgnVCM20000099cceb0aRCRD.html",
"http://www.terra.tv/Noticias/Actualidad/7213-458761/Manifestacion-contra-los-recortes-en-Madrid.htm",
"http://vidayestilo.terra.es/living-in/",
"http://noticias.terra.es/mundo/renuncia-y-sucesor-de-benedicto-xvi/conclave-asi-se-elige-a-un-papa,a07fe5219523d310VgnVCM4000009bcceb0aRCRD.htmlvgnextfmt=fmtSg2",
"http://vidayestilo.terra.es/living-in-pekin/blog",
"http://noticias.terra.es/fotos/",
"http://entretenimiento.terra.es/en-terra-de-series/blog",
"http://vidayestilo.terra.es/el-corcho-flota/blog/",
"http://noticias.terra.es/los-pq-de-romanillos/blog",
"http://noticias.terra.es/espana/",
"http://entretenimiento.terra.es/corazon/camila-alves-una-mama-a-la-ultima,be89c7d2ad85d310VgnVCM20000099cceb0aRCRD.html",
"http://noticias.terra.es/espana/rajoy-cita-a-ccoo-ugt-y-ceoe-para-presentar-el-plan-para-jovenes-y-autonomos,dce207f71255d310VgnCLD2000000dc6eb0aRCRD.html",
"http://entretenimiento.terra.es/en-terra-de-series/blog/2013/03/10/noticias-de-la-semana-vuelve-sherlock-y-se-va-breaking-bad/",
"http://motor.terra.es",
"http://noticias.terra.es/mundo/renuncia-y-sucesor-de-benedicto-xvi/",
"http://noticias.terra.es/sucesos/",
"http://deportes.terra.es/ciclismo",
"http://vidayestilo.terra.es/quiero-conducir-quiero-vivir/blog/2013/03/08/%C2%A1la-velocidad-mata/",
"http://deportes.terra.es/equipos/sevilla",
"http://deportes.terra.es/equipos/espanyol",
"http://entretenimiento.terra.es/cine/primeras-imagenes-del-don-juan-de-joseph-gordon-levitt,5afeabfcbe85d310VgnVCM3000009acceb0aRCRD.html",
"http://deportes.terra.es/los-cancheros/blog/2013/03/04/libertadores-de-sangre/",
"http://deportes.terra.es/la-federacion-espanola-promocionara-la-marca-espana-a-traves-de-la-copa-del-mundo-2014,7cb407f71255d310VgnCLD2000000dc6eb0aRCRD.html",
"http://deportes.terra.es/ramon-trecet/blog",
"http://noticias.terra.es/espana/los-mossos-ven-peligrosisimo-que-camacho-fuese-escoltada,106107f71255d310VgnCLD2000000dc6eb0aRCRD.html",
"http://www.terra.tv/Deportes/Futbol/7207-458966/La-esperada-remontada-del-Barcelona-ante-el-Milan.htm",
"http://vidayestilo.terra.es/salud/cuerpo-de-diosa/blog/2013/03/07/gente-que-habla-y-no-escucha/",
"http://noticias.terra.es/tecnologia/la-app-del-papa-retransmite-en-directo-y-a-traves-de-webcams,eb73ba6ce295d310VgnVCM20000099cceb0aRCRD.html",
"http://entretenimiento.terra.es/corazon/camila-alves-una-mama-a-la-ultima,e8ca64cdb095d310VgnVCM20000099cceb0aRCRD.html",
"http://deportes.terra.es/futbol/futbol-internacional",
"http://deportes.terra.es/futbol/",
"http://www.terra.tv/Vida-y-Estilo/7262-458970/Sofisticacion-para-cerrar-ModaLisboa.htm",
"http://deportes.terra.es/valencia/ricardo-costa-y-joao-pereira-la-lian-en-twitter,f7bda7215295d310VgnVCM3000009acceb0aRCRD.html",
"http://vidayestilo.terra.es/autopista-en-la-red/blog/",
"http://deportes.terra.es/real-madrid/ozil-khedira-y-kaka-se-divierten-con-la-videoconsola,fb8040bea985d310VgnVCM3000009acceb0aRCRD.html",
"http://noticias.terra.es/la-mirada-de-jon-barandica/blog",
"http://deportes.terra.es/equipos/barcelona",
"http://entretenimiento.terra.es/corazon/fotos/",
"http://entretenimiento.terra.es/cine/el-complejo-universo-particular-de-almodovar,0a5ca0c475d3d310VgnVCM5000009ccceb0aRCRD.htmlvgnextfmt=fmtSg2",
"http://entretenimiento.terra.es/corazon/el-viento-le-juega-una-mala-pasada-a-britney-spears,4e0684117685d310VgnVCM20000099cceb0aRCRD.html",
"http://noticias.terra.es/con-la-que-esta-cayendo/blog",
"http://deportes.terra.es/automovilismo/formula1/dos-heridos-tras-la-exhibicion-de-ferrari-en-rio-de-janeiro,5da88382f375d310VgnCLD2000009acceb0aRCRD.html",
"http://entretenimiento.terra.es/fotos/",
"http://deportes.terra.es/motociclismo",
"http://entretenimiento.terra.es/corazon/el-viento-le-juega-una-mala-pasada-a-britney-spears,054884117685d310VgnVCM20000099cceb0aRCRD.html",
"http://deportes.terra.es/equipos/real-sociedad",
"http://entretenimiento.terra.es/musica",
"http://noticias.terra.es/con-la-que-esta-cayendo/blog/2013/03/10/%C2%BFtendria-exito-falete-si-fuera-delgado-2/",
"http://www.terra.tv/Noticias/Actualidad/Buenos-dias/10696-458592/La-presidenta-de-la-Asociacion-de-las-Victimas-del-Terrorismo-valora-el-11M.htm",
"http://vidayestilo.terra.es/living-in-estocolmo/blog",
"http://deportes.terra.es/automovilismo/formula1/massa-recorre-las-calles-de-rio-de-janeiro-con-su-ferrari,25b88382f375d310VgnCLD2000009acceb0aRCRD.html",
"http://noticias.terra.es/espana/la-audiencia-de-cordoba-niega-vulneracion-de-derechos-planteados-por-breton,4eb407f71255d310VgnCLD2000000dc6eb0aRCRD.html",
"http://noticias.terra.es/espana/rajoy-recuerda-a-victimas-del-11m-y-reafirma-su-lucha-contra-el-terrorismo,ce4107f71255d310VgnCLD2000000dc6eb0aRCRD.html",
"http://deportes.terra.es/automovilismo/formula1/montezemolo-asegura-que-alonso-seguira-en-ferrari-hasta-2015,d1d007f71255d310VgnCLD2000000dc6eb0aRCRD.html",
"http://www.terra.es/portada/ultimas/",
"http://noticias.terra.es",
"http://deportes.terra.es/tenis",
"http://entretenimiento.terra.es/cine/es-cine-mama/blog",
"http://noticias.terra.es/espana/comunidades-autonomas/",
"http://www.autopista.es/noticias/todas-las-noticias/articulo/multa-anulada-argumentos-ilogicos",
"http://deportes.terra.es/los-cancheros/blog",
"http://deportes.terra.es/baloncesto/nba/hornets-ganan-a-los-blazers-sin-claver,655f07f71255d310VgnCLD2000000dc6eb0aRCRD.html",
"http://top.terra.es",
"http://deportes.terra.es/baloncesto/liga-acb/",
"http://noticias.terra.es/gomez-bermudez-admite-la-querella-de-los-papeles-de-barcenas,023656df6795d310VgnVCM20000099cceb0aRCRD.html",
"http://www.terra.tv/Deportes/Planeta-13T/10907-458949/El-planteamiento-del-Barca-ante-el-Milan.htm",
"http://entretenimiento.terra.es/el-trampolin-de-splash-espera-hoy-a-jesulin-y-a-falete,c064d3d184e4d310VgnVCM5000009ccceb0aRCRD.html",
"http://vidayestilo.terra.es/living-in-roma/blog",
"http://deportes.terra.es/tiger-woods-gana-el-torneo-de-el-doral-en-miami,0f0d07f71255d310VgnCLD2000000dc6eb0aRCRD.html",
"http://noticias.terra.es/sobrio-homenaje-a-las-victimas-del-11m-nueve-anos-despues,c7e8bbfaa985d310VgnVCM20000099cceb0aRCRD.html",
"http://vidayestilo.terra.es/belleza/",
"http://deportes.terra.es/automovilismo/rally-dakar/",
"http://entretenimiento.terra.es/corazon/el-momento-mas-duro-de-ortega-cano,0bb6c326c785d310VgnVCM20000099cceb0aRCRD.html",
"http://entretenimiento.terra.es/corazon/blake-lively-y-emma-stone-comparten-a-ryan-reynolds,a5fabbfaa985d310VgnVCM20000099cceb0aRCRD.html",
"http://www.invertia.com/empresas/portada.asp",
"http://deportes.terra.es/barcelona/nos-hemos-dejado-al-papi-la-remontada-segun-angel-mur,fbadbb6fa065d310VgnVCM20000099cceb0aRCRD.html",
"http://s1.trrsf.com/navbar/js/json_landing_101.js",
"http://www.autopista.es/novedades/todas-las-novedades",
"http://deportes.terra.es/futbol/segunda-division",
"http://entretenimiento.terra.es/corazon/noelia-lopez-sufre-un-accidente-de-trafico,12ae0b2a8595d310VgnVCM20000099cceb0aRCRD.html",
"http://deportes.terra.es/futbol/champions-league",
"http://vidayestilo.terra.es/pareja/",
"http://entretenimiento.terra.es/corazon/jesus-vazquez-y-su-marido-fans-de-siempre-asi,90da1c55e485d310VgnVCM20000099cceb0aRCRD.html",
"http://vidayestilo.terra.es/padres",
"http://vidayestilo.terra.es/living-in/sao-paulo/blog/2013/03/07/locos-por-los-huevos/",
"http://vidayestilo.terra.es/moda/",
"http://deportes.terra.es/futbol/benitez-pone-en-tela-de-juicio-la-educacion-de-alex-ferguson,6cea07f71255d310VgnCLD2000000dc6eb0aRCRD.html",
"http://www.invertia.com/mercados/bolsa/portada.asp",
"http://deportes.terra.es/videos/",
"http://deportes.terra.es/equipos/athletic-de-bilbao",
"http://vidayestilo.terra.es/belleza/arreglate-ya/blog",
"http://deportes.terra.es/fotos/",
"http://deportes.terra.es/equipos/valencia",
"http://deportes.terra.es/baloncesto/nba/",
"http://vidayestilo.terra.es/el-corcho-flota/blog/2013/03/10/%C2%BFque-quedo-del-sabado-sabadete/",
"http://vidayestilo.terra.es/living-in/barcelona/blog/2013/03/07/antidoto-contra-la-depresion-por-lluvia/",
"http://vidayestilo.terra.es/living-in/pekin/blog/2013/03/06/muere-hugo-chavez-un-buen-amigo-de-china/",
"http://entretenimiento.terra.es/corazon/",
"http://noticias.terra.es/buenos-dias",
"http://s1.trrsf.com/transversais/qet/poll/_js/trr_poll.js",
"http://www.invertia.com/noticias/aena-cobrara-euro-usar-carros-equipajes-barajas-2828151.htm",
"http://noticias.terra.es/sucesos/detenido-un-dentista-por-arrancarle-los-dientes-por-dinero,a5e207f71255d310VgnCLD2000000dc6eb0aRCRD.html",
"http://idrops.terra.es/framework2/jsframework/com.terra.latam.gadgetframework.nocache.js",
"http://noticias.terra.es/ciencia/",
"http://noticias.terra.es/rajoy-respalda-a-cospedal-en-un-acto-sin-nombrar-a-barcenas,449561950095d310VgnVCM20000099cceb0aRCRD.html",
"http://entretenimiento.terra.es/videos/",
"http://vidayestilo.terra.es/parque-cerrado/blog/2013/03/07/mejor-chocolate-que-piedras/",
"http://home-es.terra.com.br/rss/Controllerchannelid=c8ab5db043fb5310VgnVCM4000009bf154d0RCRD&ctName=atomo-noticia&lg=es-es",
"http://s1.trrsf.com/atm/3/core/apps/carousel/_css/skin-default.css",
"http://deportes.terra.es/equipos/mallorca",
"http://deportes.terra.es/futbol/kick-and-pass/blog",
"http://vidayestilo.terra.es/contrasentido/blog/",
"http://entretenimiento.terra.es/musica/",
"http://deportes.terra.es/ramon-trecet/blog/2013/03/05/la-expulsion-de-nani-condiciona-el-partido/",
"http://vidayestilo.terra.es/moda/apuntes-moda/tenemos-chica-nueva-en-la-oficina-cinco-dias-cinco-looks,0480e4708b55d310VgnVCM5000009ccceb0aRCRD.html",
"http://deportes.terra.es",
"http://deportes.terra.es/equipos/getafe",
"http://vidayestilo.terra.es/quiero-conducir-quiero-vivir/blog/",
"http://deportes.terra.es/equipos/deportivo-la-coruna",
"http://deportes.terra.es/futbol/copa-confederaciones/",
"http://noticias.terra.es/mundo/europa/presidente-boliviano-evo-morales-visitara-francia-el-miercoles-y-el-jueves,95b407f71255d310VgnCLD2000000dc6eb0aRCRD.html",
"http://vidayestilo.terra.es/xtreme/blog",
"http://terra.tv/default.aspxplay=1&cid=458961",
"http://deportes.terra.es/equipos/atletico-de-madrid",
"http://www.autopista.es/pruebas/todas-las-pruebas",
"http://vidayestilo.terra.es/living-in/roma/blog/2013/03/10/polvere-di-tempo/",
"http://entretenimiento.terra.es/corazon/blake-lively-y-emma-stone-dos-guapas-de-estreno,87f2aa4bca85d310VgnVCM20000099cceb0aRCRD.html",
"http://twitter.com/terranoticiases",
"http://noticias.terra.es/mundo/asia-pacifico/japon-ano-dos-despues-de-fukushima,a80f07f71255d310VgnCLD2000000dc6eb0aRCRD.html",
"http://deportes.terra.es/confesionesdesdemilan/blog/2013/03/03/%E2%80%98cassanate%E2%80%99-en-appiano-gentile/",
"http://vidayestilo.terra.es/moda/el-estilista/blog/2013/03/11/las-tendencias-de-las-tachuelas-en-los-zapatos/",
"http://www.terra.es/correo/",
"http://entretenimiento.terra.es/cultura/un-libro-ensena-a-comportarse-como-un-autentico-torrente,58a85e7272e4d310VgnCLD2000000dc6eb0aRCRD.html",
"http://noticias.terra.es/kiosko-global/blog/2013/03/11/crimenes-que-necesitan-un-rescate-europeo/",
"http://deportes.terra.es/equipos/osasuna",
"http://www.terra.tv/Noticias/Actualidad/7213-458930/Que-harias-si-estas-surfeando-y-aparecen-unas-orcas-a-tu-lado.htm",
"http://vidayestilo.terra.es/belleza/arreglate-ya/blog/2013/03/11/el-tinte-que-usa-jennifer-lawrence/",
"http://noticias.terra.es/mundo/renuncia-y-sucesor-de-benedicto-xvi/un-domingo-en-el-vaticano-mucha-politica-y-poco-papa,72db67e13455d310VgnVCM20000099cceb0aRCRD.html",
"http://vidayestilo.terra.es/living-in/estocolmo/blog/2013/03/10/final-de-melodifestivalen-asi-fue-el-evento-mas-esperado-del-ano-en-suecia/",
"http://noticias.terra.es/espana/homenajes-a-las-victimas-de-los-atentados-del-11m,21787c4ae495d310VgnVCM5000009ccceb0aRCRD.html",
"http://noticias.terra.es/los-cardenales-se-reunen-por-ultima-vez-antes-del-conclave,13851c55e485d310VgnVCM20000099cceb0aRCRD.html",
"http://deportes.terra.es/elcuentaquilometros/blog/2013/03/03/el-calvario-de-andy-schleck/",
"http://vidayestilo.terra.es/contrasentido/blog/2013/02/08/subastas-publicas-de-los-coches-oficiales-el-gran-misterio/",
"http://deportes.terra.es/futbol/primera-division",
"http://entretenimiento.terra.es/cine/los-amantes-pasajeros-de-almodovar-despegan-con-exito,26cd66131b85d310VgnVCM3000009acceb0aRCRD.html",
"http://deportes.terra.es/barcelona/alves-he-visto-a-leo-bajo-animicamente,caf107f71255d310VgnCLD2000000dc6eb0aRCRD.html",
"http://deportes.terra.es/futbol/kick-and-pass/blog/2013/03/08/angel-rangel-un-catalan-con-corazon-gales/",
"http://www.recetasderechupete.com/recetas-de-navidad/2763/",
"http://www.terra.es/portada/blogs/",
"http://vidayestilo.terra.es/salud/propiedades-medicas-de-la-marihuana-segun-revista-brasilena,009b871e4c55d310VgnVCM3000009acceb0aRCRD.html",
"http://deportes.terra.es/ciclismo/laurent-jalabert-gravemente-herido-tras-un-accidente,81a9bdad2995d310VgnVCM3000009acceb0aRCRD.html",
"http://deportes.terra.es/barcelona/las-remontadas-mas-magicas-en-el-camp-nou,0ab8664c1395d310VgnVCM3000009acceb0aRCRD.html",
"http://www.telefonicaonline.com/on/pub/servicios/onTOEntrada/0,,entrada%2Baviso_legal%2Bv_segmento%2BAHOG%2Bv_idioma%2Bes%2BambitoAcceso%2Bpub,00.htmlv_segmento=AHOG&v_idioma=es&v_pagina=HO&v_hueco=MCR&v_posicion=1&v_procede=home",
"http://vidayestilo.terra.es/living-in/londres/blog/2013/03/10/%C2%A1felicidades-mamas/",
]


import timeit


#------------------------------------------------------------------------------
def urllib2_test():
    import urllib2

    errors = 0
    oks = 0
    for a in url:
        try:
            req = urllib2.Request(a)

            handler = urllib2.urlopen(req)

            oks += 1
        except:
            errors += 1
            continue

        print ".",
    print
    print "Errors: %s | Oks: %s." % (str(errors), str(oks))


#------------------------------------------------------------------------------
def request_test():
    from requests import Request, Session

    errors = 0
    oks = 0
    for a in url:
        try:
            req = Request(url=a)
            p = req.prepare()

            s = Session()
            r = s.send(p)
            oks += 1
        except:
            errors += 1
            continue

        print ".",
    print
    print "Errors: %s | Oks: %s." % (str(errors), str(oks))


#------------------------------------------------------------------------------
def urllib3_test():
    from urllib3 import PoolManager

    errors = 0
    oks = 0
    p = PoolManager(20)
    for a in url:
        try:
            p.request(method="GET", url=a)
            oks += 1
        except:
            errors += 1
            continue

        print ".",
    print
    print "Errors: %s | Oks: %s." % (str(errors), str(oks))


#------------------------------------------------------------------------------
def httplib2_test():
    from httplib2 import Http

    errors = 0
    oks = 0
    for a in url:
        try:
            h = Http(".cache")
            r, content = h.request(a, "GET")
            oks += 1
        except:
            errors += 1
            continue
        print ".",

    print
    print "Errors: %s | Oks: %s." % (str(errors), str(oks))


#------------------------------------------------------------------------------
if __name__=='__main__':

    print "Testing python HTTP libs performance:"
    print
    print "Each library will request '%s' URLs." % len(url)

    print
    print "'Request' library time: %s s" % str(timeit.timeit(request_test, number=1))
    print
    print "'urllib2' library time: %s s" % str(timeit.timeit(urllib2_test, number=1))
    print
    print "'httplib2' library time: %s s" % str(timeit.timeit(httplib2_test, number=1))
    print
    print "'urllib3' library time: %s s" % str(timeit.timeit(urllib3_test, number=1))
