# EMS — Energy Management System

## Projecte
Sistema de gestió energètica per habitatge unifamiliar a Catalunya.
Desenvolupa't en Python/FastAPI amb especificació OpenAPI auto-generada.
Deploy: primer local (WSL + Docker Compose), després integrat amb Home Assistant existent.

## Dispositius i Protocols

### Solar — Hoymiles microinversors + DTU-W100/Pro
- **Llibreria**: `pysolarmanv5` (comunicació local LAN)
- **Connexió**: UDP/TCP port 8899, IP del DTU a `.env` com `HOYMILES_DTU_IP`
- **Serial number**: a `.env` com `HOYMILES_SERIAL` (nombre de sèrie del DTU, no del panell)
- **Dades clau**:
  - `dc_power` (W) — producció instantània total
  - `today_production` (kWh) — energia del dia
  - `total_production` (kWh) — energia total acumulada
  - `status` — online/offline
- **Polling**: cada 30 segons (no sobrecarregar el DTU)
- **Fitxer**: `integrations/solar/hoymiles.py`

### Wallbox — Pulsar Max
- **Protocol**: Wallbox REST API oficial (cloud) — `api.wall-box.com`
- **Auth**: OAuth2 amb `email` + `password` → token JWT
- **Credencials**: a `.env` com `WALLBOX_EMAIL`, `WALLBOX_PASSWORD`, `WALLBOX_CHARGER_ID`
- **Endpoints clau**:
  - `GET /v2/charger/{id}/status` — estat actual
  - `PUT /v2/charger/{id}` — control (max current en Amperes, lock/unlock)
  - `POST /v2/charger/{id}/remote-action` — start/stop càrrega
- **Rang de corrent**: 6A mínim, 32A màxim (Pulsar Max trifàsic)
- **Fitxer**: `integrations/wallbox/pulsar.py`

### Home Assistant
- **Ja en funcionament** a la xarxa local
- **Integració**: MQTT — el EMS publica dades, HA subscriu
- **MQTT Broker**: Mosquitto en Docker (aquest projecte), o broker existent de HA
- **Topics**:
  - `ems/solar/power` — producció instantània (W)
  - `ems/solar/today` — energia diària (kWh)
  - `ems/solar/status` — online/offline
  - `ems/wallbox/status` — estat del carregador
  - `ems/wallbox/power` — potència de càrrega actual (W)
  - `ems/wallbox/current_limit` — límit de corrent configurat (A)
  - `ems/ems/mode` — mode actiu: manual/auto/eco
  - `ems/ems/action` — última acció presa pel gestor
- **Fitxer**: `core/mqtt_publisher.py`

## Arquitectura del Codi

```
ems/
├── CLAUDE.md               ← aquest fitxer
├── .env                    ← secrets (no committejar mai)
├── .env.example            ← plantilla sense secrets
├── docker-compose.yml
├── requirements.txt
├── api/
│   ├── main.py             ← app FastAPI, inclou tots els routers
│   ├── dependencies.py     ← dependency injection (sessions, config)
│   ├── routers/
│   │   ├── solar.py        ← endpoints /solar/*
│   │   ├── wallbox.py      ← endpoints /wallbox/*
│   │   └── ems.py          ← endpoints /ems/* (mode, stats)
│   ├── models/
│   │   ├── solar.py        ← Pydantic models de resposta solar
│   │   └── wallbox.py      ← Pydantic models de resposta wallbox
│   └── schemas/            ← Pydantic schemas de request bodies
├── core/
│   ├── energy_manager.py   ← lògica principal EMS (modes AUTO/ECO/MANUAL)
│   ├── mqtt_publisher.py   ← publica a MQTT broker
│   ├── scheduler.py        ← polling periòdic (apscheduler)
│   └── config.py           ← llegeix .env amb pydantic-settings
├── integrations/
│   ├── solar/
│   │   └── hoymiles.py     ← wrapper pysolarmanv5
│   └── wallbox/
│       └── pulsar.py       ← wrapper Wallbox REST API
└── tests/
    ├── test_solar.py
    ├── test_wallbox.py
    └── test_energy_manager.py
```

## Regles de Negoci — Fase 1

### Mode MANUAL
- Cap control automàtic del wallbox
- El wallbox funciona amb la seva configuració pròpia

### Mode AUTO
- Si `excedent_solar > THRESHOLD_ON` (default: 1400W) durant `HISTERESI_ON` minuts → activa càrrega al mínim (6A)
- Si `excedent_solar < THRESHOLD_OFF` (default: 500W) durant `HISTERESI_OFF` minuts → desactiva càrrega
- Thresholds configurables via `.env`

### Mode ECO
- Càrrega contínua però `current_limit = floor(excedent_solar / VOLTAGE / PHASES)`
- Mínim 6A (≈1380W trifàsic), màxim 32A
- Si excedent < mínim → baixa a 6A (no talla la càrrega)
- Actualitza el límit cada cicle de polling (30s)

### Histeresi (tots els modes automàtics)
- No fer cap acció si l'estat ha canviat fa menys de `HISTERESI_MINUTS` (default: 5)
- Evitar flapping en dies nuvolosos

## Convencions de Codi

- **Python 3.11+** — usar `match/case` quan escaigui
- **Async/await** a tot arreu — FastAPI + httpx (async) + asyncio
- **Pydantic v2** per a tots els models i configuració
- **`pydantic-settings`** per llegir `.env` — una sola instància `Settings` com singleton
- **`httpx.AsyncClient`** per a totes les crides HTTP externes (Wallbox API)
- **`APScheduler`** per polling periòdic, no `while True` + `sleep`
- **Logging** amb `structlog` o Python `logging` estàndard, no `print()`
- **Tests**: `pytest` + `pytest-asyncio` + `respx` per mockejar HTTP
- **Errors**: sempre capturar excepcions específiques, mai `except Exception` silent
- **Mai hardcodejar** IPs, credencials, o thresholds — tot via `.env`

## Variables d'Entorn (.env.example)

```bash
# Hoymiles DTU
HOYMILES_DTU_IP=192.168.1.XXX
HOYMILES_SERIAL=XXXXXXXXXX

# Wallbox
WALLBOX_EMAIL=email@example.com
WALLBOX_PASSWORD=secret
WALLBOX_CHARGER_ID=XXXXXXXX

# MQTT
MQTT_HOST=localhost
MQTT_PORT=1883
MQTT_USERNAME=ems
MQTT_PASSWORD=secret

# EMS Config
EMS_DEFAULT_MODE=manual
EMS_THRESHOLD_ON_W=1400
EMS_THRESHOLD_OFF_W=500
EMS_HISTERESI_MINUTS=5
EMS_VOLTAGE=230
EMS_PHASES=3
EMS_POLL_INTERVAL_S=30

# API
API_HOST=0.0.0.0
API_PORT=8000
```

## Endpoints OpenAPI — Fase 1

```
GET  /solar/production      → producció actual + estat DTU
GET  /solar/stats           → energia avui / total
GET  /wallbox/status        → estat carregador + sessió activa
POST /wallbox/start         → inicia càrrega
POST /wallbox/stop          → atura càrrega
PUT  /wallbox/current-limit → body: {amps: int}
GET  /ems/status            → mode + última acció + timestamp
PUT  /ems/mode              → body: {mode: "manual"|"auto"|"eco"}
GET  /health                → health check (per Docker)
```

## Fases del Projecte

- **Fase 1** (actual): Solar Hoymiles + Wallbox Pulsar Max + MQTT → HA
- **Fase 2**: Aerotèrmia (Modbus o API fabricant)
- **Fase 3**: Dashboard web integrat
- **Fase 4**: Deploy com addon Home Assistant o servei extern permanent

## Notes de Desenvolupament

- Desenvolupament en **WSL (Ubuntu)** sobre Windows
- Docker Compose per tots els serveis (api + mosquitto)
- Hot-reload en dev: `uvicorn api.main:app --reload`
- Per debugar pysolarmanv5: primer provar amb script standalone `scripts/test_solar.py`
- L'API de Wallbox té rate limiting — no fer més de 1 crida cada 10s al mateix endpoint
