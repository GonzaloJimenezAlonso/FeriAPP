from flask import Flask, request, jsonify, render_template_string
import requests
import os

app = Flask(__name__)

# Configura tu API KEY aquí
API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "TU_API_KEY_AQUI")

# =========================
# 🔧 CONFIGURACIÓN
# =========================
CASA = "37.371069,-5.977354"
PUNTOS_FERIA = {
    "portada": "37.367850,-5.995283",
    "alternativo": "37.371642,-5.996819"
}

HTML = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Calculador de Costes</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {{ background-color: #f1f5f9; }}
        .main-card {{ background: white; border-radius: 20px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); }}
        .price-box {{ background: linear-gradient(135deg, #1e293b 0%, #334155 100%); }}
        #map {{ height: 200px; border-radius: 15px; margin-top: 15px; filter: contrast(0.8) brightness(1.1); }}
    </style>
</head>
<body class="p-4 max-w-md mx-auto">

    <div class="main-card p-6 space-y-5">
        <h1 class="text-xl font-extrabold text-center text-slate-800 tracking-tight uppercase">Calculadora de Ruta</h1>
        
        <div class="space-y-4">
            <div>
                <label class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Tipo de Servicio</label>
                <select id="mode" class="w-full mt-1 p-3 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none">
                    <option value="delivery">LLEVAR (Casa -> Cliente -> Feria -> Casa)</option>
                    <option value="pickup">RECOGER (Casa -> Feria -> Cliente -> Casa)</option>
                </select>
            </div>

            <div>
                <label class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Punto de Feria</label>
                <select id="feria_point" class="w-full mt-1 p-3 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none">
                    <option value="portada">Portada Principal</option>
                    <option value="alternativo">Punto Alternativo (C/ Infante Carlos)</option>
                </select>
            </div>

            <div>
                <label class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Ubicación Cliente</label>
                <input id="address" type="text" placeholder="Calle o coordenadas..." class="w-full mt-1 p-3 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none">
                <button onclick="useLocation()" class="text-xs text-blue-500 mt-2 font-medium">📍 Usar mi posición actual</button>
            </div>
        </div>

        <button onclick="calcular()" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-4 rounded-xl transition-all shadow-lg shadow-blue-100 uppercase tracking-wider text-sm">
            Calcular Precio Final
        </button>

        <div id="result" class="hidden space-y-3">
            <div class="price-box p-6 rounded-2xl text-center shadow-inner">
                <p class="text-blue-400 text-[10px] font-bold uppercase tracking-[0.2em]">Total a cobrar</p>
                <h2 id="cost-display" class="text-white text-5xl font-black mt-1">0.00€</h2>
            </div>
            <div class="flex justify-between items-center px-2">
                <span id="km-display" class="text-slate-500 text-sm font-medium">0.0 km</span>
                <span class="text-slate-400 text-[10px] uppercase font-bold italic">Tarifa: 0.40€/km + 20€ base</span>
            </div>
        </div>

        <div id="map"></div>
    </div>

    <script src="https://maps.googleapis.com/maps/api/js?key={API_KEY}&libraries=places"></script>
    <script>
        let map, directionsRenderer, directionsService;

        function initMap() {{
            map = new google.maps.Map(document.getElementById("map"), {{
                center: {{ lat: 37.37, lng: -5.98 }}, zoom: 12,
                disableDefaultUI: true
            }});
            directionsService = new google.maps.DirectionsService();
            directionsRenderer = new google.maps.DirectionsRenderer({{ map: map }});
            new google.maps.places.Autocomplete(document.getElementById("address"));
        }}

        async function calcular() {{
            const address = document.getElementById("address").value;
            if(!address) return alert("Introduce una dirección");

            const res = await fetch('/calculate', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{ 
                    address, 
                    mode: document.getElementById("mode").value,
                    feria_point: document.getElementById("feria_point").value
                }})
            }});

            const data = await res.json();
            if (data.error) return alert("Error: " + data.error);

            document.getElementById("cost-display").innerText = data.cost.toFixed(2) + "€";
            document.getElementById("km-display").innerText = data.km + " km totales";
            document.getElementById("result").classList.remove("hidden");

            directionsService.route({{
                origin: data.origin,
                destination: data.destination,
                waypoints: data.waypoints,
                travelMode: 'DRIVING',
                optimizeWaypoints: false
            }}, (result, status) => {{
                if (status === 'OK') directionsRenderer.setDirections(result);
            }});
        }}

        function useLocation() {{
            if (navigator.geolocation) {{
                navigator.geolocation.getCurrentPosition(pos => {{
                    document.getElementById("address").value = pos.coords.latitude + "," + pos.coords.longitude;
                }});
            }}
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
    f_point = data['feria_point']

    punto_feria = PUNTOS_FERIA[f_point]

    # Configuramos los waypoints UNICAMENTE como los puntos de parada reales
    if mode == "delivery":
        # Ruta: Casa -> Cliente -> Feria -> Casa
        way_list = [address, punto_feria]
    else:
        # Ruta: Casa -> Feria -> Cliente -> Casa
        way_list = [punto_feria, address]

    params = {
        "origin": CASA,
        "destination": CASA,
        "waypoints": "|".join(way_list),
        "key": API_KEY
    }

    response = requests.get("https://maps.googleapis.com/maps/api/directions/json", params=params).json()

    if response.get('status') != 'OK':
        return jsonify({"error": "No se pudo calcular la ruta. Comprueba la dirección."})

    route = response['routes'][0]
    # Sumar distancia de todos los tramos (Legs)
    total_m = sum(leg['distance']['value'] for leg in route['legs'])
    km = total_m / 1000
    
    # Cálculo: 20€ base + 0.40€/km
    cost = (km * 0.40) + 20

    # Formatear para el mapa JS
    js_waypoints = [{"location": loc, "stopover": True} for loc in way_list]

    return jsonify({
        "km": round(km, 2),
        "cost": round(cost, 2),
        "origin": CASA,
        "destination": CASA,
        "waypoints": js_waypoints
    })

if __name__ == '__main__':
    app.run(debug=True)
