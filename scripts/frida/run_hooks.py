#!/usr/bin/env python3
"""Lanzador de hooks de Frida para la sesion de analisis dinamico.

Uso: python3 scripts/frida/run_hooks.py <paquete> <script.js> <salida.txt> [segundos]

Lanza la aplicacion (spawn), instala el script de hooks y registra los eventos
durante el intervalo indicado. Las rutas son relativas y se pasan por argv, de
modo que funciona en local y en CI.
"""
import sys
import time

import frida


def main():
    paquete = sys.argv[1]
    ruta_script = sys.argv[2]
    ruta_salida = sys.argv[3]
    segundos = int(sys.argv[4]) if len(sys.argv) > 4 else 300

    eventos = []

    def on_message(message, data):
        if message.get("type") == "send":
            eventos.append(str(message.get("payload")))
        elif message.get("type") == "error":
            eventos.append("[script-error] " + str(message.get("description")))

    dispositivo = frida.get_usb_device(timeout=30)
    print(f"[+] dispositivo: {dispositivo.name}")
    pid = dispositivo.spawn([paquete])
    sesion = dispositivo.attach(pid)
    script = sesion.create_script(open(ruta_script, encoding="utf-8").read())
    script.on("message", on_message)
    script.load()
    dispositivo.resume(pid)
    print(f"[+] {paquete} lanzado (pid {pid}); observando {segundos}s")

    limite = time.time() + segundos
    while time.time() < limite:
        time.sleep(5)

    try:
        sesion.detach()
    except Exception:
        pass

    with open(ruta_salida, "w", encoding="utf-8") as f:
        f.write("\n".join(eventos) + "\n")
    print(f"[+] {len(eventos)} eventos escritos en {ruta_salida}")


if __name__ == "__main__":
    main()
