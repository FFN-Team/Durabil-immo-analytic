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
