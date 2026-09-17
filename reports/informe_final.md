# Informe tecnico: analisis de la aplicacion Android "lol" (sample.apk)

Documento de referencia de la auditoria de ingenieria inversa del archivo
`sample.apk`. El detalle crudo (volcados de cadenas, manifiesto decodificado,
logs de ejecucion y capturas) acompana este informe en los directorios
`static/` y `dynamic/` del repositorio.

## 1. Resumen ejecutivo

| Campo | Resultado |
|-------|-----------|
| Veredicto | **PUP (aplicacion potencialmente no deseada) de infraccion de copyright; sin conducta de malware clasico detectada** |
| Nivel de riesgo | Medio |
| Categoria | Agregador/reproductor de streaming pirata para moviles y Android TV |
| Canal de distribucion | `https://modlyo.com/versiones/lol_200.apk` (sitio y backend propios) |
| Identificacion | `com.example.lol`, etiqueta "lol", versionName 1.0.0, versionCode 1001 |

La aplicacion es un cliente de streaming de peliculas y series construido con
Flutter que combina un catalogo legitimo (TMDB/OMDb) con enlaces de
reproduccion obtenidos por scraping de al menos diez sitios pirata en espanol
y una red de hosters de video. Toda la logica reside en el snapshot Dart AOT
(`libapp.so`) y se apoya en un backend privado (`modlyo.com`) que actua como
plano de control: decide los servidores disponibles, aloja subtitulos, valida
la version instalada y puede forzar la actualizacion o desactivar fuentes de
forma remota.

No se han detectado comportamientos tipicos de malware Android: sin acceso a
SMS, contactos, ubicacion, camara ni microfono; sin SDK de analitica,
publicidad ni telemetria; sin anti-analisis; sin exfiltracion de datos
personales. Los riesgos residen en tres puntos: (1) el permiso
`REQUEST_INSTALL_PACKAGES` se usa para descargar e instalar actualizaciones
directamente desde `modlyo.com` sin verificacion de firma visible en el
cliente, lo que convierte al backend en un canal potencial de ejecucion
arbitraria si se ve comprometido; (2) la infraccion sistematica de derechos de
autor; y (3) trafico en claro permitido (`usesCleartextTraffic="true"`).

## 2. Informacion del APK

| Propiedad | Valor |
|-----------|-------|
| Archivo | `sample.apk` (descarga original: `lol_200.apk`) |
| Tamano | 21.853.058 bytes (20,8 MiB) |
| SHA-256 | `4cefd5bee99887fd1b0b06b545228695e4ed311949948d37ac922fdb09e3cecf` |
| MD5 | `d59956c3990c7ae6613faaf89c194f36` |
| Tipo MIME | `application/vnd.android.package-archive` |
| Paquete | `com.example.lol` |
| versionName / versionCode | 1.0.0 / 1001 |
| minSdk / targetSdk | 24 (Android 7.0) / 36 (Android 16) |
| Framework | Flutter (embedding v2), Dart AOT en `lib/armeabi-v7a/libapp.so` (10,7 MB) |
| Librerias nativas | `libflutter.so` (8,6 MB), `libapp.so`, `libdartjni.so`, `libdatastore_shared_counter.so` (solo armeabi-v7a) |
| Esquema de firma | APK Signature Scheme v2, 1 certificado |
| Certificado | CN=Android Debug, O=Android, C=US, serie 0x1 |
| Huella del certificado (SHA-256) | `44:ac:4c:9a:6b:22:95:96:31:3c:89:db:15:72:ab:8b:9b:fa:bb:35:a4:86:18:81:4a:0a:02:52:0e:db:82:07` |
| Validez del certificado | 2026-09-03 a 2056-08-26 |

Observaciones de contexto: el APK esta firmado con un certificado de
depuracion creado dos semanas antes de la fecha de distribucion analizada, y
el nombre de paquete es el de plantilla (`com.example.lol`). Es coherente con
compilaciones artesanales distribuidas fuera de tiendas oficiales, sin proceso
de publicacion ni procedencia verificable. El archivo fue obtenido del sitio
del propio operador, cuya marca aparece tambien dentro de la app
(`www.modlyo.com`) junto a sus redes sociales (`t.me/lol_oficialapp`,
`instagram.com/lol_oficialapp`, `tiktok.com/@lol_oficialapp`).

## 3. Analisis del manifiesto

El manifiesto decodificado completo esta en
`static/apk_extracted/AndroidManifest.xml` y su interpretacion en
`static/manifiesto_analisis.md`. Puntos clave:

### 3.1 Permisos (10)

| Permiso | Riesgo | Uso previsto |
|---------|--------|--------------|
| `INTERNET` | Bajo | Streaming y APIs de catalogo |
| `ACCESS_NETWORK_STATE` | Bajo | Deteccion de conectividad |
| `REQUEST_INSTALL_PACKAGES` | **Alto** | Instalacion de `/lol_update.apk` descargado del backend propio (auto-actualizacion forzada) |
| `WRITE_EXTERNAL_STORAGE` (maxSdk 28) | Medio | Descargas en Android 9 o anterior |
| `READ_EXTERNAL_STORAGE` (maxSdk 32) | Bajo | Lectura de archivos descargados |
| `READ_MEDIA_IMAGES/VIDEO/AUDIO` | Bajo | Acceso a media en Android 13+ |
| `WAKE_LOCK` | Bajo | Pantalla encendida durante reproduccion (wakelock_plus) |
| `DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION` | Informativo | Permiso de firma interno de androidx |

No se solicitan permisos de alto abuso habituales en malware: ni SMS, ni
contactos, ni telefono, ni ubicacion, ni camara, ni microfono, ni accesibilidad,
ni `SYSTEM_ALERT_WINDOW`.

### 3.2 Componentes

Solo dos actividades, un receptor estandar de androidx protegido por el
permiso `DUMP` y tres proveedores (dos `FileProvider` y el `InitializationProvider`
de androidx). **No hay servicios en segundo plano**, lo que descarta
persistencia silenciosa o ejecucion oculta. El receptor `ProfileInstallReceiver`
esta exportado pero protegido por permiso privilegiado. La actividad principal
exporta los lanzamientos normal y LEANBACK (Android TV/Fire TV).

### 3.3 Configuracion de seguridad

- `android:usesCleartextTraffic="true"`: HTTP en claro habilitado globalmente;
  aprovechado para consultar `http://www.omdbapi.com/`.
- `android:allowBackup`: no declarado (por defecto `true`).
- `android:networkSecurityConfig`: ausente; sin anclajes ni restricciones.
- `android:debuggable`: no declarado (correcto).
- Queries: `ACTION_PROCESS_TEXT` (busqueda desde texto seleccionado) y
  `ACTION_VIEW` de APKs (coherente con el instalador).

## 4. Analisis estatico de codigo

### 4.1 Arquitectura y ofuscacion

El envoltorio Java/Kotlin (`classes.dex`, 2,2 MB, 1.530 clases) esta ofuscado
con **R8 en modo completo** (paquetes de una o dos letras: `a.a`, `a0.o`,
`f4.e`; mapa `r8-map-id-0c789b1e...`). Contiene solo el runtime Flutter, los
plugins y androidx/media3 (ExoPlayer con HLS/DASH). No hay reglas
anti-decompilacion: jadx procesa el DEX con solo 13 errores menores.

La totalidad de la logica de negocio esta en **Dart compilado AOT** dentro de
`libapp.so`: no hay smali de la logica y el analisis se apoya en las ~22.000
cadenas del snapshot (`static/strings/libapp_strings.txt`). Las cadenas **no
estan cifradas**: URLs, nombres de paginas Dart (`package:lol/fuentes/apis/...`),
mensajes de interfaz y claves de configuracion aparecen en texto plano. No se
detectan empaquetadores comerciales (DexGuard, Bangcle, Ijiami, Tencent Legu).

Estructura interna reconstruida del modulo Dart `package:lol`:

- `fuentes/apis/home/pelisplus.dart`, `servicio/pelisplus.dart` (clase
  `PelisPlusService`), `fuentes/apis/contenido/detalle_pelisplus.dart`
- `PoseidonService`, flag `poseidon_enabled` (fuente PoseidonHD)
- `detalle_cinehax.dart`, `searchCineHax`
- `BuscarFuentesPage` (selector de fuentes)
- Sistema de actualizacion: `Actualiza para continuar.`,
  `Por favor actualiza la aplicacion`, `Actualizar ahora`,
  `Descargar actualizacion`, `Error descarga APK:`, `/lol_update.apk`
- Cadena `CT_xor` junto al nombre del APK de actualizacion (identificador de
  servidor/fuente; sin indicios de un desempaquetador XOR en memoria)

### 4.2 APIs sensibles

| Categoria | Resultado |
|-----------|-----------|
| Red (Java) | Solo stack de sistema; sin OkHttp/Retrofit. La red real va por Dart `HttpClient` |
| Criptografia | No hay `Cipher`/`SecretKeySpec` propios; los candidatos hex de 32 caracteres detectados son claves de API (TMDB) y constantes del runtime |
| Carga dinamica | Sin `DexClassLoader`/`PathClassLoader`/`InMemoryDexClassLoader` |
| Reflexion | Limitada a androidx/window (`reflectionguard`), patron estandar |
| Shell | Sin `Runtime.exec` ni `ProcessBuilder` |
| Acceso a datos personales | Ninguno en el DEX ni en las cadenas Dart |
| WebViews | Inyeccion de JavaScript con puente `MediaDetector`: vigila `absUrl.includes('.m3u8'|'.mp4'|'.ts'|'.m4s')` y devuelve la URL a Dart (tecnica de captura de enlaces) |

### 4.3 Claves embebidas

Candidatos a clave de API (32 caracteres hex) en el snapshot Dart:
`439c478a771f35c05022f9feabcca01c`, `5eeefca380d02919dc2c6558bb6d8a5d`,
`a2d9bbed370d9f678e34006f8750a5a5`, `d6031998d1b3bbfebf59cc9bbff9aee1`,
`e87579c11079f43dd824993c2cee5ed3`. Al menos uno corresponde a la clave v3 de
TMDB (parametro `?api_key=` observado junto a los endpoints). El trafico
capturado en el analisis dinamico permite confirmar cual se usa en cada
peticion.

## 5. Analisis de red

Inventario completo en `static/endpoints.md`; volcados crudos en
`static/strings/{urls,domains,ips,por_archivo}.txt`. En total: **38 dominios**
y 130 URLs literales, sin IPs operativas, sin WebSocket/MQTT y sin tunel DNS.

### 5.1 Plano de control: backend del operador (modlyo.com)

| Endpoint | Metodo | Parametros | Proposito | Riesgo |
|----------|--------|------------|-----------|--------|
| `https://modlyo.com/apitv/version_api.php?version_code=100` | GET | version_code | Validacion de version y entrega de actualizacion (`/lol_update.apk`) | Medio-alto: instalacion remota de APK |
| `https://modlyo.com/apitv/version_api.php?version_code=200` | GET | version_code | Idem para la rama 2.0.0 | Medio-alto |
| `https://modlyo.com/apitv/desactivar_servidor.php` | GET/POST | dinamicos | **Interruptor remoto de servidores/fuentes** | Medio |
| `https://modlyo.com/appapi/api_servidores.php?idcontenido=` | GET | idcontenido | Servidores de reproduccion por titulo | Bajo-medio |
| `https://www.modlyo.com/api/servidores.php` | GET | - | Catalogo de servidores | Bajo-medio |
| `https://www.modlyo.com/apitv/apicuevana.php?type={movie\|capitulo}&id=` | GET | type, id | Proxy de contenido tipo Cuevana | Bajo-medio |
| `https://modlyo.com/subtitulo/contenido/` | GET | ruta | Subtitulos del operador | Bajo |

### 5.2 APIs publicas de metadatos

| Endpoint | Proposito | Riesgo |
|----------|-----------|--------|
| `https://api.themoviedb.org/3/{search/multi,tv,find,...}?api_key=` | Catalogo TMDB | Bajo |
| `https://image.tmdb.org/t/p/{w92..original}` | Imagenes | Bajo |
| `http://www.omdbapi.com/?i=` | Valoraciones; **HTTP en claro** | Medio |
| `https://api.introdb.app` | Intros de series | Bajo |
| `https://opensubtitles-v3.strem.io/subtitles/{movie,series}/` | Subtitulos | Bajo |

### 5.3 Sitios raspados y hosters de reproduccion

Fuentes de scraping: `www.pelisplushd.la`, `www.poseidonhd2.co`, `cinehax.com`,
`wv3.cuevana3.eu`, `www.cinecalidad.am`, `serieskao.top`, `hackstore.mx`,
`xupalace.org`, `lamovie.cc`, `net27.cc`.

Hosters/embeds consumidos por el reproductor: `embedwish.com`, `streamwish.to`,
`strwish.com`, `awish.pro`, `wishfast.top`, `hanerix.com`, `hglink.to`,
`unlimplay.com`, `dr0pstream.com`, `goodstream.one`, `embed69.org`,
`tioplus.app`, `buzzheavier.com`, `pixeldrain.com`.

### 5.4 Patrones de comunicacion

- Toda la señal (control y catalogo) viaja por HTTPS salvo OMDb (HTTP).
- Sin endpoints de exfiltracion: no hay Pastebin, bots de Telegram para C2,
  ni coleccion de datos del dispositivo hacia terceros.
- La unicidad del trafico de red es funcional: catalogo, enlaces, subtitulos,
  trailers (YouTube) y comprobacion de version.

## 6. Protecciones identificadas

Detalle completo en `static/protections.md`. Resumen:

| Proteccion | Estado | Evidencia |
|------------|--------|-----------|
| Ofuscacion Java | Presente (R8 full, estandar) | Nombres `a.a`, `f4.e`, mapa r8 en clases |
| Ofuscacion de logica | N/A (Dart AOT) | `libapp.so` sin simbolos Java |
| Cifrado de cadenas | **Ausente** | URLs y claves en texto plano en el snapshot |
| Empaquetadores | **Ausentes** | DEX normal, sin shells comerciales |
| Anti-debugging | **Ausente** | Sin `isDebuggerConnected`, `TracerPid`, `ptrace` |
| Deteccion de root | **Ausente** | Sin `su`, `magisk`, `busybox`, `RootBeer` |
| Deteccion de emulador | **Ausente** | Sin `qemu`, `goldfish`, `sdk_gphone` |
| Deteccion de Frida/Xposed | **Ausente** | Sin cadenas ni hooks defensivos |
| SSL pinning | **Ausente** | Sin `CertificatePinner`, TrustManager propio ni `network_security_config` |
| Anti-tampering | **Ausente** | Sin verificacion de firma propia en ejecucion |
| Carga dinamica de codigo | **Ausente** | Sin DEX loaders; la "actualizacion" instala un APK externo |

Bypass para analisis: al no existir pinning, basta la CA de mitmproxy en el
almacen del sistema del emulador (`/system/etc/security/cacerts`); no se
requiere degradar TLS por Frida. La superficie de evasion real es, por tanto,
minima: el control de la aplicacion esta en el servidor (version minima
forzada, interruptor de servidores), no en el cliente.

## 7. Analisis dinamico

Entorno: runner de GitHub Actions, AVD Pixel 4 virtual, imagen
`system-images;android-30;google_apis;x86_64` (Android 11), emulador headless
con aceleracion KVM, proxy de red del emulador hacia `mitmdump` (host),
certificado de mitmproxy instalado en el almacen del sistema y `frida-server`
como root. Hooks activos: `java.net.URL`, `HttpsURLConnection`, `Cipher`,
`DexClassLoader`, `Runtime.exec`, `System.loadLibrary`, `SSLContext.init` y
`getPackageInfo`. Procedimiento reproducible en `dynamic/README.md`; el flujo
automatico vive en `.github/workflows/dynamic-analysis.yml`.

### 7.1 Comportamiento observado

(RESULTADOS_DINAMICOS)

### 7.2 Trafico capturado

(RESULTADOS_DINAMICOS)

### 7.3 Comparacion estatico-dinamico

(RESULTADOS_DINAMICOS)

## 8. Indicadores de Compromiso (IoC)

Archivo y binario:

```
SHA-256:  4cefd5bee99887fd1b0b06b545228695e4ed311949948d37ac922fdb09e3cecf
MD5:      d59956c3990c7ae6613faaf89c194f36
Paquete:  com.example.lol (etiqueta "lol", versionCode 1001)
Cert:     CN=Android Debug,O=Android,C=US serial 0x1
Cert SHA-256: 44:ac:4c:9a:6b:22:95:96:31:3c:89:db:15:72:ab:8b:9b:fa:bb:35:a4:86:18:81:4a:0a:02:52:0e:db:82:07
```

Infraestructura de control y distribucion:

```
modlyo.com                          (backend de control)
www.modlyo.com                      (backend de control)
https://modlyo.com/apitv/version_api.php?version_code={100,200}
https://modlyo.com/apitv/desactivar_servidor.php
https://modlyo.com/appapi/api_servidores.php?idcontenido=
https://www.modlyo.com/api/servidores.php
https://www.modlyo.com/apitv/apicuevana.php?type={movie,capitulo}&id=
https://modlyo.com/subtitulo/contenido/
/lol_update.apk                     (artefacto de auto-actualizacion)
```

Dominios objetivo/hosters (detencion por categoria):

```
www.pelisplushd.la  www.poseidonhd2.co  cinehax.com  wv3.cuevana3.eu
www.cinecalidad.am  serieskao.top  hackstore.mx  xupalace.org
lamovie.cc  net27.cc  embedwish.com  streamwish.to  strwish.com
awish.pro  wishfast.top  hanerix.com  hglink.to  unlimplay.com
dr0pstream.com  goodstream.one  embed69.org  tioplus.app
buzzheavier.com  pixeldrain.com
```

Presencia del operador: `t.me/lol_oficialapp`,
`instagram.com/lol_oficialapp`, `tiktok.com/@lol_oficialapp`.

Regla YARA orientativa en `reports/evaluacion.md`.

## 9. Conclusiones y recomendaciones

### 9.1 Conclusiones

La aplicacion "lol" no encaja en ninguna familia de malware Android: no roba
datos, no espia, no cifra archivos, no instala silenciosamente nada por si
misma y no evade el analisis. Es una herramienta de consumo de contenido
pirata, sustentada en scraping y en un backend propio, con utilidades de
gestion remota (version minima, servidores activos) propias de un servicio
operado por una persona o grupo concreto.

El riesgo tecnico relevante no esta en el codigo ejecutado hoy, sino en la
**cadena de confianza de la distribucion**: el operador puede empujar un APK
cualquiera a la base instalada mediante la actualizacion forzada, y el cliente
no valida la firma del paquete entrante. Un compromiso de `modlyo.com` (o de
la red que conecta, si el trafico cayera a HTTP) habilitaria la ejecucion
arbitraria en cada dispositivo que acepte el dialogo de actualizacion.

### 9.2 Recomendaciones

1. **Usuarios**: no instalar la aplicacion; si esta presente, desinstalarla y
   revisar aplicaciones instaladas recientemente de origen desconocido.
2. **Organizaciones/MDM**: bloquear el paquete `com.example.lol`, el dominio
   `modlyo.com` y las categorias de hosters listadas en los IoC; alertar sobre
   APKs firmados con certificados "Android Debug".
3. **Propietarios de derechos**: notificar a los sitios fuente y al hosting de
   `modlyo.com` segun sus procedimientos de abuso.
4. **Investigadores**: mantener la muestra aislada; la ausencia de protecciones
   permite replicar el analisis con el procedimiento de `dynamic/README.md`.
5. **Ciclo de vida del analisis**: revocar cualquier credencial utilizada
   durante la auditoria una vez concluido el trabajo.

## Anexo A. Metodologia y herramientas

| Herramienta | Version | Uso |
|-------------|---------|-----|
| apktool | 2.9.3 | Decodificacion de recursos y manifiesto |
| jadx | 1.5.1 | Descompilacion del DEX (1.530 clases) |
| androguard | 4.1.4 | Metadatos, permisos y certificado de firma v2 |
| strings/grep (coreutils, binutils) | sistema | Extraccion de cadenas de `libapp.so` y DEX |
| scripts propios | `scripts/extract_strings.py`, `scripts/static_info.py` | Automatizacion reproducible |
| mitmproxy | (CI) | Interceptacion de trafico HTTPS |
| Frida | (CI) | Instrumentacion en tiempo de ejecucion |
| Android SDK / emulator | API 30 (CI) | Ejecucion controlada headless |

Limitaciones documentadas: la logica Dart no se decompila a fuente legible
(snapshot AOT), por lo que el analisis de esa capa se basa en cadenas,
comportamiento y trafico; el analisis dinamico depende de la disponibilidad
del backend del operador en el momento de la ejecucion; y solo se analizo la
variante `armeabi-v7a` incluida en el APK.

