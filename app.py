from flask import Flask, jsonify, render_template
from flask_cors import CORS
import pandas as pd
import datetime


app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"])


# Chargement du dataset
CSV_FILE = "data/data_final.csv"
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
    # print(data)
    return jsonify(data)

@app.route('/annonces-pro-vs-particulier')
def annonces_pro_vs_particulier():
    data = df["type"].value_counts().sort_index().to_dict()
    return jsonify(data)

@app.route('/annonces-par-agence')
def annonces_par_agence():
    data = df["name"].value_counts().head(20).to_dict()
    return jsonify(data)

@app.route('/date-publication-annonces')
def date_publication_annonces():
    filtered_series = df["first_publication_date"].dropna()
    converted_series = filtered_series.apply(lambda _: datetime.datetime.strptime(_, "%d/%m/%Y %H:%M").date())
    return jsonify({ "dates": converted_series.to_list() })


# Analyse des biens disponibles
# - année de construction par ville
@app.route('/annee-construction-par-ville')
def annee_construction_par_ville():
    filtered_df = df[['city', 'building_year']].dropna()
    filtered_df = filtered_df[filtered_df['building_year'] > 1800]  # Suppression des valeurs incorrectes
    data = filtered_df.groupby("city")["building_year"].apply(list).to_dict()
    return jsonify(data)


# Attractivité des annonces

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

########################## MAIN ###################### 

if __name__ == '__main__':
    app.run(debug=True, port=5000)
