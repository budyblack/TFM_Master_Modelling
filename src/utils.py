from dotenv import load_dotenv
import os
from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from pymilvus import MilvusClient
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_milvus import Milvus
from datetime import datetime
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import MessagesState, StateGraph, START, END
import tools
import geopandas as gpd
from shapely.geometry import Point
import csv
import pandas as pd


def openai_model():
    load_dotenv()
    openai_key = os.getenv("OPENAI_KEY")
    os.environ["OPENAI_API_KEY"] = openai_key
    
    return ChatOpenAI(model="gpt-4o-mini", temperature=0)

def milvus_connection_args():
    milvus_port = os.getenv("MILVUS_PORT_19530")
    #CREATE/LOAD VECTORSTORE
    connection_args={
        "uri":f"http://standalone:19530",
        "token":"root:Milvus",
        "db_name":"default"
    }
    return connection_args
    
def Docker_manage_vectorstore():
    #embedding_model = SentenceTransformer("dunzhang/stella_en_1.5B_v5", trust_remote_code=True).cuda()
    embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    pdf_paths = ['data/vectorstore/AMB_available_Information_(HUA).pdf', 'data/vectorstore/AMB_Actuacions_millora_protecció_platges_litoral_nord_metropolità.pdf', 'data/vectorstore/AMB_Dinamica_litoral_Port_Masnou.pdf', 'data/vectorstore/AMB_Dinàmica_litoral_sud_metropolità.pdf', 'data/vectorstore/AMB_Estudi_platges_Nord.pdf', 'data/vectorstore/AMB_Estudis_previs_estabilitza_Gavà_Viladecans.pdf', 'data/vectorstore/AMB_Informe_sobre_la_qualitat_sanitària_de_la_sorra_a_les_platges_Metropolitanes_2020.pdf', 'data/vectorstore/AMB_Servei_platges_metropolitana.pdf', 'data/vectorstore/AMB_Socioeconomic_Impact_of_Barcelona_Metropolitan_Beaches.pdf', 'data/vectorstore/Berna_ApendixI.pdf', 'data/vectorstore/Berna_ApendixII.pdf', 'data/vectorstore/Berna_ApendixIII.pdf', 'data/vectorstore/Berna_ApendixIV.pdf', 'data/vectorstore/BOE_Amenazadas_Barcerlona.pdf', 'data/vectorstore/BOE_ProteccionEspecial_Amenazadas.pdf', 'data/vectorstore/Especies_interés_DirectivaHabitats.pdf', 'data/vectorstore/Invasoras_catalogadas_Catalunya.pdf', 'data/vectorstore/Invasoras_Europa.pdf', 'data/vectorstore/Listado_por_categoria_amenaza.pdf', 'data/vectorstore/Plantas_alóctonas_invasoras_Catalunya.pdf']
    connection_args = milvus_connection_args()
    client = MilvusClient(**connection_args)
    collection_name = "Species_pdf"
    #client.drop_collection(collection_name=collection_name)
    if not client.has_collection(collection_name):
        print("Species_Milvus collection does not exist under the database")
        # Split the pdf data into smaller chunks
        docs = []
        for pdf in pdf_paths:
            loader = PyPDFLoader(pdf)
            doc = loader.load()
            docs.extend(doc)
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks_data = text_splitter.split_documents(docs)

        # Create vectorstore from Milvus
        vectorstore = Milvus.from_documents(
            documents=chunks_data,
            embedding=embedding_model,
            collection_name =collection_name,
            collection_description="Pdf and information about a lot of species.",
            connection_args=connection_args)
        print("Species_Milvus collection is created under the database")
    else:
        #print("Species_Milvus collection already exist")
        vectorstore = Milvus(
            embedding_function=embedding_model,
            collection_name=collection_name,
            connection_args=connection_args)
    
    return vectorstore


def manage_vectorstore():
    #embedding_model = SentenceTransformer("dunzhang/stella_en_1.5B_v5", trust_remote_code=True).cuda()
    embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    pdf_paths = ['data/vectorstore/AMB_available_Information_(HUA).pdf', 'data/vectorstore/AMB_Actuacions_millora_protecció_platges_litoral_nord_metropolità.pdf', 'data/vectorstore/AMB_Dinamica_litoral_Port_Masnou.pdf', 'data/vectorstore/AMB_Dinàmica_litoral_sud_metropolità.pdf', 'data/vectorstore/AMB_Estudi_platges_Nord.pdf', 'data/vectorstore/AMB_Estudis_previs_estabilitza_Gavà_Viladecans.pdf', 'data/vectorstore/AMB_Informe_sobre_la_qualitat_sanitària_de_la_sorra_a_les_platges_Metropolitanes_2020.pdf', 'data/vectorstore/AMB_Servei_platges_metropolitana.pdf', 'data/vectorstore/AMB_Socioeconomic_Impact_of_Barcelona_Metropolitan_Beaches.pdf', 'data/vectorstore/Berna_ApendixI.pdf', 'data/vectorstore/Berna_ApendixII.pdf', 'data/vectorstore/Berna_ApendixIII.pdf', 'data/vectorstore/Berna_ApendixIV.pdf', 'data/vectorstore/BOE_Amenazadas_Barcerlona.pdf', 'data/vectorstore/BOE_ProteccionEspecial_Amenazadas.pdf', 'data/vectorstore/Especies_interés_DirectivaHabitats.pdf', 'data/vectorstore/Invasoras_catalogadas_Catalunya.pdf', 'data/vectorstore/Invasoras_Europa.pdf', 'data/vectorstore/Listado_por_categoria_amenaza.pdf', 'data/vectorstore/Plantas_alóctonas_invasoras_Catalunya.pdf']

    #connection_args = milvus_connection_args()
    connection_args={
        "uri":"http://localhost:19530",
        "token":"root:Milvus",
        "db_name":"default"
    }
    client = MilvusClient(**connection_args)
    collection_name = "Species_pdf"
    #client.drop_collection(collection_name=collection_name)
    if not client.has_collection(collection_name):
        print("Species_Milvus collection does not exist under the database")
        # Split the pdf data into smaller chunks
        docs = []
        for pdf in pdf_paths:
            loader = PyPDFLoader(pdf)
            doc = loader.load()
            docs.extend(doc)
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks_data = text_splitter.split_documents(docs)

        # Create vectorstore from Milvus
        vectorstore = Milvus.from_documents(
            documents=chunks_data,
            embedding=embedding_model,
            collection_name =collection_name,
            collection_description="Pdf and information about a lot of species.",
            connection_args=connection_args)
        print("Species_Milvus collection is created under the database")
    else:
        #print("Species_Milvus collection already exist")
        vectorstore = Milvus(
            embedding_function=embedding_model,
            collection_name=collection_name,
            connection_args=connection_args)
    
    return vectorstore

def general_context():
    with open("data/types_context.txt", "r") as file:
        type_context = file.read()
    with open("data/dunas_context.txt", "r") as file:
        dunas_context = file.read()
    #places = "{'Gavà':{'Platja de Gavà':[['GV02'-'GV23',461-482]]},'Viladecans':{'La Murtra':[['VC01'-'VC02',483-484]],'La Pineda Viladecans':[['VC03'-'VC12',485-494]],'La Pineda de Ca'l Francès':[['VC13'-'VC14',495-496]],'El Remolar (Viladecans)':[['VC15'-'VC17',497-499]],'Platja de l'Estany':[['GV24',508]]},'Sant Adrià del Besós':{'Fòrum':[['SA01'-'SA03',500-501]],'Parc del Litoral':[['SA04'-'SA08',503-507]],'Mora':[['BD01',454]]},'Castelldefels':{'Baixador':[['CF01'-'CF02',509-510],['CF03'-'CF04',515-516],['CF05'-'CF06',518-519],['CF07'-'CF09',523-525],['CF10',527],['CF11'-'CF13',529-531],['CF14'-'CF15',535-536],['CF16'-'CF17',538-539]],'La Pineda Castelldefels':[['CF39',514],['CF38',517],['CF37',520],['CF36',521],['CF40',526],['CF35',522],['CF34',528],['CF33',532],['CF32',533],['CF31',534],['CF30',545],['CF29',547],['CF24',548],['CF25',549],['CF28',550],['CF26',551],['CF27',552]],'Lluminetes':[['CF18'-'CF22',540-544],['CF23',546]],'Platja de Gavà':[['GV01',460]]},'Montgat':{'Cala Taps':[['MG01',553]],'Platja de les Roques':[['MG02'-'MG03',554-555]],'Les Barques':[['MG04'-'MG08',556-560]],'Can Tano':[['MG09'-'MG10',561-562]],'Montsolís':[['MG11'-'MG15',563-567]],'Els Toldos':[['MG16'-'MG17',568-569]]},'Badalona Sud':{'Mora':[['BD02'-'BD04',455-457]]},'Badalona Nord':{'Coco':[['BD05',458],['BD06',459]],'Pont del Petroli':[['BD07'-'BD09',511-513],['BD10'-'BD11',570-571]],'L'Estació':[['BD12'-'BD15',572-575]],'Patins a Vela':[['BD16',576]],'Pescadors':[['BD17'-'BD22',577-582]],'Pont d'en Botifarreta':[['BD23'-'BD28',583-588]],'Cristall':[['BD29'-'BD31',589-591]],'Barca Maria':[['BD32'-'BD38',592-598]]},'El Prat de Llobregat':{'El Remolar (El Prat)':[['PR01',599]],'La Roberta':[['PR02'-'PR12',600-610]],'Can Camins':[['PR13'-'PR23',611-621]],'La Ricarda':[['PR26',624]],'Platja Naturista':[['PR24'-'PR25',622-623]],'Ca l'Arana':[['PR27',625]]},'Barcelona Sud':{'Sant Sebastià':[['BC01'-'BC06',626-631]],'Sant Miquel':[['BC07'-'BC10',632-635]],'Barceloneta':[['BC11'-'BC13',636-638]],'Somorrostro':[['BC14'-'BC18',639-643]]},'Barcelona Nord':{'Nova Icària':[['BC19'-'BC23',644-648]],'Bogatell':[['BC24',649],['BC25',665],['BC26'-'BC28',650-652]],'Mar Bella':[['BC29'-'BC34',653-658]],'Nova Mar Bella':[['BC35'-'BC38',659-662]],'Llevant':[['BC39'-'BC40',663-664],['BC41'-'BC42',666-667],['BC43'-'BC44',668-669]]}}"
    places = "{'Gavà': {'Platja de Gavà'}, 'Viladecans': {'La Pineda de Ca\\'l Francès', 'La Murtra', 'La Pineda Viladecans', 'Platja de l\\'Estany', 'El Remolar (Viladecans)'}, 'Sant Adrià del Besós': {'Parc del Litoral', 'Mora', 'Fòrum'}, 'Castelldefels': {'Platja de Gavà', 'Baixador', 'La Pineda Castelldefels', 'Lluminetes'}, 'Montgat': {'Can Tano', 'Els Toldos', 'Les Barques', 'Montsolís', 'Platja de les Roques', 'Cala Taps'}, 'Badalona Sud': {'Mora'}, 'Badalona Nort': {'Pont del Petroli', 'Barca Maria', 'Coco', 'Patins a Vela', 'L\\'Estació', 'Pont d\\'en Botifarreta', 'Cristall', 'Pescadors'}, 'El Prat de Llobregat': {'La Ricarda', 'La Roberta', 'Can Camins', 'El Remolar (El Prat)', 'Platja Naturista', 'Ca l\\'Arana'}, 'Barcelona Sud': {'Somorrostro', 'Sant Sebastià', 'Barceloneta', 'Sant Miquel'}, 'Barcelona Nord': {'Bogatell', 'Nova Icària', 'Llevant', 'Mar Bella', 'Nova Mar Bella'} }"
    return f"El proyecto de donde extraes información de las especies se llama BiplatgesMet. Este proyecto registra observaciones de especies en el litoral del Area Metropolitana de Barcelona (AMB), concretamente de las playas y zonas dunares, y no recoge datos de especies observadas en lugares alejados de estos entornos litorales. La falta de observaciones o de información en las observaciones registradas se debe a que la gente no registra o lo hace de manera incompleta, anima a que registren más y aporten al proyecto. Los nombres científicos deben ir en cursiva. Diferencia entre especie, observacion y identificaciones en cada observacion. Los lugares de estudio por el momento son los siguientes (en el formato: {'{'}'place':{'{'}'subplace'{'}'}{'}'}): {places}.\nSi obtienes como información gran cantidad de especies distintas, esto no significa que haya gran diversidad en esa zona. Además, hay ciertos tipos de especies que son buenas para el medio y otras que son malas, según el tipo de especie que sea. Los nombres exactos de los tipos de especies que hay registros son: 'Invasora', 'Exótica', 'Introduced', 'Protegida', 'Estrictamente Protegida', 'Amenazada', 'En Peligro', 'Explotación reglamentada'. En un dataframe se indica también que especies son nativas y cuales introduced, y el place de esto. Las definiciones de los tipos de especies son:\n{type_context}\nContexto sobre las dunas:\n{dunas_context}"


#Langgrpah
def graph_app(model, tools):
    #DEFINE MODEL WITH TOOLS
    tool_node = ToolNode(tools)
    bound_model = model.bind_tools(tools)
    memory = MemorySaver()

    #CREATE LANGGRAPH
    def should_continue(state: MessagesState):
        """Return the next node to execute."""
        last_message = state["messages"][-1]
        # If there is no function call, then we finish
        if not last_message.tool_calls:
            return END
        return "action"


    def call_model(state: MessagesState):
        response = bound_model.invoke(state["messages"])
        # We return a list, because this will get added to the existing list
        return {"messages": response}

    def call_tool_context(state: MessagesState):
        # Call the context tool explicitly
        context_response = general_context()
        system_message = SystemMessage(content=context_response)
        
        return {
            "messages": state["messages"] + [system_message],
            "tool_context_called": True
        }
    
    def initial_decision(state: MessagesState):
        if not state.get("tool_context_called", False):
            return "context"
        return "agent"

    workflow = StateGraph(MessagesState)

    workflow.add_node("agent", call_model)
    workflow.add_node("action", tool_node)
    workflow.add_node("context", call_tool_context)

    workflow.add_conditional_edges(START, initial_decision, ["context", "agent"])

    workflow.add_conditional_edges(
        "agent",
        should_continue,
        ["action", END],
    )

    workflow.add_edge("action", "agent") #After calling a tool, the agent is called next
    workflow.add_edge("context", "agent")

    app = workflow.compile(checkpointer=memory)

    return app


def create_app():
    model = openai_model()
    vectorstore = Docker_manage_vectorstore()
    retriever = tools.tool_retriever(vectorstore)
    wikipedia_context = tools.tool_wikipedia()
    python_tool = tools.CustomPythonTool()
    app = graph_app(model, [python_tool, retriever, tools.tool_dashboard_context, wikipedia_context]) #tools.tool_get_info

    return app

def create_app_summary():
    model = openai_model()
    vectorstore = Docker_manage_vectorstore()
    retriever = tools.tool_retriever(vectorstore)
    wikipedia_context = tools.tool_wikipedia()
    python_tool = tools.CustomPythonTool()
    app = graph_app(model, [python_tool, retriever, tools.tool_dashboard_context, wikipedia_context])

    return app

def generate_summary(app, period, language="Español"):
    with open("data/Documents.txt", "r", encoding="utf-8") as file:
        document_data = file.read()
    with open("data/types_context.txt", "r") as file:
        type_context = file.read()
    with open("data/dunas_context.txt", "r") as file:
        dunas_context = file.read()
    
    config = {"configurable": {"thread_id": "1"}}

    input_message = [SystemMessage(content=f"""Eres una IA que responde en {language} de la forma más completa y detallada posible, sin asumir ni inventar nada. La respuesta final representa un resumen de lo más relevante, en el período requerido por el usuario, acerca de un proyecto que se llama BioplatgesMet (si el periodo requerido no es el estudiado finalmente, menciona el porque). Este proyecto registra observaciones de especies en el litoral del Area Metropolitana de Barcelona (AMB), concretamente de las playas y zonas dunares, y no recoge datos de especies observadas en lugares alejados de estos entornos litorales. 
                                            En casao que la información que encuentres indique que no hay observaciones o no hay observaciones relevantes en el periodo requerido, mencionalo. La respuesta puede ser tan larga como sea necesaria, no hay límite de palabras. Devuelve la información en el mejor formato que creas conveniente (parágrafo, listado, tabla, etc.).
                                            En caso que obtengas muchas especies de interés, no digas que hay gran diversidad. Además, hay ciertos tipos de especies que son buenas para el medio y otras que son malas (explicado en el contexto general). Especifica cuantas observaciones hay de especies invasoras, exoticas, amenazadas y protegidas, si no hay de algun tipo, mencionalo también. Los nombres científicos deben ir en cursiva. Diferencia bien entre especies y observaciones (equivale a una o varias observaciones de una especie). El hecho de que no haya registro de especies de interés se debe en gran parte a que la gente no está registrando, por lo que deberías animar a que registren y se impliquen en el proyecto.
                                            Utiliza la functión python_tool para obtener todas las observaciones de especies relevantes en el período requerido (especies de interes en el df2)(incluye el número de observaciones para cada especie observada, el tipo de especie que es y donde se han observado). Utiliza también la función 'VectorstoreRetriever' para obtener toda la información posible que se encuentra en el vectorstore (realiza tantas consultas como necesites).
                                            Referencia la información siempre que sea posible, si sale del vectorstore referencia el contenido con el nombre del documento."""),
                    HumanMessage(content=f"Obtén las observaciones más relevantes entre el {period}."
                                f"Teniendo en cuenta la información que hay dentro del vectorstore que se adjunta más abajo, busca informació relevante acerca de los lugares de avistamiento, de las especies de más interés y toda información que creas que pueda aportar a la respuesta final."
                                f"Para la respuesta, devuelve las observaciones y la información más relevante del período requerido teniendo en cuenta el contexto, las observaciones que obtengas, los lugares de avistamiento, el tipo de especies observadas en cada lugar, y toda la información obtenida que creas relevante."
                                f"Información que se encuentra en el vectorstore:\n{document_data}")
                    ]
    final_response = None
    for event in app.stream({"messages": input_message}, config, stream_mode="values"):
        final_response = event["messages"][-1].content

    input_message = [SystemMessage(content=f"Eres una IA que mejora la respuesta anterior de la forma mas completa y detallada posible en {language}, sin asumir ni inventar nada. La respuesta final representa un resumen de lo más relevante, en el período requerido por el usuario, acerca de un proyecto que se llama BioplatgesMet (si el periodo requerido no es el estudiado finalmente, menciona el porque). Este proyecto registra observaciones de especies en el litoral del Area Metropolitana de Barcelona (AMB), concretamente de las playas y zonas dunares, y no recoge datos de especies observadas en lugares alejados de estos entornos litorales."
                                            f"Debe incluir toda la información del mensaje anterior devuelto por el asistente, más toda la información nueva relevante que obtengas. La respuesta puede ser tan larga como sea necesaria, no hay límite de palabras. Agrega la información en el mejor formato que creas conveniente (parágrafo, listado, tabla, etc.)"
                                            f"En caso que obtengas muchas especies de interés, no digas que hay gran diversidad. Especifica cuantas observaciones hay de especies invasoras, exoticas, amenazadas y protegidas, si no hay de algun tipo, mencionalo también. Los nombres científicos deben ir en cursiva. Diferencia bien entre especies y observaciones (equivale a una o varias observaciones de una especie). El hecho de que no haya registro de especies de interés se debe en gran parte a que la gente no está registrando, por lo que deberías animar a que registren y se impliquen en el proyecto."
                                            f"Utiliza la función 'CSV_Agent', el cual llama a un agente de IA que tiene acceso a un dataframe con todas las observaciones a lo largo del tiempo (van des del 2022-6-01 hasta hoy, {datetime.today().date().strftime("%Y-%m-%d")}). Este agente NO tiene acceso al historial de este chat. Realizar varias consultas simples y concretas (es posible que el nombre de la especie, lugar o tipo que le des al Agent no sea exactamente el que se encuentra en el dataframe, en la consulta menciona que sea un nombre similar al que das). Puedes llamar al agente tantas veces como sea necesario para completar al máximo la respuesta. No busques información en el período de interés del reporte, dado que ya tienes esta información en el historial del chat."
                                            f"En la respuesta debes intentar responder preguntas como por ejemplo: ¿En que playas hay menos observaciones y a dónde debo orientar los esfuerzos de muestreo? ¿Alguna de las especies interesantes observadas en el período de estudio han sufrido una ampliación del rango de distribución (se encuentran en nuevas localizaciones que no se habían localizado antes)?"
                                            f"Al final de la respuesta, agrega preguntas que puedan desencadenar en una conversación."),
                    HumanMessage(content=f"Teniendo en cuenta la respuesta anterior y las especies relevantes observadas en el período requerido (entre el {period}, si no hay, mencionalo y di que estas estudiando otro periodo), agrega a la respuesta un analisis de datos teniendo en cuenta todas las observaciones registradas a lo largo del tiempo (estudiando todos los registros y/o los meses anteriores) para mejorar la respuesta anterior."
                                        #f"Llama al agente para realizar distintos estudios y obtener tendencias de las especies de interés observadas (especifícale cuales han sido), información acerca de los lugares de avistamiento (especifícale cuales han sido), los tipos de especies que más se observan, y otros estudios que creas que pueden aportar a mejorar la respuesta anterior, teniendo en cuenta la información disponible de las observaciones registradas (features del dataframe)."
                                        f"La respuesta debe incorporar toda la información de la respuesta anterior y todo lo que descubras ahora, de modo que quede un buen resumen de los hechos mas relevantes en el periodo de estudio."
                                        f"Agrega posibles preguntas que puedan desencadenar en conversaciones.")]
    for event in app.stream({"messages": input_message}, config, stream_mode="values"):
        final_response = event["messages"][-1].content
    if final_response:
        return final_response
    else:
        return "No se ha podido realizar el resumen en el período requerido."


def get_sector(latitude, longitude, geo_file="data/subzonas/poligons_bioplatgesmet.gpkg", csv_file="data/subzonas/poligonos_BioPlatgesMet.csv"):
    """
    Returns the sector (subzone) that contains the given latitude and longitude.

    Parameters:
    latitude (float): Latitude of the point.
    longitude (float): Longitude of the point.
    geo_file (str): Path to the GeoPackage file containing subzone polygons. Default is "data/subzonas/poligons_bioplatgesmet.gpkg".

    Returns:
    str: Sector name or a message indicating the point is not in any subzone.
    """

    sector_to_id = {}
    with open(csv_file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sector_to_id[row['Sectors']] = row['id_place']

    # Step 1: Load the .gpkg file
    subzones = gpd.read_file(geo_file)

    # Step 2: Create a GeoDataFrame for the point
    point = gpd.GeoDataFrame(
        geometry=[Point(longitude, latitude)],
        crs=subzones.crs  # Important! Must match the CRS of your subzones
    )

    # Step 3: Perform spatial join to find subzone
    result = gpd.sjoin(point, subzones, how="left", predicate="within")

    # Step 4: Check if point is within a subzone and return the sector name
    if result.empty or pd.isna(result.iloc[0]['Sectors']):
        return None, None, None
    else:
        sector = result.iloc[0]['Sectors']
        return sector, result.iloc[0].get('PLATJA', None), sector_to_id.get(sector, None)
