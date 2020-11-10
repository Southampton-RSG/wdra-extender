# WDRAX
Web Data Research Assistant Extender


## About WDRAX

The WDRA Extender service uses the Twitter API to fill out data captured from the WDRA (Web Data Research Assistant) Chrome extension.

The WDRA browser plugin allows researchers to capture Twitter data without any programming expertise.
Its key value is in being able to capture data from historic searches, which is impossible with the Twitter API and any services built on the API.
The weakness of WebDataRA is that it is limited to data that is visible in the Web page.
This complementary web service allows you to backfill the WebDataRA spreadsheet with extra information obtained from the Twitter API or with analysis that is difficult to produce in a browser.
It is anticipated that more powerful text and network analysis will be provided to facilitate more sophisticated computation social science research methodologies.


## Development Actions

### Running a Local Version

To run a local version of WDRAX for testing purposes:


#### Using Flask Directly

```
$ python3 -m venv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
$ export FLASK_APP="wdra_extender/app.py"
$ python -m flask db upgrade
$ python -m flask run
```

#### Using Docker

Copy the `docker-compose.yml.example` file and fill in your Twitter API credentials, then:

```
$ docker-compose up --build
```


### Updating Python Dependencies

The `requirements.txt` and `requirements-devel.txt` files for this project have been generated using [pip-tools](https://github.com/jazzband/pip-tools).
To update pinned dependency versions:

```
$ pip-compile --upgrade requirements.in
$ pip-compile --upgrade requirements-devel.in
```
