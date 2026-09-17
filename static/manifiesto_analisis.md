# Analisis del AndroidManifest.xml

Archivo decodificado: `static/apk_extracted/AndroidManifest.xml` (apktool 2.9.3).
Metadatos completos: `static/manifest_info.txt`.

## Identificacion

| Campo | Valor |
|-------|-------|
| Paquete | `com.example.lol` |
| Etiqueta | `lol` |
| versionName / versionCode | 1.0.0 / 1001 |
| minSdk / targetSdk | 24 (Android 7.0) / 36 (Android 16) |
| Compilado con SDK | 36 |
| Actividad principal | `com.example.lol.MainActivity` (Flutter) |
| Orientacion | Movil y Android TV (feature `android.software.leanback`, banner, `com.google.android.tv=true`) |

El nombre de paquete `com.example.lol` es el valor por defecto de las plantillas;
indica una compilacion sin proceso de publicacion profesional, coherente con la
distribucion directa por el sitio del desarrollador.

## Permisos solicitados (10)

| Permiso | Nivel de riesgo | Evaluacion |
|---------|-----------------|------------|
| `android.permission.INTERNET` | Bajo | Necesario: streaming y APIs de catalogo. |
| `android.permission.ACCESS_NETWORK_STATE` | Bajo | Deteccion de conectividad. |
| `android.permission.REQUEST_INSTALL_PACKAGES` | **Alto** | Permite instalar otros APKs. En una app de streaming no es necesario; se usa para el mecanismo de auto-actualizacion que descarga `/lol_update.apk` desde el backend propio. Es el permiso mas sensible del manifiesto. |
| `android.permission.WRITE_EXTERNAL_STORAGE` (maxSdk=28) | Medio | Escritura en almacenamiento compartido en Android 9 o anterior (descargas). |
| `android.permission.READ_EXTERNAL_STORAGE` (maxSdk=32) | Bajo | Lectura de archivos descargados. |
| `android.permission.READ_MEDIA_IMAGES` | Bajo | Acceso a galeria (Android 13+). |
| `android.permission.READ_MEDIA_VIDEO` | Bajo | Idem. |
| `android.permission.READ_MEDIA_AUDIO` | Bajo | Idem. |
| `android.permission.WAKE_LOCK` | Bajo | Mantener pantalla encendida durante reproduccion (wakelock_plus). |
| `com.example.lol.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION` | Informativo | Permiso de firma generado por androidx para receptores no exportados. |

No se solicitan permisos tipicos de malware Android: ni SMS, ni contactos,
ni telefono, ni ubicacion, ni camara, ni microfono, ni accesibilidad.

## Componentes

| Tipo | Componente | Exportado | Observacion |
|------|------------|-----------|-------------|
| Actividad | `com.example.lol.MainActivity` | Si | Launcher normal y LEANBACK_LAUNCHER (TV). Maneja enlaces `lol://user/...` y `lol://content/...` en codigo (sin intent-filter VIEW declarado). |
| Actividad | `io.flutter.plugins.urllauncher.WebViewActivity` | No | Plugin url_launcher. |
| Receptor | `androidx.profileinstaller.ProfileInstallReceiver` | Si | Protegido por `android.permission.DUMP`; estandar de androidx. |
| Proveedor | `androidx.core.content.FileProvider` (`com.example.lol.fileprovider`) | No | Comparte archivos internos (descargas). |
| Proveedor | `com.crazecoder.openfile.FileProvider` | No | Plugin open_file; su `filepaths.xml` incluye `root-path path="."`, alcance innecesariamente amplio. |
| Proveedor | `androidx.startup.InitializationProvider` | No | Estandar androidx. |
| Servicios | (ninguno) | - | Sin servicios en segundo plano: no hay persistencia ni ejecucion oculta. |

## Configuracion de seguridad de la aplicacion

| Atributo | Valor | Evaluacion |
|----------|-------|------------|
| `android:usesCleartextTraffic` | **true** | Permite HTTP en claro para todo el dominio de la app. Se observo su uso: la consulta a `http://www.omdbapi.com/` (API de valoraciones) viaja sin cifrar y es interceptable en la red local. |
| `android:debuggable` | No declarado | Correcto (false por defecto). |
| `android:allowBackup` | No declarado | Por defecto `true`: los datos de la app (incluido el datastore de preferencias) pueden extraerse con `adb backup` en configuraciones antiguas. Riesgo bajo. |
| `android:networkSecurityConfig` | No declarado | Sin politica de anclaje de certificados ni restricciones de dominio. |
| `android:extractNativeLibs` | false | Librerias nativas sin extraer (carga directa desde el APK). |

## Consultas (queries)

- `ACTION_PROCESS_TEXT` sobre `text/plain`: permite recibir texto seleccionado en
  otras apps (busqueda de titulos desde el portapapeles).
- `ACTION_VIEW` con MIME `application/vnd.android.package-archive`: intent de
  apertura de APKs, coherente con el permiso `REQUEST_INSTALL_PACKAGES` y el
  flujo `Actualiza para continuar` detectado en el snapshot Dart.
