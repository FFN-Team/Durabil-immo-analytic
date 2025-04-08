from flask import Flask, jsonify, render_template
from flask_cors import CORS
import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics.pairwise import euclidean_distances
from scipy.cluster.hierarchy import linkage, fcluster
import matplotlib.pyplot as plt
from sklearn.preprocessing import LabelEncoder
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import OrdinalEncoder, LabelEncoder
from sklearn.cluster import KMeans
from flask import request
from datetime import datetime, timedelta


app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"])


# Chargement du dataset
CSV_FILE = "data/data_final.csv"
df = pd.read_csv(CSV_FILE, delimiter=';', encoding="utf-8")
# Remarque : entete du CSV : 
#list_id;url;price;body;subject;first_publication_date;index_date;status;nb_images;country_id;region_id;region_name;department_id;city;zipcode;lat;lng;type;name;siren;has_phone;is_boosted;favorites;square;land_plot_surface;rooms;bedrooms;nb_bathrooms;nb_shower_room;energy_rate;ges;heating_type;heating_mode;fees_at_the_expanse_of;fai_included;mandate_type;price_per_square_meter;immo_sell_type;is_import;nb_floors;nb_parkings;building_year;virtual_tour;old_price;annual_charges;orientation;is_virtual_tour;transport_exists_nearby;school_exists_nearby;medical_service_exists_nearby;centre_of_town_exists_nearby;nb_square_meter_basement;nb_square_meter_balcony


@app.route('/api/annonces', methods=['GET'])
def get_annonces():
    try:
        df = pd.read_json("resource/annonces.json")

        annonces = []
        for annonce in df["annonces"]:
            city = annonce.get("zipcode")
            latitude = annonce.get("lat")
            longitude = annonce.get("lng")
            price = annonce.get("Price")
            price

            annonces.append({
                "city": city,
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


@app.route('/annee-construction-par-ville')
def annee_construction_par_ville():
    filtered_df = df[['city', 'building_year']].dropna()
    filtered_df = filtered_df[filtered_df['building_year'] > 1800]  # Suppression des valeurs incorrectes
    data = filtered_df.groupby("city")["building_year"].apply(list).to_dict()
    return jsonify(data)


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



@app.route('/demande-recente-like', methods=['GET'])
def demande_recente():
    try:
        days_diff = int(request.args.get('days', 30)) 

        df_copy = df[['city', 'first_publication_date','favorites']].copy()

        df_copy['first_publication_date'] = pd.to_datetime(df_copy['first_publication_date'], format='%d/%m/%Y  %H:%M').dt.strftime('%d/%m/%Y')
        df_copy['days_difference'] = (datetime.now() - pd.to_datetime(df_copy['first_publication_date'], format='%d/%m/%Y')).dt.days
                
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



@app.route('/best-favorites')
def best_favorites():
    df_copy = df[['list_id','zipcode','lat','lng','favorites']].copy()
    df_copy = df_copy[df_copy['favorites'] > 100] 
    
    return jsonify(df_copy.to_dict(orient='records'))
    

@app.route('/bad-ads')
def bad_ads():
    df_copy = df[['list_id','zipcode','lat','lng','first_publication_date']].copy()

    df_copy['first_publication_date'] = pd.to_datetime(df_copy['first_publication_date'], format='%d/%m/%Y  %H:%M').dt.strftime('%d/%m/%Y')
    df_copy['days_difference'] = (datetime.now() - pd.to_datetime(df_copy['first_publication_date'], format='%d/%m/%Y')).dt.days
    print(df_copy)
                
    recent_df = df_copy[df_copy['days_difference'] >= 360]
    print(recent_df)

    return jsonify(recent_df.to_dict(orient='records')) 


@app.route('/date-publication-annonces')
def date_publication_annonces():
    filtered_series = df["first_publication_date"].dropna()
    converted_series = filtered_series.apply(lambda _: datetime.datetime.strptime(_, "%d/%m/%Y %H:%M").date())
    return jsonify({ "dates": converted_series.to_list() })




########################## MAIN ###################### 

if __name__ == '__main__':
    app.run(debug=True, port=5000)
