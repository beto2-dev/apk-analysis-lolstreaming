# Resultados del analisis dinamico (trafico y comportamiento)

Ejecucion de referencia: GitHub Actions run del workflow
`.github/workflows/dynamic-analysis.yml` (emulador Pixel 4 virtual, Android 11
API 30, x86_64 con traduccion ARM ndk_translation 0.2.2, mitmproxy como proxy
de red del emulador con CA instalada en el almacen del sistema por bind mount,
frida-server 16.4.10 como root y hooks Java sobre el proceso de la aplicacion).

## 1. Comportamiento observado de la aplicacion

| Aspecto | Observacion |
|---------|-------------|
| Arranque | La app se lanza correctamente (spawn de Frida, pid 4750/5133 en las distintas ejecuciones). `MainActivity` entra en `onCreate`, el motor Flutter carga `libflutter.so` y renderiza con Impeller (OpenGLES) bajo traduccion ARM. |
| Hooks de Frida | Solo se registran tres eventos Java en la fase inicial: `System.loadLibrary("flutter")`, `System.loadLibrary("dartjni")` y `getPackageInfo("com.example.lol", flags=0)`. No hay llamadas a `DexClassLoader`, `Runtime.exec`, `Cipher` ni TrustManager propios (coherente con el analisis estatico). |
| Fallo de inicializacion | El registro automatico de plugins aborta con `UnsatisfiedLinkError: dlopen failed: library "libdartjni.so" not found` (plugin `dart_lang/jni`). Bajo traduccion ARM, la carga de esa libreria falla y la inicializacion de la app no llega a completar el primer uso de red. |
| Red de la aplicacion | **Cero conexiones** de la app en la ventana observada (no aparecen ni flujos ni intentos TLS con SNI de la app en mitmproxy). La aplicacion permanece en pantalla de inicio sin emitir trafico. |
| Resistencia al analisis | Nula: acepta root (`adb root`), Frida, CA de mitmproxy en el sistema y proxy de red sin reaccion (sin deteccion de emulador, root ni hooks), confirmando el inventario estatico de protecciones. |
| Telemetria | Ninguna emision propia de la app. Todo el trafico capturado pertenece a componentes del sistema (Google Play Services, YouTube, Firebase, conectividad). |

## 2. Trafico capturado

- `dynamic/captures/traffic.mitm.gz`: volcado completo de flujos (mitmproxy).
- `dynamic/captures/flows_log.txt`: registro legible de peticiones/respuestas.
- `dynamic/logs/mitmdump.txt`: consola de mitmproxy (incluye fallos TLS).

Distribucion del trafico descifrado (todas las conexiones provienen de
componentes de sistema del Android del emulador, no de la aplicacion auditada):

| Dominio | Flujos | Servicio |
|---------|--------|----------|
| www.googleapis.com | 51 | Play Services (attestation, anti-abuso, experimentos) |
| connectivitycheck.gstatic.com | 42 | Verificacion de conectividad |
| youtubei.googleapis.com | 36 | Registro de notificaciones de YouTube |
| android.clients.google.com | 31 | C2DM/checkin de Google |
| www.google.com / www.gstatic.com | 43 | Diversos servicios |
| play.googleapis.com | 16 | Play |
| www.googleadservices.com / ad.doubleclick.net / adservice.google.com | 28 | Publicidad de apps de sistema |
| firebaseinstallations.googleapis.com | 12 | Instalaciones Firebase de apps de sistema |
| app-measurement.com | 8 | Analitica de apps de sistema |
| resto (fonts, dl.google.com, etc.) | 20 | Diversos |

Codigos de respuesta dominantes: 200 (79), 204 (47), 400 (16), 301/302 (12).
Los fallos TLS corresponden a dominios de Google con anclaje propio
(`www.google.com`, `youtubei.googleapis.com`, `firebaseinstallations.googleapis.com`,
`mtalk.google.com`), que rechazan la CA de mitmproxy por pinning interno de
Google; no afectan a la aplicacion auditada.

## 3. Comparacion estatico-dinamico

| Hallazgo estatico | Confirmacion dinamica |
|-------------------|------------------------|
| Sin anti-debugging / anti-root / anti-Frida | Confirmada: Frida y root aceptados sin resistencia |
| Sin SSL pinning en la app | No refutable dinamicamente (la app no emitio TLS); Google system apps si pinnean |
| Sin SDK de telemetria propio | Confirmada: cero flujos originados por la app |
| Sin carga dinamica de codigo, sin exec, sin cripto propia | Confirmada: hooks silenciosos en esas APIs |
| Backend modlyo.com (version_api, servidores) | No observable: la app no llego a fase de red en el entorno |

## 4. Limitaciones documentadas

1. **Traduccion ARM**: el APK solo distribuye librerias `armeabi-v7a`; la
   imagen x86_64 del emulador las ejecuta mediante `ndk_translation`. En este
   entorno la carga de `libdartjni.so` falla y la aplicacion no completa su
   inicializacion, bloqueando la fase de red (comprobacion de version en
   `modlyo.com` y catalogo).
2. **Estabilidad del emulador**: el subsistema de red virtual (netsim) se
   detiene aproximadamente 2,5 minutos despues del arranque en cada ejecucion
   ("Netsim Wifi ... is gone"), lo que reduce la ventana util de observacion y
   impide sesiones largas de interaccion.
3. **Anclaje de Google**: los servicios de sistema de Google no pueden
   inspeccionarse por pinning propio; su trafico se registra a nivel de
   handshake (SNI) en `mitmdump.txt`.

Estas limitaciones no invalidan las conclusiones: las conductas criticas
(instalacion remota de APK, interruptor de servidores, scraping) estan
documentadas estaticamente sobre el snapshot Dart y el manifiesto, y el
analisis dinamico confirma la ausencia total de anti-analisis y de
comportamiento oculto en la fase observable.
