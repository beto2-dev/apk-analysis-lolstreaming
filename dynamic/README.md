# Analisis dinamico en emulador Android

## Metodologia

El analisis dinamico se ejecuta en un runner de GitHub Actions con un emulador
Android real. El flujo de trabajo completo esta en
`.github/workflows/dynamic-analysis.yml` y se lanza manualmente
(`workflow_dispatch`), o automaticamente cada vez que se dispare desde la
pestaña Actions del repositorio.

Pasos que automatiza el workflow:

1. **Entorno**: instalacion de `frida-tools`, `mitmproxy`, SDK de Android
   (platform-tools, emulator, build-tools 30.0.3) e imagen de sistema
   `system-images;android-30;google_apis;x86_64` (Android 11, con root
   disponible).
2. **AVD**: dispositivo virtual tipo `pixel_4` llamado `auditoria`.
3. **Interceptacion de red**: `mitmdump` escucha en `127.0.0.1:8080` del host,
   guarda los flujos en `dynamic/captures/traffic.mitm` y, mediante el
   complemento `scripts/dynamic/flow_logger.py`, vuelca un resumen legible en
   `dynamic/captures/flows_log.txt`.
4. **Emulador**: arranque headless con
   `-no-window -no-audio -no-boot-anim -gpu swiftshader_indirect`,
   `-writable-system` y `-http-proxy http://10.0.2.2:8080`. El proxy del
   emulador opera a nivel de red del invitado, de modo que captura tambien el
   trafico de Dart `HttpClient` (Flutter), que ignora la configuracion de proxy
   del sistema Android.
5. **Autoridad certificadora**: `adb root`, `adb remount` y copia del
   certificado de mitmproxy a `/system/etc/security/cacerts/<hash>.0` para que
   las conexiones TLS del sistema (incluida Dart) acepten la interceptacion.
6. **Instrumentacion**: `frida-server` (misma version que `frida-tools`) se
   sube a `/data/local/tmp/` y se ejecuta como root. La aplicacion se lanza con
   spawn mediante `scripts/frida/run_hooks.py`, que carga `scripts/frida/hooks.js`
   (registro de `java.net.URL`, `HttpsURLConnection`, OkHttp, `Cipher.doFinal`,
   `DexClassLoader`, `Runtime.exec`, `System.loadLibrary`, `SSLContext.init` y
   `getPackageInfo`).
7. **Observacion**: 300 segundos con hooks activos mas 90 segundos de
   observacion pasiva; posteriormente se recolectan:
   - `dynamic/logs/logcat.txt` y `logcat_crash.txt` (buffer completo y buffer de
     errores)
   - `dynamic/logs/frida_hooks.txt` (eventos de los hooks)
   - `dynamic/logs/archivos_app.txt` (listado de archivos de la app) y
     `dynamic/files_app/` (copias de los datos de `/data/data/<paquete>`,
     excluyendo caches)
   - `dynamic/captures/traffic.mitm` y `flows_log.txt`
8. **Publicacion**: los resultados se suben como artefacto de la ejecucion y se
   publican por commit en este directorio.

## Limitaciones

- El analisis dinamico depende de que el backend `modlyo.com` siga activo; si
  el interruptor remoto (`desactivar_servidor.php`) o el control de versiones
  (`version_api.php`) bloquean la aplicacion, el trafico observado se limita a
  esas comprobaciones iniciales.
- La resolucion de video no se reproduce si los hosters externos exigen
  interaccion (cortafuegos de embeds); aun asi, las peticiones DNS/TLS a los
  dominios quedan registradas en `traffic.mitm`.
- El runner efimero no tiene sesion de Google ni datos previos: si la
  aplicacion cambiara de comportamiento segun el dispositivo, los resultados
  corresponden a un Pixel 4 virtual con Android 11 recien formateado.

## Reproduccion local

```bash
# 1) Emulador con imagen rootable
avdmanager create avd -n auditoria -k "system-images;android-30;google_apis;x86_64"
emulator -avd auditoria -no-window -writable-system -http-proxy http://127.0.0.1:8080 &

# 2) mitmproxy en el host
mitmdump -s scripts/dynamic/flow_logger.py -w dynamic/captures/traffic.mitm

# 3) CA de mitmproxy en el sistema
adb root && adb remount
H=$(openssl x509 -inform PEM -subject_hash_old -in ~/.mitmproxy/mitmproxy-ca.pem | head -1)
adb push ~/.mitmproxy/mitmproxy-ca-cert.pem /system/etc/security/cacerts/$H.0

# 4) Frida
pip install frida-tools
adb push frida-server /data/local/tmp/ && adb shell chmod 755 /data/local/tmp/frida-server
adb shell "/data/local/tmp/frida-server &"

# 5) Lanzamiento instrumentado
adb install sample.apk
python3 scripts/frida/run_hooks.py com.example.lol scripts/frida/hooks.js dynamic/logs/frida_hooks.txt 300
```
