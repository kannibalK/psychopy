# -*- coding: utf-8 -*-
from __future__ import division
"""
ioHub DataStore to Pandas DataFrame Module with Event Filtering Support

.. file: psychopy.iohub.datastore.pandas.__init__.py

Copyright (C) 2012-2013 iSolver Software Solutions
Distributed under the terms of the GNU General Public License 
(GPL version 3 or any later version).

.. moduleauthor:: Sol Simpson <sol@isolver-software.com> and
                  Pierce Edmiston <pierce.edmiston@gmail.com>
"""

import numpy as np
import pandas as pd
#import matplotlib as mpl
#import matplotlib.pyplot as plt

from interestarea import Polygon

#from interestperiod import InterestPeriodDefinition

# TODO Replace with EventConstants.getConstants()
# when code change is added to iohub source.
def getEventConstants():
    from psychopy.iohub import EventConstants
    return EventConstants._names

                  
class ioHubPandasDataView(object):
    def __init__(self,datastore_file):
        self._hdf_store=pd.HDFStore(datastore_file)        
        self._event_constants=None
        self._event_table_info=None
        self._experiment_meta_data=None
        self._session_meta_data=None
        self._condition_variables=None

        self._event_data_by_type=dict()
        self._all_events=None
        
    @property
    def hdf_store(self):
        """
        hdf_store
        """
        return self._hdf_store

    @property
    def event_constants(self):
        """
        event_constants
        """
        if self._event_constants is None:
            self._event_constants=getEventConstants()
        return self._event_constants
        
    @property
    def event_table_info(self):
        """event_table_info property."""
        if self._event_table_info is None:
            self._event_table_info=self._hdf_store.select('class_table_mapping', columns=['class_id','class_name','table_path'])
            self._event_table_info['class_id']=self._event_table_info['class_id'].map(self.event_constants)            
            self._event_table_info.set_index('class_id',inplace=True)
        return self._event_table_info

    @property
    def experiment_meta_data(self):
        """experiment_meta_data property."""
        if self._experiment_meta_data is None:
            self._experiment_meta_data=self._hdf_store.select('/data_collection/experiment_meta_data')
            self._experiment_meta_data.replace('', np.nan,inplace=True)
            self._experiment_meta_data.set_index(['experiment_id','code'],inplace=True)             
        return self._experiment_meta_data

    @property
    def session_meta_data(self):
        """session_meta_data property."""
        if self._session_meta_data is None:
            self._session_meta_data=self._hdf_store.select('/data_collection/session_meta_data')
            self._session_meta_data.replace('', np.nan,inplace=True)
            self._session_meta_data.set_index(['session_id'],inplace=True)
        return self._session_meta_data

    @property
    def condition_variables(self):
        """condition_variables property."""
        experiment_index_name='experiment_id'
        session_index_name='session_id'
        if self._condition_variables is None:
            cv_table_proto='/data_collection/condition_variables/EXP_CV_%d'
            for experiment_id in self.experiment_meta_data.index.levels[0].values:
                exp_cv=cv_table_proto%experiment_id
                try:            
                    cv_df=self._hdf_store.select(exp_cv)
                    
                    # check that the cv table has a experiment index 
                    # and session index column and that each is named
                    # as expected. Correct any issues as much as possible.
                    #
                    cv_cols=cv_df.columns.values.tolist()
                    reset_column_names=False
                    exp_id_col=None
                    sess_id_col=None
                    for i,c in enumerate(cv_cols):
                        if exp_id_col is None and c.lower()==experiment_index_name:
                            if c != experiment_index_name:
                                # rename found exp col to match 
                                # standard exp col label
                                print
                                print '** Renaming condition_variables column {0} to {1} to match existing experiment index column label'.format(c,experiment_index_name)
                                print
                                cv_cols[i]=experiment_index_name
                                reset_column_names=True
                            exp_id_col=experiment_index_name

                        if sess_id_col is None and c.lower()==session_index_name:
                            # rename found exp col to match 
                            # standard session col label
                            if c != session_index_name:                                
                                print
                                print '** Renaming condition_variables column {0} to {1} to match expected session index column label'.format(c,session_index_name)
                                print
                                cv_cols[i]=session_index_name
                                reset_column_names=True
                            sess_id_col=session_index_name
                    
                    # If the cv df had an exp or sess index label 
                    # /case insensitive/ match, update col names
                    # with standard exp and / or sess index names.
                    if reset_column_names:
                        cv_df.columns=cv_cols
                    
                    # No exp index col was found in the df, create one.
                    if exp_id_col is None:
                        print
                        print '** No experiment index column found. Adding %s column to df with value of %d'%(experiment_index_name,experiment_id)
                        print
                        cv_df[experiment_index_name]=experiment_id
                        
                    # No sess_id_col was found in the df, create one.
                    if sess_id_col is None:
                        print
                        print '** No session index column found. Adding %s column to df with nan values.'%(session_index_name)
                        print
                        cv_df[session_index_name]=np.nan
                        
                    try:
                        cv_df.set_index([experiment_index_name,session_index_name],inplace=True)
                    except Exception, e:
                        print "Could not set index for CV table."
                        print e
                        
                    if self._condition_variables is None:
                        self._condition_variables=cv_df
                        
                    else:
                        self._condition_variables.append(cv_df)
                except Exception, e:
                    print 'Error loading experiment CV: ', e
        return self._condition_variables
        
    @property
    def all_events(self):
        """all_events property."""
        if self._all_events is None:
            self._createGlobalEventData()
        return self._all_events

    def __getattr__(self,n):
        if not self._event_data_by_type.get(n):
            try:
                row=self.event_table_info.ix[n]
                if not row['table_path'].endswith('KeyboardCharEvent'):
                    event_data=self._hdf_store.select(row['table_path'])
                    event_data=event_data[event_data.type == self.event_constants[n]]
                    event_data['type']=n
                    event_data.set_index(['experiment_id','session_id','time'],inplace=True)   
                    event_data.sort_index(inplace=True)
                    event_data.reset_index('time',inplace=True)
                    self._event_data_by_type[n]=event_data
                else:            
                    raise AttributeError(self.__class__.__name__+" does not support "+n)
            except Exception, e:
                raise AttributeError(self.__class__.__name__+" does not have a data frame for "+n)
                raise e
        return self._event_data_by_type[n]

    def _createGlobalEventData(self):
        SKIP_EVENT_TYPES=['KEYBOARD_CHAR','KEYBOARD_KEY','MOUSE_INPUT', 'TOUCH']
        global_event_fields=['time','device_id','event_id','type','device_time',
                             'logged_time','confidence_interval','delay',
                             'filter_id']
                             
        for index,row in self.event_table_info.iterrows():
            if index not in SKIP_EVENT_TYPES:
                event_data=getattr(self,index,None)
                if event_data is None:                    
                    raise AttributeError("_createGlobalEventData:"+index+" event type does not exist.")
                    
                if self._all_events is None:
                    self._all_events=event_data[global_event_fields]                 
                else:
                    self._all_events=pd.concat([self._all_events,event_data[global_event_fields]],axis=0)

        self._all_events.set_index(['time'],append=True,inplace=True)   
        self._all_events.sort_index(inplace=True)
        self._all_events.reset_index('time',inplace=True)
            
    def close(self):
        if self._hdf_store:
            self._hdf_store.close()
            self._hdf_store=None
       
    def __del__(self):
        self._hdf_store=None
        self._event_constants=None
        self._event_table_info=None
        self._experiment_meta_data=None
        self._session_meta_data=None
        self._condition_variables=None
        self._event_data_by_type.clear()
        self._all_events=None