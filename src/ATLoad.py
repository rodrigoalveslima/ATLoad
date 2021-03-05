# Copyright (C) 2020 Georgia Tech Center for Experimental Research in Computer
# Systems

import collections
import random
import threading
import time

import numpy
import yaml


class Session:
  def _run(self, start_time, start_at, stop_at, request_graph, surges,
      throughput):
    self._logs = []
    self._request_graph = request_graph
    # Wait to start.
    while time.time() < start_at:
      time.sleep(0.1)
    # Session loop.
    request = "main"
    while time.time() < stop_at:
      second = int(time.time() - start_time)
      surge_intensity = surges[second] if second < len(surges) else 1
      n = numpy.random.poisson(throughput)
      if n > 0:
        for i in range(n):
          time.sleep(1 / (n * surge_intensity))
          request = self._select_next_request(request)
          threading.Thread(target=getattr(self, request)).start()
      else:
        time.sleep(1 / surge_intensity)

  def _select_next_request(self, request):
    r = random.uniform(0, sum(self._request_graph[request].values()))
    for request, weight in self._request_graph[request].items():
      if r < weight:
        return request
      r -= weight

  def _log(self, message):
    self._logs.append((time.time(), message))


class Workload:
  def __init__(self, conf_filename, log_filename, session_cls, *args):
    with open(conf_filename) as conf_file:
      conf = yaml.safe_load(conf_file)
    self._log_filename = log_filename
    self._session_cls = session_cls
    self._args = args
    self._sessions = conf["sessions"]
    self._throughput = conf["throughput"]
    self._duration = conf["duration"]
    self._request_graph = dict([(request, collections.OrderedDict(
        conf["request_graph"][request])) for request in conf["request_graph"]])
    self._surges = [1 for i in range(self._duration["total"])]
    for surge in conf["surges"]:
      for second in range(surge["start"], surge["start"] + surge["duration"]):
        self._surges[second] = surge["intensity"]

  def run(self):
    start_time = time.time()
    # Initialize sessions.
    sessions = [self._session_cls(*self._args) for i in range(self._sessions)]
    # Run each session in its own thread.
    threads = [threading.Thread(target=session._run, args=[
        start_time,
        start_time + self._duration["ramp_up"] * (i / self._sessions),
        start_time + self._duration["total"] -
            self._duration["ramp_down"] * (i / self._sessions),
        self._request_graph,
        self._surges,
        self._throughput / self._sessions])
        for (i, session) in enumerate(sessions)]
    for thread in threads:
      thread.start()
    # Wait until all sessions are finished.
    for thread in threads:
      thread.join()
    # Flush session logs in chronological order.
    logs = []
    while True:
      session_i = None
      for (i, session) in enumerate(sessions):
        if session._logs and (session_i is None or
            session._logs[0][0] < sessions[session_i]._logs[0][0]):
          session_i = i
      if session_i is None:
        break
      logs.append(sessions[session_i]._logs.pop(0)[1])
    with open(self._log_filename, 'w') as log_file:
      for (i, log) in enumerate(logs):
        if i:
          log_file.write("\n")
        log_file.write(log)
