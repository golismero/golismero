Scan = Backbone.Model.extend({
	url: "/test/escaneos.json",
    defaults: {
        targets: [],
        name: '',
		profile: new Profile(),
		progress:'',
		status:'',
		creationDate: new Date()
    }
    
});

Scans = Backbone.Collection.extend({
	url: "/test/escaneos.json",
    model: Scan,
	parse : function(response){
		return response;  
   }    
});