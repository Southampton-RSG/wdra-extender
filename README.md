# WDRAX
Web Data Research Assistant Extender


## About WDRAX

The WDRA browser plugin allows researchers to capture Twitter data without any programming expertise.
The weakness of WebDataRA is that it is limited to data that is visible in the Web page.
This complementary web service allows you to backfill the WebDataRA spreadsheet with extra information obtained from the
Twitter API or with analysis that is difficult to produce in a browser.
It is anticipated that more powerful text and network analysis will be provided to facilitate more sophisticated
computation social science research methodologies.


## Development Actions

### Configuration

Regardless of the method you use to run WDRAX, you will need to provide some configuration parameters.
The required options are `TWITTER_CONSUMER_KEY`, `TWITTER_CONSUMER_SECRET`, `TWITTER_ACCESS_TOKEN` and 
`TWITTER_ACCESS_TOKEN_SECRET` - for guidance on getting a Twitter API key see the 
[Twitter API docs](https://developer.twitter.com/en/docs/twitter-api/getting-started/guide).

In addition to these required parameters, 
there are a number of optional parameters which can be seen in `wdra_extender/settings.py`.

The method used to get these configuration values into WDRAX is different in each deployment method 
and is described in the relevant section below.

### Running a Local Version

To run a local version of WDRAX for testing purposes there are a number of options described below.

#### Using Flask Directly

For development and initial testing, it's useful to run WDRAX with a minimum of additional infrastructure.
Flask provides a minimal web server which we can use for this.

This method uses a `settings.ini` file to provide configuration - copy the `settings.ini.j2` template and fill in the missing values.

First a redis (https://redis.io/download) data store is required. Install and launch for your system. (MacOS use brew or source)

```
$ python3 -m venv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
$ celery -A wdra_extender.app:celery worker --loglevel=info --concurrency=1
$ export FLASK_APP="wdra_extender/app.py"
$ python -m flask db upgrade
$ python -m flask run
```

WDRAX will be accessible on localhost using port 8000.

#### Using Docker

Docker with `docker-compose` (easy install via pip3) allows us to split the application into multiple independent components and run these together.
Since this is how we'll be running in production, it can be useful to test this locally as well.

This method embeds the configuration in a `docker-compose.yml` file - copy the `docker-compose.yml.j2` template and fill in the missing values.

```
$ docker-compose up --build
```

WDRAX will be accessible on localhost using port 8000.


#### Using Vagrant

Vagrant is a wrapper around a virtualisation provider (e.g. VirtualBox) which can automatically configure and provision a virtual machine (VM) from the command line.
After creating a new VM, Vagrant will automatically run the Ansible provisioning scripts for a production deployment.
This method gives us as close as possible to a production deployment.

This method uses a `vagrant_extra_vars.yml.j2` file to provide configuration - copy the `vagrant_extra_vars.yml.j2` template and fill in the missing values.

```
$ vagrant up
```

WDRAX will be accessible on localhost using port 8888.


### Updating Python Dependencies

The `requirements.txt` and `requirements-devel.txt` files for this project have been generated using [pip-tools](https://github.com/jazzband/pip-tools).
To update pinned dependency versions:

```
$ pip-compile --upgrade requirements.in
$ pip-compile --upgrade requirements-devel.in
```
