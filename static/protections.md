# Protecciones, evasion y endurecimiento identificados (analisis estatico)

Revision del DEX descompilado (jadx 1.5.1, 1.530 clases), del snapshot Dart AOT
(`libapp.so`, 10,7 MB) y de las librerias nativas.

## 1. Ofuscacion

| Aspecto | Hallazgo |
|---------|----------|
| Java/Kotlin (envoltorio) | **R8 en modo completo**: paquetes y clases renombrados a 1-2 caracteres (`a.a`, `a0.o`, `f4.e`, `n5.h`); mapa de nombres presente en el comentario `r8-map-id-0c789b1e...`. No es DexGuard ni ofuscador comercial: es la configuracion estandar de release de Flutter. |
| Logica de la aplicacion | Todo el codigo de negocio esta en Dart compilado **AOT** dentro de `libapp.so` (arbol de simbolos Dart, sin codigo Java). Esto no es una "proteccion" deliberada sino el modelo de Flutter, pero dificulta la ingenieria inversa: no hay smali de la logica, solo cadenas y estructuras del snapshot. |
| Cadenas | **Sin cifrado de cadenas**: todas las URLs, rutas de paginas Dart (`package:lol/fuentes/apis/home/pelisplus.dart`), mensajes de UI y claves de configuracion aparecen en texto plano en `libapp.so`. |
| Empaquetadores | No se detectan: ni DPT-Shell, ni Bangcle/Qihoo, ni Ijiami, ni Tencent Legu, ni DexGuard. El DEX es un DEX normal (`classes.dex`, 2,2 MB). |
| Ofuscacion de control | Sin aplanamiento de flujo de control ni anti-descompilacion apreciable en el envoltorio; jadx decompila con solo 13 errores menores de 1.530 clases. |

La cadena `CT_xor` aparece junto a `/lol_update.apk` en el snapshot Dart; por
contexto parece un identificador de servidor/fuente y no un desempaquetador
XOR. El analisis dinamico no observo descifrado en memoria de codigo nuevo.

## 2. Anti-debugging

**No detectado.** En el DEX no existen referencias a
`android.os.Debug.isDebuggerConnected()`, `TracerPid`, `ptrace`, `Debug` flags
ni temporizacion anti-analisis. En el snapshot Dart no hay cadenas de deteccion
de debuggers de Flutter (`--enable-vm-service`, `dart:developer` abuso) ni
comprobaciones de `ro.debuggable`.

## 3. Deteccion de root / emulador / hooks

**No detectado.** Sin cadenas `su`, `busybox`, `Superuser`, `magisk`,
`frida`, `xposed`, `substrate`, `qemu`, `goldfish`, `ranchu`, `sdk_gphone`,
ni uso de `RootBeer` o equivalentes. El unico `SecurityContext_...` presente es
`SecurityContext_TrustBuiltinRoots`, que es la validacion TLS estandar de Dart.

Consecuencia practica: la aplicacion se ejecuta sin objeciones sobre emuladores
o dispositivos rooteados, lo que facilita el analisis (y el uso normal en TV Box
rooteados, publico tipico de esta clase de apps).

## 4. Anti-tampering / integridad

**No detectado.** No hay verificacion de la firma propia en tiempo de ejecucion
(las referencias a `getPackageInfo` provienen de androidx, no de codigo propio),
ni checksum sobre el DEX, ni deteccion de re-empaquetado. Combinado con el uso
de un **certificado de depuracion** (ver `static/certificado.txt`), la
integridad de la instalacion no esta protegida de ningun modo.

## 5. SSL pinning y seguridad TLS

**No hay pinning.** No aparece `okhttp3.CertificatePinner`, `X509TrustManager`
personalizados, `network_security_config.xml`, ni anclajes en el snapshot Dart.
Dart `HttpClient` usa `SecurityContext.defaultContext` (raices del sistema).

Debilidades asociadas:
- `android:usesCleartextTraffic="true"`: HTTP en claro permitido; la app lo
  aprovecha para OMDb (`http://www.omdbapi.com/`).
- Sin `networkSecurityConfig`, cualquier subdominio es alcanzable por HTTP.

Bypass para analisis: al no existir pinning, basta instalar la CA de mitmproxy
en el almacen del sistema del emulador (procedimiento en `dynamic/README.md`).
No es necesario Frida para degradar TLS.

## 6. Carga dinamica de codigo

**No detectada en el DEX** (sin `DexClassLoader`, `PathClassLoader`,
`InMemoryDexClassLoader`, ni `System.loadLibrary` de librerias ajenas a
Flutter). La descarga de `/lol_update.apk` es instalacion de un APK completo
mediante `REQUEST_INSTALL_PACKAGES`, no carga de codigo en el proceso: el
codigo descargado se ejecuta como una aplicacion nueva, no dentro de la actual.
El flujo nativo `libdartjni.so` (paquete `dart_lang/jni`) permite a Dart invocar
JNI, pero no hay indicios de que se carguen librerias arbitrarias del disco.

## 7. Otras observaciones de endurecimiento y comportamiento

- **Auto-actualizacion forzada**: cadenas `Actualiza para continuar.`,
  `Por favor actualiza la aplicacion`, `Actualizar ahora`,
  `Descargar actualizacion`, `Error descarga APK:` y archivo `/lol_update.apk`.
  El backend (`version_api.php`) decide la version minima. Sin verificacion de
  firma del APK descargado visible en el cliente: si el backend se viera
  comprometido, seria un vector de distribucion de codigo arbitrario. Este es
  el riesgo tecnico mas relevante de la aplicacion.
- **Scraping con WebView e inyeccion JavaScript**: el snapshot Dart contiene el
  JavaScript inyectado que vigila `absUrl.includes('.m3u8'|'.mp4'|'.ts'|'.m4s')`
  y notifica por `window.MediaDetector.postMessage(absUrl)`. Es la tecnica de
  captura de enlaces de reproduccion.
- **Interruptor remoto**: `desactivar_servidor.php` permite al operador
  desactivar servidores/fuentes en instalaciones ya desplegadas.
- **FileProvider amplio**: `filepaths.xml` del plugin `open_file` declara
  `root-path path="."`, que expone por URI cualquier ruta si otra app obtiene un
  URI grant. Riesgo bajo pero innecesario.
- **Deep links**: `lol://user/{...}` y `lol://content/{...}` se procesan en
  `MainActivity` aunque el manifiesto no declara intent-filters VIEW: los
  enlaces solo llegan si otra aplicacion lanza el intent explicitamente.
- **Sin telemetria ni publicidad**: no hay SDK de analitica, crash reporting ni
  anuncios (verificado en DEX y snapshot Dart). La privacidad del usuario no es
  recolectada por SDKs de terceros; lo unico que sale del dispositivo es
  peticiones de catalogo y de reproduccion.

## 8. Valoracion global de protecciones

La aplicacion no intenta impedir su analisis: ni anti-root, ni anti-emulador,
ni anti-Frida, ni pinning, ni empaquetado. Su superficie de ingenieria inversa
descansa unicamente en la opacidad natural del snapshot Dart AOT. El control
esta del lado del servidor (interruptor de servidores, version minima forzada y
distribucion de actualizaciones), lo que permite al operador gestionar el
parque de instalaciones sin codigo local protegido.
