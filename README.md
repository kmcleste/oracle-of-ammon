# Oracle of Ammon

[![PyPI version shield](https://img.shields.io/pypi/v/oracle-of-ammon?color=blue&style=flat-square)](https://pypi.org/project/oracle-of-ammon/)
[![Python version shield](https://img.shields.io/pypi/pyversions/oracle-of-ammon?color=blue&style=flat-square)](https://pypi.org/project/oracle-of-ammon/)
[![MIT License](https://img.shields.io/github/license/kmcleste/oracle-of-ammon?style=flat-square)](https://github.com/kmcleste/oracle-of-ammon/blob/main/LICENSE)

A simple CLI tool for creating Search APIs.

## Installation

Creating a virtual environment is highly recommended. To do so, run:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Once your environment is active, simply install the package with:

```bash
pip install oracle-of-ammon
```

## Usage

To get started, checkout the help menu:

```bash
oracle-of-ammon --help
```

[![Image of oracle-of-ammon cli help documentaiton](https://github.com/kmcleste/oracle-of-ammon/blob/main/images/oracle-of-ammon-help.gif?raw=true)](https://github.com/faressoft/terminalizer)

Here, you will see we currently have two options: **summon** and **locust**.

### Summon

By default, Summon is configured to initialize an empty search service on port 8000. The API framework used is [FastAPI](https://fastapi.tiangolo.com/) and the underlying search engine is built on [Haystack](https://docs.haystack.deepset.ai/). If you would like to initialize the search service with documents upon startup, provide a filepath with the `--path` option. Once the service has been initialized, you can view the API docs at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs). A static version of the swagger documentation can also be found [here](https://petstore.swagger.io/?url=https://raw.githubusercontent.com/kmcleste/oracle-of-ammon/main/openapi.json#/).

| Option        | Type | Default         | Description                                                                                                                         |
| ------------- | ---- | --------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| --path        | TEXT | None            | Filepath used to pre-index document store.                                                                                          |
| --sheet-name  | TEXT | None            | If using an excel file, select which sheet(s) to load. If none provided, all sheets will be loaded. Expects a comma-separated list. |
| --title       | TEXT | Oracle of Ammon | API documentation title.                                                                                                            |
| --index       | TEXT | document        | Default index name.                                                                                                                 |
| --faq         | BOOL | TRUE            | Selector for content preloaded into document store.                                                                                 |

Supported Filetypes:

- FAQ: CSV, TSV, JSON, XLSX, TXT
- Semantic: TXT

See the [`data`](https://github.com/kmcleste/oracle-of-ammon/tree/main/oracle_of_ammon/data) directory for examples of accepted files.

[![Oracle of Ammon CLI - Summon](https://github.com/kmcleste/oracle-of-ammon/blob/main/images/oracle-of-ammon-summon.gif?raw=true)](https://github.com/faressoft/terminalizer)

### Locust

[Locust](https://locust.io/) is an open source tool for load testing. You're able to swarm your system with millions of simultaneous users -- recording service performance and other metrics. By default, Locust will start on port 8089. To start a new load test, simply enter the number of users you want to simulate, their spawn rate, and the host address to swarm.

[![Image of locust config](https://github.com/kmcleste/oracle-of-ammon/blob/main/images/locust-config.png?raw=true)](https://locust.io)]

## Coming Eventually 👀

- ~~Semantic search~~
- ~~Document search~~
- ~~Document summarization~~
- Document ranking
- ~~Multiple index support~~
- Annotations/Feedback
- Fine tuning
- Additional locust endpoints
- Dynamic Locust config
- Custom pipelines
- Dedicated docs wiki
