#!/usr/bin/env python3
"""Metadatos del APK: paquete, version, SDK, permisos, componentes y firma.

Vuelca la informacion del AndroidManifest.xml (decodificado con androguard)
y los certificados de firma (esquemas v1/v2/v3) en static/.
Uso: python3 scripts/static_info.py [ruta/al/archivo.apk]
"""
import os
import subprocess
import sys
import tempfile
import zipfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APK_PATH = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, "sample.apk")
OUT = os.path.join(REPO, "static")
os.makedirs(OUT, exist_ok=True)


def main():
    from loguru import logger
    logger.remove()  # silencia el log de depuracion de androguard
    from androguard.core.apk import APK
    a = APK(APK_PATH)

    lines = []
    add = lines.append
    add("# Metadatos del APK")
    add("")
    add(f"- Paquete: {a.get_package()}")
    add(f"- versionName: {a.get_androidversion_name()} / versionCode: {a.get_androidversion_code()}")
    add(f"- minSdk: {a.get_min_sdk_version()} / targetSdk: {a.get_target_sdk_version()}")
    add(f"- App label: {a.get_app_name()}")
    add(f"- Actividad principal: {a.get_main_activity()}")
    add(f"- Permisos ({len(a.get_permissions())}):")
    for p in sorted(a.get_permissions()):
        add(f"  - {p}")
    add(f"- Actividades ({len(a.get_activities())}):")
    for x in sorted(a.get_activities()):
        add(f"  - {x}")
    add(f"- Servicios ({len(a.get_services())}):")
    for x in sorted(a.get_services()):
        add(f"  - {x}")
    add(f"- Receptores ({len(a.get_receivers())}):")
    for x in sorted(a.get_receivers()):
        add(f"  - {x}")
    add(f"- Proveedores ({len(a.get_providers())}):")
    for x in sorted(a.get_providers()):
        add(f"  - {x}")
    for attr in ("debuggable", "allowBackup", "usesCleartextTraffic",
                 "networkSecurityConfig", "extractNativeLibs", "name", "appComponentFactory"):
        v = None
        man = os.path.join(OUT, "apk_extracted", "AndroidManifest.xml")
        if os.path.exists(man):
            import xml.etree.ElementTree as ET
            ns = "{http://schemas.android.com/apk/res/android}"
            root = ET.parse(man).getroot()
            app = root.find("application")
            if app is not None:
                v = app.get(ns + attr)
        else:
            v = "(manifiesto decodificado no disponible)"
        if v is not None:
            add(f"- application/@{attr}: {v}")

    with open(os.path.join(OUT, "manifest_info.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))

    # --- Certificados de firma ---
    cert_lines = ["# Certificados de firma del APK", ""]
    certs = []
    try:
        certs = a.get_certificates_v2()
        scheme = "v2"
    except Exception:
        certs = []
    if not certs:
        try:
            certs = a.get_certificates_v3()
            scheme = "v3"
        except Exception:
            certs = []
    if certs:
        from cryptography import x509
        from cryptography.hazmat.primitives import hashes
        cert_lines.append(f"Esquema de firma: APK Signature Scheme {scheme} ({len(certs)} certificado(s))")
        for c in certs:
            # androguard devuelve objetos asn1crypto.x509.Certificate
            def safe(fn, default):
                try:
                    return fn()
                except Exception:
                    return default
            cert_lines.append("")
            cert_lines.append(f"Asunto:    {safe(lambda: c.subject.human_friendly, str(c.subject))}")
            cert_lines.append(f"Emisor:     {safe(lambda: c.issuer.human_friendly, str(c.issuer))}")
            cert_lines.append(f"Serie:      {safe(lambda: hex(c.serial_number), '?')}")
            cert_lines.append(f"Validez:    {safe(lambda: str(c['tbs_certificate']['validity']['not_before'].native), '?')} -> {safe(lambda: str(c['tbs_certificate']['validity']['not_after'].native), '?')}")
            try:
                fp = c.sha256.hex(":")
                cert_lines.append(f"SHA-256:    {fp}")
            except Exception as e:
                cert_lines.append(f"SHA-256: error {e}")
    else:
        # Alternativa: bloque PKCS#7 de firma JAR (v1)
        with zipfile.ZipFile(APK_PATH) as z:
            rsa = [n for n in z.namelist() if n.startswith("META-INF/") and n.upper().endswith((".RSA", ".DSA", ".EC"))]
        if rsa:
            with tempfile.TemporaryDirectory() as td:
                p = os.path.join(td, os.path.basename(rsa[0]))
                with zipfile.ZipFile(APK) as z, open(p, "wb") as f:
                    f.write(z.read(rsa[0]))
                r = subprocess.run(
                    ["openssl", "pkcs7", "-inform", "DER", "-in", p, "-print_certs", "-text"],
                    capture_output=True, text=True)
                cert_lines.append("Esquema de firma: JAR v1 (PKCS#7)")
                cert_lines.append(r.stdout[:3000])
        else:
            cert_lines.append("No se encontraron certificados de firma (v1/v2/v3).")
    with open(os.path.join(OUT, "certificado.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(cert_lines) + "\n")
    print("\n".join(cert_lines))


if __name__ == "__main__":
    main()
