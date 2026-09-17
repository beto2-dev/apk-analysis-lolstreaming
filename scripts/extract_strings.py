#!/usr/bin/env python3
"""Extraccion de cadenas de red (URLs, IPs, dominios) desde el APK.

Analiza los artefactos binarios del APK (libapp.so de Flutter / snapshot Dart,
classes*.dex, recursos y assets) y vuelca los resultados en static/strings/.
Uso:  python3 scripts/extract_strings.py [ruta/al/archivo.apk]

Las rutas se resuelven de forma relativa a la raiz del repositorio, de modo
que el script funciona tanto en local como en CI.
"""
import os
import re
import sys
import zipfile
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APK = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, "sample.apk")
OUT = os.path.join(REPO, "static", "strings")
os.makedirs(OUT, exist_ok=True)

URL_RE = re.compile(rb"(?:https?|wss?|ftp)://[A-Za-z0-9\-._~:/?#\[\]@!$&'()*+,;=%]+")
IP_RE = re.compile(rb"\b(?:\d{1,3}\.){3}\d{1,3}\b")
DOMAIN_RE = re.compile(
    rb"\b[a-zA-Z0-9](?:[a-zA-Z0-9\-_]{0,61}[a-zA-Z0-9])?"
    rb"(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9\-_]{0,61}[a-zA-Z0-9])?)+"
    rb"\.(?:com|net|org|io|xyz|top|ru|cn|app|dev|tv|cc|me|info|biz|co|es|mx|ar|cl|pe|br|uk|de|fr|nl|se|ch|jp|kr|us|la|gg|ly|to|ai|cloud|site|online|store|space|fun|pro|one|life|live|news|media|stream|video|movie|plus|shop|link|page|app|fast|icu|vip)\b",
    re.IGNORECASE,
)
B64_RE = re.compile(rb"[A-Za-z0-9+/]{40,}={0,2}")

# Ruido tipico (versiones, namespaces, rutas internas)
NOISE = {
    b"1.0.0", b"0.0.0", b"127.0.0.1", b"0.0.0.0", b"255.255.255.255",
    b"2.0.0", b"1.0.0.0", b"10.0.2.2", b"192.168.", b"169.254.",
}


def printable_strings(data, minlen=6):
    """Cadenas ASCII/UTF-8 imprimibles contiguas (estilo strings(1))."""
    cur = bytearray()
    for byte in data:
        if 32 <= byte < 127 or byte in (9,):
            cur.append(byte)
        else:
            if len(cur) >= minlen:
                yield bytes(cur)
            cur = bytearray()
    if len(cur) >= minlen:
        yield bytes(cur)


def main():
    urls, ips, domains, b64 = set(), set(), set(), set()
    per_source = defaultdict(set)
    raw_texts = []

    with zipfile.ZipFile(APK) as z:
        targets = []
        for name in z.namelist():
            low = name.lower()
            if low.endswith(".dex") or "/libapp.so" in low or low.endswith(".so") \
               or low.endswith(".arsc") or "flutter_assets" in low:
                targets.append(name)

        for name in targets:
            data = z.read(name)
            src_urls = set(m.group(0).decode(errors="replace") for m in URL_RE.finditer(data))
            src_ips = set(
                m.group(0).decode() for m in IP_RE.finditer(data)
                if not any(m.group(0).startswith(n) for n in NOISE)
            )
            src_domains = set(m.group(0).decode().lower().strip(".") for m in DOMAIN_RE.finditer(data))
            src_b64 = set(m.group(0).decode() for m in B64_RE.finditer(data))
            urls |= src_urls; ips |= src_ips; domains |= src_domains; b64 |= src_b64
            per_source[name] |= src_urls | src_domains
            if name.endswith(("libapp.so",)) or name.endswith(".dex"):
                raw_texts.append((name, data))

    def dump(fname, items, header):
        path = os.path.join(OUT, fname)
        with open(path, "w", encoding="utf-8") as f:
            f.write(header + "\n")
            for item in sorted(items):
                f.write(item + "\n")
        print(f"[+] {path}: {len(items)} entradas")
        return path

    dump("urls.txt", urls, "# URLs extraidas del APK (libapp.so, dex, assets, recursos)")
    dump("ips.txt", ips, "# Direcciones IP literales (filtrado localhost/documentacion)")
    dump("domains.txt", domains, "# Dominios observados")
    dump("base64_candidates.txt", list(b64)[:500], "# Candidatos Base64 (posibles cadenas ofuscadas; muestra limitada)")

    # Volcado completo de cadenas para referencia
    with open(os.path.join(OUT, "libapp_strings.txt"), "w", encoding="utf-8", errors="replace") as f:
        f.write("# Cadena de caracteres imprimibles de lib/armeabi-v7a/libapp.so\n")
        for name, data in raw_texts:
            if name.endswith("libapp.so"):
                for s in printable_strings(data):
                    f.write(s.decode(errors="replace") + "\n")
    print(f"[+] static/strings/libapp_strings.txt listo")

    # Resumen por archivo para trazabilidad
    with open(os.path.join(OUT, "por_archivo.txt"), "w", encoding="utf-8") as f:
        for name in sorted(per_source):
            if per_source[name]:
                f.write(f"== {name}\n")
                for item in sorted(per_source[name]):
                    f.write("  " + item + "\n")
    print("[+] static/strings/por_archivo.txt listo")
    print(f"\nTotal: {len(urls)} URLs | {len(domains)} dominios | {len(ips)} IPs | {len(b64)} candidatos Base64")


if __name__ == "__main__":
    main()
