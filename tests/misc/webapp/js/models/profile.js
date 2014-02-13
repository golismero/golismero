Profile = Backbone.Model.extend({
	url: "/test/profiles.json",
    defaults: {
        name: ''
    }
    
});

Profiles = Backbone.Collection.extend({
	url: "/test/profiles.json",
    model: Profile,	
	parse : function(response){
		return response;  
   }    
});