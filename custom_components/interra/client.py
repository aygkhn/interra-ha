"""Interra paneline kalıcı TCP bağlantısı (ayrı thread) + protokol.

HA'dan bağımsız, saf Python. Durum güncellemelerini ve cihaz listesini
callback'lerle iletir; yeniden bağlanmayı kendi yönetir.
"""
from __future__ import annotations

import json
import logging
import socket
import threading
import time
from typing import Callable

from .const import (
    ACK_INTERVAL,
    COVER_TYPES,
    OT_TO_FLAG,
    REQ_DB,
    REQ_DEVICE,
    REQ_LOGIN,
    REQ_REGISTER,
    REQ_STATUS,
    SHOWN_TYPES,
    VALUE_KEYS,
)

_LOGGER = logging.getLogger(__name__)


class InterraClient:
    def __init__(self, host, port, username, password, local_host=None, local_port=None):
        # Bağlantı adayları: önce YEREL (ağ kablosu/LAN — hızlı ve güvenilir),
        # erişilemezse PUBLIC (internet). Her yeniden bağlanmada yerel tekrar denenir.
        self._candidates = []
        if local_host:
            self._candidates.append((local_host, int(local_port or port)))
        self._candidates.append((host, int(port)))
        self._active = self._candidates[0]
        self._user = username
        self._pass = password
        self._sock: socket.socket | None = None
        self._auth: str | None = None
        self._buf = b""
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._ready = threading.Event()

        self.devices: dict[int, dict] = {}
        # callback'ler (HA tarafı bağlar)
        self.on_devices: Callable[[], None] | None = None
        self.on_state: Callable[[int, bool | None, str | None], None] | None = None
        self.on_connection: Callable[[bool], None] | None = None

    # ---- yaşam döngüsü ----
    def start(self):
        threading.Thread(target=self._run, name="interra-client", daemon=True).start()
        threading.Thread(target=self._ack_loop, name="interra-ack", daemon=True).start()

    def stop(self):
        self._stop.set()
        try:
            if self._sock:
                self._sock.close()
        except OSError:
            pass

    def wait_ready(self, timeout=25):
        return self._ready.wait(timeout)

    # ---- bağlantı ----
    def _connect(self):
        # Adayları sırayla dene (public -> local); ilk bağlananı kullan
        last_err = None
        # Birden çok aday varsa ölü yereli hızlı geçmek için kısa timeout
        timeout = 5 if len(self._candidates) > 1 else 12
        for host, port in self._candidates:
            try:
                self._sock = socket.create_connection((host, port), timeout=timeout)
                self._sock.settimeout(None)
                self._active = (host, port)
                self._auth = None
                self._buf = b""
                _LOGGER.info("Interra bağlandı %s:%s", host, port)
                self._send({"data": {"userName": self._user, "password": self._pass},
                            "meta": {"requestType": REQ_LOGIN, "authID": None}})
                return
            except OSError as err:
                last_err = err
                _LOGGER.warning("Interra %s:%s erişilemedi (%s)", host, port, err)
        raise last_err or ConnectionError("bağlantı adayı yok")

    def _run(self):
        while not self._stop.is_set():
            try:
                self._connect()
                while not self._stop.is_set():
                    chunk = self._sock.recv(65536)
                    if not chunk:
                        raise ConnectionError("kapandı")
                    self._buf += chunk
                    while b"\n" in self._buf:
                        line, self._buf = self._buf.split(b"\n", 1)
                        line = line.rstrip(b"\r")
                        if line and line != b"CACK":
                            self._on_line(line.decode("utf-8", "replace"))
            except Exception as err:  # noqa: BLE001
                if self._stop.is_set():
                    break
                _LOGGER.warning("Interra bağlantı hatası: %s — 5 sn sonra yeniden", err)
                if self.on_connection:
                    self.on_connection(False)
                time.sleep(5)

    def _ack_loop(self):
        while not self._stop.is_set():
            time.sleep(ACK_INTERVAL)
            try:
                self._send_raw("CACK")
            except OSError:
                pass

    # ---- gönderme ----
    def _send(self, obj):
        self._send_raw(json.dumps(obj))

    def _send_raw(self, text):
        data = (text + "\r\n").encode()
        with self._lock:
            if self._sock:
                self._sock.sendall(data)

    # ---- alma ----
    def _on_line(self, line: str):
        try:
            env = json.loads(line)
        except ValueError:
            return
        meta = env.get("meta") or {}
        rt = meta.get("requestType")
        if meta.get("authID") and not self._auth:
            self._auth = meta["authID"]
            _LOGGER.info("Interra giriş başarılı")
            if self.on_connection:
                self.on_connection(True)
            self._send({"data": {"type": 1}, "meta": {"requestType": REQ_DB, "authID": self._auth}})
            return
        if meta.get("errorCode") and not self._auth:
            _LOGGER.error("Interra giriş hatası %s: %s", meta.get("errorCode"), meta.get("error"))
            return
        if rt == REQ_DB:
            self._apply_dump(env.get("data") or {})
        elif rt in (REQ_STATUS, REQ_REGISTER):
            self._apply_status(env.get("data"))

    def _apply_dump(self, data):
        locname = {l["id"]: (l.get("name") or "").strip() for l in data.get("locations", [])}
        attr: dict[int, set] = {}
        for a in data.get("deviceAttributes", []):
            did = a.get("deviceId", a.get("id"))
            attr.setdefault(did, set()).add(a.get("key"))
        devs: dict[int, dict] = {}
        for d in data.get("devices", []):
            if d.get("visibility") != 1 or d.get("parentId"):
                continue
            ot = d.get("objectType", 0)
            if ot not in SHOWN_TYPES:
                continue
            devs[d["id"]] = {
                "name": (d.get("name") or f"Cihaz {d['id']}").strip(),
                "room": locname.get(d.get("locationId"), ""),
                "type": ot,
                "has_value": bool(attr.get(d["id"], set()) & VALUE_KEYS),
                "location": d.get("locationId"),
                "is_cover": ot in COVER_TYPES,
            }
        self.devices = devs
        _LOGGER.info("Interra DB: %d cihaz", len(devs))
        self._ready.set()
        if self.on_devices:
            self.on_devices()
        # her (konum, tip) için anlık durum + abonelik
        pairs = {(d["location"], d["type"]) for d in devs.values()}
        for loc, ot in pairs:
            self._send({"data": {"id": str(loc), "objectType": str(ot)},
                        "meta": {"requestType": REQ_STATUS, "authID": self._auth}})
            flag = OT_TO_FLAG.get(ot)
            if flag is not None:
                self._send({"data": None, "meta": {"requestType": REQ_REGISTER, "authID": self._auth,
                            "flags": [{"id": flag, "value": True, "data": loc}]}})

    def _apply_status(self, data):
        if data is None:
            return
        arr = data if isinstance(data, list) else [data]
        for s in arr:
            if not s or s.get("id") is None:
                continue
            if self.on_state:
                self.on_state(s["id"], s.get("isActive"), s.get("readValueStatus", s.get("readValue")))

    # ---- komutlar ----
    def action(self, dev_id, action_type, value=0):
        if not self._auth:
            return
        self._send({"data": {"actionType": str(action_type), "id": str(dev_id), "value": str(value)},
                    "meta": {"requestType": REQ_DEVICE, "authID": self._auth}})
