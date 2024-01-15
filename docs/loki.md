# Loki logging

Loki is a log indexing system built around the idea of only indexing the
metadata of the logs. It can also added as a source in Grafana, and so is often
described as "like Prometheus, but for logs".

## Uploading logs to Loki

Logs can be uploaded to Loki via two methods:

- Directly from the [Docker](#logs-from-docker) container's logs.
- As part of the [`workflow run`](#logs-from-workflow-run) CLI command.

### Logs from Docker

To upload logs from a Docker container requires configuring the Docker logs to
use the Loki driver. The driver should be installed on all available nodes - if
you believe that this is not the case, please contact a sysadmin. There are two
ways that you might want to configure Docker to use Loki: a stand-alone
container, or service within a compose file.

1. Stand-alone container:
      To use Loki in a stand-alone container, the `--log-driver` flag must be
      set to `loki` and the `--log-opt` flag must be used.

      ``` sh
      docker run --log-driver=loki \
      --log-opt loki-url="http://frb-vsop:3100/loki/api/v1/push" \
      --log-opt loki-retries=5 \
      --log-opt loki-batch-size=400 \
      --log-opt loki-external-labels="site=chime" \
      grafana/grafana
      ```

2. Service within a compose file:
      To use Loki in a compose file, the `logging` mapping must be defined.
      Below is an example which must be placed on the same indentation level as `image`.

      ``` yaml
      logging: &loki-logging
        driver: loki
        options:
          loki-url: "http://frb-vsop:3100/loki/api/v1/push"
          loki-retries: "5"
          loki-batch-size: "102400"  # 100 KB
          loki-external-labels: "site=chime"
      ```

      Here, the `&loki-logging` tag allows this configuration to be used throughout
      the compose file. The tag can be used for another service using:

      ``` yaml
      logging:
        <<: *loki-logging
      ```

!!! info "Note: Correct URL for site must be given!"
    In the examples above, the URL is correctly given for Chime site. However, this
    will change for the other sites. See below for the correct URLs for each site.

    ``` yaml
    loki_urls:
      aro: "http://localhost:3100/loki/api/v1/push"
      canfar: "https://frb.chimenet.ca/loki/loki/api/v1/push"
      cedar: "http://localhost:3100/loki/api/v1/push"
      chime: "http://frb-vsop:3100/loki/api/v1/push"
      gbo: "http://aux:3100/loki/api/v1/push"
      hco: "http://aux:3100/loki/api/v1/push"
      kko: "http://aux:3100/loki/api/v1/push"
      local: "https://frb.chimenet.ca/loki/loki/api/v1/push"
    ```

### Logs from `workflow run`

There is no set-up required to upload logs to Loki when using `workflow run`. As
`workflow` always attempts to upload logs by default; it knows which Loki URL to
submit the logs to based on the `--site` flag. However, this can be overridden by
using the `--loki-url` flag. See below for an example of the output from `workflow
run` with the Loki lines highlighted. In this case, it didn't contact the Loki server
as the Loki URL was overridden and set to 'http://not-real-url'.

``` txt hl_lines="11 20"
26 Apr 2023 14:18:46 EDT INFO      chimefrb.workflow Workflow Run CLI
26 Apr 2023 14:18:46 EDT INFO      chimefrb.workflow Bucket   : test
26 Apr 2023 14:18:46 EDT INFO      chimefrb.workflow Function : None
26 Apr 2023 14:18:46 EDT INFO      chimefrb.workflow Command  : None
26 Apr 2023 14:18:46 EDT INFO      chimefrb.workflow Mode     : Dynamic
26 Apr 2023 14:18:46 EDT INFO      chimefrb.workflow Lifetime : infinite
26 Apr 2023 14:18:46 EDT INFO      chimefrb.workflow Sleep    : 1s
26 Apr 2023 14:18:46 EDT INFO      chimefrb.workflow Work Site: local
26 Apr 2023 14:18:46 EDT INFO      chimefrb.workflow Log Level: INFO
26 Apr 2023 14:18:46 EDT INFO      chimefrb.workflow Base URL : https://frb.chimenet.ca/buckets
26 Apr 2023 14:18:46 EDT INFO      chimefrb.workflow Loki URL : http://not-real-url
26 Apr 2023 14:18:46 EDT INFO      chimefrb.workflow Prod URL :
                                  https://frb.chimenet.ca/frb-master/v1/events/query-file?filename=
26 Apr 2023 14:18:46 EDT INFO      chimefrb.workflow Execution Environment
26 Apr 2023 14:18:46 EDT INFO      chimefrb.workflow Operating System: Darwin
26 Apr 2023 14:18:46 EDT INFO      chimefrb.workflow Python Version  : 3.11.2
26 Apr 2023 14:18:46 EDT INFO      chimefrb.workflow Python Compiler : Clang 14.0.0 (clang-1400.0.29.202)
26 Apr 2023 14:18:46 EDT INFO      chimefrb.workflow Virtualization  : None
26 Apr 2023 14:18:46 EDT INFO      chimefrb.workflow Configuration Checks
26 Apr 2023 14:18:46 EDT INFO      chimefrb.workflow Loki Logs: ❌
26 Apr 2023 14:18:46 EDT INFO      chimefrb.workflow Base URL : ✅
26 Apr 2023 14:18:46 EDT INFO      chimefrb.workflow Starting Workflow Lifecycle
```

## Querying logs

Logs submitted to Loki can be queried via Grafana's Explore page. At Chime this is
found at <https://grafana.chimenet.ca/explore>. At the top of this page, to the right
of "Explore" there is a drop down menu, this is where the source is selected. Loki
sources are indicated by orange/yellow 'L'-shaped icon, in the list there should be
one named "CHIME/FRB Logs", select this source if it is not already selected.

Loki queries are made using LogQL, a PromQL-inspired query language. Here a basic
introduction will be given, if you wish to know more about anything discussed here
please refer to the [LogQL documentation](https://grafana.com/docs/loki/latest/logql/).

LogQL has two types of queries:

- Log queries: contents of logs.
- Metric queries: values based on query results.

### Log queries

LogQL queries all have a log stream selector. These are placed within curly braces
`{}`. The streams that are available depends on the method that was used the upload
the logs to Loki.

#### Log streams

| Streams       | Method: Docker   | Method: Workflow |
|---------------|------------------|------------------|
| site          | :material-check: | :material-check: |
| host          | :material-check: | :material-close: |
| pipeline      | :material-close: | :material-check: |
| logger        | :material-close: | :material-check: |
| severity      | :material-check: | :material-check: |
| source        | :material-check: | :material-close: |
| swarm_service | :material-check: | :material-close: |
| swarm_stack   | :material-check: | :material-close: |

The stream selector chooses the log streams that will be included in the query.
Eg.: `{site="chime"}` would show all logs from Chime site and
`{swarm_stack="datatrail"}` would show all logs from the Datatrail stack.

##### Log stream operators

However, `=` is not the only stream operator that can be used. There are also the
following operators:

- `=`: Equal.
- `!=`: Not equal.
- `=~`: Regex match.
- `!~`: Not regex match.

##### Multiple log stream operators

Additionally, multiple stream operations can be combined together:
`{swarm_stack!="datatrail", site="chime"}`. This would show all logs from Chime,
but not those belonging to the Datatrail stack.

#### Log pipeline

Log streams can be followed by a _log pipeline_, which is a set of expressions
that can be linked together and applied to the log stream to filter it. The expressions
are applied in order from left to right.

##### Line filter expression

Line filter expressions have a filter operator followed by text or a regex. The operators
are:

- `|=`: Equal.
- `!=`: Not equal.
- `|~`: Regex match.
- `!~`: Not regex match.

Examples:

- `|= "foo"` would show all logs that contain `foo` in the log line.
- `!=bar` would exclude all logs that contain `bar` in the log line.
- ```|~ `error=\w+` ``` would show all logs that contain `error`
  followed by one or more words in the log line.

##### Parser expression and Label filter expressions

Please refer to the Loki documentation for these.

- [Label filter expression](https://grafana.com/docs/loki/latest/logql/log_queries/#label-filter-expression)
- [Parser expression](https://grafana.com/docs/loki/latest/logql/log_queries/#parser-expression)

### Metric queries

Metric queries apply functions to log query results, in order to create metrics from
logs. Examples of uses of Metrics queries include calculating the rate of error
messages, or finding the top N log sources with the most errors over a specified
time period.

#### Log range aggregation

These are queries followed by a duration, the duration can come after either the
log stream or pipeline. Durations are numbers followed by one of the following units:

- `ms`: milliseconds
- `s`: seconds
- `m`: minutes
- `h`: hours
- `d`: days, assuming a day has always 24h
- `w`: weeks, assuming a week has always 7d
- `y`: years, assuming a year has always 365d

The functions that are available are:

- `rate(log-range)`: calculates the number of entries per second.
- `count_over_time(log-range)`: counts the entries for each log stream within the
    given range.
- `bytes_rate(log-range)`: calculates the number of bytes per second for each stream.
- `bytes_over_time(log-range)`: counts the amount of bytes used by each log
    stream for a given range.
- `absent_over_time(log-range)`: returns an empty vector if the range vector passed
    to it has any elements and a 1-element vector with the value 1 if the range vector
    passed to it has no elements. (absent_over_time is useful for alerting on when no
    time series and logs stream exist for label combination for a certain amount of time.)

!!! example "Example: Range aggregation query"
    ```
    rate({site="chime"}[5m])
    ```

There also exist operators that can be used to aggregate the metrics by log streams, resulting
in fewer metrics. The operators are:

- `sum`: Calculate sum over labels.
- `avg`: Calculate the average over labels.
- `min`: Select minimum over labels.
- `max`: Select maximum over labels.
- `stddev`: Calculate the population standard deviation over labels.
- `stdvar`: Calculate the population standard variance over labels.
- `count`: Count number of elements in the vector.
- `topk`: Select largest k elements by sample value.
- `bottomk`: Select smallest k elements by sample value.
- `sort`: returns vector elements sorted by their sample values, in ascending order.
- `sort_desc`: Same as sort, but sorts in descending order.

!!! example "Example: Range aggregation query"
    ```
    sum(rate({site="chime"}[5m]))
    ```
    or
    ```
    sum by (host) (rate({site="chime"}[5m]))
    ```
