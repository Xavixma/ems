#!/usr/bin/with-contenv bashio

bashio::log.info "Starting EMS - Energy Management System..."

# --- Hoymiles DTU ---
export HOYMILES_DTU_IP="$(bashio::config 'hoymiles_dtu_ip')"

# --- Wallbox ---
export WALLBOX_CHARGER_ID="$(bashio::config 'wallbox_charger_id')"
export WALLBOX_EMAIL="$(bashio::config 'wallbox_email')"
export WALLBOX_PASSWORD="$(bashio::config 'wallbox_password')"

# --- MQTT (defaults to HA Mosquitto add-on) ---
export MQTT_HOST="$(bashio::config 'mqtt_host')"
export MQTT_PORT="$(bashio::config 'mqtt_port')"
export MQTT_USERNAME="$(bashio::config 'mqtt_username')"
export MQTT_PASSWORD="$(bashio::config 'mqtt_password')"

# --- InfluxDB (optional — leave influxdb_url empty to disable) ---
export INFLUXDB_URL="$(bashio::config 'influxdb_url')"
export INFLUXDB_TOKEN="$(bashio::config 'influxdb_token')"
export INFLUXDB_ORG="$(bashio::config 'influxdb_org')"
export INFLUXDB_BUCKET="$(bashio::config 'influxdb_bucket')"

# --- EMS tuning ---
export EMS_DEFAULT_MODE="$(bashio::config 'ems_default_mode')"
export EMS_THRESHOLD_ON_W="$(bashio::config 'ems_threshold_on_w')"
export EMS_THRESHOLD_OFF_W="$(bashio::config 'ems_threshold_off_w')"
export EMS_HISTERESI_MINUTS="$(bashio::config 'ems_histeresi_minuts')"
export EMS_VOLTAGE="$(bashio::config 'ems_voltage')"
export EMS_PHASES="$(bashio::config 'ems_phases')"
export EMS_POLL_INTERVAL_S="$(bashio::config 'ems_poll_interval_s')"

# --- API (fixed inside the container) ---
export API_HOST="0.0.0.0"
export API_PORT="8000"

bashio::log.info "Configuration loaded. Starting API on port ${API_PORT}..."

exec uvicorn api.main:app --host "${API_HOST}" --port "${API_PORT}"
