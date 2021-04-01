# WDRAX
The Web Data Research Assistant eXtender (v2) is a tool wrapped around the Twitter API. Currently, it implements two 
functions; Firstly the original tool hydrates tweet IDs using the twarc package. Secondly, there is a search function 
using search_tweets-v2 that generates an API call to either the 'recent' or 'all' endpoints.
The 'eXtender' part is currently disabled on this branch but active on main.

### Configuration

On fist login to WDRAX, you will need to provide your Twitter API credentials and select relevant endpoints.
The required options are `TWITTER_CONSUMER_KEY`, `TWITTER_CONSUMER_SECRET`, `TWITTER_ACCESS_TOKEN` and 
`TWITTER_ACCESS_TOKEN_SECRET` - for guidance on getting a Twitter API key see the 
[Twitter API docs](https://developer.twitter.com/en/docs/twitter-api/getting-started/guide).

## Development Actions

### Creating migrations
The postgres db can be run with localhost enabled using the alternative docker-compose file docker-compose-db-local.yml
Then change the settings.ini file by switching to DATABASE_URL=postgresql://wdrax:wdrax@localhost:5432/db.postgres
Then run:
```
$ export FLASK_APP="wdra_extender/app.py"
$ python -m flask db migrate
$ python -m flask db upgrade
```
Commit the new migrations change the settings back and its good to go.

### Updating Python Dependencies

The `requirements.txt` and `requirements-devel.txt` files for this project have been generated using [pip-tools](https://github.com/jazzband/pip-tools).
To update pinned dependency versions:

```
$ python3 -m venv venv
$ source venv/bin/activate
$ pip-compile --upgrade requirements.in
$ pip-compile --upgrade requirements-devel.in
$ pip install -r requirements.txt
```

### Running the server

#### Locally using Docker

Docker with `docker-compose` (easy install via pip3) allows us to split the application 
into multiple independent components and run these together.
There are 4 images and 5 containers that run:
Databases
  - redis, PostgreSQL, and neo4j 
Webserver
  - wdrax
Job Runner
  - runner
Since this is how we'll be running in production, it can be useful to test this locally as well.

This method embeds the configuration in a `docker-compose.yml` file 
 - copy the `docker-compose.yml.j2` template from roles/wdrax/templates/
 - fill in the missing values
 - rename to (`docker-compose.yml`) and move into the main directory

Run:
```
$ docker-compose up --build
```

WDRAX will be accessible on localhost using port 8000. Navigate to [http://localhost:8000/wdrax/]


### Remotely using Ansible (which then runs Docker)

Ansible configures the remote servers
Edit the inventory file and then set the hosts in the playbook
With the correct ssh keys and git authentication this can be done from a blank server
Run:
```
ansible-playbook /mnt/hgfs/wdra-extender/playbook.yml -i /mnt/hgfs/wdra-extender/inventory.yml -kK
```