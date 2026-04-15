from flask import Flask, request, jsonify, render_template_string
import requests
import os

app = Flask(__name__)

API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "TU_API_KEY_AQUI")

# =========================
# 🔧 CONFIGURACIÓN
# =========================
CASA = "37.371069,-5.977354"
# Dos puntos de feria
FERIA_1 = "37.367850,-5.995283" # Portada
FERIA_2 = "37.371642,-5.996819" # Nueva ubicación
# Puntos para forzar el rodeo de Juan Pablo II (vía alternativa)
EVITAR_JUAN_PABLO_II = "37.3635,-5.9915|37.3588,-5.9928" 

HTML = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Calculador de Costes Pro</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {{ background-color: #f8fafc; color: #1e293b; font-family: system-ui, -apple-system, sans-serif; }}
        .card {{ background: white; border-radius: 24px; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.1); border: 1px solid #e2e8f0; }}
        .price-card {{ background: linear-gradient(135deg, #059669 0%, #10b981 100%); color: white; }}
        #map {{ height: 180px; border-radius: 16px; margin-top: 15px; border: 1px solid #cbd5e1; }}
        select, input {{ transition: all 0.2s; }}
        select:focus, input:focus {{ border-color: #3b82f6; box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2); }}
    </style>
</head>
<body class="p-4 max-w-lg mx-auto">

    <div class="card p-6 space-y-5">
        <header class="text-center">
            <h1 class="text-2xl font-black text-slate-800 tracking-tight">ROUTE COST <span class="text-blue-600">PRO</span></h1>
            <p class="text-slate-500 text-sm">Calculador logístico optimizado</p>
        </header>
        
        <div class="grid grid-cols-2 gap-3">
            <div class="col-span-2 space-y-1">
                <label class="text-xs font-bold text-slate-400 uppercase ml-1">Servicio</label>
                <select id="mode" class="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl outline-none text-sm">
                    <option value="delivery text-xs">🚚 LLEVAR (Casa -> Cliente)</option>
                    <option value="pickup text-xs">📦 RECOGER (Feria -> Cliente)</option>
                </select>
            </div>

            <div class="col-span-2 space-y-1">
                <label class="text-xs font-bold text-slate-400 uppercase ml-1">Punto de Feria</label>
                <select id="feria_point" class="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl outline-none text-sm">
                    <option value="1">📍 Portada (Principal)</option>
                    <option value="2">📍 Punto Alternativo (37.371, -5.996)</option>
                </select>
            </div>
        </div>

        <div class="space-y-1">
            <label class="text-xs font-bold text-slate-400 uppercase ml-1">Destino Cliente</label>
            <input id="address" type="text" placeholder="Ej: Calle Sierpes, Sevilla" class="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl outline-none text-sm">
            <button onclick="useLocation()" class="text-xs text-blue-600 font-semibold px-1 pt-1">📍 Usar mi ubicación</button>
        </div>

        <div class="flex items-center space-x-3 p-3 bg-red-50 rounded-xl border border-red-100">
            <input type="checkbox" id="evitar" checked class="w-5 h-5 accent-red-600">
            <label for="evitar" class="text-xs text-red-700 font-bold uppercase">Evitar Av. Juan Pablo II / Cortes</label>
        </div>

        <button onclick="calcular()" class="w-full bg-slate-900 hover:bg-black text-white font-bold py-4 rounded-2xl transition shadow-xl active:scale-[0.98]">
            CALCULAR AHORA
        </button>

        <div id="result-container" class="hidden animate-in fade-in zoom-in duration-300">
            <div class="price-card rounded-2xl p-5 text-center shadow-lg shadow-emerald-200">
                <span class="text-xs font-bold uppercase opacity-80 tracking-widest">Presupuesto Estimado</span>
                <div id="cost-display" class="text-5xl font-black my-1">0.00€</div>
                <div id="km-display" class="text-xs opacity-90 font-medium">0 km totales</div>
            </div>
        </div>

        <div id="map"></div>
    </div>

    <script src="https://maps.googleapis.com/maps/api/js?key={API_KEY}&libraries=places"></script>
    <script>
        let map, directionsRenderer, directionsService;

        function initMap() {{
            map = new google.maps.Map(document.getElementById("map"), {{
                center: {{ lat: 37.37, lng: -5.98 }}, zoom: 13,
                disableDefaultUI: true,
                styles: [{{ "featureType": "poi", "elementType": "labels", "stylers": [{{ "visibility": "off" }}] }}]
            }});
            directionsService = new google.maps.DirectionsService();
            directionsRenderer = new google.maps.DirectionsRenderer({{ map: map }});
            new google.maps.places.Autocomplete(document.getElementById("address"));
        }}

        async function calcular() {{
            const address = document.getElementById("address").value;
            if(!address) return;

            const res = await fetch('/calculate', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{ 
                    address, 
                    mode: document.getElementById("mode").value,
                    feria_point: document.getElementById("feria_point").value,
                    evitar: document.getElementById("evitar").checked 
                }})
            }});

            const data = await res.json();
            if (data.error) return alert(data.error);

            document.getElementById("cost-display").innerText = data.cost.toFixed(2) + "€";
            document.getElementById("km-display").innerText = data.km + " KM de recorrido total";
            document.getElementById("result-container").classList.remove("hidden");

            // Dibujar en mapa
            directionsService.route({{
                origin: data.origin,
                destination: data.destination,
                waypoints: data.waypoints_list,
                travelMode: 'DRIVING'
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
    evitar = data['evitar']
    f_point = data['feria_point']

    punto_feria_elegido = FERIA_1 if f_point == "1" else FERIA_2

    # Construcción de la ruta lógica
    # Usamos el prefijo 'via:' para que Google pase por ahí pero no lo cuente como parada de carga/descarga
    waypoints_raw = []

    if evitar:
        # Añadimos puntos de control para obligar a rodear Juan Pablo II
        for wp in EVITAR_JUAN_PABLO_II.split('|'):
            waypoints_raw.append(f"via:{wp}")

    if mode == "delivery":
        # Casa -> Cliente -> Feria -> Casa
        waypoints_raw.insert(0, address)
        waypoints_raw.append(punto_feria_elegido)
    else:
        # Casa -> Feria -> Cliente -> Casa
        waypoints_raw.insert(0, punto_feria_elegido)
        waypoints_raw.append(address)

    params = {
        "origin": CASA,
        "destination": CASA,
        "waypoints": "|".join(waypoints_raw),
        "key": API_KEY
    }

    response = requests.get("https://maps.googleapis.com/maps/api/directions/json", params=params).json()

    if response.get('status') != 'OK':
        return jsonify({"error": "No se pudo calcular la ruta. Revisa la dirección."})

    route = response['routes'][0]
    total_m = sum(leg['distance']['value'] for leg in route['legs'])
    km = total_m / 1000
    cost = (km * 0.40) + 20

    # Preparar waypoints para el mapa JS
    js_waypoints = [{"location": loc.replace("via:", ""), "stopover": not loc.startswith("via:")} for loc in waypoints_raw]

    return jsonify({
        "km": round(km, 2),
        "cost": round(cost, 2),
        "origin": CASA,
        "destination": CASA,
        "waypoints_list": js_waypoints
    })

if __name__ == '__main__':
    app.run(debug=True)
