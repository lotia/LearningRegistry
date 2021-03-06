import logging, json
from lr.lib.harvest import harvest
import lr.lib.helpers as helpers
import iso8601
from datetime import datetime
from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect
from pylons.decorators import rest
from lr.lib.base import BaseController, render
import lr.lib.helpers
log = logging.getLogger(__name__)
import ast
class HarvestController(BaseController):
    """REST Controller styled on the Atom Publishing Protocol"""
    # To properly map this controller, ensure your config/routing.py
    # file has a resource setup:
    #     map.resource('harvest', 'harvest')
    def __parse_date(self,date):
        last_update_date = iso8601.parse_date(date)
        last_update = helpers.convertToISO8601UTC(last_update_date)    
        return last_update
    def harvest(self, params, body, verb):
        h = harvest()
        def getrecord():
          data = self.get_base_response(verb,body)
          by_doc_ID = params.has_key('by_doc_ID') and ast.literal_eval(str(params['by_doc_ID']))
          by_resource_ID = params.has_key('by_resource_ID') and ast.literal_eval(str(params['by_resource_ID']))
          if not params.has_key('request_id'):
            data['OK'] = False
            data['error'] = 'badArgument'
            return json.dumps(data)
          if by_doc_ID and by_resource_ID:
            data['OK'] = False
            data['error'] = 'badArgument'
            return json.dumps(data)

          request_id = params['request_id']
          if by_doc_ID:
            records = map(lambda doc: {'record':{"header":{'identifier':doc.id, 'datestamp':helpers.convertToISO8601Zformat(datetime.today()),'status':'active'}},'resource_data':doc},[h.get_record(request_id)])
          else:
            records = map(lambda doc: {'record':{"header":{'identifier':doc.id, 'datestamp':helpers.convertToISO8601Zformat(datetime.today()),'status':'active'}},'resource_data':doc},h.get_records_by_resource(request_id))
          data['getrecord'] ={
            'record': records
            }
          return json.dumps(data)
        def listidentifiers():
            return self.list_identifiers(h,body,params,verb)            
        def listrecords():
            return self.list_records(h,body,params,verb)
        def identify():
            data = self.get_base_response(verb,body)
            data['identify']={
                                    'node_id':        'string',
                                    'repositoryName':    'string',
                                    'baseURL':        'string',
                                    'protocolVersion':    '2.0',
                                    'service_version':    'string',
                                    'earliestDatestamp':    'string',
                                    'deletedRecord':    'string',
                                    'granularity':        'string',
                                    'adminEmail':        'string'
                                 }
            return json.dumps(data)
        def listmetadataformats():
            data = self.get_base_response(verb,body)
            data['listmetadataformats']=h.list_metadata_formats()
            return json.dumps(data)
        def listsets():
            data = self.get_base_response(verb,body)
            data['OK']=False
            data['error']='noSetHierarchy'
            return json.dumps(data)
        switch = {
                    'getrecord':getrecord,
                    'listrecords':listrecords,
                    'listidentifiers':listidentifiers,
                    'identify': identify,
                    'listmetadataformats': listmetadataformats,                   
                    'listsets': listsets
                 }
        return switch[verb]()
    def _test_time_params(self, params):
        
        if not params.has_key('from'):
            from_date = self.__parse_date('1990-10-10 12:12:12.0Z')
        else:
            from_date = self.__parse_date(params['from'])
        if not params.has_key('until'):
            until_date = self.__parse_date(datetime.utcnow().isoformat()+ "Z")
        else:
            until_date = self.__parse_date(params['until'])
        return from_date,until_date         
    def list_records(self, h , body , params, verb = 'GET' ):                
        data = self.get_base_response(verb,body)
        if params.has_key('from'):
            data['request']['from'] = params['from']
        if params.has_key('until'):
            data['request']['until'] = params['until']
        from_date, until_date = self._test_time_params(params)
        data['listrecords'] =  []
        base_response =  json.dumps(data).split('[')
        yield base_response[0] +'['
        def debug_map(doc):
            data ={'record':{"header":{'identifier':doc.id, 'datestamp':helpers.convertToISO8601Zformat(datetime.today()),'status':'active'},'resource_data':doc}}
            return data
        if from_date > until_date:
          data['OK'] = False
          data['error'] = 'badArgument'
        else:
            first = True
            for doc in h.list_records(from_date,until_date):                        
                if not first:
                    yield ','
                first = False
                yield json.dumps(debug_map(doc))
        yield base_response[1]

    def list_identifiers(self,h,body ,params, verb = 'GET'):        
        data = self.get_base_response(verb,body)
        if params.has_key('from'):
            data['request']['from'] = params['from']
        if params.has_key('until'):
            data['request']['until'] = params['until']
        from_date, until_date = self._test_time_params(params)
        data['listidentifiers'] =  []
        base_response =  json.dumps(data).split('[')
        yield base_response[0] +'['
        first = True;
        for id in h.list_identifiers(from_date,until_date):
            if not first:
                yield ','
            first = False            
            return_value = {"header":{'identifier':id, 'datestamp':helpers.convertToISO8601Zformat(datetime.today()) ,'status':'active'}}
            yield json.dumps(return_value)
        yield base_response[1]
        

    def get_base_response(self, verb, body):
      return {
               'OK':True,
               'error':'',
               'responseDate':helpers.convertToISO8601Zformat(datetime.today()),
               'request':{
                 'verb':verb,
                 'HTTP_request': body
                 }    
              }


    def index(self, format='html'):
        """GET /harvest: All items in the collection"""
        abort(405,'Method not allowed')

    def create(self):
        """POST /harvest: Create a new item"""
        abort(405,'Method not allowed')

    def new(self, format='html'):
        """GET /harvest/new: Form to create a new item"""
        abort(405,'Method not allowed')
        # url('new_harvest')

    def update(self, id):
        """PUT /harvest/id: Update an existing item"""
        abort(405,'Method not allowed')
    def delete(self, id):
        """DELETE /harvest/id: Delete an existing item"""
        abort(405,'Method not allowed')
    def show(self, id, format='html'):
        """GET /harvest/id: Show a specific item"""
        return self.harvest(request.params,request.body,id)
    def edit(self, id, format='html'):
        """GET /harvest/id/edit: Form to edit an existing item"""
        abort(405,'Method not allowed')

    #code below is to allow posting to /harvest/VERB
    #as REST uses POST only for creating, posting to an existing doc isn't allowed
    @rest.dispatch_on(POST='create_getrecord')
    def getrecord(self):
       """getrecord"""
    def create_getrecord(self):     
        post_data = json.loads(request.body)      
        return self.harvest(post_data,request.body,'getrecord')

    @rest.dispatch_on(POST='create_listrecords')
    def listrecords(self):
       """listrecords"""
       log.debug('test')
    def create_listrecords(self):
       params = json.loads(request.body)       
       return self.harvest(params,request.body,'listrecords')

    @rest.dispatch_on(POST='create_listidentifiers')
    def listidentifiers(self):
       """listidentifiers"""
       log.debug('test')
    def create_listidentifiers(self):
       params = json.loads(request.body)       
       return self.harvest(params,request.body,'listidentifiers')

    @rest.dispatch_on(POST='create_identify')
    def identify(self):
       """identify"""
       log.debug('test')
    def create_identify(self):       
       return self.harvest(None,request.body,'identify')

    @rest.dispatch_on(POST='create_listmetadataformats')
    def listmetadataformats(self):
       """listmetadataformats"""
    def create_listmetadataformats(self):      
       return self.harvest(None,request.body,'listmetadataformats')

    @rest.dispatch_on(POST='create_listsets')
    def listsets(self):
        """listsets"""
    def create_listsets(self):
       return self.harvest(None,request.body,'listsets')

