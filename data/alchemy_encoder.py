from sqlalchemy.ext.declarative import DeclarativeMeta
import json
import datetime
import time


class AlchemyEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj.__class__, DeclarativeMeta):
            # an SQLAlchemy class
            fields = {}
            for field in [x for x in dir(obj) if not x.startswith('_')
                                                 and x not in ['metadata', 'query', 'query_class']]:
                data = obj.__getattribute__(field)
                if isinstance(data, datetime.date):
                    data = int(time.mktime(data.timetuple()))
                try:
                    json.dumps(data)  # this will fail on non-encodable values, like other classes
                    fields[field] = data
                except TypeError:
                    fields[field] = None
            # a json-encodable dict
            return fields

        return json.JSONEncoder.default(self, obj)
