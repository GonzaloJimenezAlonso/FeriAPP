from flask import Flask, request, jsonify, render_template_string
import requests
import os

app = Flask(__name__)

# Asegúrate de configurar tu API KEY
API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "TU_API_KEY_AQUI")

# =========================
# 🔧 CONFIGURACIÓN
# =========================
CASA = "37.371069,-5.977354"
FERIA = "37.367850,-5.995283"
FERIA_WAYPOINTS = "Av. de la Palmera, Sevilla|Puente de las Delicias, Sevilla"

HTML = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Calculador de Costes Pro</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {{ background-color: #f3f4f6; color: #1f2937; }}
        .card {{ background: white; border-radius: 16px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }}
        .price-badge {{ background: #ecfdf5; color: #059669; border: 2px solid #10b981; }}
        #map {{ height: 200px; border-radius: 12px; filter: grayscale(0.5); opacity: 0.7; }}
    </style>
</head>
<body class="p-4 max-w-md mx-auto">

    <div class="card p-6 space-y-4">
        <h1 class="text-2xl font-bold text-center text-blue-600 mb-4">🚗 Route Cost Pro</h1>
        
        <div class="space-y-2">
            <label class="text-sm font-semibold text-gray-600 uppercase">Modo de servicio</label>
            <select id="mode" class="w-full p-3 border rounded-lg bg-gray-50 focus:ring-2 focus:ring-blue-500 outline-none">
                <option value="delivery">Llevar (Casa -> Cliente -> Feria -> Casa)</option>
                <option value="pickup">Recoger (Casa -> Feria -> Cliente -> Casa)</option>
            </select>
        </div>

        <div class="space-y-2">
            <label class="text-sm font-semibold text-gray-600 uppercase">Dirección del Cliente</label>
            <input id="address" type="text" placeholder="Calle, ciudad..." class="w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none">
            <button onclick="useLocation()" class="text-xs text-blue-600 font-medium flex items-center hover:underline">
                📍 Usar mi ubicación actual
            </button>
        </div>

        <div class="flex items-center space-x-2 p-2 bg-amber-50 rounded-lg">
            <input type="checkbox" id="feria" class="w-5 h-5 accent-amber-500">
            <label for="feria" class="text-sm text-amber-800 font-medium">Evitar puntos conflictivos Feria</label>
        </div>

        <button onclick="calcular()" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-4 rounded-xl transition duration-200 shadow-lg">
            CALCULAR RUTA
        </button>

        <div id="loader" class="hidden text-center text-gray-500 animate-pulse">Calculando mejor ruta...</div>

        <div id="result-container" class="hidden space-y-4 pt-4 border-t">
            <div class="price-badge rounded-2xl p-6 text-center">
                <p class="text-sm uppercase font-bold tracking-widest opacity-80">Precio Final</p>
                <h2 id="cost-display" class="text-5xl font-black mt-1">0.00€</h2>
            </div>
            
            <div class="flex justify-between text-sm px-2 text-gray-500 italic">
                <span id="km-display">0 km totales</span>
                <span>Tarifa: 0.40€/km + 20€ base</span>
            </div>
        </div>

        <div id="map" class="mt-4"></div>
    </div>

    <script src="https://maps.googleapis.com/maps/api/js?key={API_KEY}&libraries=places"></script>
    <script>
        let map, directionsRenderer, directionsService;

        function initMap() {{
            map = new google.maps.Map(document.getElementById("map"), {{
                center: {{ lat: 37.3891, lng: -5.9845 }},
                zoom: 12,
                disableDefaultUI: true
            }});
            directionsService = new google.maps.DirectionsService();
            directionsRenderer = new google.maps.DirectionsRenderer({{
                map: map,
                suppressMarkers: false
            }});
            new google.maps.places.Autocomplete(document.getElementById("address"));
        }}

        function useLocation() {{
            if (navigator.geolocation) {{
                navigator.geolocation.getCurrentPosition(pos => {{
                    document.getElementById("address").value = pos.coords.latitude + "," + pos.coords.longitude;
                }});
            }}
        }}

        async function calcular() {{
            const address = document.getElementById("address").value;
            const mode = document.getElementById("mode").value;
            const feria = document.getElementById("feria").checked;
            const loader = document.getElementById("loader");
            const resultContainer = document.getElementById("result-container");

            if(!address) return alert("Escribe una dirección");

            loader.classList.remove("hidden");
            resultContainer.classList.add("hidden");

            try {{
                const res = await fetch('/calculate', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{ address, mode, feria }})
                }});

                const data = await res.json();

                if (data.error) {{
                    alert("Error: " + data.error);
                }} else {{
                    document.getElementById("cost-display").innerText = data.cost + "€";
                    document.getElementById("km-display").innerText = data.km + " km totales (ida y vuelta)";
                    resultContainer.classList.remove("hidden");
                    
                    // Dibujar ruta en el mapa
                    const request = {{
                        origin: data.origin,
                        destination: data.destination,
                        waypoints: data.waypoints_list,
                        travelMode: 'DRIVING'
                    }};
                    
                    directionsService.route(request, (result, status) => {{
                        if (status === 'OK') {{
                            directionsRenderer.setDirections(result);
                        }}
                    }});
                }}
            }} catch (e) {{
                alert("Error de conexión");
            }} finally {{
                loader.classList.add("hidden");
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
    feria = data['feria']

    # Lógica de paradas según modo
    # Modo Delivery: Casa -> Cliente -> Feria -> Casa
    # Modo Pickup: Casa -> Feria -> Cliente -> Casa
    if mode == "delivery":
        way_list = [address, FERIA]
    else:
        way_list = [FERIA, address]

    if feria:
        for wp in FERIA_WAYPOINTS.split('|'):
            way_list.append(wp)

    # Convertir lista de waypoints para la URL de Google
    waypoints_str = "|".join(way_list)

    params = {
        "origin": CASA,
        "destination": CASA,
        "waypoints": waypoints_str,
        "key": API_KEY
    }

    url = "https://maps.googleapis.com/maps/api/directions/json"
    response = requests.get(url, params=params).json()

    if response.get('status') != 'OK':
        return jsonify({"error": response.get('error_message', 'No se pudo encontrar la ruta')})

    try:
        legs = response['routes'][0]['legs']
        total_m = sum(leg['distance']['value'] for leg in legs)
        
        km = total_m / 1000
        # Tu fórmula: 20€ base + 0.40€ por km
        cost = (km * 0.40) + 20

        # Formatear waypoints para que el JS los entienda fácilmente
        js_waypoints = [{"location": loc, "stopover": True} for loc in way_list]

        return jsonify({
            "km": round(km, 2),
            "cost": round(cost, 2),
            "origin": CASA,
            "destination": CASA,
            "waypoints_list": js_waypoints
        })
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(debug=True)
