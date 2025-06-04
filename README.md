# MinkaAnalyst

This repository contains the code for [BPMChat](https://bpmchat.iiia.es) (among other developments of the GUARDEN project).


## How to setup a working copy 

Currently only Ubuntu 24.04 (native and thorough WSL) have been tested for development. Any other platform is untested and likely to have issues arising.

1. To setup your working copy do:

    ```
    $ git clone https://github.com/IIIA-ML/MinkaAnalyst.git
    $ cd MinkaAnalyst
    $ cp env.example .env
    # Edit the file called .env and complete the OPENAI_KEY. If required Do also complete the SACO variables.
    $ source bin/init-local.sh
    ```
2. [Install docker engine](https://docs.docker.com/engine/install/) in your machine.
3. Get the latest vector store:
    The vector store can be downloaded from saco.csic by executing:

    ```
    docker compose up etcd minio standalone -d
    bin/restore_milvus.sh
    docker compose down
    ```

    Otherwise, it will be created from scratch when running the program.
4. Update species:

    ```
    bin/init-import.py
    ```
5. Bring the system up 

    ```
    docker compose build
    docker compose up -d
    ```
    This will automatically execute the streamlit chatbot. It can will be accessible at [http://localhost:13000](http://localhost:13000).
    Any change int the code, will automatically change the app.

## Branching model

Currently we are working with just two branches, master and develop. Work always at the develop branch (or, even better fork your own branch from develop before starting working and merge it with developed once finished). *Please be extremely careful before pushing anything to master*. Pushing to master will automatically update the contents of [BPMChat](https://bpmchat.iiia.es).

## Additional information

### Vector Store back up 
If the vector store is updated, you can back it up with
`bin/backup_milvus.sh`

### Weekly summary
If you want to post the Weekly Summary in Discourse, edit the file `bin/update_summaries_and_discourse_post.py` and uncomment the lines 14 and 15. 
You will need to add as environmental variables the `DISCOURSE_API_KEY` and the `DISCOURSE_API_USERNAME`.
