# Catalogo de endpoints y conexiones de red (analisis estatico)

Fuentes: `static/strings/urls.txt`, `static/strings/domains.txt`,
`static/strings/por_archivo.txt` (extraccion automatica de `libapp.so` — snapshot
Dart AOT de Flutter —, `classes.dex`, recursos y assets) y revision manual del
codigo descompilado. Los nombres de pagina Dart (`package:lol/fuentes/...`)
confirman la funcion de cada grupo.

Resumen: **38 dominios distintos**, 130 URLs literales. No se observan IPs
literales operativas (las tres detectadas son falsos positivos de constantes
binarias), ni protocolos WebSocket/MQTT, ni trafico DNS fuera de banda.

## 1. Backend propio del distribuidor (modlyo.com)

Infraestructura privada del desarrollador del mod. Es el plano de control de la
aplicacion: decide que servidores de reproduccion se muestran, distribuye
actualizaciones y puede desactivar fuentes de forma remota.

| # | URL / endpoint | Metodo | Parametros | Proposito probable | Riesgo |
|---|----------------|--------|------------|--------------------|--------|
| 1 | `https://modlyo.com/apitv/version_api.php?version_code=100` | GET | version_code | Comprobacion de version (build 1.0.0, code 100) y obtencion de actualizacion (`/lol_update.apk`) | Medio: canal de instalacion remota de APK |
| 2 | `https://modlyo.com/apitv/version_api.php?version_code=200` | GET | version_code | Idem, rama de version 2.0.0 hardcodeada | Medio |
| 3 | `https://modlyo.com/apitv/desactivar_servidor.php` | GET/POST | (dinamicos) | **Interruptor remoto**: desactiva servidores/fuentes de reproduccion | Medio: control remoto de funcionalidad |
| 4 | `https://modlyo.com/appapi/api_servidores.php?idcontenido=` | GET | idcontenido | Lista de servidores/enlaces de reproduccion para un titulo | Bajo-Medio |
| 5 | `https://www.modlyo.com/api/servidores.php` | GET | - | Catalogo global de servidores | Bajo-Medio |
| 6 | `https://www.modlyo.com/apitv/apicuevana.php?type=movie&id=` | GET | type, id | Proxy de contenido tipo Cuevana para peliculas | Bajo-Medio |
| 7 | `https://www.modlyo.com/apitv/apicuevana.php?type=capitulo&id=` | GET | type, id | Idem para episodios de series | Bajo-Medio |
| 8 | `https://modlyo.com/subtitulo/contenido/` | GET | ruta | Subtitulos alojados por el distribuidor | Bajo |

## 2. APIs publicas de metadatos (uso legitimo)

| # | Endpoint | Proposito | Riesgo |
|---|----------|-----------|--------|
| 9 | `https://api.themoviedb.org/3/search/multi`, `/3/tv/`, `/3/find/`, `/3/...?api_key=` | Catalogo de peliculas/series (TMDB v3) | Bajo |
| 10 | `https://image.tmdb.org/t/p/{w92,w185,w300,w342,w500,w780,original}` | Posterografia e imagenes | Bajo |
| 11 | `http://www.omdbapi.com/?i=` | Valoraciones (IMDb, RT, Metacritic). **Via HTTP en claro** (permitido por `usesCleartextTraffic=true`): interceptable | Medio |
| 12 | `https://api.introdb.app` | Intros de series (salto automatico de intro) | Bajo |
| 13 | `https://opensubtitles-v3.strem.io/subtitles/movie/` y `/subtitles/series/` | Subtitulos (API v3 de OpenSubtitles usada por Stremio) | Bajo |

Candidatos a clave de API (32 hex) embebidos en el snapshot Dart:
`439c478a771f35c05022f9feabcca01c`, `5eeefca380d02919dc2c6558bb6d8a5d`,
`a2d9bbed370d9f678e34006f8750a5a5`, `d6031998d1b3bbfebf59cc9bbff9aee1`,
`e87579c11079f43dd824993c2cee5ed3` (ver `static/strings/base64_candidates.txt`).
Al menos uno corresponde a la clave TMDB v3; las demas son constantes
criptograficas del runtime Dart. El analisis dinamico permite confirmarlo.

## 3. Sitios de streaming raspados (fuentes de enlaces)

La app contiene scrapers propios para estos sitios (`package:lol/fuentes/apis/...`,
clases `PelisPlusService`, `PoseidonService`, `searchCineHax`, flag
`poseidon_enabled`):

| # | Dominio | Rutas observadas | Papel |
|---|---------|------------------|-------|
| 14 | `www.pelisplushd.la` | `/search?s=` | Busqueda y enlaces (sitio pirata ES) |
| 15 | `www.poseidonhd2.co` | `/` | Idem |
| 16 | `cinehax.com` | `/buscar/?q=`, `/ver/?tipo=` | Idem |
| 17 | `wv3.cuevana3.eu` | `/search?q=`, `/ver-pelicula/` | Cuevana (espejo) |
| 18 | `www.cinecalidad.am` | `/ver-pelicula/`, `/ver-el-episodio/` | CineCalidad |
| 19 | `serieskao.top` | `/search?s=`, `/vidurl/` | Series |
| 20 | `hackstore.mx` | `/` | Descargas/estrenos |
| 21 | `xupalace.org` | `/video/` | Reproduccion |
| 22 | `lamovie.cc` | `/` | Catalogo |
| 23 | `net27.cc` | `/` | Catalogo |

## 4. Hosters de video y CDNs de reproduccion (embeds)

Enlaces finales que el reproductor (`video_player_android` / ExoPlayer,
HLS/DASH) consume. La app tambien extrae `.m3u8/.mp4/.ts/.m4s` de WebViews con
el puente JavaScript `MediaDetector` (ver `static/protections.md`).

| # | Dominio | Rutas | Papel |
|---|---------|-------|-------|
| 24 | `embedwish.com` | `/e/` | Embed de video |
| 25 | `streamwish.to` | `/e/` | Embed de video |
| 26 | `strwish.com` | `/e/` | Embed de video (espejo StreamWish) |
| 27 | `awish.pro` | `/e/` | Embed de video |
| 28 | `wishfast.top` | `/e/` | Embed de video |
| 29 | `hanerix.com` | `/e/` | Embed de video |
| 30 | `hglink.to` | `/e/` | Embed de video |
| 31 | `unlimplay.com` | `/f/embed/movie/`, `/f/embed/tv/` | Embed por tipo |
| 32 | `dr0pstream.com` | `/e/` | Embed de video |
| 33 | `goodstream.one` | `/` | Streaming |
| 34 | `embed69.org` | `/static/lang/{ESP,LAT,SUB,JAP}.png` | Embed + selectors de idioma |
| 35 | `tioplus.app` | `/search/` | Buscador de enlaces |
| 36 | `buzzheavier.com` | `/v/` | Almacen de archivos |
| 37 | `pixeldrain.com` | `/`, `/api/file/` | Almacen de archivos (API) |

## 5. Redes sociales del desarrollador y miscelaneos

| # | URL | Papel | Riesgo |
|---|-----|-------|--------|
| 38 | `https://t.me/lol_oficialapp` | Canal de Telegram del proyecto | Bajo |
| 39 | `https://instagram.com/lol_oficialapp` | Redes sociales | Bajo |
| 40 | `https://tiktok.com/@lol_oficialapp` | Redes sociales | Bajo |
| 41 | `https://img.youtube.com/vi/` y `https://www.youtube.com/watch?v=` | Trailer | Bajo |
| 42 | `https://letterboxd.com/imdb/` | Enlace de valoraciones | Bajo |
| 43 | `time.android.com` | Referencia de hora (NTP/HTTP date) | Bajo |

## Patrones de comunicacion

- Todo el trafico de control y catalogo es **HTTPS** salvo la consulta OMDb
  (**HTTP**), habilitada por `android:usesCleartextTraffic="true"`.
- No hay WebSocket, MQTT, ni tunel DNS en las cadenas extraidas.
- No se identifican endpoints de exfiltracion de datos personales, servicios de
  paste (Pastebin), bots de Telegram para C2, ni farmacias de credenciales.
- El telemetria no existe como modulo: no hay SDK de analitica (Firebase,
  Crashlytics, AdMob, AppLovin, etc.) ni en el DEX ni en el snapshot Dart.
- El deep link `lol://user/{perfil}` permite abrir perfiles de usuario de la app
  desde enlaces externos.

## Comparacion con el trafico dinamico

La lista completa de dominios anteriores es el inventario maximo; el trafico
real observado en el emulador depende del estado del backend
(`static/../dynamic/endpoints_dynamic.md`). Las diferencias se documentan alli.
