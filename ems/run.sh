#!/bin/sh

CONFIG=/data/options.json

export HOYMILES_DTU_IP="$(jq -r '.hoymiles_dtu_ip' "$CONFIG")"
export WALLBOX_CHARGER_ID="$(jq -r '.wallbox_charger_id' "$CONFIG")"
export WALLBOX_EMAIL="$(jq -r '.wallbox_email' "$CONFIG")"
export WALLBOX_PASSWORD="$(jq -r '.wallbox_password' "$CONFIG")"
export MQTT_HOST="$(jq -r '.mqtt_host' "$CONFIG")"
export MQTT_PORT="$(jq -r '.mqtt_port' "$CONFIG")"
export MQTT_USERNAME="$(jq -r '.mqtt_username' "$CONFIG")"
export MQTT_PASSWORD="$(jq -r '.mqtt_password' "$CONFIG")"
export INFLUXDB_HOST="$(jq -r '.influxdb_host // "a0d7b954-influxdb"' "$CONFIG")"
export INFLUXDB_PORT="$(jq -r '.influxdb_port // 8086' "$CONFIG")"
export INFLUXDB_DATABASE="$(jq -r '.influxdb_database // "ems"' "$CONFIG")"
export INFLUXDB_USERNAME="$(jq -r '.influxdb_username // ""' "$CONFIG")"
export INFLUXDB_PASSWORD="$(jq -r '.influxdb_password // ""' "$CONFIG")"
export EMS_DEFAULT_MODE="$(jq -r '.ems_default_mode' "$CONFIG")"
export EMS_THRESHOLD_ON_W="$(jq -r '.ems_threshold_on_w' "$CONFIG")"
export EMS_THRESHOLD_OFF_W="$(jq -r '.ems_threshold_off_w' "$CONFIG")"
export EMS_HISTERESI_MINUTS="$(jq -r '.ems_histeresi_minuts' "$CONFIG")"
export EMS_VOLTAGE="$(jq -r '.ems_voltage' "$CONFIG")"
export EMS_PHASES="$(jq -r '.ems_phases' "$CONFIG")"
export EMS_POLL_INTERVAL_S="$(jq -r '.ems_poll_interval_s' "$CONFIG")"
export API_HOST="0.0.0.0"
export API_PORT="8000"

exec uvicorn api.main:app --host "${API_HOST}" --port "${API_PORT}"
