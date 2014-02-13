var AppRouter = Backbone.Router.extend({

    routes: {
        ""                  	: "home",
		"home"					: "home",
		"users"					: "users",
        "users/:userid"			: "users",
		"scans"					: "scans",
        "profiles"	        	: "profiles",
        "profiles/:profileid" 	: "profiles"
    },

    initialize: function () {
        this.sidebarView = new SidebarView();
        $('#sidebar').html(this.sidebarView.el);
		//inicializamos el sidebar
		sidebar();
    },

    home: function (id) {
        if (!this.homeView) {
            this.homeView = new HomeView();
        }
        $('#principal').html(this.homeView.el);
		
        this.sidebarView.selectMenuItem('home-menu');
    },
	users: function (id) {	
        //if (!this.usersView) {
			
			if(!this.userList ){
				this.userList = new Users();
			}
			var userList = this.userList;
			var _contextRooter = this;
			var data = {
				startAt : 2,
				count : 10 
			};
			_contextRooter.usersView = new UsersView({model:userList});
			$('#principal').html(_contextRooter.usersView.el);
			/*userList.fetch({data:data, success: function(){
				_contextRooter.usersView = new UsersView({model:userList});
				$('#principal').html(_contextRooter.usersView.el);
				
			},error:function(p, error){
				alert("Error " + p);
				}
			});*/
            		
        /*}else{
			$('#principal').html(this.usersView.el);
			this.usersView.activateEvents();
		}*/
        this.sidebarView.selectMenuItem('users-menu');
    },
	scans: function (id) {	
        //if (!this.scansView) {
			if(!this.scanList){
				this.scanList = new Scans();
			}
			var scanList = this.scanList;
			this.scansView = new ScansView({model:scanList});
			/*scanList.fetch({success: function(){
				_contextRooter.scansView = new ScansView({model:scanList});
				$('#principal').html(_contextRooter.scansView.el);
				
			},error:function(p, error){
				alert("Error " + p);
				}
			});*/
            		
        //}else{
			$('#principal').html(this.scansView.el);
		//}
        this.sidebarView.selectMenuItem('scans-menu');
    },
	
	profiles: function (id){
		if(!this.profileList ){
			this.profileList = new Profiles();
		}
		var profileList = this.profileList;
		this.profilesView = new ProfilesView({model:profileList});
		$('#principal').html(this.profilesView.el);
			
        this.sidebarView.selectMenuItem('profiles-menu');
	}
});

utils.loadTemplate(['SidebarView', 'HomeView', 'UsersView', 'ScansView', 'ProfilesView'], function() {
	i18n.init(function(t) {
		$("body").i18n();	
		window.app = new AppRouter();
		Backbone.history.start();		
	});
    	 
});