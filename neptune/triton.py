import neptune
import toml
import os,sys
import numpy as np
import simplejson as json
import time
import tailer
import neptune

class Triton:

   def __init__(self,watch_path,island,namespace,proj_name):

       self.session_config_path = ""
       self.config_toml=""
       self.log_path = watch_path
       self.island_num=island
       self.exp_params={}
       self.exp_pqn=namespace+"/"+proj_name
       self.experiment=""
       self.watchlist=["best","mean","champion"]

   
   def read_toml(self,path):

      self.config_toml = toml.load(path)

   def read_json_log(self,path):

      with open(path) as log:
         jl=json.load(log)
      return jl

   def build_json_experiment(self):
      
      _exp_config = self.config_toml
      
      #This is a bit messy, but more literate, IMO
  
      _exp_params={'num_islands': _exp_config['num_islands'],'mutation_rate': _exp_config['mutation_rate'],
                 'mutation_exponent': _exp_config['mutation_exponent'],
                 'crossover_period': _exp_config['crossover_period'],
                 'crossover_rate': _exp_config['crossover_rate'],
                 'max_init_len': _exp_config['max_init_len'],
                 'min_init_len': _exp_config['min_init_len'],
                 'pop_size': _exp_config['pop_size'],
                 'max_length': _exp_config['max_length']
                 }
    
      _exp_json=read_json_log(json_path)
      _exp_name=exp_json['chromosome']['name']
      _exp_desc=str(exp_json['tag'])
      
i     neptune.init(self.exp_pqn,api_token=None) 

      self.experiment=neptune.create_experiment(name=_exp_name,params=_exp_params)

   def build_csv_experiment(self):
      _exp_config = self.config_toml
      exp_number=1

      _exp_params={'num_islands': _exp_config['num_islands'],'mutation_rate': _exp_config['mutation_rate'],
                  'mutation_exponent': _exp_config['mutation_exponent'],
                  'crossover_period': _exp_config['crossover_period'],
                  'crossover_rate': _exp_config['crossover_rate'],
                  'max_init_len': _exp_config['max_init_len'],
                  'min_init_len': _exp_config['min_init_len'],
                  'pop_size': _exp_config['pop_size'],
                  'max_length': _exp_config['max_length']
                  }

      #_exp_name=_exp_config['population_name']
      _exp_name="zygapoph-fenestra-squamate-condyl"

      neptune.init(self.exp_pqn,api_token=None) 
      self.experiment=neptune.create_experiment(name=_exp_name,params=_exp_params)
      print(f" Created experiment {_exp_name} in {self.exp_pqn}")
      
   def get_session(self):
 
      return Session.with_default_backend(api_token=None)

   def get_experiment(self):

      return self.experiment 

   def get_experiment_context(self): 
       
       _session = Session.with_default_backend(api_token=None)
       _project = _session.get_project(self.exp_pqn)
       _exp = _project.get_experiments(id=self.exp_name)[0]

       return tuple(_session,_project,_exp)
 
   def log_stats_to_experiment(self,logtype,names,stats,path,island):
  
      for s in range(0,len(stats)):
         #metric_num=str(s)
         #metric_name=str("metric_"+metric_num)
         metric_name=str(island+"_"+logtype+"_"+names[s])
         self.experiment.log_metric(metric_name,stats[s])   
