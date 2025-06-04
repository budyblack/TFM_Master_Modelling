#!/usr/bin/env python
import streamlit_utils
import streamlit as st
import gettext
from streamlit_cookies_controller import CookieController
import time


st.set_page_config(layout="wide", page_icon="img/minka-logo.png", page_title="Chatbot MINKA")

#if not st.experimental_user.is_logged_in:
#    st.login()
#else:
controller = CookieController()
if controller.get("terms_of_use") is not True:
    time.sleep(1)
    streamlit_utils.terms_of_use(controller)
else:
    def sidebar():
        global _, selected_language_name, language
        
        
        # Define a variable sidebar width as a percentage
        sidebar_width = 15  # Set percentage (e.g., 20% of screen width)

        # Inject custom CSS
        st.markdown(
            f"""
            <style>
                [data-testid="stSidebar"] {{
                    width: {sidebar_width}vw !important;
                }}
            </style>
            """,
            unsafe_allow_html=True,
        )
        # Wrapping elements in a container with the CSS class
        with st.sidebar:
            streamlit_utils.sidebar_style()
            language_options = {_('Spanish'): 'esp', _('English'): 'en', _('Catalan'): 'cat'}
            selected_language_name = st.selectbox(_('Language'), list(language_options.keys()))
            language = language_options[selected_language_name]
            try:
                localizator = gettext.translation('base', localedir='locales', languages=[language])
                localizator.install()
                _ = localizator.gettext 
            except:
                pass
                
            st.markdown(f"""
                <div class="centered" width=15%>
                    <div style="text-align: center;">
                        <a href="https://bioplatgesmet.institutmetropoli.cat/" target="_blank" class="clickable-image">
                            <img src="data:image/png;base64,{streamlit_utils.get_image_base64('./img/logo-BioplatgesMet.png')}" alt="BioPlatgesMet Project" width=30%>
                        </a>
                    </div>
                </div> 
                """, 
                unsafe_allow_html=True
            )
            
    #          style="margin-bottom: 100px;">
            st.button(_("How it works?"), type="primary", on_click=streamlit_utils.button_information, args=(_,))
            st.button(_("New conversation"), on_click=streamlit_utils.reset_conversation, args=(controller,))
            st.button(_("Last week summary"), on_click=streamlit_utils.week_summary)
            st.button(_("Last month summary"), on_click=streamlit_utils.month_summary)
            st.button(_("Specific period summary"), on_click=streamlit_utils.period_summary)
            #st.button(_("Log out"), type="tertiary", on_click=st.logout)
            st.markdown("</div>", unsafe_allow_html=True)
            
            
    
    _ = gettext.gettext

    streamlit_utils.setup(controller)

    # Start of the main set of streamlit commands


    sidebar()

    main = st.container()
    with main:
        streamlit_utils.main_style()
        caption = st.container()
        chat_area = st.container()
        input_chat = st.container()
        footer = st.container()

    with caption:
        st.title(_("💬 Virtual Lifeguard: Species and Beaches Explorer of Catalonia"))
        st.caption(_("🚀 A chatbot specialized in species observed on the beaches of Catalonia, part of the MINKA project named BioplatgesMet. The chatbot can answer any question or provide a summary for a specific period via buttons in the left sidebar."))

    with chat_area:
        for message in st.session_state.messages:
            if message["role"] == "user":
                st.chat_message("user").markdown(message["content"])
            else:
                streamlit_utils.process_response(controller, message["content"])
            #with st.chat_message(message["role"]):
            #    st.markdown(message["content"])

        streamlit_utils.buttons_print(controller, language, _)

    with input_chat:
        prompt = st.chat_input(key="Chat")

    with chat_area:
        streamlit_utils.query(controller=controller, prompt=prompt, language=selected_language_name)

    with footer:
        # Footer Section
        footer_css = f"""
        <footer class="footer">
            <div class="footer-container">
                <img src="data:image/png;base64,{streamlit_utils.get_image_base64('./img/footer.png')}" alt="Logos">
            </div>
        </footer>
        """
        st.markdown(footer_css, unsafe_allow_html=True)
