# =========================
# PRO APP FINAL: Route Cost Calculator (Delivery / Pickup Logic)
# =========================
# Features:
# - Modes: "Llevar" (Delivery) / "Recoger" (Pickup)
# - Only 1 input address
# - Fixed Casa + Feria locations
# - Full round trip calculation
# - Map + Autocomplete + My Location
# =========================

from flask import Flask, request, jsonify, render_template_string
import requests
import os

app = Flask(__name__)

API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

# =========================
# 🔧 CONFIGURACIÓN (EDITA ESTO)
# =========================

# Coordenadas o dirección de tu casa
CASA = "37.371069, -5.977354"

# Punto fijo de la Feria (entrada recomendada)
FERIA = "37.367850, -5.995283"

# Waypoints para evitar calles cortadas (EDITAR AQUÍ)
FERIA_WAYPOINTS = "Av. de la Palmera, Sevilla|Puente de las Delicias, Sevilla|Calle Torneo, Sevilla"

# =========================

HTML = f"""
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Route Cost Pro</title>
<style>
body {{ font-family: Arial; padding: 10px; }}
input, button, select {{ width: 100%; padding: 12px; margin: 6px 0; }}
#map {{ height: 300px; margin-top: 10px; }}
button {{ background: #007bff; color: white; border: none; }}
</style>
</head>
<body>

<h2>🚗 Route Cost Pro</h2>

<select id="mode">
  <option value="delivery">Llevar</option>
  <option value="pickup">Recoger</option>
</select>

<input id="address" placeholder="Dirección cliente">

<button onclick="useLocation()">📍 Usar mi ubicación</button>

<label>
<input type="checkbox" id="feria"> Evitar Feria
</label>

<button onclick="calcular()">Calcular</button>

<div id="result"></div>
<div id="map"></div>

<script src="https://maps.googleapis.com/maps/api/js?key={API_KEY}&libraries=places"></script>

<script>
let map, directionsService, directionsRenderer;

function initMap() {{
  map = new google.maps.Map(document.getElementById("map"), {{
    center: {{ lat: 37.3891, lng: -5.9845 }},
    zoom: 13
  }});

  directionsService = new google.maps.DirectionsService();
  directionsRenderer = new google.maps.DirectionsRenderer();
  directionsRenderer.setMap(map);

  new google.maps.places.Autocomplete(document.getElementById("address"));
}}

function useLocation() {{
  navigator.geolocation.getCurrentPosition(pos => {{
    const lat = pos.coords.latitude;
    const lng = pos.coords.longitude;
    document.getElementById("address").value = lat + "," + lng;
  }});
}}

async function calcular() {{
  const address = document.getElementById("address").value;
  const mode = document.getElementById("mode").value;
  const feria = document.getElementById("feria").checked;

  const res = await fetch('/calculate', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{ address, mode, feria }})
  }});

  const data = await res.json();

  if (data.error) {{
    document.getElementById("result").innerText = data.error;
    return;
  }}

  document.getElementById("result").innerHTML =
    `Distancia total: ${{data.km}} km <br> Coste: ${{data.cost}} €`;

  directionsRenderer.setDirections(data.directions);
}}

window.onload = initMap;
</script>

</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/calculate', methods=['POST'])
def calculate():
    data = request.json
    address = data['address']
    mode = data['mode']
    feria = data['feria']

    # Construcción de ruta según modo
    if mode == "delivery":
        origin = CASA
        destination = CASA
        waypoints = f"{address}|{FERIA}"
    else:
        origin = CASA
        destination = CASA
        waypoints = f"{FERIA}|{address}"

    if feria:
        waypoints += f"|{FERIA_WAYPOINTS}"

    params = {
        "origin": origin,
        "destination": destination,
        "waypoints": waypoints,
        "key": API_KEY
    }

    url = "https://maps.googleapis.com/maps/api/directions/json"
    response = requests.get(url, params=params).json()

    try:
        legs = response['routes'][0]['legs']
        total_m = sum(leg['distance']['value'] for leg in legs)
    
    except Exception as e:
    return jsonify({"error": str(e)})

    km = total_m / 1000
    cost = (km * 0.40) + 20

    return jsonify({
        "km": round(km, 2),
        "cost": round(cost, 2),
        "directions": response['routes'][0]
    })
