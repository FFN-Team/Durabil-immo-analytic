from flask import Flask, jsonify, render_template
from flask_cors import CORS
import pandas as pd
import datetime
from collections import defaultdict 
from sklearn.preprocessing import OrdinalEncoder, LabelEncoder
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import numpy as np
from sklearn.decomposition import PCA
from flask import request
from sklearn.cluster import AgglomerativeClustering
from scipy.cluster.hierarchy import linkage, dendrogram
from scipy.spatial.distance import cdist
from sklearn import metrics
from sklearn.cluster import KMeans
import json
import matplotlib.pyplot as plt
import joblib





app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"])


# Chargement du dataset
CSV_FILE = "data/data_final.csv"
CSV_FILE_FILTRED = "data/data_final_pretraited.csv"
df = pd.read_csv(CSV_FILE, delimiter=';', encoding="utf-8")
df_filtred = pd.read_csv(CSV_FILE_FILTRED, delimiter=';', encoding="utf-8")
# Remarque : entete du CSV : 
# list_id;url;price;body;subject;first_publication_date;index_date;status;nb_images;country_id;region_id;region_name;department_id;city;zipcode;lat;lng;type;name;siren;has_phone;is_boosted;favorites;square;land_plot_surface;rooms;bedrooms;nb_bathrooms;nb_shower_room;energy_rate;ges;heating_type;heating_mode;elevator;fees_at_the_expanse_of;fai_included;mandate_type;price_per_square_meter;immo_sell_type;is_import;nb_floors;nb_parkings;building_year;virtual_tour;old_price;annual_charges;orientation;is_virtual_tour
    
######################################################
######################################################

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
    


######################################################
######################################################

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

######################################################
######################################################

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



######################################################
######################################################

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



######################################################
######################################################


@app.route('/api/annonces/<annonceId>', methods=['GET'])
def get_annonce(annonceId):
    # Convertir annonceId en entier
    annonceId = int(annonceId)

    try:
        # df = pd.read_json("resource/annonces.json")
        
        annonces = []
        
        for annonce in df.to_dict(orient='records'):
            if annonce.get('list_id') == annonceId:
                ID = annonce.get("list_id")
                URL = annonce.get("url")
                zipCode = annonce.get("zipcode")
                Description = annonce.get("body")
                square = annonce.get("square")
                rooms = annonce.get("rooms")
                price = annonce.get("price")

                annonces.append({
                    "id": ID,
                    "url": URL,
                    "zipCode": zipCode,
                    "description": Description,
                    "square": square,
                    "rooms": rooms,
                    "price": price
                })

        if not annonces:
            return jsonify({"message": "Aucune annonce trouvée avec cet ID"}), 404

        return jsonify(annonces)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

######################################################
######################################################

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



######################################################
######################################################

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



######################################################
######################################################

@app.route('/')
def index():
    return render_template("index.html")



######################################################
######################################################

@app.route('/annonces-par-sell-type')
def get_data():
    data = df["immo_sell_type"].value_counts().sort_index().to_dict()
    return jsonify(data)



######################################################
######################################################

@app.route('/annonces-par-ville')
def annonces_par_ville():
    data = df["city"].value_counts().sort_values(ascending=False).to_dict()
    # print(data)
    return jsonify(data)



######################################################
######################################################

@app.route('/annonces-pro-vs-particulier')
def annonces_pro_vs_particulier():
    data = df["type"].value_counts().sort_index().to_dict()
    return jsonify(data)



######################################################
######################################################

@app.route('/annonces-par-agence')
def annonces_par_agence():
    data = df["name"].value_counts().head(20).to_dict()
    return jsonify(data)



######################################################
######################################################

@app.route('/annee-construction-par-ville')
def annee_construction_par_ville():
    filtered_df = df[['city', 'building_year']].dropna()
    filtered_df = filtered_df[filtered_df['building_year'] > 1800]  # Suppression des valeurs incorrectes
    data = filtered_df.groupby("city")["building_year"].apply(list).to_dict()
    return jsonify(data)



######################################################
######################################################

@app.route('/nb-moyen-favorites-par-annonce-boost')
def nb_moyen_favorites_par_annonce_boost():
    filtered_df = df[["first_publication_date", "is_boosted", "favorites"]].dropna()
    filtered_df["year"] = filtered_df["first_publication_date"].apply(
        lambda _: datetime.datetime.strptime(_, "%d/%m/%Y %H:%M").year
    )
    filtered_df["month"] = filtered_df["first_publication_date"].apply(
        lambda _: datetime.datetime.strptime(_, "%d/%m/%Y %H:%M").month
    )
    filtered_df = filtered_df.drop("first_publication_date", axis=1)
    
    boosted_and_non_boosted_df = filtered_df.groupby(["year", "month", "is_boosted"])["favorites"].agg(['sum', 'count'])
    useless_rows_indexes = drop_useless_rows_boosted_and_non_boosted(boosted_and_non_boosted_df)
    total_df = filtered_df.groupby(["year", "month"])["favorites"].agg(['sum', 'count'])
    drop_useless_rows(total_df, useless_rows_indexes)

    concat_df = pd.concat([boosted_and_non_boosted_df, total_df])
    concat_df["average_number_of_favorites_per_ad"] = get_average_numbers_of_favorites_per_ad(concat_df)

    return jsonify(get_dict_nb_moyen_favorites_par_annonce_boost(concat_df))

def drop_useless_rows_boosted_and_non_boosted(boosted_and_non_boosted_df):
    df_temp = boosted_and_non_boosted_df.groupby(["year", "month"]).count()
    useless_rows_indexes = []

    for tuple in df_temp.itertuples():
        if tuple.count == 1: 
            useless_rows_indexes.append(tuple.Index)
            boosted_and_non_boosted_df.drop(tuple.Index, inplace=True)
    return useless_rows_indexes

def drop_useless_rows(df, useless_rows_indexes):
    for index in useless_rows_indexes:
        df.drop(index, inplace=True)

def get_average_numbers_of_favorites_per_ad(df):
    average_number_of_favorites_per_ad = []
    
    for i in range(len(df.values)):
        number_of_favorites = df.values[i][0]
        number_of_ads = df.values[i][1]
        average_number_of_favorites_per_ad.append(number_of_favorites / number_of_ads)

    return average_number_of_favorites_per_ad

def get_dict_nb_moyen_favorites_par_annonce_boost(df):
    dict = {}
    for tuple in df.itertuples():
        if tuple.Index[0] not in dict.keys():
            dict.update({ tuple.Index[0]: {} })
    for tuple in df.itertuples():
        year = tuple.Index[0]
        month = tuple.Index[1]
        if month not in dict[year].keys():
            dict[year].update({ month: {} })
    for tuple in df.itertuples():
        year = tuple.Index[0]
        month = tuple.Index[1]
        type = get_boosted_label(tuple.Index[2]) if len(tuple.Index) == 3 else "Total"
        dict[year][month].update({ 
            type: tuple.average_number_of_favorites_per_ad 
        })
    return dict

def get_boosted_label(value):
    return "Boosted" if value == 1 else "Non boosted"



######################################################
######################################################

@app.route('/evolution-nb-images-favorites')
def evolution_nb_images_favorites():
    filtered_df = df[["first_publication_date", "nb_images", "favorites"]].dropna()
    filtered_df["year"] = filtered_df["first_publication_date"].apply(
        lambda _: datetime.datetime.strptime(_, "%d/%m/%Y %H:%M").year
    )
    filtered_df["month"] = filtered_df["first_publication_date"].apply(
        lambda _: datetime.datetime.strptime(_, "%d/%m/%Y %H:%M").month
    )
    filtered_df = filtered_df.drop("first_publication_date", axis=1)
    sorted_df = filtered_df.sort_values(by=["year", "month", "nb_images"])
    useless_rows = get_useless_rows_nb_images(sorted_df)

    dict = get_dict_evolution_nb_images_favorites(sorted_df, useless_rows)
    return jsonify(dict)

def get_dict_evolution_nb_images_favorites(df, useless_rows):
    df_year = df["year"].drop_duplicates()
    dict = {}
    for year in df_year:
        dict.update({ year: {} })
    for tuple in df.itertuples():
        if tuple.month not in dict[tuple.year].keys():
            dict[tuple.year].update({ tuple.month: {} })
    for tuple in df.itertuples():
        dict[tuple.year][tuple.month].update({ 
            "Nb_Images": [], 
            "Nb_Favorites": []
        })
    for tuple in df.itertuples():
        dict[tuple.year][tuple.month]["Nb_Images"].append(tuple.nb_images)
        dict[tuple.year][tuple.month]["Nb_Favorites"].append(tuple.favorites)
    
    for i in range(len(useless_rows["year"])):
        year = useless_rows["year"][i]
        month = useless_rows["month"][i]
        if len(dict[year][month]["Nb_Images"]) < 2:
            dict[year].pop(month)
    
    for year in useless_rows["year"]:
        if year in dict.keys() and len(dict[year]) == 0:
            dict.pop(year)

    return dict

def get_useless_rows_nb_images(df):
    df_temp = df.groupby(["year", "month"]).count()
    useless_rows = { "year" : [], "month": [] }
    for tuple in df_temp.itertuples():
        if tuple.nb_images == 1: 
            useless_rows["year"].append(tuple.Index[0])
            useless_rows["month"].append(tuple.Index[1])
    return useless_rows



######################################################
######################################################

@app.route('/nb-moyen-favorites-par-type-vendeur-annonce')
def nb_moyen_favorites_par_type_vendeur_annonce():
    filtered_df = df[["first_publication_date", "type", "favorites"]].dropna()
    filtered_df["year"] = filtered_df["first_publication_date"].apply(
        lambda _: datetime.datetime.strptime(_, "%d/%m/%Y %H:%M").year
    )
    filtered_df["month"] = filtered_df["first_publication_date"].apply(
        lambda _: datetime.datetime.strptime(_, "%d/%m/%Y %H:%M").month
    )
    filtered_df = filtered_df.drop("first_publication_date", axis=1)
    all_type_of_seller_df = filtered_df.groupby(["year", "month", "type"])["favorites"].agg(['sum', 'count'])
    useless_rows_indexes = drop_useless_rows_boosted_and_non_boosted(all_type_of_seller_df)

    total_df = filtered_df.groupby(["year", "month"])["favorites"].agg(['sum', 'count'])
    drop_useless_rows(total_df, useless_rows_indexes)

    concat_df = pd.concat([all_type_of_seller_df, total_df])
    concat_df["average_number_of_favorites_per_type_of_seller"] = get_average_numbers_of_favorites_per_ad(concat_df)

    return jsonify(get_dict_nb_moyen_favorites_par_type_vendeur_boost(concat_df))

def get_dict_nb_moyen_favorites_par_type_vendeur_boost(df):
    dict = {}
    for tuple in df.itertuples():
        if tuple.Index[0] not in dict.keys():
            dict.update({ tuple.Index[0]: {} })
    for tuple in df.itertuples():
        year = tuple.Index[0]
        month = tuple.Index[1]
        if month not in dict[year].keys():
            dict[year].update({ month: {} })
    for tuple in df.itertuples():
        year = tuple.Index[0]
        month = tuple.Index[1]
        type = tuple.Index[2] if len(tuple.Index) == 3 else "Total"
        dict[year][month].update({ 
            type: tuple.average_number_of_favorites_per_type_of_seller 
        })
    return dict



######################################################
######################################################

@app.route('/clusters')
def clustering():
    features = ['square', 'land_plot_surface', 'rooms', 'bedrooms', 'nb_bathrooms',
                'nb_shower_room', 'nb_floors', 'nb_parkings', 'energy_rate', 
                'ges', 'heating_type', 'heating_mode']

    filtered_df = df[features].copy()
    
    filtered_df['land_plot_surface'] = filtered_df['land_plot_surface'].fillna(0)
    filtered_df['nb_floors'] = filtered_df['nb_floors'].fillna(1)
    filtered_df['nb_parkings'] = filtered_df['nb_parkings'].fillna(0)
    filtered_df['nb_bathrooms'] = filtered_df['nb_bathrooms'].fillna(1)
    filtered_df['nb_shower_room'] = filtered_df['nb_shower_room'].fillna(1)

    encoder = OrdinalEncoder()
    label_enc = LabelEncoder()
    filtered_df['energy_rate'] = encoder.fit_transform(filtered_df[['energy_rate']])
    filtered_df['ges'] = encoder.fit_transform(filtered_df[['ges']])
    filtered_df['heating_type'] = label_enc.fit_transform(filtered_df['heating_type'])
    filtered_df['heating_mode'] = label_enc.fit_transform(filtered_df['heating_mode'])

    filtered_df = filtered_df.dropna().copy()

    try:
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(filtered_df)

        kmeans = KMeans(n_clusters=4, random_state=42)
        clusters = kmeans.fit_predict(X_scaled)

        pca = PCA(n_components=2)
        components = pca.fit_transform(X_scaled)

        total_inertia = np.sum(X_scaled ** 2, axis=1)  
        coords_squared = components ** 2
        cos2 = np.sum(coords_squared, axis=1) / total_inertia

        individuals = []
        for i in range(len(components)):
            if cos2[i] >= 0.5:
                individuals.append({
                    "x": components[i][0],
                    "y": components[i][1],
                    "cluster": int(clusters[i]),
                    "cos2": float(cos2[i])
                })

        loadings = pca.components_.T * np.sqrt(pca.explained_variance_)
        
        variables = []
        for i, var in enumerate(filtered_df.columns):
            variables.append({
                "var": var,
                "x": float(loadings[i, 0]),
                "y": float(loadings[i, 1])
            })

        return jsonify({
            "individuals": individuals,
            "variables": variables
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500



######################################################
######################################################

@app.route('/demande-recente-like', methods=['GET'])
def demande_recente():
    try:
        days_diff = int(request.args.get('days', 30)) 

        df_copy = df[['city', 'first_publication_date','favorites']].copy()

        df_copy['first_publication_date'] = pd.to_datetime(df_copy['first_publication_date'], format='%d/%m/%Y  %H:%M').dt.strftime('%d/%m/%Y')
        df_copy['days_difference'] = (datetime.datetime.now() - pd.to_datetime(df_copy['first_publication_date'], format='%d/%m/%Y')).dt.days
                
        recent_df = df_copy[df_copy['days_difference'] <= days_diff]

        demande_par_ville = recent_df['city'].value_counts().to_dict()
        favorites_par_ville = recent_df.groupby('city')['favorites'].sum().to_dict()

        # Calcul des favoris moyens par annonce pour chaque ville
        favorites_moyenne_par_ville = {
            city: favorites_par_ville[city] / demande_par_ville[city] 
            for city in demande_par_ville
        }

        result = {
            "demande_par_ville": demande_par_ville,
            "favorites_par_ville": favorites_par_ville,
            "favorites_moyenne_par_ville": favorites_moyenne_par_ville  # Ajout de la moyenne des favoris par annonce
        }

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500



######################################################
######################################################

@app.route('/api-correlation-prix')
def correlation():

    #price;zipcode;lat;lng;square;land_plot_surface;rooms;bedrooms;nb_bathrooms;nb_shower_room;energy_rate;ges;heating_type;heating_mode;nb_floors;nb_parkings;building_year;annual_charges;orientation;transport_exists_nearby;school_exists_nearby;medical_service_exists_nearby;centre_of_town_exists_nearby;
    df_copy = df[['price','city','lat','lng','square','land_plot_surface','rooms','bedrooms','nb_bathrooms','nb_shower_room','energy_rate','ges','heating_type','heating_mode','nb_floors','nb_parkings','building_year','annual_charges','orientation','transport_exists_nearby','school_exists_nearby','medical_service_exists_nearby','centre_of_town_exists_nearby']].copy()
    print(df_copy)
    print(df_copy.isnull().sum()) 

    df_copy['land_plot_surface'] = df_copy['land_plot_surface'].fillna(0)
    df_copy['nb_floors'] = df_copy['nb_floors'].fillna(1)
    df_copy['nb_parkings'] = df_copy['nb_parkings'].fillna(0)
    df_copy['nb_bathrooms'] = df_copy['nb_bathrooms'].fillna(1)
    df_copy['nb_shower_room'] = df_copy['nb_shower_room'].fillna(1)
    df_copy['transport_exists_nearby'] = df_copy['transport_exists_nearby'].fillna(0)
    df_copy['school_exists_nearby'] = df_copy['school_exists_nearby'].fillna(0)
    df_copy['medical_service_exists_nearby'] = df_copy['medical_service_exists_nearby'].fillna(0)
    df_copy['centre_of_town_exists_nearby'] = df_copy['centre_of_town_exists_nearby'].fillna(0)

    encoder = OrdinalEncoder()
    label_enc = LabelEncoder()
    df_copy['energy_rate'] = encoder.fit_transform(df_copy[['energy_rate']])
    df_copy['ges'] = encoder.fit_transform(df_copy[['ges']])
    df_copy['heating_type'] = label_enc.fit_transform(df_copy['heating_type'])
    df_copy['heating_mode'] = label_enc.fit_transform(df_copy['heating_mode'])
    df_copy['orientation'] = label_enc.fit_transform(df_copy['orientation'])
    df_copy['city'] = label_enc.fit_transform(df_copy['city'])

    df_copy['total_services_score'] = (
        4*df_copy['transport_exists_nearby'] +
        1*df_copy['school_exists_nearby'] +
        2*df_copy['medical_service_exists_nearby'] +
        3*df_copy['centre_of_town_exists_nearby']
    )

    df_copy['conso_score'] = (
        df_copy['energy_rate'] +
        df_copy['ges']
    )

    df_copy = df_copy.drop(['transport_exists_nearby', 'school_exists_nearby','medical_service_exists_nearby','centre_of_town_exists_nearby','energy_rate','ges'], axis=1)


    print(df_copy.isnull().sum()) 
    filtered_df = df_copy.dropna().copy()
    print(filtered_df)


    correlation_matrix = filtered_df.corr()
    price_correlation = correlation_matrix['price'].drop('price')
    return jsonify(price_correlation.to_dict())



######################################################
######################################################

@app.route('/date-publication-annonces')
def date_publication_annonces():
    filtered_series = df["first_publication_date"].dropna()
    converted_series = filtered_series.apply(lambda _: datetime.datetime.strptime(_, "%d/%m/%Y %H:%M").date())
    return jsonify({ "dates": converted_series.to_list() })



######################################################
######################################################

@app.route('/best-favorites')
def best_favorites():
    df_copy = df[['list_id','url','zipcode','lat','lng','favorites']].copy()
    df_copy = df_copy[df_copy['favorites'] > 100] 
    return jsonify(df_copy.to_dict(orient='records'))
    


######################################################
######################################################

@app.route('/bad-ads')
def bad_ads():
    df_copy = df[['list_id','url','zipcode','lat','lng','first_publication_date']].copy()

    df_copy['first_publication_date'] = pd.to_datetime(df_copy['first_publication_date'], format='%d/%m/%Y  %H:%M').dt.strftime('%d/%m/%Y')
    df_copy['days_difference'] = (datetime.datetime.now() - pd.to_datetime(df_copy['first_publication_date'], format='%d/%m/%Y')).dt.days
    print(df_copy)
                
    recent_df = df_copy[df_copy['days_difference'] >= 360]
    print(recent_df)

    return jsonify(recent_df.to_dict(orient='records'))




######################################################
######################################################

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




######################################################
######################################################
@app.route('/cities')
def cities() : 
    all_cities = df['city'].drop_duplicates()  # pour avoir seulement les valeurs uniques
    print(all_cities)
    return all_cities.to_json(orient="records")




######################################################
######################################################

# @app.route('/biens-similaires')
@app.route('/biens-similaires', methods=['POST'])
def biens_similaires():
    try:
        data = request.get_json()
        # data = {
        #     "filtres_names": ["price", "city", "square", "land_plot_surface", "school_exists_nearby"],
        #     "filtres_vals": {
        #         "price": 4000,
        #         "city": "Nanterre",
        #         "square": 180,
        #         "land_plot_surface": 300,
        #         'school_exists_nearby': 1
        #     },
        #     "poids" : {
        #         "price": 1,
        #         "city": 1,
        #         "square": 1,
        #         "land_plot_surface": 5,
        #         'school_exists_nearby': 1
        #     }
        # }

        filtres_names = data['filtres_names']
        filtres_vals = data['filtres_vals']
        poids_filtres = data['poids']

        model_folder_path = ""
        model_nature = ""
        cluster_pred = ""

        if((len(filtres_names)==4) and (all(filtre in filtres_names for filtre in ['price', 'city', 'square', 'land_plot_surface']))) :
            model_folder_path = "model_ML/Combi/ORV/"
            model_nature = "kmeans"
        
        if((len(filtres_names)==5) and (all(filtre in filtres_names for filtre in ['price', 'city', 'square', 'land_plot_surface', 'transport_exists_nearby']))) :
            model_folder_path = "model_ML/Combi/Trans/"
            model_nature = "kmeans"

        if((len(filtres_names)==6) and (all(filtre in filtres_names for filtre in ['price', 'city', 'square', 'land_plot_surface', 'transport_exists_nearby', 'school_exists_nearby']))) :
            model_folder_path = "model_ML/Combi/Trans_Sch/"
            model_nature = "kmeans"

        if((len(filtres_names)==6) and (all(filtre in filtres_names for filtre in ['price', 'city', 'square', 'land_plot_surface', 'transport_exists_nearby', 'medical_service_exists_nearby']))) :
            model_folder_path = "model_ML/Combi/Trans_Med/"
            model_nature = "cah"

        if((len(filtres_names)==7) and (all(filtre in filtres_names for filtre in ['price', 'city', 'square', 'land_plot_surface', 'transport_exists_nearby', 'school_exists_nearby', 'medical_service_exists_nearby']))) :
            model_folder_path = "model_ML/Combi/Trans_Sch_Med/"
            model_nature = "cah"

        if((len(filtres_names)==5) and (all(filtre in filtres_names for filtre in ['price', 'city', 'square', 'land_plot_surface', 'school_exists_nearby']))) :
            model_folder_path = "model_ML/Combi/Sch/"
            model_nature = "kmeans"

        if((len(filtres_names)==6) and (all(filtre in filtres_names for filtre in ['price', 'city', 'square', 'land_plot_surface', 'school_exists_nearby', 'medical_service_exists_nearby']))) :
            model_folder_path = "model_ML/Combi/Sch_Med/"
            model_nature = "kmeans"

        if((len(filtres_names)==5) and (all(filtre in filtres_names for filtre in ['price', 'city', 'square', 'land_plot_surface', 'medical_service_exists_nearby']))) :
            model_folder_path = "model_ML/Combi/Med/"
            model_nature = "kmeans"




        # Prédiction cluster
        bien_voulu = pd.DataFrame([filtres_vals])
        poids = pd.DataFrame([poids_filtres]) 

        label_enc_city = joblib.load("model_ML/encoder/label_enc_city.pkl")
        bien_voulu['city'] = label_enc_city.transform(bien_voulu['city'])

        scaler_path = model_folder_path + "scaler.pkl"
        scaler = joblib.load(scaler_path)
        bien_voulu_std = scaler.transform(bien_voulu)

        if(model_nature =="kmeans") : 
            model_path = model_folder_path + "kmeans_model.pkl"
            kmeans = joblib.load(model_path)
            cluster_pred = kmeans.predict(bien_voulu_std)

        if(model_nature =="cah") : 
            model_path = model_folder_path + "KNClassif_model.pkl"
            KNClassif = joblib.load(model_path)
            cluster_pred = KNClassif.predict(bien_voulu_std)

        # Biens proches au bien voulu dans le cluster
        data_clustered_path = model_folder_path + "data_with_cluster.csv"
        df = pd.read_csv(data_clustered_path, sep=';')
        df = df[df['cluster'] == int(cluster_pred[0])]
        df = df.drop("cluster", axis=1)
        
        df = pd.DataFrame(scaler.transform(df), columns=df.columns)
        bien_voulu = pd.DataFrame(scaler.transform(bien_voulu), columns=bien_voulu.columns)

        df['distance'] = np.linalg.norm((df.values - bien_voulu.values) * poids.values, axis=1)

        df_sorted = df.sort_values('distance')
        selected_indexes = df_sorted.head(5).index

        return df_filtred.loc[selected_indexes]['list_id'].astype(np.int64).to_json(orient="records")
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


###################################################### 
########################## MAIN ######################
###################################################### 

if __name__ == '__main__':
    app.run(debug=True, port=5000)
