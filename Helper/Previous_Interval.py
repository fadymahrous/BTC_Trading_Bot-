import re
import pandas as pd
from datetime import timedelta



class Previous_Interval:
    def __init__(self):
        self.conversion_factor= {'s':1/60,'m':1,'h':60,'d':1440,'w':10080,'M':43200}
        self.unit_to_time_frequency_alias = {'s':'S','m':'min','h':'h','d':'D','w':'W-MON','M':'M'}
    
    def get_previous_floored_timestamp(self,interval:str):
        match = re.match(r"(\d+)([smhdwM])", interval)
        if not match:
            return None
        value, unit = match.groups()
        interval_multiply_min=int(value)*self.conversion_factor[unit]
        minutes = timedelta(minutes=interval_multiply_min)

        flooring_string=str(value)+self.unit_to_time_frequency_alias[unit]
        result = (pd.Timestamp.utcnow() - minutes).floor(flooring_string)

        return result

if __name__=='__main__':
    testing=Previous_Interval()
    prev_time=testing.get_previous_floored_timestamp('5m')
    print(prev_time)