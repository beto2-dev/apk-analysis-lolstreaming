# Evaluacion de malware: sample.apk (com.example.lol "lol")

> Documento de trabajo de la fase de analisis. El resumen ampliado, con el
> detalle de cada evidencia, esta en `reports/informe_final.md`.

## Clasificacion

| Campo | Resultado |
|-------|-----------|
| Veredicto | **PUP / aplicacion de infraccion de copyright sin conducta de malware clasico** (ver matiz de riesgo de actualizacion abajo) |
| Tipo | Agregador de streaming pirata (scraper de enlaces + reproductor) |
| Familia | No corresponde a una familia de malware conocida; es un "mod" propio del canal `lol_oficialapp` |
| Nivel de riesgo global | **Medio** |
| Riesgo de privacidad | Bajo: no recolecta datos personales mas alla del trafico de catalogo |
| Riesgo de dispositivo | Medio: `REQUEST_INSTALL_PACKAGES` + auto-actualizacion desde backend propio sin verificacion de firma visible en el cliente |

## Justificacion del veredicto

A favor de la clasificacion como PUP (y no malware):

1. **Ninguna conducta maliciosa clasica detectada**: sin SMS, contactos,
   ubicacion, camara, microfono, accesibilidad, superposicion de ventanas,
   criptoransomware ni robo de credenciales bancarias en el codigo estatico ni
   en las llamadas hookeadas durante la ejecucion.
2. **Sin telemetria oculta**: no hay SDK de analitica, publicidad ni crash
   reporting (verificado en DEX y snapshot Dart). El trafico observado
   corresponde a catalogo (TMDB/OMDb), subtitulos y enlaces de reproduccion.
3. **Sin evasion**: sin anti-root, anti-emulador, anti-Frida, anti-debugging ni
   SSL pinning. Una aplicacion maliciosa profesional suele intentar impedir al
   menos parte de ese analisis.
4. **Funcionalidad coherente con lo declarado**: es literalmente lo que parece,
   una app de ver peliculas/series enlazando a hosters publicos, con backend
   propio en modlyo.com para agrupar servidores y subtitulos.

Motivos que impiden clasificarla como benigna:

1. **Infraccion sistematica de derechos de autor**: reproduce contenido
   procedente de sitios pirata (PelisPlusHD, PoseidonHD, Cuevana, CineCalidad,
   entre otros) via scraping y embeds.
2. **Canal de instalacion remota**: el permiso `REQUEST_INSTALL_PACKAGES` se
   usa para descargar e instalar `/lol_update.apk` desde `modlyo.com` con
   bloqueo de uso ("Actualiza para continuar."). El cliente no verifica la
   firma del APK descargado: el compromiso del backend (o de la red en caso de
   caida a HTTP) se convertira en ejecucion arbitraria en cada dispositivo.
3. **Control remoto de funcionalidad**: `desactivar_servidor.php` permite
   alterar el comportamiento de las instalaciones desplegadas a voluntad del
   operador.
4. **Firma con certificado de depuracion** y distribucion fuera de tiendas:
   sin procedencia verificable ni actualizaciones de seguridad auditables.
5. **Trafico en claro** permitido (`usesCleartextTraffic=true`, OMDb via HTTP).

## Indicadores de Compromiso (IoC)

Archivo y firma:

| Tipo | Valor |
|------|-------|
| SHA-256 | `4cefd5bee99887fd1b0b06b545228695e4ed311949948d37ac922fdb09e3cecf` |
| MD5 | `d59956c3990c7ae6613faaf89c194f36` |
| Paquete | `com.example.lol` (etiqueta "lol", versionCode 1001) |
| Certificado de firma | CN=Android Debug, O=Android, C=US, serie 0x1, SHA-256 `44:ac:4c:9a:6b:22:95:96:31:3c:89:db:15:72:ab:8b:9b:fa:bb:35:a4:86:18:81:4a:0a:02:52:0e:db:82:07` |

Infraestructura de control (modlyo.com):

| Tipo | Valor |
|------|-------|
| Backend de control | `modlyo.com`, `www.modlyo.com` |
| Actualizacion remota | `https://modlyo.com/apitv/version_api.php?version_code=100` (y `=200`), payload `/lol_update.apk` |
| Interruptor remoto | `https://modlyo.com/apitv/desactivar_servidor.php` |
| Servidores de contenido | `https://modlyo.com/appapi/api_servidores.php?idcontenido=`, `https://www.modlyo.com/api/servidores.php`, `https://www.modlyo.com/apitv/apicuevana.php?type={movie\|capitulo}&id=` |
| Subtitulos propios | `https://modlyo.com/subtitulo/contenido/` |

Sitios objetivo de scraping y hosters asociados:

`www.pelisplushd.la`, `www.poseidonhd2.co`, `cinehax.com`, `wv3.cuevana3.eu`,
`www.cinecalidad.am`, `serieskao.top`, `hackstore.mx`, `xupalace.org`,
`lamovie.cc`, `net27.cc`, `embedwish.com`, `streamwish.to`, `strwish.com`,
`awish.pro`, `wishfast.top`, `hanerix.com`, `hglink.to`, `unlimplay.com`,
`dr0pstream.com`, `goodstream.one`, `embed69.org`, `tioplus.app`,
`buzzheavier.com`, `pixeldrain.com`

Presencia del operador:

`t.me/lol_oficialapp`, `instagram.com/lol_oficialapp`, `tiktok.com/@lol_oficialapp`

## Reglas de deteccion sugeridas (YARA, orientativas)

```yara
rule Android_PUP_Modlyo_Lol_Streaming
{
    meta:
        descripcion = "Agregador de streaming pirata con auto-actualizacion modlyo"
        severidad = "media"
    strings:
        $pkg = "com.example.lol" ascii
        $upd1 = "modlyo.com/apitv/version_api.php" ascii
        $upd2 = "modlyo.com/apitv/desactivar_servidor.php" ascii
        $apk  = "/lol_update.apk" ascii
        $scr  = "package:lol/fuentes/apis/" ascii
    condition:
        uint32(0) == 0x56415244 and 2 of ($pkg, $upd1, $upd2, $apk, $scr)
}
```

(El prefijo `PK\x03\x04` aplicaria al APK contenedor; sobre el archivo crudo
del snapshot Dart conviene usar `2 of` con `$pkg/$upd*/$scr`.)

## Acciones recomendadas

1. **No instalar** en dispositivos personales o corporativos; si esta
   instalada, desinstalarla y revisar que no existan aplicaciones instaladas
   por ella (lista de instalacion en ajustes).
2. **Bloqueo en controles corporativos/MDM**: bloquear el paquete
   `com.example.lol`, el dominio `modlyo.com` y la regla YARA anterior.
3. **Reporte**: notificar al equipo de abuse de la infraestructura de hosting
   de `modlyo.com` y a los titulares de derechos afectados.
4. Si se requiere conservar la muestra: mantenerla cifrada y aislada, y rotar
   cualquier credencial que haya circulado durante el analisis.
