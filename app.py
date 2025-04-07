from flask import Flask, jsonify, render_template
from flask_cors import CORS
import pandas as pd
import json
from collections import defaultdict 
from datetime import datetime


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

@app.route('/api/regions/<regionCode>/cities-polygon', methods=['GET'])
def get_region_polygon(regionCode):
    try:
        df = pd.read_json("resource/france-cities-data.json")

        citiesPolygon = []
        
        for city in df["data"]:
            if city.get("reg_code") == regionCode:
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

@app.route('/api/annonces/avg-price', methods=['GET'])
def avg_price_par_ville():
    try:
        # Charger les données des annonces depuis le fichier JSON
        df = pd.read_json("resource/annonces.json")
        
        # Créer un dictionnaire pour stocker la somme des prix et le nombre d'annonces par ville (ou par code postal)
        prix_total = defaultdict(float)
        nombre_annonces = defaultdict(int)
        
        # Parcourir chaque annonce et incrémenter le compteur et la somme des prix pour chaque code postal
        for annonce in df['annonces']:
            zip_code = annonce.get('zipcode')  # Récupérer le code postal de l'annonce
            prix = annonce.get('Price')  # Récupérer le prix de l'annonce
            if zip_code and prix is not None:  # Vérifier que le code postal et le prix existent
                # Convertir le code postal en string (chaîne de caractères)
                zip_code_str = str(zip_code)
                prix_total[zip_code_str] += prix  # Ajouter le prix à la somme pour la ville
                nombre_annonces[zip_code_str] += 1  # Incrémenter le compteur d'annonces
        
        # Calculer le prix moyen par ville
        villes = []
        for zip_code in prix_total:
            if nombre_annonces[zip_code] > 0:
                avg_price = prix_total[zip_code] / nombre_annonces[zip_code]  # Calcul du prix moyen
                villes.append({"zipCode": zip_code, "avgPrice": round(avg_price, 2)})
        
        # Retourner le résultat sous forme de JSON
        return jsonify({"villes": villes})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# @app.route('/api/annonces/avg-price-per-m2', methods=['GET'])
# def avg_price_per_m2_par_ville():
#     try:
#         # Charger les données des annonces depuis le fichier JSON
#         df = pd.read_json("resource/annonces.json")
        
#         # Créer un dictionnaire pour stocker la somme des prix par m² et la somme des surfaces pour chaque ville
#         prix_par_m2_total = defaultdict(float)
#         surface_total = defaultdict(float)
        
#         # Parcourir chaque annonce et incrémenter les sommes pour chaque code postal
#         for annonce in df['annonces']:
#             zip_code = annonce.get('zipcode')  # Récupérer le code postal de l'annonce
#             prix = annonce.get('Price')  # Récupérer le prix de l'annonce
#             surface = annonce.get('square')  # Récupérer la surface de l'annonce en m²
            
#             # Vérifier que le code postal, le prix et la surface existent
#             if zip_code and prix is not None and surface is not None:
#                 try:
#                     # Convertir explicitement en float les valeurs de prix et surface si elles ne sont pas vides ou invalides
#                     prix = float(prix) if prix not in [None, ''] else 0
#                     surface = float(surface) if surface not in [None, ''] else 0
                    
#                     if prix > 0 and surface > 0:  # Ignorer les annonces avec un prix ou une surface de 0
#                         # Convertir le code postal en string (chaîne de caractères)
#                         zip_code_str = str(zip_code)
                        
#                         # Calculer le prix par m² pour cette annonce
#                         prix_par_m2 = prix / surface
                        
#                         # Ajouter le prix par m² à la somme pour cette ville
#                         prix_par_m2_total[zip_code_str] += prix_par_m2
#                         surface_total[zip_code_str] += surface  # Ajouter la surface à la somme des surfaces
#                 except ValueError:
#                     # Si la conversion échoue, ignorer cette annonce
#                     continue
        
#         # Calculer le prix moyen par m² par ville
#         villes = []
#         for zip_code in prix_par_m2_total:
#             if surface_total[zip_code] > 0:
#                 avg_price_per_m2 = prix_par_m2_total[zip_code] / surface_total[zip_code]  # Calcul du prix moyen par m²
#                 villes.append({"zipCode": zip_code, "avgPricePerM2": round(avg_price_per_m2, 2)})
        
#         # Retourner le résultat sous forme de JSON
#         return jsonify({"villes": villes})
    
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

@app.route('/api/annonces/avg-price-per-m2', methods=['GET'])
def avg_price_per_m2_par_ville():
    try:
        # Charger les données des annonces depuis le fichier JSON
        df = pd.read_json("resource/annonces.json")
        
        # Créer un dictionnaire pour stocker la somme des prix au m² et le nombre d'annonces pour chaque ville
        prix_par_m2_total = defaultdict(float)
        nombre_annonces = defaultdict(int)
        
        # Parcourir chaque annonce et incrémenter la somme des prix au m² pour chaque code postal
        for annonce in df['annonces']:
            zip_code = annonce.get('zipcode')  # Récupérer le code postal de l'annonce
            prix_par_m2 = annonce.get('price_per_square_meter')  # Récupérer le prix au m² de l'annonce
            
            # Vérifier que le code postal et le prix au m² existent et sont valides
            if zip_code and prix_par_m2 is not None:
                try:
                    # Convertir explicitement en float si ce n'est pas déjà un float
                    prix_par_m2 = float(prix_par_m2) if isinstance(prix_par_m2, str) else prix_par_m2
                    
                    if prix_par_m2 > 0:  # Ignorer les annonces avec un prix au m² de  0 ou invalide
                        # Convertir le code postal en string (chaîne de caractères)
                        zip_code_str = str(zip_code)
                        
                        # Ajouter le prix au m² à la somme pour cette ville
                        prix_par_m2_total[zip_code_str] += prix_par_m2
                        nombre_annonces[zip_code_str] += 1  # Incrémenter le compteur d'annonces
        
                except ValueError:
                    # Si la conversion échoue, ignorer cette annonce
                    continue
        
        # Calculer le prix moyen par m² par ville
        villes = []
        for zip_code in prix_par_m2_total:
            if nombre_annonces[zip_code] > 0:
                avg_price_per_m2 = prix_par_m2_total[zip_code] / nombre_annonces[zip_code]  # Calcul du prix moyen par m²
                villes.append({"zipCode": zip_code, "avgPricePerM2": round(avg_price_per_m2, 2)})
        
        # Retourner le résultat sous forme de JSON
        return jsonify({"villes": villes})
    
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

@app.route('/api/annonces/count', methods=['GET'])
def count_annonces_par_ville():
    try:
        # Charger les données des annonces depuis le fichier JSON
        df = pd.read_json("resource/annonces.json")
        
        # Créer un dictionnaire pour stocker le nombre d'annonces par ville (ou par code postal)
        annonces_count = defaultdict(int)
        
        # Parcourir chaque annonce et incrémenter le compteur pour chaque code postal
        for annonce in df['annonces']:
            zip_code = annonce.get('zipcode')  # Récupérer le code postal de l'annonce
            if zip_code:  # Vérifier que le code postal existe
                # Convertir le code postal en string (chaîne de caractères)
                zip_code_str = str(zip_code)
                annonces_count[zip_code_str] += 1
        
        # Construire la réponse dans le format attendu
        villes = [{"zipCode": zip_code, "count": count} for zip_code, count in annonces_count.items()]
        
        # Retourner le résultat sous forme de JSON
        return jsonify({"villes": villes})
    
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

@app.route('/api/cities/<zipCode>', methods=['GET'])
def getCity(zipCode):
    try:
        df = pd.read_json("resource/france-cities-data.json")

        cities = []
        
        for city in df["data"]:
            if city.get("code_postal") == zipCode:
                nouveauZipCode = city.get("code_postal")
                name = city.get("nom_standard")
                population = city.get("population")
                superficie_km2 = city.get("superficie_km2")
                densite = city.get("densite")
                grille_densite_texte = city.get("grille_densite_texte")
                niveau_equipements_services_texte = city.get("niveau_equipements_services_texte")
                nom_unite_urbaine = city.get("nom_unite_urbaine")
                reg_nom = city.get("reg_nom")
                dep_nom = city.get("dep_nom")
                canton_nom = city.get("canton_nom")
                url_wikipedia = city.get("url_wikipedia")
                url_villedereve = city.get("url_villedereve")


                cities.append({
                            "zipCode": nouveauZipCode,
                            "name": name,
                            "population": population,
                            "superficie_km2" : superficie_km2,
                            "densite": densite,
                            "grille_densite_texte": grille_densite_texte,
                            "niveau_equipements_services_texte": niveau_equipements_services_texte,
                            "nom_unite_urbaine": nom_unite_urbaine,
                            "reg_nom": reg_nom,
                            "dep_nom": dep_nom,
                            "canton_nom": canton_nom,
                            "url_wikipedia": url_wikipedia,
                            "url_villedereve": url_villedereve
                        })

        return jsonify(cities)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/best-favorites')
def best_favorites():
    df_copy = df[['list_id','url','zipcode','lat','lng','favorites']].copy()
    df_copy = df_copy[df_copy['favorites'] > 100] 
    return jsonify(df_copy.to_dict(orient='records'))
    

@app.route('/bad-ads')
def bad_ads():
    df_copy = df[['list_id','url','zipcode','lat','lng','first_publication_date']].copy()

    df_copy['first_publication_date'] = pd.to_datetime(df_copy['first_publication_date'], format='%d/%m/%Y  %H:%M').dt.strftime('%d/%m/%Y')
    df_copy['days_difference'] = (datetime.now() - pd.to_datetime(df_copy['first_publication_date'], format='%d/%m/%Y')).dt.days
    print(df_copy)
                
    recent_df = df_copy[df_copy['days_difference'] >= 360]
    print(recent_df)

    return jsonify(recent_df.to_dict(orient='records'))


########################## MAIN ###################### 

if __name__ == '__main__':
    app.run(debug=True, port=5000)
