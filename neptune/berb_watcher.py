import neptune,triton
import toml
import os,sys
import numpy as np
import pandas as pd
import simplejson as json
import time
import tailer
import argparse
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

write_count=0
current_epoch=0
island="island_0"
log_metrics={}
log_state={}
log_type=["mean","best","champion"]

def on_created(event):
   if event.is_directory:
   #config-0 at the top-level of a log tree indicates an experiment
   #has started to run. Call build_experiment to create it in neptune
      if event.src_path.endswith("config-0"):
         print(f"{event.src_path} has been created")
         session_config_path = event.src_path+"/config.toml"
         triton.read_toml(session_config_path)
         triton.build_experiment()

   #csv files have stats we are interested in 
   if event.src_path.endswith("csv") and island in event.src_path : 
      logname = str(event.src_path.split("/")[-1])
      log_state[logname]=0
      print(f"log_state is now: {log_state}")
      print(f"{event.src_path} has been created")
          

def on_modified(event):
   #if the file that's been modified is a csv file 
   #we have some logging work to do 
 
   #Scope-limit csv files we care about for now 
   if event.src_path.endswith(".csv") and island in event.src_path:
      print(f"{event.src_path} has been modified")
      logpath = event.src_path
      logname=str(event.src_path.split("/")[-1])
      print(log_state)
      print(logname)
 
   #if this is the first time this file has been read, get the column names to attach to the neptune log_metrics
      if log_state[logname] == 0:
         pdlog=pd.read_csv(logpath)
         log_metrics[logname]=list(pdlog.columns)
         log_state[logname] = 1

      lt = [t for t in log_type if t in logpath]
         
      if len(lt) == 1:
         logline=tailer.tail(open(logpath),1)[0]
         stats=[float(l) for l in logline.strip().split(",")]
         triton.log_stats_to_experiment(lt[0],log_metrics[logname],stats,logpath)

if __name__ == "__main__":
    # create the event handler
    patterns="*.csv"
    ignore_patterns = ["^./.git"]
    ignore_directories = False
    case_sensitive = True
#    my_event_handler = RegexMatchingEventHandler(ignore_regexes=ignore_patterns, ignore_directories=ignore_directories, case_sensitive=case_sensitive)
    my_event_handler = PatternMatchingEventHandler(patterns, ignore_patterns, ignore_directories, case_sensitive)

    my_event_handler.on_created = on_created
    my_event_handler.on_modified = on_modified

    # create an observer
    path = "/home/armadilo/logs/berbalang/Roper/Tournament"
    go_recursively = True
    my_observer = Observer()
    my_observer.schedule(my_event_handler, path, recursive=go_recursively)

    triton = triton.Triton(path,0,"special-circumstances","sandbox")

    my_observer.start()
    try:
        while True:
            time.sleep(5)
    except:
        my_observer.stop()
        print("Observer Stopped")
    my_observer.join()
