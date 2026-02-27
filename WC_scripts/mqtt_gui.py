#!/usr/bin/env python3
import json
import time
import tkinter as tk
from tkinter import ttk, messagebox

import paho.mqtt.client as mqtt

# ====== MQTT SETTINGS (igual que tu script) ======
MQTT_HOST = "155.210.152.63"
MQTT_PORT = 8080
MQTT_USERNAME = "emoncms"
MQTT_PASSWORD = "paip2020"
MQTT_TOPIC = "cooler"

MQTT_MEASUREMENT = "control"
MQTT_DEVICE = "control"
MQTT_QOS = 0
MQTT_RETAIN = False

# Si tu puerto 8080 fuese WebSockets (solo si te falla):
USE_WEBSOCKETS = False
WS_PATH = "/mqtt"
# ===============================================

# ====== BRIDGE SETTINGS (configurable arriba) ======
BRIDGE_SCRIPT = "serie_json_2_hwinfo_mqtt.py"  # puede ser nombre o ruta
BRIDGE_PORT = "COM6"
# ===============================================


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Cooler Control (MQTT)")

        # Ventana suficientemente alta + redimensionable en vertical (importante con escalado Windows)
        self.geometry("560x460")
        self.resizable(False, True)
        self.minsize(560, 420)

        # ---- runtime ----
        self.bridge_proc = None

        self.status_var = tk.StringVar(value="MQTT: desconectado")
        self.text_var = tk.StringVar(value="")

        # Config puente editable
        self.bridge_script_var = tk.StringVar(value=BRIDGE_SCRIPT)
        self.bridge_port_var = tk.StringVar(value=BRIDGE_PORT)

        frm = ttk.Frame(self, padding=12)
        frm.pack(fill="both", expand=True)

        # Deja que el LOG (fila 7) absorba el espacio extra
        frm.grid_rowconfigure(7, weight=1)

        # ---- Config bridge arriba ----
        cfg = ttk.LabelFrame(frm, text="Bridge (Serie -> HWiNFO + MQTT)", padding=10)
        cfg.grid(row=0, column=0, columnspan=3, sticky="we")

        ttk.Label(cfg, text="Script:").grid(row=0, column=0, sticky="w")
        self.bridge_script_entry = ttk.Entry(cfg, textvariable=self.bridge_script_var, width=46)
        self.bridge_script_entry.grid(row=0, column=1, columnspan=2, sticky="we", padx=(8, 0))

        ttk.Label(cfg, text="Puerto:").grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.bridge_port_entry = ttk.Entry(cfg, textvariable=self.bridge_port_var, width=12)
        self.bridge_port_entry.grid(row=1, column=1, sticky="w", padx=(8, 0), pady=(6, 0))

        # Botones Run/Stop dentro de la caja del bridge (a la derecha del puerto)
        btns = ttk.Frame(cfg)
        btns.grid(row=1, column=2, sticky="e", pady=(6, 0))

        self.btn_bridge_start = ttk.Button(btns, text="Run bridge", command=self.start_bridge)
        self.btn_bridge_stop = ttk.Button(btns, text="Stop bridge", command=self.stop_bridge)
        self.btn_bridge_start.pack(side="left", padx=(0, 8))
        self.btn_bridge_stop.pack(side="left")

        cfg.grid_columnconfigure(1, weight=1)

        # ---- Experimento ----
        ttk.Label(frm, text="Experimento (se envía como fields.text):").grid(
            row=1, column=0, columnspan=3, sticky="w", pady=(10, 0)
        )
        self.entry = ttk.Entry(frm, textvariable=self.text_var, width=70)
        self.entry.grid(row=2, column=0, columnspan=3, sticky="we", pady=(4, 10))
        self.entry.focus_set()

        self.btn_start = ttk.Button(frm, text="Start", command=lambda: self.send_cmd("start"))
        self.btn_stop = ttk.Button(frm, text="Stop", command=lambda: self.send_cmd("stop"))
        self.btn_send = ttk.Button(frm, text="Send (custom)", command=self.send_custom)

        self.btn_start.grid(row=3, column=0, sticky="we", padx=(0, 8))
        self.btn_stop.grid(row=3, column=1, sticky="we", padx=(0, 8))
        self.btn_send.grid(row=3, column=2, sticky="we")

        ttk.Label(frm, textvariable=self.status_var).grid(
            row=4, column=0, columnspan=3, sticky="w", pady=(8, 0)
        )

        ttk.Label(frm, text="Log:").grid(row=5, column=0, sticky="w", pady=(10, 0))
        self.log = tk.Text(frm, height=9, width=70, state="disabled")
        self.log.grid(row=6, column=0, columnspan=3, sticky="nsew", pady=(4, 0))

        for c in range(3):
            frm.grid_columnconfigure(c, weight=1)

        # ---- MQTT client ----
        if USE_WEBSOCKETS:
            self.client = mqtt.Client(transport="websockets")
            self.client.ws_set_options(path=WS_PATH)
        else:
            self.client = mqtt.Client()

        self.client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect

        try:
            self.client.connect(MQTT_HOST, MQTT_PORT, keepalive=30)
            self.client.loop_start()
            self._log(f"Conectando a {MQTT_HOST}:{MQTT_PORT} topic='{MQTT_TOPIC}' ...")
        except Exception as e:
            self._set_status("MQTT: error al conectar")
            self._log(f"ERROR connect: {e}")

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    # ---------- UI helpers ----------
    def _set_status(self, s: str):
        self.after(0, lambda: self.status_var.set(s))

    def _log(self, s: str):
        def _do():
            self.log.configure(state="normal")
            self.log.insert("end", s + "\n")
            self.log.see("end")
            self.log.configure(state="disabled")

        self.after(0, _do)

    # ---------- MQTT callbacks ----------
    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self._set_status("MQTT: conectado")
            self._log("MQTT conectado OK")
        else:
            self._set_status(f"MQTT: fallo connect rc={rc}")
            self._log(f"MQTT connect rc={rc}")

    def _on_disconnect(self, client, userdata, rc):
        self._set_status("MQTT: desconectado")
        self._log(f"MQTT desconectado rc={rc}")

    # ---------- MQTT publish ----------
    def _publish(self, cmd: str, text: str):
        payload = {
            "measurement": MQTT_MEASUREMENT,
            "tags": {"device": MQTT_DEVICE},
            "fields": {"cmd": cmd, "text": text},
            "ts": time.time(),
        }
        msg = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
        info = self.client.publish(MQTT_TOPIC, msg, qos=MQTT_QOS, retain=MQTT_RETAIN)
        info.wait_for_publish(timeout=3)
        self._log(f"PUB -> {MQTT_TOPIC} : {msg}")

    def send_cmd(self, cmd: str):
        text = self.text_var.get().strip()
        try:
            self._publish(cmd, text)
        except Exception as e:
            messagebox.showerror("MQTT", f"No se pudo publicar:\n{e}")
            self._log(f"ERROR publish: {e}")

    def send_custom(self):
        text = self.text_var.get().strip()
        if not text:
            messagebox.showinfo("Enviar", "Escribe algo en el campo de texto.")
            return
        try:
            self._publish("custom", text)
        except Exception as e:
            messagebox.showerror("MQTT", f"No se pudo publicar:\n{e}")
            self._log(f"ERROR publish: {e}")

    # ---------- Bridge control ----------
    def start_bridge(self):
        import subprocess, sys
        from pathlib import Path

        if self.bridge_proc and self.bridge_proc.poll() is None:
            self._log("Bridge ya está corriendo.")
            return

        script = self.bridge_script_var.get().strip()
        port = self.bridge_port_var.get().strip()
        if not script or not port:
            messagebox.showerror("Bridge", "Completa Script y Puerto (COMx).")
            return

        p = Path(script)
        if not p.is_absolute():
            p = Path(__file__).resolve().parent / p

        cmd = [sys.executable, str(p), port]
        try:
            self.bridge_proc = subprocess.Popen(cmd)
            self._log(f"Bridge START -> {' '.join(cmd)}")
        except Exception as e:
            self._log(f"ERROR start bridge: {e}")
            messagebox.showerror("Bridge", f"No se pudo lanzar:\n{e}")

    def stop_bridge(self):
        import subprocess

        if not self.bridge_proc or self.bridge_proc.poll() is not None:
            self._log("Bridge no está corriendo.")
            return
        try:
            self.bridge_proc.terminate()
            try:
                self.bridge_proc.wait(timeout=3)
                self._log("Bridge STOP -> terminado")
            except subprocess.TimeoutExpired:
                self.bridge_proc.kill()
                self._log("Bridge STOP -> kill (no respondió a terminate)")
        except Exception as e:
            self._log(f"ERROR stop bridge: {e}")
            messagebox.showerror("Bridge", f"No se pudo parar:\n{e}")

    # ---------- Close ----------
    def on_close(self):
        try:
            self.stop_bridge()
        except Exception:
            pass
        try:
            self.client.loop_stop()
            self.client.disconnect()
        except Exception:
            pass
        self.destroy()


if __name__ == "__main__":
    App().mainloop()