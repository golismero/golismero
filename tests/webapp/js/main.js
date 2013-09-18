var AppRouter = Backbone.Router.extend({

    routes: {
        ""                  	: "home",
		"home"					: "home",
		"users"					: "users",
        "users/:userid"			: "users",
		"scans"					: "scans"/*,
        "profiles"	        	: "profiles",
        "profiles/:profileid" 	: "profiles"*/
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
        if (!this.usersView) {
			var userList = new Users();
			var _contextRooter = this;
			userList.fetch({success: function(){
				_contextRooter.usersView = new UsersView({model:userList});
				$('#principal').html(_contextRooter.usersView.el);
				
			},error:function(p, error){
				alert("Error " + p);
				}
			});
            		
        }else{
			$('#principal').html(this.usersView.el);
			this.usersView.activateEvents();
		}
        this.sidebarView.selectMenuItem('users-menu');
    },
	scans: function (id) {	
        if (!this.scansView) {
			var scanList = new Scans();
			var _contextRooter = this;
			scanList.fetch({success: function(){
				_contextRooter.scansView = new ScansView({model:scanList});
				$('#principal').html(_contextRooter.scansView.el);
				
			},error:function(p, error){
				alert("Error " + p);
				}
			});
            		
        }else{
			$('#principal').html(this.scansView.el);
		}
        this.sidebarView.selectMenuItem('scans-menu');
    }
});

utils.loadTemplate(['SidebarView', 'HomeView', 'UsersView', 'ScansView'], function() {
	i18n.init(function(t) {
		$("body").i18n();	 
	});
    window.app = new AppRouter();
    Backbone.history.start();	 
});