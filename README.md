# ATLoad
ATLoad is a Python library to build workload generators for benchmarks. It
enables the generation of reproducible bursty workloads that are representative
of online services.

ATLoad uses an open-loop system: requests are made according to the workload
specification, without waiting for responses to previous requests. Also, it uses
a Poisson distribution to generate think times (i.e., intervals between
consecutive requests made by a single client).

Furthermore, ATLoad enables control over:
- *workload volume* by defining the average number of requests to be made per
second (throughput).
- *workload burstiness* by defining periods with increased throughput.
- *workload characteristic* by defining a graph where nodes are request types
and arc weights are transition probabilities between request types. For example,
consider a microblog application. A write-intensive workload can be created by
setting high probabilities for writing a post after every other request.
Similarly, a read-intensive workload can be created by setting high
probabilities for reading posts after every other request.

## Workload Configuration
As an example, consider a workload simulating 200 clients making a total of 100
requests per second on average. This workload has 3 request types (`write`,
`read`, and `delete`) and 2 periods with increased throughput: the first surge
doubles the throughput for 10 seconds after 2 minutes and the second surge
multiplies the throughput by 3 for 5 seconds after 3 minutes.
```
sessions: 200             # number of concurrent sessions
throughput: 100           # number of requests to be made per second on average
duration:
  total: 300              # total duration in seconds
  ramp_up: 60             # ramp up time in seconds
  ramp_down: 60           # ramp down time in seconds
surges:
  - start: 120            # (1st burst) start time in seconds
    duration: 10          # (1st burst) duration in seconds
    intensity: 2          # (1st burst) value to multiply the throughput
  - start: 180            # (2nd burst) start time in seconds
    duration: 5           # (2nd burst) duration in seconds
    intensity: 3          # (2nd burst) value to multiply the throughput
request_graph:
  main:
    write: 1.0            # probability of writing first
    read: 0               # probability of reading first
    delete: 0             # probability of deleting first
  write:
    read: .5              # probability of reading after writing
    delete: .5            # probability of deleting after writing
  read:
    read: .1              # probability of reading after reading
    delete: .9            # probability of deleting after reading
  delete:
    read: .3              # probability of reading after deleting
    delete: .7            # probability of deleting after deleting
```

## Session Implementation (Python 3)
Requests are made by multiple *sessions* simulating clients. Each session is an
instance of a class that inherits from `ATLoad.Session` and runs on its own
thread. Each request type is implemented by a method of the same name in that
class. Requests also run on separate threads.

As an example, consider this class that implements a session with those 3
request types (`write`, `read`, and `delete`):
```
import argparse
import datetime

import ATLoad


class Session(ATLoad.Session):
  def write(self):
    # Implement write.
    pass

  def read(self):
    # Implement read.
    pass

  def delete(self):
    # Implement delete.
    pass


if __name__ == "__main__":
  # Parse command-line arguments.
  parser = argparse.ArgumentParser(description="Generate a workload")
  parser.add_argument("--workload_conf", required=True, action="store",
      type=str, help="Path to the workload configuration file")
  parser.add_argument("--log", required=True, action="store", type=str,
      help="Path to the log file")
  args = parser.parse_args()
  # Generate workload.
  workload = ATLoad.Workload(args.workload_conf, args.log, Session)
  workload.run()
```

## Developer
- Rodrigo Alves Lima (ral@gatech.edu)

## License
Copyright (C) 2020 Georgia Tech Center for Experimental Research in Computer
Systems.
Licensed under the Apache License 2.0.
