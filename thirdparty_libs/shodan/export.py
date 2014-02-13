import sys
from datetime import datetime
from xml.sax import make_parser, handler

# Type conversion helper functions
def parse_date(args):
    return datetime.strptime(args, '%d.%m.%Y')


class ExportSaxParser(handler.ContentHandler):
    """Parses Shodan's export XML file and executes the callback for each
    entry.
    """
    
    # Callbacks
    entry_cb = None
    
    # Keep track of where we're at
    _in_host = False
    _in_data = False
    _host = None
    _data = u''
    
    # Conversion schemas
    _host_attr_schema = {
        'port': int,
        'updated': parse_date,
    }
    
    def __init__(self, entry_cb=None):
        # Define the callbacks
        self.entry_cb = entry_cb
    
    # ContentHandler methods
    
    def startElement(self, name, attrs):
        if name =='host':
            # Extract all the attribute information
            self._host = {}
            for (name, value) in attrs.items():
                # Convert the field to a native type if it's defined in the schema
                self._host[name] = self._host_attr_schema.get(name, lambda x: x)(value)
            
            # Update the state machine
            self._in_host = True
        elif name == 'data':
            self._in_data = True
            self._data = u''
    
    def endElement(self, name):
        if name == 'host':
            # Execute the callback
            self.entry_cb(self._host)
            
            # Update the state machine
            self._in_host = False
        elif name == 'data':
            self._host['data'] = self._data
            
            self._in_data = False
    
    def characters(self, content):
        if self._in_data:
            self._data += content
            
    
class ExportParser(object):
    
    entry_cb = None
    
    def __init__(self, entry_cb=None):
        self.entry_cb = entry_cb
    
    def parse(self, filename):
        parser = make_parser()
        parser.setContentHandler(ExportSaxParser(self.entry_cb))
        parser.parse(filename)


if __name__ == '__main__':
    def test_cb(entry):
        print entry
    
    import sys
    parser = ExportParser(test_cb)
    parser.parse(sys.argv[1])

