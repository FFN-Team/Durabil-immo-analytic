from flask import Flask, jsonify, render_template
from flask_cors import CORS
import pandas as pd


app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"])


# Chargement du dataset
CSV_FILE = "data/extracted_data_transformed.csv"
df = pd.read_csv(CSV_FILE, delimiter=';', encoding="utf-8")
# Remarque : entete du CSV : 
# list_id;url;price;body;subject;first_publication_date;index_date;status;nb_images;country_id;region_id;region_name;department_id;city;zipcode;lat;lng;type;name;siren;has_phone;is_boosted;favorites;square;land_plot_surface;rooms;bedrooms;nb_bathrooms;nb_shower_room;energy_rate;ges;heating_type;heating_mode;elevator;fees_at_the_expanse_of;fai_included;mandate_type;price_per_square_meter;immo_sell_type;is_import;nb_floors;nb_parkings;building_year;virtual_tour;old_price;annual_charges;orientation;is_virtual_tour

@app.route('/api/france-polygon', methods=['GET'])
def get_france_polygon():
    try:
        df = pd.read_json("resource/france-cities-data.json")

        citiesPolygon = []
        
        for city in df["data"]:
            zipCode = city.get("code_postal")
            name = city.get("nom_standard")
            polygon = city.get("polygone")

            # Vérification : Si le polygone est une liste
            if isinstance(polygon, list):
                # Vérification que chaque élément du polygone est une paire [latitude, longitude]
                valid_polygon = True
                for coord in polygon:
                    if not (isinstance(coord, list) and len(coord) == 2 and
                            isinstance(coord[0], (int, float)) and isinstance(coord[1], (int, float))):
                        valid_polygon = False
                        break
                
                if valid_polygon:
                    # Inverser la latitude et la longitude dans chaque paire
                    inverted_polygon = [[coord[1], coord[0]] for coord in polygon]  # Inverse la paire [latitude, longitude] en [longitude, latitude]
                    
                    citiesPolygon.append({
                        "zipCode": zipCode,
                        "name": name,
                        "polygon": inverted_polygon
                    })

        return jsonify(citiesPolygon)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/<zipcode>/mean-price', methods=['GET'])
def get_avg_price(zipcode):
    try:
        # Charger les données du fichier JSON
        df = pd.read_json("resource/annonces.json")

        # Récupérer toutes les annonces pour le code postal donné
        annonces = []
        for annonce in df["annonces"]:
            if annonce.get("zipcode") == zipcode:
                price = annonce.get("Price")
                area = annonce.get("square")

                if price and area:  # Ajouter uniquement si le prix et la surface sont présents
                    annonces.append({
                        "price": price,
                        "area": area
                    })

        # Si aucune annonce n'est trouvée pour ce code postal
        if not annonces:
            return jsonify({"error": "Aucune annonce trouvée pour ce code postal"}), 404

        # Calculer le prix moyen au mètre carré
        total_price = 0
        total_area = 0
        
        for annonce in annonces:
            total_price += annonce["price"]  # Accéder avec la bonne clé
            total_area += annonce["area"]  # Accéder avec la bonne clé
        
        # Eviter la division par zéro
        if total_area == 0:
            return jsonify({"error": "Surface totale est nulle"}), 400
        
        avg_price = total_price / total_area

        # Retourner le prix moyen sous forme de JSON
        return jsonify({
            "zipcode": zipcode,
            "avg_price_per_m2": round(avg_price, 2)  # Arrondi à 2 décimales
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/annonces', methods=['GET'])
def get_annonces():
    try:
        df = pd.read_json("resource/annonces.json")

        annonces = []
        for annonce in df["annonces"]:
            ID = annonce.get("ID")
            zipCode = annonce.get("zipcode")
            latitude = annonce.get("lat")
            longitude = annonce.get("lng")
            price = annonce.get("Price")

            annonces.append({
                "id": ID,
                "zipCode": zipCode,
                "latitude": latitude,
                "longitude": longitude,
                "price": price
            })

        return jsonify(annonces)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/price', methods=['GET'])
def get_price():
    try:
        df = pd.read_json("resource/exemple_annonces.json")

        annonces = []
        for annonce in df['annonce']:
            city = annonce.get("location").get("city")
            latitude = annonce.get("location").get("lat")
            longitude = annonce.get("location").get("lng")
            price = annonce.get("price")

            annonces.append({
                "city": city,
                "latitude": latitude,
                "longitude": longitude,
                "price": price
            })

        return jsonify(annonces)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500




@app.route('/')
def index():
    return render_template("index.html")



@app.route('/annonces-par-sell-type')
def get_data():
    data = df["immo_sell_type"].value_counts().sort_index().to_dict()
    return jsonify(data)

@app.route('/annonces-par-ville')
def annonces_par_ville():
    data = df["city"].value_counts().sort_values(ascending=False).to_dict()
    print(data)
    return jsonify(data)

@app.route('/annonces-pro-vs-particulier')
def annonces_pro_vs_particulier():
    data = df["type"].value_counts().sort_index().to_dict()
    return jsonify(data)

@app.route('/annonces-par-agence')
def annonces_par_agence():
    data = df["name"].value_counts().head(20).to_dict()
    return jsonify(data)


# Analyse des biens disponibles
# - année de construction par ville
@app.route('/annee-construction-par-ville')
def annee_construction_par_ville():
    filtered_df = df[['city', 'building_year']].dropna()
    filtered_df = filtered_df[filtered_df['building_year'] > 1800]  # Suppression des valeurs incorrectes
    data = filtered_df.groupby("city")["building_year"].apply(list).to_dict()
    return jsonify(data)



########################## MAIN ###################### 

if __name__ == '__main__':
    app.run(debug=True, port=5000)
