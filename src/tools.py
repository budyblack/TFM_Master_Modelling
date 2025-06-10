import pandas as pd
import ast
from datetime import date, datetime, timedelta
from langchain.agents import Tool
from langchain_core.tools import create_retriever_tool
from langchain_experimental.agents.agent_toolkits import create_csv_agent
from langchain_core.messages import HumanMessage
from langchain.agents.agent_types import AgentType
from langchain_community.retrievers import WikipediaRetriever
import math
import requests
from typing import Optional
from pydantic import BaseModel, Field
from langchain.tools import tool
from langchain_experimental.tools.python.tool import PythonREPLTool
import plotly.express as px
import plotly.io as pio
import re
import uuid



#Tools
def general_context(var: str):
    with open("data/types_context.txt", "r") as file:
        type_context = file.read()
    with open("data/dunas_context.txt", "r") as file:
        dunas_context = file.read()
    places = {'Gavà':{'Platja de Gavà':[['GV02'-'GV23',461-482]]},'Viladecans':{'La Murtra':[['VC01'-'VC02', 483-484]], 'La Pineda Viladecans': [['VC03'-'VC12', 485-494]], "La Pineda de Ca'l Francès": [['VC13'-'VC14', 495-496]], 'El Remolar (Viladecans)': [['VC15'-'VC17', 497-499]], "Platja de l'Estany": [['GV24', 508]]}, 'Sant Adrià del Besós': {'Fòrum': [['SA01'-'SA03', 500-501]], 'Parc del Litoral': [['SA04'-'SA08', 503-507]],'Mora': [['BD01', 454]]}, 'Castelldefels': {'Baixador': [['CF01'-'CF02', 509-510],['CF03'-'CF04', 515-516],['CF05'-'CF06', 518-519],['CF07'-'CF09', 523-525],['CF10', 527],['CF11'-'CF13', 529-531],['CF14'-'CF15', 535-536],['CF16'-'CF17', 538-539]], 'La Pineda Castelldefels': [['CF39', 514], ['CF38', 517], ['CF37', 520], ['CF36', 521], ['CF40', 526], ['CF35', 522], ['CF34', 528], ['CF33', 532], ['CF32', 533], ['CF31', 534], ['CF30', 545], ['CF29', 547], ['CF24', 548], ['CF25', 549], ['CF28', 550], ['CF26', 551], ['CF27', 552]], 'Lluminetes': [['CF18'-'CF22', 540-544], ['CF23', 546]], 'Platja de Gavà': [['GV01', 460]]}, 'Montgat platges': {'Cala Taps': [['MG01', 553]], 'Platja de les Roques': [['MG02'-'MG03', 554-555]], 'Les Barques': [['MG04'-'MG08', 556-560]], 'Can Tano': [['MG09'-'MG10', 561-562]], 'Montsolís': [['MG11'-'MG15', 563-567]], 'Els Toldos': [['MG16'-'MG17', 568-569]]}, 'Badalona sud': {'Mora': [['BD02'-'BD04', 455-457]]},'Badalona nort': {'Coco': [['BD05', 458], ['BD06', 459]], 'Pont del Petroli': [['BD07'-'BD09', 511-513], ['BD10'-'BD11', 570-571]], "L'Estació": [['BD12'-'BD15', 572-575]],'Patins a Vela': [['BD16', 576]], 'Pescadors': [['BD17'-'BD22', 577-582]],"Pont d'en Botifarreta": [['BD23'-'BD28', 583-588]],'Cristall': [['BD29'-'BD31', 589-591]],'Barca Maria': [['BD32'-'BD38', 592-598]]},'El Prat': {'El Remolar (El Prat)': [['PR01', 599]],'La Roberta': [['PR02'-'PR12', 600-610]],'Can Camins': [['PR13'-'PR23', 611-621]],'La Ricarda': [['PR26', 624]],'Platja Naturista': [['PR24'-'PR25', 622-623]],"Ca l'Arana": [['PR27', 625]]},'Barcelona - Zona Sud':{'Sant Sebastià': [['BC01'-'BC06', 626-631]],'Sant Miquel': [['BC07'-'BC10', 632-635]],'Barceloneta': [['BC11'-'BC13', 636-638]],'Somorrostro': [['BC14'-'BC18', 639-643]]},'Barcelona - Zona Nort': {'Nova Icària': [['BC19'-'BC23', 644-648]],'Bogatell': [['BC24', 649], ['BC25', 665],['BC26'-'BC28', 650-652]],'Mar Bella': [['BC29'-'BC34', 653-658]],'Nova Mar Bella': [['BC35'-'BC38', 659-662]],'Llevant': [['BC39'-'BC40', 663-664],['BC41'-'BC42', 666-667],['BC43'-'BC44', 668-669]]}}
    return f"El proyecto de donde extraes información de las especies se llama BiplatgesMet. Este proyecto registra observaciones de especies en el litoral del Area Metropolitana de Barcelona (AMB), concretamente de las playas y zonas dunares, y no recoge datos de especies observadas en lugares alejados de estos entornos litorales. La falta de observaciones o de información en las observaciones registradas se debe a que la gente no registra o lo hace de manera incompleta, anima a que registren más y aporten al proyecto. Los nombres científicos deben ir en cursiva. Diferencia entre especie, observacion y identificaciones en cada observacion. Los lugares de estudio por el momento son los siguientes (en el formato: {'{'}'place':['subplace':['sector','place_id']]{'}'}): {str(places)}.\nSi obtienes como información gran cantidad de especies distintas, esto no significa que haya gran diversidad en esa zona. Además, hay ciertos tipos de especies que son buenas para el medio y otras que son malas, según el tipo de especie que sea. Los nombres exactos de los tipos de especies que hay registros son: 'Invasora', 'Exótica', 'Introduced', 'Protegida', 'Estrictamente Protegida', 'Amenazada', 'En Peligro', 'Explotación reglamentada'. En un dataframe se indica también que especies son nativas y cuales introduced, y el place de esto. Las definiciones de los tipos de especies son:\n{type_context}\nContexto sobre las dunas:\n{dunas_context}"

class GeneralContextInput(BaseModel):
    topic: Optional[str] = Field(default=None, description="No argument needed to get context.")

@tool(args_schema=GeneralContextInput)
def tool_context(topic: Optional[str] = None) -> str:
    """First function to call when starting a chat."""
    return general_context(topic)

@tool(args_schema=GeneralContextInput)
def get_places_tool(topic: Optional[str] = None) -> str:
    """Call before python_tool when asked for a place in order to get the concrete name and know if it is a place, subplace, sector or place_id, or if it exist. It returns a dictionary of all the places, subplaces, sectors and id_places in the project, in the format: {'place':['subplace':['sector','place_id']]}."""
    places = {'Gavà':{'Platja de Gavà':[['GV02'-'GV23',461-482]]},'Viladecans':{'La Murtra':[['VC01'-'VC02', 483-484]], 'La Pineda Viladecans': [['VC03'-'VC12', 485-494]], "La Pineda de Ca'l Francès": [['VC13'-'VC14', 495-496]], 'El Remolar (Viladecans)': [['VC15'-'VC17', 497-499]], "Platja de l'Estany": [['GV24', 508]]}, 'Sant Adrià del Besós': {'Fòrum': [['SA01'-'SA03', 500-501]], 'Parc del Litoral': [['SA04'-'SA08', 503-507]],'Mora': [['BD01', 454]]}, 'Castelldefels': {'Baixador': [['CF01'-'CF02', 509-510],['CF03'-'CF04', 515-516],['CF05'-'CF06', 518-519],['CF07'-'CF09', 523-525],['CF10', 527],['CF11'-'CF13', 529-531],['CF14'-'CF15', 535-536],['CF16'-'CF17', 538-539]], 'La Pineda Castelldefels': [['CF39', 514], ['CF38', 517], ['CF37', 520], ['CF36', 521], ['CF40', 526], ['CF35', 522], ['CF34', 528], ['CF33', 532], ['CF32', 533], ['CF31', 534], ['CF30', 545], ['CF29', 547], ['CF24', 548], ['CF25', 549], ['CF28', 550], ['CF26', 551], ['CF27', 552]], 'Lluminetes': [['CF18'-'CF22', 540-544], ['CF23', 546]], 'Platja de Gavà': [['GV01', 460]]}, 'Montgat platges': {'Cala Taps': [['MG01', 553]], 'Platja de les Roques': [['MG02'-'MG03', 554-555]], 'Les Barques': [['MG04'-'MG08', 556-560]], 'Can Tano': [['MG09'-'MG10', 561-562]], 'Montsolís': [['MG11'-'MG15', 563-567]], 'Els Toldos': [['MG16'-'MG17', 568-569]]}, 'Badalona sud': {'Mora': [['BD02'-'BD04', 455-457]]},'Badalona nort': {'Coco': [['BD05', 458], ['BD06', 459]], 'Pont del Petroli': [['BD07'-'BD09', 511-513], ['BD10'-'BD11', 570-571]], "L'Estació": [['BD12'-'BD15', 572-575]],'Patins a Vela': [['BD16', 576]], 'Pescadors': [['BD17'-'BD22', 577-582]],"Pont d'en Botifarreta": [['BD23'-'BD28', 583-588]],'Cristall': [['BD29'-'BD31', 589-591]],'Barca Maria': [['BD32'-'BD38', 592-598]]},'El Prat': {'El Remolar (El Prat)': [['PR01', 599]],'La Roberta': [['PR02'-'PR12', 600-610]],'Can Camins': [['PR13'-'PR23', 611-621]],'La Ricarda': [['PR26', 624]],'Platja Naturista': [['PR24'-'PR25', 622-623]],"Ca l'Arana": [['PR27', 625]]},'Barcelona - Zona Sud':{'Sant Sebastià': [['BC01'-'BC06', 626-631]],'Sant Miquel': [['BC07'-'BC10', 632-635]],'Barceloneta': [['BC11'-'BC13', 636-638]],'Somorrostro': [['BC14'-'BC18', 639-643]]},'Barcelona - Zona Nort': {'Nova Icària': [['BC19'-'BC23', 644-648]],'Bogatell': [['BC24', 649], ['BC25', 665],['BC26'-'BC28', 650-652]],'Mar Bella': [['BC29'-'BC34', 653-658]],'Nova Mar Bella': [['BC35'-'BC38', 659-662]],'Llevant': [['BC39'-'BC40', 663-664],['BC41'-'BC42', 666-667],['BC43'-'BC44', 668-669]]}}
    return str(places)

def ensure_list(value):
    if isinstance(value, list):
        return value
    elif isinstance(value, str):
        try:
            # Attempt to parse if it's a string representation of a list
            return ast.literal_eval(value)
        except (ValueError, SyntaxError):
            # If parsing fails, return the string wrapped in a list
            return [value]
    else:
        # If it's neither a list nor a string, wrap in a list
        return [value]

def get_info_period(period: str):
    df1 = pd.read_csv("data/obs_tipos.csv")
    df2 = pd.read_csv("data/Experts_taxons_information.csv")
    #df3 = pd.read_csv("data/Final_types.csv")
    df1["observed_on"] = pd.to_datetime(df1["observed_on"])

    date1 = period.split('y')[0].strip()
    date2 = period.split('y')[1].strip()
    observations = df1[(df1["observed_on"] >= date1) & (df1["observed_on"] <= date2)]

    final_result = ""
    #if observations.empty:
    #    final_result = "There are not observations for the period asked, so we are studying the period before. "
    #    date2_dt = datetime.strptime(date2, '%Y-%m-%d')
    #    first_day_of_previous_month = (date2_dt.replace(day=1) - timedelta(days=1)).replace(day=1)
    #    last_day_of_previous_month = (date2_dt.replace(day=1) - timedelta(days=1))
    #    date1 = first_day_of_previous_month.strftime('%Y-%m-%d')
    #    date2 = last_day_of_previous_month.strftime('%Y-%m-%d')
    #    observations = df1[(df1["observed_on"] >= date1) & (df1["observed_on"] <= date2)]
    summary = observations.groupby(['taxon_name', 'place']).agg(tipo=('tipo', 'first'), observations_count=('identifications_count', 'sum'), places=('place', 'unique'), Establishment_means=('Establishment means', 'first'), Conservation_status=('Conservation status', 'first'), Phylum=('class', 'first')).reset_index()
    #summary = summary.merge(df3[['taxon_name', 'type']], on='taxon_name', how='left')
    #summary['type'] = summary.apply(lambda row: clean_and_merge_types(row['tipo_df1'], row['tipo_df2']), axis=1)  #In case of also merging type for df3, put it here
    interesting_species = df2.loc[df2['taxon_name'].isin(df1['taxon_name']), 'taxon_name'].unique().tolist()
    
    #We also take into account the raptilia which are of interest and cannot be added easily in the lists of species of interest
    reptilia = summary.loc[summary["Phylum"]=='Reptilia', 'taxon_name'].unique().tolist()
    
    result = []
    taxon_name = ''
    for index, row in summary.iterrows():
        if row["taxon_name"] in interesting_species or row["taxon_name"] in reptilia:
            # Generate the taxon info
            if taxon_name == '':
                taxon_name = row['taxon_name']
                taxon_obs = []
            if taxon_name != row['taxon_name']:
                #print(establishment_means)
                result.append(f"{taxon_name}: (tipo: {taxon_type + conservation_status + establishment_means}, observations: {taxon_obs})")
                taxon_obs = []
                taxon_name = row['taxon_name']
            if row['Conservation_status'] == []:
                conservation_status = []
            else:
                conservation_status = row['Conservation_status']
            if row['Establishment_means'] == []:
                establishment_means = []
            else:
                establishment_means = row['Establishment_means']
            if row['tipo'] == []:
                taxon_type = []
            else:
                taxon_type = row['tipo']
            taxon_type = ensure_list(taxon_type)
            conservation_status = ensure_list(conservation_status)
            establishment_means = ensure_list(establishment_means)
            
            if row["taxon_name"] in reptilia:
                taxon_type.append('Monitoreo por impacto positivo')

            taxon_obs.append(f'lugar obs.: {", ".join(row["places"])}, numero de obs.: {row["observations_count"]}')
        if index == summary.index[-1]:
            if row["taxon_name"] in interesting_species:
                result.append(f"{taxon_name}: (tipo: {taxon_type + conservation_status + establishment_means}, observations: {taxon_obs})")
            else:
                result.append(f"{taxon_name}: (tipo: {taxon_type + conservation_status + establishment_means}, observations: {taxon_obs})")
    
    final_result = f"{final_result}Observations of interesting species between {date1} and {date2}:\n{result}"

    return final_result

class InfoPeriodInput(BaseModel):
    topic: str = Field(description="The period you want to study, in this format: 'YY-MM-DD y YY-MM-DD' (example: 2024-11-02 y 2024-11-09).")

@tool(args_schema=InfoPeriodInput)
def tool_get_info(topic: str) -> str:
    """Returns the observations of only interesting species in all the beaches, in the desired period (arg: 'YY-MM-DD y YY-MM-DD')."""
    return get_info_period(topic)


def tool_retriever(vectorstore):
    tool = create_retriever_tool(
        vectorstore.as_retriever(search_kwargs={"k": 2, "score_threshold": 0.5}),
        "VectorstoreRetriever",
        "Search information about specific species, places, convents, and others from a vectorstore. You may do as many querys as possible to obtain disperse information. The querys must be precise on the information you want to retrieve, it is not connected to the chat memory.",
    )

    return tool

def tool_wikipedia():
    retriever = WikipediaRetriever()
    tool = create_retriever_tool(
        retriever,
        "WikipediaRetriever",
        "Returns information from wikipendia of the passed taxon name species or information wanted.",
    )

    return tool


def tool_csv_agent(model):
    csv_agent_with_tool = create_csv_agent(
        llm=model,
        path=["data/obs_tipos.csv", "data/Experts_taxons_information.csv"],
        pandas_kwargs={
            "encoding": "utf-8",
            "delimiter": ","
        },
        prefix="""You are working with 2 pandas dataframes in Python named df1, df2.
                Assume 'df1' and 'df2' are the dataframes provided and are already loaded in the environment.
                If asked or you think is better to generate a map or a plot, you can use the library plotly (for example for a map do plotly.express.scatter_map(df, lat='latitude', lon='longitude', color='subplace',hover_data={{...}}), the color is always the subplace if not specified). Then, save the plot using pio.write_json(fig, './tmp/plot_id.json'), where you will put as id a unique id to identify this plot. Write in the response the file saved.
                1. Data Context:
                - 'df1': Contains registered observations of species from 08-06-2022 till now. The 'df1' have the following features: observed_on,observed_on_time,taxon_name,place,subplace,sector,id_place,latitude,longitude,identifications_count,kingdom,phylum,class,order,family,genus,tipo,Establishment means,Conservation status,taxon_url_information,user_url. 
                    - The origin of the specie (if it is native or has been introduced) is contained in 'Establishment means' and 'Conservation status'.
                    - The observation place is given by the columns 'place', 'subplace', 'sector' and 'id_place'. The 'place' has one of the following values (corresponding on places contained inside the litoral Area Metropolitana de Barcelona): 'Montgat', 'Castelldefels', 'Gavà', 'El Prat de Llobregat', 'Sant Adrià del Besòs', 'Viladecans', 'Barcelona' and 'Badalona'. Each of this places are divided in subplaces, which are the concrete beaches where the specie has been seen, and the subplace is given by the columns 'suplace' (the name of the beach), 'sector' and 'id_place' (identifiers of the beach).
                    - The types of the specie observed are contained in the columns 'tipo' and 'Establishment means'. The 'tipo' column contains as value an array of one or more than one of the following types: 'Invasora', 'Exótica', 'Introduced', 'Protegida', 'Estrictamente Protegida', 'Amenazada', 'En Peligro', 'Explotación reglamentada'. To filter by the type, you can use for example: df1[df1['tipo'].str.contains('Protegida', case=False, na=False)]
                    - The observed date is in 'observed_on' (don't use 'observed_on_time' if not asked for the hour). Ensure proper handling of periods (you need to transform the columns of 'observed_on' and 'observed_on_time' in 'df1' to proper format time).
                - 'df2': Contains the most interesting species in column 'taxon_name'.
                2. Final answer guidance:
                - Distinguish between the concept observation, given by the rows in the dataframe, can exist more than one observation per specie; the concept specie, which name is given by the 'taxon_name' and each observation reffer to a specific specie; and the concept identification, which in one observation can be seen one or more identification of that specie, given by 'identifications_count'.
                - When asked for species, first filter df1 and consider only unique 'taxon_name' values to ensure species are counted, and not observations nor identifications.
                - Do not invent or sample any data or information during the run or in the response, use all the data provided that are already loaded in the environment.
                - If there is no observations or no data of something (except the type and Establishment methods), mention that it is due to a bad registration of the data, and encourage to register more.
                - If asked for a prediction, study all the registered data asked and make a prediction based on that.""",
        #extra_tools=[get_info_good],
        #agent_type=AgentType.OPENAI_FUNCTIONS,
        agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        allow_dangerous_code=True,
        max_iterations=5
    )

    csv_agent_tool = Tool(
        name="CSV_Agent",
        func=lambda input_text: csv_agent_with_tool.invoke(
            [HumanMessage(content=input_text)]
        ),
        description=("Call an Agent that has access to all the observations registered in the project and returns the information in the format asked. Specify the format you want the response: text, list, table, plot, map, etc.. It is not conected to the chat memory, so take into account the anterior messages to detail the query. Is the only way of creating plots or maps.")
    )

    return csv_agent_tool


#Context retrieved from the BioplatgesMet dashboard
def load_csv(file_path: str) -> pd.DataFrame:
    return pd.read_csv(file_path)


def get_message(directory: str, grupo: str, df_obs: pd.DataFrame, days: int) -> str:
    """Get message for a group of species."""
    # Leer el archivo de especies
    df_grupo = load_csv(f"{directory}/data/species/{grupo}.csv")
    species_ids = df_grupo.taxon_id.to_list()

    # Filtrar las observaciones del grupo y ordenar por más recientes
    last_obs = df_obs[df_obs.taxon_id.isin(species_ids)].sort_values(
        by="observed_on", ascending=False
    )

    # Filtrar observaciones de los últimos x días
    fecha_actual = date.today()
    limite = fecha_actual - timedelta(days=days)
    last_week = last_obs[
        last_obs.observed_on >= limite.strftime("%Y-%m-%d")
    ].reset_index(drop=True)

    msg = ""

    # Agrupamos las observaciones por taxon_name y contamos cada grupo
    if len(last_week) > 0:

        grouped = last_week.groupby("taxon_name")

        # Ordenar los grupos por el tamaño de cada grupo, de mayor a menor
        sorted_groups = sorted(grouped, key=lambda x: len(x[1]), reverse=True)

        for taxon_name, group in sorted_groups:
            msg += f"{taxon_name}: {len(group)} observacions\n"

            # Iteramos en cada observación dentro del grupo para agregar detalles
            for _, row in group.iterrows():
                # Construimos fecha con formato DD-MM-YYYY
                fecha = f"{row['observed_on'][-2:]}-{row['observed_on'][-5:-3]}-{row['observed_on'][0:4]}"
                msg += (
                    f"    - Registrat el {fecha} a {row['address']} por *{row['user_login']}*: "
                    f"https://minka-sdg.org/observations/{row['id']}\n"
                )

    else:
        msg = f"Cap observació registrada.\n"
    return msg


def get_members_df(id_project: int) -> pd.DataFrame:
    """Get members of a project."""
    session = requests.Session()
    # Extraemos los ids de las personas que se han unido al proyecto
    total_results = []
    url = f"https://api.minka-sdg.org/v1/projects/{id_project}/members"
    total = session.get(url).json()["total_results"]
    # Iteramos por las páginas de resultados
    for i in range(1, math.ceil(total / 100) + 1):
        url = f"https://api.minka-sdg.org/v1/projects/{id_project}/members?per_page=100&page={i}"
        results = requests.get(url).json()["results"]
        total_results.extend(results)
    df_members = pd.json_normalize(total_results)
    # Eliminamos la columna de conteo total de observaciones, para que no lleve a confusión
    df_members.drop(columns=["observations_count"], inplace=True)
    # Sacamos el número de observaciones de cada persona
    url2 = (
        f"https://api.minka-sdg.org/v1/observations/observers?project_id={id_project}"
    )
    df_observers = pd.json_normalize(session.get(url2).json()["results"])
    df_result = pd.merge(
        df_members,
        df_observers[["user_id", "observation_count"]],
        on="user_id",
        how="left",
    )
    df_result = df_result.sort_values(by="created_at", ascending=False)
    return df_result


def generar_reporte_nuevas_especies(df_sorted: pd.DataFrame, days: int) -> str:
    """
    Genera un reporte de las nuevas especies registradas en los últimos días especificados.

    """

    # Procesar primeras observaciones
    first_observed = (
        df_sorted.drop_duplicates(subset=["taxon_name"], keep="first")
        .sort_values(by=["observed_on"], ascending=False)
        .reset_index(drop=True)
    )

    # Convertir fechas y filtrar por días recientes
    first_observed["observed_on"] = pd.to_datetime(first_observed["observed_on"])
    days_ago = datetime.now() - timedelta(days=days)
    last_days = first_observed[first_observed["observed_on"] >= days_ago]

    # Filtrar taxonomías no deseadas
    last_days = last_days[
        ~last_days.taxon_rank.isin(["kingdom", "phylum", "class"])
    ].reset_index(drop=True)

    # Agrupar por taxón icónico
    grouped_counts = (
        last_days.groupby("iconic_taxon").size().sort_values(ascending=False)
    )

    # Generar reporte
    text_report = ""
    for taxon, count in grouped_counts.items():
        text_report += f"""\n\n {count} {taxon}:\n"""

        # Filtrar observaciones del grupo actual
        group = last_days[last_days["iconic_taxon"] == taxon]
        for _, row in group.iterrows():
            taxon_name = row["taxon_name"]
            observation_id = row["id"]
            address = row["address"]
            text_report += f" - {taxon_name}(https://minka-sdg.org/observations/{observation_id}) a {address}.\n"

    return text_report

def generate_context(period_selected: str):
    grupos = ["amenazadas", "exoticas", "invasoras", "protegidas"]
    main_project = 264

    directory = "iia_bioplatgesmet"
    # Cargar datos y crear primeras observaciones
    df_obs = load_csv(f"{directory}/data/{main_project}_obs.csv")
    df_sorted = df_obs.sort_values(by="observed_on").reset_index(drop=True)
    first_observed = (
        df_sorted.drop_duplicates(subset=["taxon_name"], keep="first")
        .sort_values(by=["observed_on"], ascending=False)
        .reset_index(drop=True)
    )


    periods = {"7 dies": 7, "14 dies": 14, "1 mes": 30, "3 mesos": 90, "6 mesos": 180}
    context = f"**Destacats del projecte BioPlatgesMet dels últims {period_selected}:**\n"


    days = periods[period_selected]

    # Reporte de gatos y ratas: crear listado de especies
    context += f"**Alerta d'espècies monitoritzades:** {get_message(directory, 'alerta', df_obs, days)}\n"


    # Reporte de especies de interés
    context += f"**Espècies d'interès registrades:**\n"
    context += f"Espècies invasores:\n{get_message(directory, 'invasoras', df_obs, days)}"
    context += f"Espècies exòtiques:\n{get_message(directory, 'exoticas', df_obs, days)}"
    context += f"Espècies amenaçades:\n{get_message(directory, 'amenazadas', df_obs, days)}"
    context += f"Espècies protegides:\n{get_message(directory, 'protegidas', df_obs, days)}"

    # Nuevas especies: últimas especies que se han registrado por primera vez
    context += "**Noves espècies registrades:**"
    text_report = generar_reporte_nuevas_especies(df_sorted, days)
    if text_report:
        context += f"{text_report}\n"
    else:
        context += "Cap espècie registrada per primera vegada.\n"

    # Nuevos usuarios: mínimo suben una observación al proyecto, separada por municipio.
    context += "**Participants incorporats al projecte:**\n"
    df_members = get_members_df(264)
    # Miembros creados en los últimos x días
    fecha_actual = date.today()
    limite = fecha_actual - timedelta(days=days)
    df_members.created_at = pd.to_datetime(df_members.created_at).dt.date
    members_last_month = df_members[df_members.created_at > limite]
    # Observaciones de cada nuevo miembro del proyecto si más de 0 observaciones
    for i, row in members_last_month.iterrows():
        # Filtrar observaciones del miembro actual
        user_obs = df_obs[df_obs.user_id == row.user_id]
        if len(user_obs) > 0:
            num_obs = len(user_obs)
            # Usar fillna('') para manejar valores NaN
            species = ", ".join(set(user_obs["taxon_name"].fillna("").to_list()))
            cities = ", ".join(set(user_obs["address"].fillna("").to_list()))
            context += f"{row['user.login']}(https://minka-sdg.org/users/{row['user.login']}): {num_obs} observacion/s a {cities}\n"

    # Mensaje si no hay nuevos usuarios
    if len(members_last_month) == 0:
        context += f"Cap nou participant amb almenys una observació."

    return context


class DashboardInput(BaseModel):
    topic: str = Field(description="The period you want to study, in one of the following formats: ['7 dies', '14 dies', '1 mes', '3 mesos', '6 mesos'].")

@tool(args_schema=DashboardInput)
def tool_dashboard_context(topic: str) -> str:
    """Returns a summary of the last registered information in the project during the period passed (monitorized and interesting species registered and new species and users added in the project)."""
    return generate_context(topic)


import geopandas as gpd
import geopandas as gpd
import plotly.graph_objects as go
from shapely.geometry import Polygon, MultiPolygon
import colorsys

class str2(str):
    def __repr__(self):
        return ''.join(('"', super().__repr__()[1:-1], '"'))

class CustomPythonTool(PythonREPLTool):
    def __init__(self):
        super().__init__()
        #df1 = pd.read_csv('data/obs_tipos.csv')
        #df2 = pd.read_csv('data/Experts_taxons_information.csv')
        gdf_gpkg = gpd.read_file("data/subzonas/poligons_bioplatgesmet.gpkg")

        #gdf_gpkg = gdf_gpkg.rename(columns={
        #    'Name': 'place',
        #    'PLATJA': 'subplace',
        #    'Sectors': 'sector'
        #})

        # Dictionary of name replacements
        #cities = {
        #    "Montgat Platges": "Montgat",
        #    "El Prat": "El Prat de Llobregat",
        #    "Barcelona - Zona Nort": "Barcelona Nord",
        #    "Barcelona - Zona Sud": "Barcelona Sud",
        #    "Badalona nort": "Badalona Nord",
        #    "Badalona sud": "Badalona Sud"
        #}

        # Apply replacements in the 'place' column
        #gdf_gpkg['place'] = gdf_gpkg['place'].replace(cities)
        def get_df1():
            return pd.read_csv('data/obs_tipos.csv')

        def get_df2():
            return pd.read_csv('data/Experts_taxons_information.csv')
        
        def get_figure():
            gdf = gpd.read_file("data/subzonas/poligons_bioplatgesmet.gpkg")
            gdf['geometry'] = gdf['geometry'].simplify(tolerance=0.0001, preserve_topology=True)
            if gdf.crs is None or gdf.crs.to_epsg() != 4326:
                gdf = gdf.to_crs(epsg=4326)

            # Group by PLATJA and Sectors
            grouped = gdf.dissolve(by=['PLATJA', 'Sectors'], as_index=False)
            platjas = gdf['PLATJA'].unique()
            sectors_per_platja = {p: gdf[gdf['PLATJA'] == p]['Sectors'].unique() for p in platjas}

            def hsl_to_rgba(h, s, l, alpha):
                r, g, b = colorsys.hls_to_rgb(h/360, l, s)
                return f"rgba({int(r*255)}, {int(g*255)}, {int(b*255)}, {alpha})"

            figure = go.Figure()

            for _, row in grouped.iterrows():
                geom = row.geometry
                platja = row['PLATJA']
                sector = row['Sectors']

                base_hue = (list(platjas).index(platja) * 360 / len(platjas)) % 360
                sectors = sectors_per_platja[platja]
                sector_index = list(sectors).index(sector)
                n_sectors = len(sectors)

                hue = (base_hue + (sector_index * 360 / (n_sectors * 1.5))) % 360
                saturation = 0.6
                lightness = 0.6

                fill_color = hsl_to_rgba(hue, saturation, lightness, 0.4)
                line_color = hsl_to_rgba(hue, saturation, lightness * 0.6, 1)

                hover_text = f"Subzone: {platja}<br>Sector: {sector}"

                lon_all = []
                lat_all = []
                polygons = geom.geoms if isinstance(geom, MultiPolygon) else [geom]

                for polygon in polygons:
                    lon, lat = polygon.exterior.xy
                    lon_all.extend(list(lon) + [None])
                    lat_all.extend(list(lat) + [None])

                figure.add_trace(go.Scattermapbox(
                    lon=lon_all,
                    lat=lat_all,
                    mode='lines',
                    fill='toself',
                    fillcolor=fill_color,
                    line=dict(color=line_color, width=2),
                    name=f"{platja} - {sector}",
                    hoverinfo='text',
                    text=hover_text,
                    showlegend=True,
                    visible='legendonly'
                ))

            # Calculate map center
            gdf_proj = gdf.to_crs(epsg=25831)
            centroids_proj = gdf_proj.geometry.centroid
            centroids_wgs84 = centroids_proj.to_crs(epsg=4326)
            center_lat = centroids_wgs84.y.mean()
            center_lon = centroids_wgs84.x.mean()

            # Layout for scattermapbox
            figure.update_layout(
                mapbox=dict(
                    style="open-street-map",
                    center={"lat": center_lat, "lon": center_lon},
                    zoom=12
                ),
                margin={"r":0, "t":0, "l":0, "b":0},
                legend=dict(
                    title="Subzones and Sectors",
                    x=0.01,
                    y=0.99,
                    bgcolor="rgba(255,255,255,0.7)"
                )
            )
            return figure

        # Inject your variables into the globals dict of the python REPL environment
        self.python_repl.globals.update({
            'get_df1': get_df1,
            'get_df2': get_df2,
            'get_figure': get_figure,
            'gdf_gpkg': gdf_gpkg,
            'pd': pd,
            'px': px,
            'pio': pio,
            'uuid': uuid,
            'go': go,
        })

        self.description = (
            """You can execute Python code to manipulate data and generate plots. You can call two pandas DataFrames: df1 and df2, doing get_df1() and get_df2(). You can also call get_figure() that returns a figure that is a OpenStreetMap with the subplaces and sectors already delimited.
                You can import the libraries plotly.expres (px), plotly.io (pio), plotly.graph_objects (go), pandas (pd) and uuid.
                To plot on a map, always get the figure with the get_figure() and do figure.add_trace(go.XYZmapbox(...)). Do not create a new fig or go.Figure(). The gdf_gpkg variable is also preloaded and ready to use.
                If you do a plot, do NOT show it and always save it using pio.write_json(figure, f'./tmp/{uuid.uuid4()}'}.json').
                1. Data Context:
                - 'df1': Contains registered observations of species from 08-06-2022 till now. The 'df1' have the following features: observed_on,observed_on_time,taxon_name,place,subplace,sector,id_place,latitude,longitude,identifications_count,kingdom,phylum,class,order,family,genus,tipo,Establishment means,Conservation status,taxon_url_information,user_url. 
                    - The origin of the specie (if it is native or has been introduced) is contained in 'Establishment means' and 'Conservation status'.
                    - The observation place is given by the columns 'place', 'subplace', 'sector' and 'id_place'. The sector have values such as 'SA03', while the id_place have values such as '502'.
                    - The types of the specie observed are contained in the columns 'tipo' and 'Establishment means'. The 'tipo' column contains as value an array of one or more than one type. To filter by the type, you can use for example: df1[df1['tipo'].str.contains('Protegida', case=False, na=False)]
                    - 'observed_on' is the date of observation.
                - 'df2': Contains the most interesting species in column 'taxon_name'.
                2. Final answer guidance:
                - Transform 'observed_on' to datetime format.
                - For obtaining the last observation registered, you should sort by date 'observed_on'.
                - Distinguish observations (rows), species ('taxon_name'), and identifications ('identifications_count').
                - Count species uniquely by filtering unique 'taxon_name'.
                - Do not invent data, use only what is loaded.
                - Mention if data is missing (except the type and Establishment methods) and encourage better and more registration.
                - When doing a map plot, you must not create a new figure using go.Figure(). Call get_figure and do figure.add_trace(...) to add your map trace.
                - If asked for a prediction, study all the registered data asked and make a prediction based on that."""
        )

    def _run(self, code: str) -> str:
        try:
            # Replace pio.write_json(fig, f"...") with file save + print path
            pattern = r'pio\.write_json\s*\(\s*(.+?)\s*,\s*(f)?([\'"])(.+?)\3\s*\)'
            def replacer(match):
                fig = match.group(1).strip()
                is_fstring = match.group(2)
                quote = match.group(3)
                template = match.group(4)

                if is_fstring:
                    return (
                        f'json_path = f{quote}{template}{quote}\n'
                        f'pio.write_json({fig}, json_path)\n'
                        f'output = "File saved in path: " + json_path\n'
                        f'output'
                    )
                else:
                    return match.group(0)

            code = re.sub(pattern, replacer, code)

            targets = [
                "La Pineda de Ca'l Francès",
                "L'Estació",
                "Pont d'en Botifarreta",
                "Ca l'Arana",
                "Platja de l'Estany"
            ]
            pattern = r"'(" + "|".join(re.escape(s) for s in targets) + r")'"

            lines=[]
            # Prepare code execution
            lines = code.split('\n')
            
            #print(lines)
            *body, last = lines if len(lines) > 1 else ([], lines[0])
            exec('\n'.join(body), self.python_repl.globals)

            try:
                result = eval(last, self.python_repl.globals)
            except:
                exec(last, self.python_repl.globals)
                result = None

            if isinstance(result, pd.DataFrame):
                return result.to_json(orient="records")
            elif result is not None:
                return str(result)
            return "Execution completed with no output."

        except Exception as e:
            return f"Error: {e}"
