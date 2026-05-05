import streamlit as st
import requests
import pandas as pd
from io import BytesIO
from urllib.parse import quote
from datetime import datetime, timedelta, date

# =========================
# CONFIG E TOKENS SECRETS
# =========================
BASE_V1 = "http://apiadvisor.climatempo.com.br/api/v1"
API_MANAGER = "http://apiadvisor.climatempo.com.br/api-manager"
GEOCODE_URL = "https://nominatim.openstreetmap.org/search"

# Puxando as chaves DIRETAMENTE do cofre do Streamlit
TOKEN_PREVISAO = st.secrets["TOKEN_PREVISAO"]
TOKEN_HIST = st.secrets["TOKEN_HISTORICO"]

MAX_DIAS = 60

# =========================
# LISTA FIXA DO SMAC (89 cidades + UF)
# =========================
SMAC_CITY_STATE = {
    "Alumínio": "SP", "Andrelândia": "MG", "Arantina": "MG", "Barbacena": "MG",
    "Barra do Piraí": "RJ", "Barra Mansa": "RJ", "Belo Horizonte": "MG", "Belo Vale": "MG",
    "Bom Jardim de Minas": "MG", "Brotas": "SP", "Brumadinho": "MG", "Caçapava": "SP",
    "Cachoeira Paulista": "SP", "Campinas": "SP", "Carandaí": "MG", "Comendador Levy Gasparian": "RJ",
    "Congonhas": "MG", "Conselheiro Lafaiete": "MG", "Coronel Xavier Chaves": "MG", "Cruzeiro": "SP",
    "Cubatão": "SP", "Dois Córregos": "SP", "Embu das Artes": "SP", "Engenheiro Paulo de Frontin": "RJ",
    "Entre Rios de Minas": "MG", "Francisco Morato": "SP", "Franco da Rocha": "SP", "Guararema": "SP",
    "Guaratinguetá": "SP", "Ibirité": "MG", "Iracemápolis": "SP", "Itabirito": "MG",
    "Itaguaí": "RJ", "Itaquaquecetuba": "SP", "Itatiaia": "RJ", "Itirapina": "SP",
    "Itu": "SP", "Jacareí": "SP", "Japeri": "RJ", "Jaú": "SP", "Jeceaba": "MG",
    "Juiz de Fora": "MG", "Jundiaí": "SP", "Lavrinhas": "SP", "Limeira": "SP",
    "Lorena": "SP", "Madre de Deus de Minas": "MG", "Mairinque": "SP", "Mangaratiba": "RJ",
    "Matias Barbosa": "MG", "Mauá": "SP", "Mendes": "RJ", "Mesquita": "RJ",
    "Moeda": "MG", "Mogi das Cruzes": "SP", "Nova Lima": "MG", "Ouro Preto": "MG",
    "Paracambi": "RJ", "Paraíba do Sul": "RJ", "Passa Vinte": "MG", "Pederneiras": "SP",
    "Pindamonhangaba": "SP", "Pinheiral": "RJ", "Porto Real": "RJ", "Praia Grande": "SP",
    "Quatis": "RJ", "Queimados": "RJ", "Queluz": "SP", "Resende": "RJ",
    "Resende Costa": "MG", "Ribeirão Pires": "SP", "Rio Claro": "SP", "Rio de Janeiro": "RJ",
    "Santo André": "SP", "Santos": "SP", "Santos Dumont": "MG", "São Brás do Suaçuí": "MG",
    "São Caetano do Sul": "SP", "São João del Rei": "MG", "São Joaquim de Bicas": "MG",
    "São José dos Campos": "SP", "São Paulo": "SP", "Sarzedo": "MG", "Seropédica": "RJ",
    "Taubaté": "SP", "Três Rios": "RJ", "Várzea Paulista": "SP", "Vassouras": "RJ",
    "Volta Redonda": "RJ",
}
SMAC_CITIES = sorted(SMAC_CITY_STATE.keys())

# =========================
# COORDENADAS FIXAS DO SMAC (Extraídas do CSV)
# =========================
SMAC_COORDS = {
    ("Alumínio", "SP"): (-23.54, -47.26),
    ("Andrelândia", "MG"): (-21.74, -44.31),
    ("Arantina", "MG"): (-21.91, -44.26),
    ("Barbacena", "MG"): (-21.23, -43.70),
    ("Barra do Piraí", "RJ"): (-22.47, -43.83),
    ("Barra Mansa", "RJ"): (-22.54, -44.17),
    ("Belo Horizonte", "MG"): (-19.98, -43.959),
    ("Belo Vale", "MG"): (-20.41, -44.02),
    ("Bom Jardim de Minas", "MG"): (-21.95, -44.19),
    ("Brotas", "SP"): (-22.28, -48.13),
    ("Brumadinho", "MG"): (-20.14, -44.2),
    ("Caçapava", "SP"): (-23.1, -45.71),
    ("Cachoeira Paulista", "SP"): (-22.67, -45.01),
    ("Campinas", "SP"): (-22.91, -47.06),
    ("Carandaí", "MG"): (-20.95, -43.81),
    ("Comendador Levy Gasparian", "RJ"): (-22.03, -43.21),
    ("Congonhas", "MG"): (-20.5, -43.86),
    ("Conselheiro Lafaiete", "MG"): (-20.66, -43.79),
    ("Coronel Xavier Chaves", "MG"): (-21.02, -44.22),
    ("Cruzeiro", "SP"): (-22.58, -44.96),
    ("Cubatão", "SP"): (-23.9, -46.43),
    ("Dois Córregos", "SP"): (-22.37, -48.38),
    ("Embu das Artes", "SP"): (-23.65, -46.85),
    ("Engenheiro Paulo de Frontin", "RJ"): (-22.55, -43.68),
    ("Entre Rios de Minas", "MG"): (-20.67, -44.07),
    ("Francisco Morato", "SP"): (-23.28, -46.75),
    ("Franco da Rocha", "SP"): (-23.32, -46.73),
    ("Guararema", "SP"): (-23.42, -46.04),
    ("Guaratinguetá", "SP"): (-22.82, -45.19),
    ("Ibirité", "MG"): (-20.02, -44.06),
    ("Iracemápolis", "SP"): (-22.58, -47.52),
    ("Itabirito", "MG"): (-20.25, -43.8),
    ("Itaguaí", "RJ"): (-22.85, -43.78),
    ("Itaquaquecetuba", "SP"): (-23.49, -46.35),
    ("Itatiaia", "RJ"): (-22.5, -44.56),
    ("Itirapina", "SP"): (-22.25, -47.82),
    ("Itu", "SP"): (-23.26, -47.3),
    ("Jacareí", "SP"): (-23.31, -45.97),
    ("Japeri", "RJ"): (-22.64, -43.65),
    ("Jaú", "SP"): (-22.3, -48.56),
    ("Jeceaba", "MG"): (-20.54, -43.98),
    ("Juiz de Fora", "MG"): (-21.76, -43.35),
    ("Jundiaí", "SP"): (-23.19, -46.88),
    ("Lavrinhas", "SP"): (-22.57, -44.9),
    ("Limeira", "SP"): (-22.57, -47.4),
    ("Lorena", "SP"): (-22.73, -45.13),
    ("Madre de Deus de Minas", "MG"): (-21.48, -44.33),
    ("Mairinque", "SP"): (-23.55, -47.18),
    ("Mangaratiba", "RJ"): (-22.95, -44.04),
    ("Matias Barbosa", "MG"): (-21.87, -43.32),
    ("Mauá", "SP"): (-23.67, -46.46),
    ("Mendes", "RJ"): (-22.53, -43.73),
    ("Mesquita", "RJ"): (-22.78, -43.43),
    ("Moeda", "MG"): (-20.33, -44.05),
    ("Mogi das Cruzes", "SP"): (-23.52, -46.19),
    ("Nova Lima", "MG"): (-19.99, -43.85),
    ("Ouro Preto", "MG"): (-20.29, -43.51),
    ("Paracambi", "RJ"): (-22.61, -43.71),
    ("Paraíba do Sul", "RJ"): (-22.16, -43.29),
    ("Passa Vinte", "MG"): (-22.21, -44.23),
    ("Pederneiras", "SP"): (-22.35, -48.78),
    ("Pindamonhangaba", "SP"): (-22.92, -45.46),
    ("Pinheiral", "RJ"): (-22.51, -44.0),
    ("Porto Real", "RJ"): (-22.42, -44.29),
    ("Praia Grande", "SP"): (-24.01, -46.4),
    ("Quatis", "RJ"): (-22.41, -44.26),
    ("Queimados", "RJ"): (-22.72, -43.56),
    ("Queluz", "SP"): (-22.54, -44.77),
    ("Resende", "RJ"): (-22.47, -44.45),
    ("Resende Costa", "MG"): (-20.92, -44.24),
    ("Ribeirão Pires", "SP"): (-23.71, -46.41),
    ("Rio Claro", "SP"): (-22.41, -47.56),
    ("Rio de Janeiro", "RJ"): (-22.861, -43.411),
    ("Santo André", "SP"): (-23.66, -46.54),
    ("Santos", "SP"): (-23.9, -46.33),
    ("Santos Dumont", "MG"): (-21.46, -43.55),
    ("São Brás do Suaçuí", "MG"): (-20.63, -43.95),
    ("São Caetano do Sul", "SP"): (-23.62, -46.55),
    ("São João del Rei", "MG"): (-21.14, -44.26),
    ("São Joaquim de Bicas", "MG"): (-20.05, -44.27),
    ("São José dos Campos", "SP"): (-23.18, -45.89),
    ("São Paulo", "SP"): (-23.496, -46.62),
    ("Sarzedo", "MG"): (-20.04, -44.15),
    ("Seropédica", "RJ"): (-22.74, -43.71),
    ("Taubaté", "SP"): (-23.03, -45.56),
    ("Três Rios", "RJ"): (-22.12, -43.21),
    ("Várzea Paulista", "SP"): (-23.21, -46.83),
    ("Vassouras", "RJ"): (-22.4, -43.66),
    ("Volta Redonda", "RJ"): (-22.52, -44.1),
}

# =========================
# UI
# =========================
st.set_page_config(page_title="SMAC • Previsão & Histórico", layout="wide")
st.title("🌦️ SMAC • Previsão (até 60 dias) & Histórico (Hourly + Diário)")

with st.sidebar:
    st.header("⚙️ Configurações")
    DEBUG = st.checkbox("Modo debug", value=False)
    st.divider()
    st.caption("✅ Coordenadas autorizadas já estão embutidas no sistema.")

# =========================
# HTTP helpers
# =========================
def http_get(url: str, timeout: int = 30):
    try:
        r = requests.get(url, timeout=timeout)
        if r.status_code >= 400:
            return False, None, r.status_code, r.text
        return True, r.json() if r.text else {}, r.status_code, ""
    except Exception as e:
        return False, None, -1, str(e)

def http_put_form(url: str, data: dict, timeout: int = 30):
    try:
        r = requests.put(url, data=data, timeout=timeout)
        if r.status_code >= 400:
            return False, None, r.status_code, r.text
        return True, r.json() if r.text else {}, r.status_code, ""
    except Exception as e:
        return False, None, -1, str(e)

# =========================
# Geocoding fallback
# =========================
@st.cache_data(ttl=86400, show_spinner=False)
def geocode_city(city: str, uf: str):
    params = {"q": f"{city}, {uf}, Brazil", "format": "json", "limit": 1}
    headers = {"User-Agent": "smac-streamlit"}
    r = requests.get(GEOCODE_URL, params=params, headers=headers, timeout=20)
    r.raise_for_status()
    data = r.json()
    if not data:
        raise ValueError(f"Geocoding não retornou coordenadas para {city}-{uf}")
    return float(data[0]["lat"]), float(data[0]["lon"])

# =========================
# Locale lookup (cidade+UF -> locale_id)
# =========================
@st.cache_data(ttl=86400, show_spinner=False)
def resolve_locale_id(city: str, uf: str, token_previsao: str):
    url = f"{BASE_V1}/locale/city?name={quote(city)}&state={uf}&token={token_previsao}"
    ok, payload, status, err = http_get(url)
    if not ok:
        raise RuntimeError(f"Erro ao resolver locale_id ({city}-{uf}). HTTP {status}: {err}")
    if not payload:
        raise RuntimeError(f"Nenhum locale encontrado para {city}-{uf}")
    return int(payload[0]["id"])

def registrar_locale_no_token(locale_id: int, token_previsao: str):
    url = f"{API_MANAGER}/user-token/{token_previsao}/locales"
    data = {"localeId[]": str(locale_id)}
    return http_put_form(url, data=data)

# =========================
# Forecast (até 60 dias)
# =========================
def fetch_forecast(locale_id: int, dias: int, token_previsao: str):
    dias = max(1, min(MAX_DIAS, int(dias)))

    url270 = f"{BASE_V1}/forecast/locale/{locale_id}/days/270?token={token_previsao}"
    ok, payload, status, err = http_get(url270)
    if ok and isinstance(payload, dict) and "data" in payload:
        return True, payload["data"][:dias], status, "", 270

    url15 = f"{BASE_V1}/forecast/locale/{locale_id}/days/15?token={token_previsao}"
    ok2, payload2, status2, err2 = http_get(url15)
    if ok2 and isinstance(payload2, dict) and "data" in payload2:
        return True, payload2["data"][:min(dias, 15)], status2, "", 15

    return False, None, (status2 if not ok else status), (err2 if not ok2 else err), None

def forecast_to_df(days_list: list, label: str, locale_id: int):
    rows = []
    for d in days_list:
        rain = d.get("rain", {}) or {}
        temp = d.get("temperature", {}) or {}
        hum = d.get("humidity", {}) or {}
        wind = d.get("wind", {}) or {}
        uv = d.get("uv", {}) or {}
        rows.append({
            "Ponto": label,
            "locale_id": locale_id,
            "Data": d.get("date_br") or d.get("date"),
            "Temp Min (°C)": temp.get("min"),
            "Temp Max (°C)": temp.get("max"),
            "Chuva (mm)": rain.get("precipitation"),
            "Prob Chuva (%)": rain.get("probability"),
            "Umidade Min (%)": hum.get("min"),
            "Umidade Max (%)": hum.get("max"),
            "Vento Médio (km/h)": wind.get("velocity_avg") or wind.get("speed"),
            "Rajada (km/h)": wind.get("gust_max") or wind.get("gust"),
            "UV Máx": uv.get("max"),
        })
    return pd.DataFrame(rows)

# =========================
# Histórico GEO/hourly
# =========================
def history_geo_hourly(lat: float, lon: float, from_dt: date, token_hist: str):
    from_str = from_dt.strftime("%Y-%m-%d")
    url = f"{BASE_V1}/history/geo/hourly?token={token_hist}&from={from_str}&latitude={lat}&longitude={lon}"
    return http_get(url)

def normalize_history_payload(payload):
    if payload is None:
        return pd.DataFrame()
    if isinstance(payload, dict) and isinstance(payload.get("data"), list):
        return pd.json_normalize(payload["data"])
    if isinstance(payload, list):
        return pd.json_normalize(payload)
    return pd.json_normalize(payload)

def pick_first_col(df: pd.DataFrame, candidates: list):
    for c in candidates:
        if c in df.columns:
            return c
    return None

def build_daily_summary(df_hourly: pd.DataFrame):
    if df_hourly.empty:
        return df_hourly
    time_col = pick_first_col(df_hourly, ["date", "datetime", "time", "timestamp"])
    if time_col is None:
        return pd.DataFrame({"warning": ["Sem coluna de tempo detectável para agregação diária."]})

    dt = pd.to_datetime(df_hourly[time_col], errors="coerce")
    df_hourly = df_hourly.assign(_day=dt.dt.date)

    rain_col = pick_first_col(df_hourly, ["rain.precipitation", "precipitation", "rain", "mm"])
    t_col = pick_first_col(df_hourly, ["temperature", "temp", "temperature.value", "temperatureC"])
    h_col = pick_first_col(df_hourly, ["humidity", "humidity.value", "rh"])
    agg = {}
    if rain_col: agg[rain_col] = "sum"
    if t_col: agg[t_col] = ["min", "max"]
    if h_col: agg[h_col] = "mean"

    g = df_hourly.groupby("_day").agg(agg)
    g.columns = ["_".join([str(x) for x in col if x]) if isinstance(col, tuple) else str(col) for col in g.columns]
    g = g.reset_index().rename(columns={"_day": "dia"})
    g["dia"] = g["dia"].astype(str)
    return g

# =========================
# XLSX
# =========================
def to_xlsx(sheets: dict):
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, index=False, sheet_name=name[:31])
    return buf.getvalue()

# =========================
# UI: Seleção das cidades SMAC
# =========================
st.subheader("📍 Cidades SMAC (pré-carregadas)")
selected_cities = st.multiselect(
    "Selecione uma ou mais cidades",
    options=SMAC_CITIES,
    default=["Barbacena"] if "Barbacena" in SMAC_CITIES else []
)
if not selected_cities:
    st.stop()

tab_prev, tab_hist = st.tabs(["🔮 Previsão (até 60 dias)", "🕒 Histórico (Hourly + Diário)"])

# =========================
# PREVISÃO
# =========================
with tab_prev:
    dias_prev = st.slider("Dias de previsão", 1, MAX_DIAS, 15)
    if st.button("Gerar Previsão (XLSX)", use_container_width=True):
        all_df = []
        for city in selected_cities:
            uf = SMAC_CITY_STATE[city]
            label = f"{city}-{uf}"
            try:
                locale_id = resolve_locale_id(city, uf, TOKEN_PREVISAO)
                registrar_locale_no_token(locale_id, TOKEN_PREVISAO)
                ok, days, status, err, used = fetch_forecast(locale_id, dias_prev, TOKEN_PREVISAO)
                if not ok:
                    st.error(f"{label}: previsão falhou (HTTP {status})")
                    if DEBUG: st.code(err)
                    continue
                df = forecast_to_df(days, label, locale_id)
                df["endpoint_days_used"] = used
                all_df.append(df)
            except Exception as e:
                st.error(f"{label}: {e}")
                if DEBUG: st.code(str(e))

        if all_df:
            out = pd.concat(all_df, ignore_index=True)
            st.dataframe(out, use_container_width=True)
            st.download_button(
                "⬇️ Download Previsão (XLSX)",
                data=to_xlsx({"Previsao": out}),
                file_name=f"previsao_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

# =========================
# HISTÓRICO
# =========================
with tab_hist:
    dias_hist = st.slider("Dias de histórico", 1, MAX_DIAS, 7)
    data_inicio = st.date_input("Data inicial", value=date.today() - timedelta(days=dias_hist))

    if st.button("Gerar Histórico (Hourly + Diário) (XLSX)", use_container_width=True):
        hourly_all = []
        daily_all = []

        for city in selected_cities:
            uf = SMAC_CITY_STATE[city]
            label = f"{city}-{uf}"

            # 1) Tenta coordenadas do mapa fixo (inserido direto no código)
            key = (city, uf)
            latlon = SMAC_COORDS.get(key)

            # 2) Fallback: geocoding (caso falhe por algum motivo ou se adicionar cidades novas)
            coords_source = "mapa_smac_embutido"
            if latlon is None:
                coords_source = "geocoding_fallback"
                try:
                    latlon = geocode_city(city, uf)
                except Exception as e:
                    st.error(f"{label}: falha ao obter coordenadas automaticamente ({coords_source})")
                    if DEBUG: st.code(str(e))
                    continue

            lat, lon = latlon

            dfs_point = []
            for i in range(dias_hist):
                d = data_inicio + timedelta(days=i)
                ok, payload, status, err = history_geo_hourly(lat, lon, d, TOKEN_HIST)
                if not ok:
                    st.warning(f"{label} em {d}: HTTP {status}")
                    if DEBUG: st.code(err)
                    if "Latitude and Longitude not allowed" in (err or ""):
                        st.error(f"{label}: coordenadas recusadas (whitelist). Fonte={coords_source}, lat/lon=({lat},{lon})")
                        break
                    continue

                dfh = normalize_history_payload(payload)
                dfh.insert(0, "Ponto", label)
                dfh.insert(1, "from_date", d.strftime("%Y-%m-%d"))
                dfh.insert(2, "lat", lat)
                dfh.insert(3, "lon", lon)
                dfh.insert(4, "coords_source", coords_source)
                dfs_point.append(dfh)

            if dfs_point:
                df_hourly = pd.concat(dfs_point, ignore_index=True)
                hourly_all.append(df_hourly)
                df_daily = build_daily_summary(df_hourly.copy())
                df_daily.insert(0, "Ponto", label)
                daily_all.append(df_daily)

        if hourly_all:
            out_hourly = pd.concat(hourly_all, ignore_index=True)
            out_daily = pd.concat(daily_all, ignore_index=True) if daily_all else pd.DataFrame()

            st.subheader("📊 Visualização na tela (completa)")
            modo = st.radio("Visualizar:", ["Resumo Diário", "Histórico Horário (Raw)"], horizontal=True)
            df_view = out_daily.copy() if modo == "Resumo Diário" else out_hourly.copy()

            with st.expander("Selecionar colunas para visualizar", expanded=False):
                cols = df_view.columns.tolist()
                selected_cols = st.multiselect("Colunas", cols, default=cols)

            st.dataframe(df_view[selected_cols], use_container_width=True, height=520)

            xlsx = to_xlsx({
                "Historico_Horario": out_hourly,
                "Resumo_Diario": out_daily if not out_daily.empty else pd.DataFrame({"info": ["Resumo diário indisponível."]})
            })

            st.download_button(
                "⬇️ Download Histórico (XLSX)",
                data=xlsx,
                file_name=f"historico_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        else:
            st.warning("Nenhum histórico foi gerado. Veja as mensagens acima.")
