#!/usr/bin/env python 
import pandas as pd
from mecoda_minka import get_dfs, get_obs
import ast
import os
import requests
from pathlib import Path
from utils import get_sector


def get_obs_from_main_project(directory, main_project):
    obs = get_obs(id_project=main_project)
    df_obs, df_photos = get_dfs(obs)
    file_path = f"{directory}/data/{main_project}_obs.csv"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    df_obs.to_csv(file_path, index=False)
    file_path = f"{directory}/data/{main_project}_photos.csv"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    df_photos.to_csv(file_path, index=False)

def get_obs_from_project_places(directory, project, cities):
    for k, v in cities.items():
        total_obs = []
        for i in range(len(v)):
            obs = get_obs(id_project=project, place_id=v[i])
            total_obs.extend(obs)
        df1, __ = get_dfs(total_obs)
        
        file_path = f"{directory}/data/obs_{k}.csv"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        df1.to_csv(file_path, index=False)


def taxon_information_Minka(directory, main_project):
    iucn = {
        0: 'No Evaluado',
        5: 'Datos Insuficientes',
        10: 'Preocupación Menor',
        20: 'Casi Amenazado',
        30: 'Vulnerable',
        40: 'En Peligro',
        50: 'En Peligro Crítico',
        60: 'Extinto en la Naturaleza',
        70: 'Extinto'
    }

    obs = pd.read_csv(f"{directory}/data/{main_project}_obs.csv")
    obs['taxon_id'] = obs['taxon_id'].dropna().astype(int)
    taxon_ids = set(int(x) for x in obs['taxon_id'] if not pd.isna(x))
    taxon_ids = sorted(taxon_ids)

    if Path("data/Minka_taxons_information.csv").exists():
        new_tax = False
        df_old = pd.read_csv("data/Minka_taxons_information.csv")
        for tax_id in taxon_ids:
            if tax_id not in set(df_old['taxon_id']):
                new_tax = True
        if not new_tax:
            print("Already up to date.")
            return
    print("Updating taxons information extracted from Minka.")

    # Initialize empty columns
    obs_cnt = []
    establishment = []
    conservation = []
    names = []

    for taxon_id in taxon_ids:
        url = f"https://api.minka-sdg.org/v1/taxa/{taxon_id}"
        headers = {
            "Accept": "application/json"
        }

        # Make the GET request
        response = requests.get(url, headers=headers)

        # Check the response status and print the result
        if response.status_code == 200:
            data = response.json()  # Convert response to JSON
            data = data['results'][0]
            observations_count = data['observations_count']
            establishment_means = []
            if data['listed_taxa'] != []:
                for est_means in data['listed_taxa']:
                    establishment_means.append(est_means['establishment_means']+' - '+est_means['place']['name'])
            conservation_status = []
            if 'conservation_status' in data.keys():
                status = data['conservation_status']['iucn']
                status = iucn[status]
                if data['conservation_status']['place'] == None:
                    status = status + ' - where:GLOBALLY'
                else:
                    status = status + ' - where:' + data['conservation_status']['place']
                conservation_status.append(status + ' - source:' + data['conservation_status']['authority'])
            names.append(data['name'])
            obs_cnt.append(observations_count)
            establishment.append(establishment_means)
            conservation.append(conservation_status)
        else:
            print(f"Error: {response.status_code}")

    df = pd.DataFrame({
        'taxon_id': taxon_ids,
        'taxon_name': names,
        #'specie': species,
        'Total observations count': obs_cnt,
        'Establishment means': establishment,
        'Conservation status': conservation
    })
    df.to_csv('data/Minka_taxons_information.csv', index=False)


def get_taxons_registered_as_species():
    url = "https://api.minka-sdg.org/v1/observations/species_counts"
    project_id = 264
    all_data = []
    page = 1
    all_data = []

    while True:
        params = {"project_id": project_id, "page": page}
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        all_data.append(data)

        if len(data['results']) < 500:
            break

        page += 1  # Move to the next page

    names = []
    ids = []
    for page in all_data:
        for results in page['results']:
            names.append(results['taxon']['name'])
            ids.append(results['taxon']['id'])

    return names, ids


def convert_to_list(value):
    if pd.isna(value):
        return []
    if isinstance(value, str):
        try:
            return ast.literal_eval(value)
        except ValueError:
            return [value.strip()]
    return value

def merge_types(row):
    combined = []
    for col in ['tipo_df1', 'tipo_df2']:
        if isinstance(row[col], list):
            combined.extend(row[col])
        elif pd.notna(row[col]):
            combined.append(row[col])
    return list(set(combined))


def join_data(directory, main_project):
    #Create csv containing all Interesting species with the type info contained in csv given by experts
    if not os.path.exists("data/Experts_taxons_information.csv"):
        df1 = pd.read_csv("data/tipo_de_especies.csv")
        df2 = pd.read_csv("data/Especies_interes.csv")

        df1['tipo'] = df1['tipo'].apply(convert_to_list)
        df2['tipo'] = df2['tipo'].apply(convert_to_list)
        df_merged = pd.merge(df1, df2, on='taxon_name', how='outer', suffixes=('_df1', '_df2'))
        df_merged['tipo'] = df_merged.apply(merge_types, axis=1)
        df_merged = df_merged[['taxon_name', 'tipo', 'source_information']]

        df_merged.to_csv('data/Experts_taxons_information.csv', index=False)


    #Join observations, taxon info given by experts and taxon info retrieved with Minka api
    files = [f"{directory}/data/{main_project}_obs.csv", "data/Experts_taxons_information.csv", "data/Minka_taxons_information.csv"]

    #names_species, ids_species = get_taxons_registered_as_species()

    dfs = []
    for file in files:
        df = pd.read_csv(file)
        dfs.append(df)

    dfs[0] = dfs[0].rename(columns={'address': 'place'})
    df_merge = pd.merge(dfs[0], dfs[1], on=['taxon_name'], how='left')
    df_merge['tipo'] = df_merge['tipo'].apply(lambda x: [] if (pd.isna(x) or x == []) else x)
    df_merge['observed_on'] = pd.to_datetime(df_merge['observed_on'])
    df_merge['observed_on_time'] = pd.to_datetime(df_merge['observed_on_time'], format='%H:%M:%S').dt.time
    df_merge['Total individuals observed in BioplatgesMet project'] = df_merge['taxon_name'].map(dfs[2].set_index('taxon_name')['Total observations count'])
    df_merge['Establishment means'] = df_merge['taxon_name'].map(dfs[2].set_index('taxon_name')['Establishment means'])
    df_merge['Conservation status'] = df_merge['taxon_name'].map(dfs[2].set_index('taxon_name')['Conservation status'])
    #df_merge['specie'] = df_merge['taxon_name'].map(dfs[2].set_index('taxon_name')['specie'])
    
    df_merge[['sector', 'subplace', 'id_place']] = df_merge.apply(
        lambda row: get_sector(row['latitude'], row['longitude']),
        axis=1,
        result_type='expand'
    )
    
    df_merge = df_merge[['observed_on', 'observed_on_time', 'taxon_name', 'taxon_id', 'place', 'subplace', 'sector', 'id_place', 'latitude', 'longitude', 'identifications_count', 'Total individuals observed in BioplatgesMet project', 'kingdom', 'phylum', 'class', 'order', 'family', 'genus', 'tipo', 'Establishment means', 'Conservation status', 'user_id']]
    #df_merge["count_as_specie"] = (df_merge["taxon_name"].isin(names_species) | df_merge["taxon_id"].isin(ids_species)).astype(bool)
    df_merge['taxon_url_information'] = df_merge['taxon_id'].apply(
        lambda x: f"https://minka-sdg.org/taxa/{int(x)}" if pd.notna(x) else None
    )
    df_merge['user_url'] = df_merge['user_id'].apply(
        lambda x: f"https://minka-sdg.org/users/{int(x)}" if pd.notna(x) else None
    )
    df_merge = df_merge.drop(columns=['user_id'])

    df_merge.to_csv('data/obs_tipos.csv', index=False)

    print("El archivo 'obs_tipos.csv' ha sido creado exitosamente.")


if __name__ == "__main__":
    directory = "iia_bioplatgesmet"
    main_project = 264
    cities = {
        "Montgat": [357],
        "Castelldefels": [349],
        "Gavà": [350],
        "El Prat de Llobregat": [351],
        "Sant Adrià del Besòs": [352],
        "Viladecans": [354],
        "Barcelona": [355, 356],
        "Badalona": [347, 348],
    }

    get_obs_from_main_project(directory, main_project)
    get_obs_from_project_places(directory, main_project, cities)

    # Incluimos ciudad en cada observación del proyecto principal
    df_obs = pd.read_csv(f"{directory}/data/{main_project}_obs.csv")

    for city in [
        "Badalona",
        "Barcelona",
        "Castelldefels",
        "El Prat de Llobregat",
        "Gavà",
        "Montgat",
        "Sant Adrià del Besòs",
        "Viladecans",
    ]:
        df_city = pd.read_csv(f"{directory}/data/obs_{city}.csv")
        df_obs.loc[df_obs["id"].isin(df_city["id"].to_list()), "address"] = city

    df_obs.to_csv(f"{directory}/data/{main_project}_obs.csv", index=False)


    taxon_information_Minka(directory, main_project)
    join_data(directory, main_project)
