#!/bin/bash

. bin/init-local.sh docker

./bin/setup-cron.sh

# Start the discourse.py script in the background
#bin/update_summaries_and_discourse_post.py &
bin/update_summaries.sh &

#Create Streamlit database (if not created already)
bin/create_db.py

# Start the Streamlit app
#streamlit run ./bin/stream_chatbot_scientific.py --server.port=8080 --server.address=0.0.0.0
streamlit run ./bin/stream_chatbot_scientific.py --server.port=8080 --server.address=0.0.0.0 --server.fileWatcherType none