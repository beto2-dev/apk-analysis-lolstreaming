# Auditoria de seguridad del APK sample.apk

Repositorio de analisis tecnico del archivo `sample.apk`
(descarga original: `https://modlyo.com/versiones/lol_200.apk`).
El objetivo del trabajo es determinar si la aplicacion es maliciosa, documentar
todas sus conexiones de red (dominios, IPs, URLs y endpoints) e inventariar las
protecciones de evasion que implementa (ofuscacion, anti-debugging, deteccion
de root/emulador, SSL pinning, carga dinamica de codigo, etc.).

## Hashes de referencia del archivo analizado

| Algoritmo | Valor |
|-----------|-------|
| SHA-256 | `4cefd5bee99887fd1b0b06b545228695e4ed311949948d37ac922fdb09e3cecf` |
| MD5 | `d59956c3990c7ae6613faaf89c194f36` |
| Tamano | 21.853.058 bytes (20,8 MiB) |
| Tipo | Android package (APK) |

## Estructura del repositorio

```
/static/       Resultados del analisis estatico (manifiesto, descompilacion,
               extraccion de cadenas, endpoints, protecciones)
/dynamic/      Resultados del analisis dinamico (capturas de trafico, logcat,
               archivos generados por la aplicacion)
/scripts/      Scripts de automatizacion (extraccion, hooks de Frida, soporte
               para el workflow de analisis dinamico)
/reports/      Informes finales (evaluacion de malware, informe tecnico)
/captures/     Artefactos complementarios (pantallazos, volcados auxiliares)
```

## Metodologia

1. **Analisis estatico**: descompilacion con `apktool` y `jadx`, revision del
   `AndroidManifest.xml`, extraccion de cadenas con `strings`/`grep`, analisis
   de APIs de red, criptografia, reflexion y carga dinamica de codigo.
2. **Analisis de red estatico**: catalogacion de endpoints clasificados por
   proposito probable (C2, exfiltracion, telemetria, publicidad, actualizacion).
3. **Analisis dinamico**: ejecucion controlada en un emulador Android
   (Android 11, API 30) dentro de GitHub Actions, con interceptacion de trafico
   mediante `mitmproxy` e instrumentacion con `Frida`. El flujo de trabajo esta
   en `.github/workflows/dynamic-analysis.yml` y se ejecuta manualmente
   (`workflow_dispatch`).
4. **Evaluacion**: clasificacion del riesgo (malware confirmado / sospechoso /
   PUP / benigno), familia estimada e indicadores de compromiso (IoC).

## Documento principal

- `reports/informe_final.md` (y `reports/informe_final.pdf`): informe tecnico
  completo con resumen ejecutivo, analisis del manifiesto, analisis de codigo,
  inventario de endpoints (estatico y dinamico), protecciones identificadas,
  comportamiento observado en el emulador, IoC y recomendaciones.
- `reports/evaluacion.md`: veredicto y justificacion.

## Aviso legal

Este analisis se realiza exclusivamente con fines de investigacion de
seguridad y respuesta a incidentes. La muestra no debe ejecutarse fuera de un
entorno controlado y aislado. Las conclusiones se limitan al archivo cuyo hash
figura arriba; cualquier redistribucion de la aplicacion original queda fuera
del alcance de este repositorio.
