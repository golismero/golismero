window.UsersView = Backbone.View.extend({
	tagName: 'div',
    className: '',
	table:null,
	collection :null,
	events:{
		'click #form-user>.close':'closePanel',
		'click #btnSaveUser':'saveUser',
		'click #users-new': 'createUser',
		'click #users-edit': 'editUser',
		'click #users-remove': 'removeUser',
	},
    initialize: function () {
        this.render();
		this.model.bind('change', this.render, this);
        this.model.bind('remove', this.render, this);
    },

    render: function () {
		if(this.collection ==null){
			this.collection = new Users();
		}
		if(this.table ==null){
			var cols = [{ title: i18n.t("user.table.id"), name: 'id', sorttype: 'number', index: true, },
						   { title: i18n.t("user.table.username"), name: 'username', index: true , filter: true, filterType: 'input'	},
						   { title: i18n.t("user.table.nameandsurname"), name: 'name', index: true, filter: true, filterType: 'input' },
						   { title: i18n.t("user.table.email"), name: 'email', index: true, filter: true, filterType: 'input' },
						   { title: i18n.t("user.table.rol"), name: 'rol', index: true } ];
			this.table = new bbGrid.View({        
				container: $('#usersTable'),    
				autofetch:true,				
				rows:10,
				rowList:[10,20,50],
				multiselect:true,
				collection: this.collection,
				colModel: cols
			});	
		}
		$(this.el).html(this.template({list:this.model.toJSON()}));
		$(this.el).find("#usersTable").html(this.table.el);
		$(this.el).i18n();
		//this.activateEvents();
        return this;
    },
	
	
	/*activateEvents: function(){
		$(this.el).find("#form-user > .close").click(function(){app.usersView.closePanel();});
		$(this.el).find("#btnSaveUser").click(function(){app.usersView.saveUser()});
	},*/
	
	closePanel: function(){
		$(this.el).find("#form-user").addClass("hide").removeClass("show");
	},
	
	saveUser: function(){
		alert("guardado");
		this.closePanel();
	},
	//resetea, obtiene los datos(si es una edicion) y muestra el formulario
	resetAndShowForm: function(model)
	{	
		if(model){
			$("#username").val(model.get("username"));
			$("#email").val(model.get("email"));
			$("#name").val(model.get("name"));
			$("#form-user legend:first").html(i18n.t("user.form.editUser"));
		}else{
			$("#form-profile legend:first").html(i18n.t("profile.form.createUser"));
		}
		$("#form-user").removeClass("hide").addClass("show");		
		utils.scrollToTop();
	},
	editUser: function() {
		var models = this.table.getSelectedModels();
		if(models!=null && models.length==1){
			this.resetAndShowForm(models[0]);
		}else{
			window.alert("Debes seleccionar un usuario");
		}
				
	},	
	createUser: function() {
		this.resetAndShowForm();		
	},
	
	removeUser: function() {
		var models = this.table.getSelectedModels();
		if(models){
			user = this.collection.get(models[0].get("id"));
			this.collection.remove(user);			
		}else{
			window.alert("Debes seleccionar uno o más usuarios");
		}		
	}
});

