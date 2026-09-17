"""Complemento de mitmproxy: registro legible de cada flujo HTTP(S).

Uso: mitmdump -s scripts/dynamic/flow_logger.py -w dynamic/captures/traffic.mitm
Escribe dynamic/captures/flows_log.txt (una linea por peticion y respuesta),
resuelto relativo a la raiz del repositorio (dos niveles sobre este archivo).
"""
import os

from mitmproxy import http

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOG = os.path.join(BASE, "dynamic", "captures", "flows_log.txt")
os.makedirs(os.path.dirname(LOG), exist_ok=True)


def _log(text):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(text + "\n")


def request(flow: http.HTTPFlow) -> None:
    params = list(flow.request.query.fields) if flow.request.query else []
    headers_clave = {
        k: flow.request.headers.get(k)
        for k in ("user-agent", "authorization", "content-type")
        if k in flow.request.headers
    }
    _log(f">>> {flow.request.method} {flow.request.pretty_url} params={params} hdr={headers_clave}")


def response(flow: http.HTTPFlow) -> None:
    status = flow.response.status_code if flow.response else 0
    body = ""
    try:
        body = flow.response.get_text(strict=False) if flow.response else ""
    except Exception:
        body = ""
    ct = flow.response.headers.get("content-type", "-") if flow.response else "-"
    preview = body[:400].replace("\n", " ") if body else ""
    _log(f"<<< {status} {flow.request.pretty_url} ct={ct} len={len(body)} :: {preview}")
