# Test task: Application to get suggestions for suitable meeting times

## 1. Input

[Original requirements](info/assignment_2.0.pdf)

###1.1 Description

The mega-corporation Buffel & Båg AB has a custom-built system for handling
meetings which has been around since the beginning of time and which is now
deemed too difficult to use. Since management doesn’t know how important the
system is they have invested far too little resources in the upgrade project,
and have decided to hire a single poor contractor (guess who) to solve the most
important problems in almost no time. At regular intervals, all information is
dumped from the existing system to a text file that can be downloaded from a
publicly available API (see link further down). An excerpt from the file can
look like this:

```
170378154979885419149243073079764064027;Colin Gomez
170378154979885419149243073079764064027;2/18/2014 10:30:00 AM;2/18/2014 11:00:00 AM;485D2AEB9DBE3...
139016136604805407078985976850150049467;Minnie Callahan
139016136604805407078985976850150049467;2/19/2014 10:30:00 AM;2/19/2014 1:00:00 PM;C165039FC08AB4...
```

As it seems, the file has lines in two different formats where the first one
contains employee id and display name and the second format has information on
the time slots where the employee is busy and therefore not available for
meetings. Unfortunately, everyone who knew something about the old system has
fled the company a long time ago. Questions regarding how the system should
work can however be answered.

**Requirements:** \
As a first step, management has asked for an application implemented in the
browser. The application should provide a UI that makes it possible for users
to get suggestions for suitable meeting times based on the following
parameters:

• participants (employee ids), one or multiple \
• desired meeting length (minutes) \
• earliest and latest requested meeting date and time • office hours (e.g. 08-17)

**The following can be good to know:**

• In the file, all times are stated in UTC. To keep things simple, don’t bother
with implementing support for local date-times unless your solution gives you
that for free \
• People work every day of the week at Buffel & Båg AB \
• Due to the crappy state of the existing system the file may contain some
irregularities, these should be ignored \
• The system only handles meetings that start every full and half hour, e.g.
08.00, 08.30, 09.00, etc. \
• Make the solution work in Chrome, you can ignore all other browsers 

**Your solution will be evaluated on aspects like:**

• The structure and the quality of the code \
• How easy it is to understand \
• How you verify that the solution works

Keep in mind that a perfect solution is not the primary goal of the assignment,
but rather to see how you interpret and work on the problem and the code you
write. Link to the file:

https://builds.lundalogik.com/api/v1/builds/freebusy/versions/1.0.0/file

**When handing in the solution:**

• Please include a README explaining how to run the solution. \
• Please do not upload your result to a public site. 

## 2. Output

### 2.1 Interpretation

1) Check by a set period of time provided public API ('
   people-time-allocation-api') which is not required auth and in case of any
   sync errors (like changed API contract, auth needed, server offline, etc) -
   notify stakeholders.

2) Perform ETL ops like: a) download (sync) txt data b) pars with filtering and
   add (associate) generated user names to id(s) c) load to e.g.
   ORM (ODM) models d) populate models to DB e) add migration(s) mechanism for
   DB schema changes. NOTES:

- during the sync in case downloaded thx has the same checksum skip it, in case
  of not just merge new portion of data with existing one and load to DB using
  the stapes provided above
- suppose to use SQL (ORM) and NOSQL (ODM) version with switcher by virt env

3) Add BE and FE which are cover such scenarios. \
User A open UI of web app and wanna get suggestion (possible time slot) to meet
with User B, User C and put the following data to get required info:
- participants name(s) which HUMAN readable version:)
- desired meeting length (minutes) to talk with both of them Meaning time
should be free for User B and User C f3) earliest and latest requested meeting
date and time: Start and End of required meeting (within the one working day)
- office hours (e.g. 08-17) Office hours of User A

**NOTES:**
1) 170378154979885419149243073079764064027;2/18/2014 10:30:00 AM;2/18/2014 11:
   00:00 AM;485D2AEB9DBE3... Meaning UserN is busy from 2/18/2014 10:30:00 AM
   till 2/18/2014 11:00:00 AM.
2) Focus on BE, FE - in case of time capacity.
3) Lint checks and Unit tests (classes, endpoints) are required.
Integration, E2E tests - in case of time capacity.
4) Add docker compose version with DB delivery (SQLite or MySQL). 
NoSQL version - in case of time capacity.

###2.2 Description

1) Dependencies \
1.1) Run via docker containers:
    - Install [docker](https://docs.docker.com/get-docker/)
      and [Docker Compose](https://docs.docker.com/compose/install/)
    - Build and run docker containers:
    ```sh
    docker-compose -f docker-compose.yml build
    docker-compose -f docker-compose.yml up
    sudo docker exec –it meet-app zsh
    ```
    - Pull and run docker containers:
    ```sh
    docker pull nestu/meet-app:core
    # https://docs.docker.com/engine/reference/run/
    ```
    NOTE: Public image is not created due to task limitation (private mode)

1.2) Run locally:

- OS: Better Linux base but can be used other (even Win Linux virtual
  subsystem)
- Install [Pyton >= 3.10](https://www.python.org/downloads/) with pip
- Install Python dependency management and packaging tool [poetry](https://python-poetry.org/docs/)
- Install dependencies to .venv dir of the project
```sh
poetry config virtualenvs.in-project true
poetry shell
poetry install
```

1.3) Access to application:
- Via browser http://localhost:8080/ \
NOTE: FE (UI) is not mandatory, will be added based on the time capacity.
- Via API requests: \
a) [Fetch API of Chrome](https://jsonplaceholder.typicode.com/) e.g.:
   ```js
   // GET
   fetch('https://jsonplaceholder.typicode.com/posts/1')
       .then(res => res.json())
       .then(console.log)
   
   // POST
   fetch('https://jsonplaceholder.typicode.com/posts', {
       method: 'POST',
       body: JSON.stringify({
           title: 'foo',
           body: 'bar',
           userId: 1
       }),
       headers: {
           'Content-type': 'application/json; charset=UTF-8'
       }
   })
       .then(res => res.json())
       .then(console.log)
   ```
   b) Postman app prepared [collection](https://learning.postman.com/docs/collaborating-in-postman/sharing/)
   
   [Download](tests/data/postman_collection.json), import and [run](https://learning.postman.com/docs/running-collections/working-with-data-files/) the collection.

## 3. TODO
- Add tests/data/postman_collection.json - actual data
- After project finish add docker and local run details to md file.
- For nor app load data from 3rd party API without storing to the file
  system,and pars load data to DB. Improve by adding async version, errors
  checks of API and parsing etc and format of data, versioning of downloaded
  data for future (like dumps) for investigation purposes, data merge logic.
- Rewrite interpretation

## 4. Examples
1) `syncs` table with examples:
<p align="center">
<img src="assets/sync-1.png" alt="`syncs` table with examples" width="100%">
</p>