import utils
import streamlit as st
from langchain_core.messages import HumanMessage, SystemMessage
import base64
from langchain.schema import HumanMessage as HMessage, AIMessage
import streamlit_db_utils
from datetime import datetime, timedelta
from streamlit_modal import Modal
import re
import os
import plotly.io as pio


image_paths = [
    "./img/logo-iiia.png",
    "./img/logo-CSIC.png",
    "./img/logo-GUARDEN.png"
]

def sidebar_style():
    st.markdown(
        """
        <style>
            .centered {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
            }
            .stButton > button {
                width: 100%;
                margin-top: 10px;
            }
            .clickable-image img:hover {
                cursor: pointer;
                transform: scale(1.1);
            }
            
            /*Information hover tool*/
            .tooltip {
                position: relative;
                display: inline-block;
            }
            .tooltip .tooltiptext {
                visibility: hidden;
                width: 200px;
                background-color: grey;
                color: black;
                text-align: center;
                border-radius: 6px;
                padding: 5px 0;
                position: absolute;
                z-index: 1;
            }
            .tooltip:hover .tooltiptext {
                visibility: visible;
            }
            
            button[kind="primary"] {
                border-color: blue;
                background: #00BFFF;
                color: white;
            }
            button[kind="primary"]:hover {
                background: #00FFFF;
                color: black;
            }
            button[kind="tertiary"] {
                border-color: red;
                background: #FF6347;
                color: white;
            }
            button[kind="tertiary"]:hover {
                background: #D2B48C;
                color: black;
            }
        </style>
        """,
        unsafe_allow_html=True
    )

def main_style():
    st.markdown("""
        <style>
        .stChatInput {
            position: fixed;
            bottom: 13% !important;
            width: auto;
            z-index: 1001 !important;
        }

        a:link, a:visited {
            color: blue;
            background-color: transparent;
            text-decoration: underline;
        }

        a:hover, a:active {
            color: red;
            background-color: transparent;
            text-decoration: underline;
        }
        
        .footer {
            position: fixed;
            bottom: 0 !important;
            left: 0;
            width: 100%;
            height: 13%;
            max-height: 13%;
            color: black;
            background-color: white;
            z-index: 1000;
            padding: 2px 0;
            justify-content: center;
            align-items: center;
        }
        .footer-container {
            width: 100%;
            height: 100%;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
        }
        .footer-container img {
            height: auto;
            width: auto;
        }
        </style>""", unsafe_allow_html=True
    )


def setup(controller):
    app = utils.create_app()

    if "app" not in st.session_state:
        st.session_state["app"] = app
    if "messages" not in st.session_state:
        streamlit_db_utils.setup_db(controller)
    if "summary_button" not in st.session_state:
        st.session_state["summary_button"] = ""
    if "prompt_button" not in st.session_state:
        st.session_state["prompt_button"] = ""
    if "specific_period" not in st.session_state:
        st.session_state["specific_period"] = ""
    if "first_query" not in st.session_state:
        st.session_state["first_query"] = 0
    if "num_images" not in st.session_state:
        st.session_state["num_images"] = 0

def reset_conversation(controller):
    if "messages" in st.session_state:
        del st.session_state["messages"]
    if "chat_message" in st.session_state:
        del st.session_state["chat_message"]
    if "app" in st.session_state:
        del st.session_state["app"]
    if "summary_button" in st.session_state:
        st.session_state["summary_button"] = ""
    if "prompt_button" in st.session_state:
        st.session_state["prompt_button"] = ""
    if "specific_period" in st.session_state:
        st.session_state["specific_period"] = ""
    if "first_query" in st.session_state:
        st.session_state["first_query"] = 0
    if "id" in st.session_state:
        del st.session_state["id"]
    if controller.get("id"):
        controller.remove("id")
    if controller.get("images"):
        for image in controller.get("images"):
            if os.path.exists(image):
                os.remove(image)
        controller.remove("images")
    if "num_images" in st.session_state:
        del st.session_state["num_images"]
    #if controller.get("terms_of_use"):
    #    controller.remove("terms_of_use")

def process_response(controller, final_response):
    image_placeholder = "{st.image("
    plotly_placeholder = "{st.plotly_chart("
    segments = re.split(r"(\{st\.(?:image|plotly_chart)\('.*?'\)\})", final_response)
    
    with st.chat_message("assistant"):
        for segment in segments:
            if segment.startswith(image_placeholder):
                image_path_match = re.search(r"st\.image\('([^']+)'\)\}", segment)
                if image_path_match:
                    image_path = image_path_match.group(1)
                    if os.path.exists(image_path):
                        st.image(image_path)  # Render the image separately
                        if controller.get("images"):
                            images_list = controller.get("images")
                            images_list.append(image_path)
                            controller.set("images", images_list)
                        else:
                            controller.set("images", [image_path])
                    else:
                        st.markdown("Error in generating the image, ask me to regenerate it.")
            elif segment.startswith(plotly_placeholder):
                plotly_path_match = re.search(r"st\.plotly_chart\('([^']+)'\)\}", segment)
                if plotly_path_match:
                    plotly_path = plotly_path_match.group(1)
                    if os.path.exists(plotly_path):
                        fig = pio.read_json(plotly_path)
                        st.plotly_chart(fig, use_container_width=True, key=f"{st.session_state["num_images"]}")  # Render the Plotly figure separately
                        st.session_state["num_images"] += 1
                        if controller.get("images"):
                            images_list = controller.get("images")
                            images_list.append(plotly_path)
                            controller.set("images", images_list)
                            
                        else:
                            controller.set("images", [plotly_path])
                    else:
                        st.markdown("Error in loading the Plotly chart, ask me to regenerate it.")
            else:
                st.markdown(segment)  # Render text normally

def normal_query(controller, prompt, language):
    config = {"configurable": {"thread_id": "1"}}

    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").markdown(prompt)
    streamlit_db_utils.add_message(cookie_id=st.session_state["id"], message=prompt, origin=1)
    
    final_response = None
    if st.session_state["first_query"] == 0:
        input_message = [SystemMessage(content=f"Ten en cuenta todo el historial de la conversación. Si una peticion ya ha sido respondida anteriormente en el chat, no regeneres la respuesta llamando a funciones y reponde directamente. Responde a la pregunta lo mas detallado posible en {language}. Si no se ha respondido la pregunta, utiliza la python_tool siempre que puedas en vez de las otras funciones, además es la única manera de guardar un plot. Las otras funciones solo úsalas en casos específicos: usa 'tool_dashboard_context' cuando te pidan un resúmen del proyecto, nuevas especies o nuevos usuarios/miembros registrados en el proyecto; usa 'VectorstoreRetriever' y 'WikipediaRetriever' para obtener información de taxons o de temas de biodiversidad. Los nombres científicos deben ir en cursiva. Diferencia entre especie, observacion y identificaciones en cada observacion. Devuelve la información en el mejor formato que creas conveniente (parágrafo,listado,tabla,plot,mapa,etc.). Si generas un plot o un json, no hagas plt.show, solo guardalo (no menciones que lo guardas) y insertalo en el texto asi, sino no se visualizará: {'{'}st.plotly_chart('./tmp/json_name.json'){'}'}."),
                        HumanMessage(content=f"{prompt}")]
        input_state = {
            "messages": input_message,
            "tool_context_called": False
        }
        st.session_state["first_query"] = 1
    else:
        input_message = [SystemMessage(content=f"Ten en cuenta todo el historial de la conversación. Si una peticion ya ha sido respondida anteriormente en el chat, no regeneres la respuesta llamando a funciones y reponde directamente. Responde a la pregunta lo mas detallado posible en {language}. Prioriza la python_tool antes que las otras funciones. Si generas un plot o un json, no hagas plt.show, solo guardalo (no menciones que lo guardas) y insertalo en el texto asi, sino no se visualizará: {'{'}st.plotly_chart('./tmp/json_name.json'){'}'}."),
                        HumanMessage(content=f"{prompt}")]
        input_state = {
            "messages": input_message,
            "tool_context_called": True
        }
    
    for event in st.session_state["app"].stream(input_state, config, stream_mode="values"):
        #event["messages"][-1].pretty_print()
        final_response = event["messages"][-1].content
        #tokens = event["messages"][-1].response_metadata
    
    if final_response is not None:
        st.session_state.messages.append({"role": "assistant", "content": final_response})
        process_response(controller, final_response)
        #st.write(tokens)
        streamlit_db_utils.add_message(cookie_id=st.session_state["id"], message=final_response, origin=0)


def week_summary():
    st.session_state["prompt_button"] = 'Last week summary'

def month_summary():
    st.session_state["prompt_button"] = 'Last month summary'

def period_summary():
    st.session_state["specific_period"] = "Period"

def buttons_print(controller, language, _):
    if st.session_state["specific_period"] != "" and st.session_state["specific_period"] != "None":
        content = _("Write the period you want to study (example: 2024-11-20 y 2024-12-01). Make sure to specifically include the 'y' and use the correct date format:")
        st.session_state.messages.append({"role": "assistant", "content": content})
        st.chat_message("assistant").markdown(content)
        streamlit_db_utils.add_message(cookie_id=st.session_state["id"], message=content, origin=0)
        st.session_state["specific_period"] = "None"

    if st.session_state["prompt_button"] != '':
        if st.session_state["prompt_button"] == 'Last week summary':
            with open(f"summaries/week_summary_{language}.txt", "r") as file:
                summary = file.read()
        if st.session_state["prompt_button"] == 'Last month summary':
            with open(f"summaries/month_summary_{language}.txt", "r") as file:
                summary = file.read()
        content = _(st.session_state["prompt_button"])
        st.session_state.messages.append({"role": "user", "content": content})
        st.chat_message("user").markdown(content)
        streamlit_db_utils.add_message(cookie_id=st.session_state["id"], message=content, origin=1)
        st.session_state.messages.append({"role": "assistant", "content": summary})
        process_response(controller, summary)
        streamlit_db_utils.add_message(cookie_id=st.session_state["id"], message=summary, origin=0)

        new_messages = [
            HMessage(content=_(st.session_state["prompt_button"])),
            AIMessage(content=summary)
        ]
        config = {"configurable": {"thread_id": "1"}}
        st.session_state["app"].update_state(config, {"messages": new_messages})

        st.session_state["prompt_button"] = ''


def query(controller, prompt=None, language="English"):
    if prompt:
        if st.session_state["specific_period"] != "":
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.chat_message("user").markdown(prompt)
            streamlit_db_utils.add_message(cookie_id=st.session_state["id"], message=prompt, origin=1)
            response = utils.generate_summary(st.session_state["app"], prompt, language)
            #st.session_state["prompt_button"] = prompt
            st.session_state.messages.append({"role": "assistant", "content": response})
            process_response(controller, response)
            streamlit_db_utils.add_message(cookie_id=st.session_state["id"], message=response, origin=0)
            st.session_state["specific_period"] = ""

        else:
            normal_query(controller, prompt, language)


def get_image_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')


def button_information(_):

    modal = Modal(key="Info",title=_("Information about the tool"), max_width=750)
    with modal.container():
        st.markdown(_("<h2>Buttons Explained:</h2><ul><li><b>Language:</b> Changes the interface and chatbot response language. However, it does not affect messages already sent.</li><li><b>New conversation:</b> Restarts the chat.</li><li><b>Last week summary</b> and <b>Last month summary:</b> Generate a pre-compiled summary for the selected period, considering all registered observations.</li><li><b>Specific period summary:</b> Allows you to enter the desired period in the chat using the specified format. The chatbot then generates the summary from scratch, which may take some time.</li></ul><h2>Chatbot Terms</h2><ul><li><b>Data collection:</b> No personal data, user authentication, tracking, or individual storage—only anonymized conversation data is used for research purposes.</li><li><b>User agreement:</b> Users should avoid sharing personal data, acknowledge that responses are generated by an AI in development, and verify information when necessary.</li><li><b>User contribution:</b> Users are encouraged to engage naturally, provide feedback on chatbot responses, suggest improvements, and refrain from sharing personal data.</li><li><b>User rights:</b> Free access is provided without requiring an account or tracking. Users can end sessions anytime and submit anonymous feedback.</li><li><b>Disclaimer:</b> The chatbot does not guarantee the accuracy of responses. Users should verify information through official sources.</li></ul>"), unsafe_allow_html=True)


def decline():
    st.warning("You need to accept the terms to proceed.")

def accept(controller):
    expiry_date = datetime.now() + timedelta(days=7)
    controller.set("terms_of_use", True, expires=expiry_date)

def terms_of_use(controller):
    #terms = st.container()
    #with terms:
    st.markdown(f"""
        <style>
            :root {{
                --bg-clr: #6c00f9;
                --white: #fff;
                --primary-text-clr: #212121;
                --secondary-text-clr: #8c8c8c;
                --bg-hvr: #5803c7;
            }}
            
            @media (prefers-color-scheme: dark) {{
                :root {{
                    --bg-clr: #4500b5;
                    --white: #121212;
                    --primary-text-clr: #e0e0e0;
                    --secondary-text-clr: #b3b3b3;
                    --bg-hvr: #370093;
                }}
            }}
            
            body {{
                background: var(--white);
                color: var(--primary-text-clr);
            }}
            
            .flex_align_justify {{
                display: flex;
                align-items: center;
                justify-content: center;
            }}
            
            .flex_align {{
                display: flex;
                align-items: center;
            }}
            
            .wrapper {{
                min-height: 60vh;
                padding: 0 10px 20px;
                display: flex;
                justify-content: center;
                align-items: center;
            }}
            
            .terms_service {{
                width: 90%;
                max-width: 600px;
                height: auto;
                background: var(--white);
                color: var(--primary-text-clr);
                border-radius: 10px;
                box-shadow: 0px 0px 3px rgba(0, 0, 0, 0.15);
                padding: 20px;
            }}
            
            .terms_service .tc_item {{
                padding: 20px;
            }}
            
            .terms_service .tc_head {{
                box-shadow: 0 1px 2px rgba(0, 0, 0, 0.15);
                padding: 15px;
                text-align: center;
                background: var(--white);
                color: var(--primary-text-clr);
            }}
            
            .terms_service .tc_head .icon {{
                width: 50px;
                height: 50px;
                background: var(--bg-clr);
                margin: 0 auto 10px;
                border-radius: 50%;
                font-size: 18px;
                color: var(--white);
                display: flex;
                align-items: center;
                justify-content: center;
            }}
            
            .terms_service .tc_head .icon img {{
                width: 100%;
                height: 100%;
                border-radius: 50%;
            }}
            
            .terms_service .tc_body {{
                max-height: 50vh;
                overflow-y: auto;
                padding-right: 10px;
            }}
            
            .terms_service .tc_body ol li {{
                margin-bottom: 15px;
            }}
            
            .terms_service .tc_body ol li h3 {{
                margin-bottom: 5px;
            }}
            
            .terms_service .tc_foot {{
                display: flex;
                justify-content: space-between;
                padding: 10px;
            }}
            
            .terms_service .tc_foot button {{
                flex: 1;
                border: 1px solid var(--bg-clr);
                padding: 10px;
                border-radius: 5px;
                cursor: pointer;
                transition: all 0.3s ease;
            }}
            
            button[kind="secondary"] {{
                background: var(--white);
                color: var(--bg-clr);
                margin-right: 10px;
            }}
            
            button[kind="primary"] {{
                background: var(--bg-clr);
                color: var(--white);
            }}
            
            button[kind="secondary"]:hover {{
                background: var(--bg-clr);
                color: var(--white);
            }}
            
            button[kind="primary"]:hover {{
                background: var(--bg-hvr);
            }}
            
            @media (max-width: 768px) {{
                .terms_service {{
                    width: 95%;
                    padding: 15px;
                }}
                
                .terms_service .tc_item {{
                    padding: 10px;
                }}
                
                .terms_service .tc_head .icon {{
                    width: 40px;
                    height: 40px;
                }}
            }}
            
            @media (max-width: 480px) {{
                .terms_service {{
                    width: 100%;
                    border-radius: 0;
                    box-shadow: none;
                }}
            }}
        </style>
                
        <div class="wrapper flex_align_justify">
        <div class="terms_service">
            <div class="tc_item tc_head">
                <div class="icon flex_align_justify">
                    <img src="data:image/png;base64,{get_image_base64('./img/terms_service.png')}" alt="Terms Service Icon">
                </div>
                <div class="text">
                <h2>Terms of Use - Guardacostas Virtual Chatbot</h2>
                <p>Last updated on February 6 2025</p>
                </div>
            </div>
            <div class="tc_item tc_body">
                <ol>
                <li>
                    <h3>What is Guardacostas Virtual?</h3>
                    <p>Guardacostas Virtual is a chatbot developed as part of the GUARDEN research project, funded by the European Union. This tool has been created by the Artificial Intelligence Research Institute of ICM CSIC (IIIA-CSIC) to support the management of urban beaches in Barcelona through interaction with citizens and beach users.</p>
                </li>
                <li>
                    <h3>What is BioPlatgesMet?</h3>
                    <p>BioPlatgesMet is a citizen science initiative focused on monitoring and protecting biodiversity in urban beach and dune ecosystems in the Barcelona metropolitan area. The project is organized by the Metropolitan Area of Barcelona (AMB) and supported by the EMBIMOS research group of the Institute of Marine Sciences (ICM-CSIC). Through collaboration with citizens, researchers, and local authorities, BioPlatgesMet gathers valuable data about coastal ecosystems using the MINKA citizen science platform. This information is then published through GBIF for broader research use.</p>
                    <p>The initiative operates across several municipalities, including Barcelona, Castelldefels, Gavà, and Viladecans, engaging nature observers, neighbors, students, and anyone interested in urban beaches.</p>
                </li>
                <li>
                    <h3>How is this chatbot used for research?</h3>
                    <p>Guardacostas Virtual is part of a research project studying how artificial intelligence can support citizen science and urban beach management. When you use this chatbot, you're contributing to research about human-AI interaction and environmental management. No personal data is collected during your interactions with the chatbot - we're interested in understanding the types of questions asked and how we can improve the chatbot's responses to better serve the community.</p>
                </li>
                <li>
                    <h3>What information is collected when I use the chatbot?</h3>
                    <p>We prioritize your privacy and research integrity. The chatbot:</p>
                    <ol>
                    <li>
                        <p>Does not collect any personal data</p>
                    </li>
                    <li>
                        <p>Does not require user authentication</p>
                    </li>
                    <li>
                        <p>Does not use any tracking mechanisms</p>
                    </li>
                    <li>
                        <p>Does not store individual user information</p>
                    </li>
                    </ol>
                    <p>The only information we retain is the content of conversations with the chatbot, which is used solely for research purposes to improve its functionality and understanding of user needs.</p>
                </li>
                <li>
                    <h3>What should I know before using the chatbot?</h3>
                    <p>By using Guardacostas Virtual, you agree that:</p>
                    <ol>
                    <li>
                        <p>You will not share any personal information during your conversations with the chatbot</p>
                    </li>
                    <li>
                        <p>The conversations may be analyzed as part of our research to improve the system</p>
                    </li>
                    <li>
                        <p>You are interacting with an AI system in development, and responses should be verified against official sources when necessary</p>
                    </li>
                    <li>
                        <p>Your feedback helps us refine and improve the chatbot's capabilities</p>
                    </li>
                    </ol>
                </li>
                <li>
                    <h3>How can I contribute to the research?</h3>
                    <p>The best way to contribute is to:</p>
                    <ol>
                    <li>
                        <p>Use the chatbot naturally to ask questions about Barcelona's urban beaches</p>
                    </li>
                    <li>
                        <p>Provide feedback about the accuracy and helpfulness of responses</p>
                    </li>
                    <li>
                        <p>Help us identify areas where the chatbot could be more useful</p>
                    </li>
                    <li>
                        <p>Avoid sharing any personal information in your questions or feedback</p>
                    </li>
                    </ol>
                </li>
                <li>
                    <h3>What are my rights as a user?</h3>
                    <p>As this is a research tool that doesn't collect personal data, you can use the chatbot freely without concerns about data privacy. You can:</p>
                    <ol>
                    <li>
                        <p>Access the chatbot without creating an account</p>
                    </li>
                    <li>
                        <p>Use the service without being tracked</p>
                    </li>
                    <li>
                        <p>End your session at any time</p>
                    </li>
                    <li>
                        <p>Provide feedback anonymously</p>
                    </li>
                    </ol>
                </li>
                <li>
                    <h3>Who owns and maintains the chatbot?</h3>
                    <p>Guardacostas Virtual is owned and maintained by the Institut d'Investigació en Intel·ligència Artificial del ICM CSIC (IIIA-CSIC). It operates as part of the GUARDEN research project.</p>
                </li>
                <li>
                    <h3>How can I contact the research team?</h3>
                    <p>For questions about the research project or to provide feedback, you can contact:</p>
                    <p>Jesús email?</p>
                </li>
                <li>
                    <h3>Disclaimer</h3>
                    <p>Guardacostas Virtual is provided as a research tool without any warranties, express or implied. While we strive for accuracy, users should verify critical information through official channels. The chatbot's responses are based on available data and should be used as a supplementary resource rather than the sole source of information for decision-making.</p>
                </li>
                </ol>
            </div>
        </div>
        </div>""", unsafe_allow_html=True
    )

    col1, col2, col3, col4 = st.columns([2, 1, 1, 2])
    with col2:
        st.button("Decline", on_click=decline)
    with col3:
        st.button("Accept", type="primary", on_click=accept, args=(controller,))