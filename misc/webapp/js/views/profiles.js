window.ProfilesView = Backbone.View.extend({
	tagName: 'div',
    className: '',
	table:null,
	collection :null,
	events:{
		'click #form-profile>.close':'closePanel',
		'click #btnSaveProfile':'saveProfile',
		'click #profiles-remove': 'removeProfile',
		'click #profiles-new': 'createProfile',
		'click #profiles-edit': 'editProfile'
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
			var cols = [{ title: i18n.t("profile.table.id"), name: 'id', sorttype: 'number', index: true, },
						   { title: i18n.t("profile.table.name"), name: 'name', index: true , filter: true, filterType: 'input'	},
						];
			this.table = new bbGrid.View({        
				container: $('#profilesTable'),    
				autofetch:true,				
				rows:10,
				rowList:[10,20,50],
				multiselect:true,
				collection: this.collection,
				colModel: cols
			});	
		}
		$(this.el).html(this.template({list:this.model.toJSON()}));
		$(this.el).find("#profilesTable").html(this.table.el);
		$(this.el).i18n();
		//this.activateEvents();
        return this;
    },
	
	
	closePanel: function(){
		$(this.el).find("#form-profile").addClass("hide").removeClass("show");
	},
	
	saveUser: function(){
		alert("guardado");
		this.closePanel();
	},
	//resetea, obtiene los datos(si es una edicion) y muestra el formulario
	resetAndShowForm: function(model)
	{	
		if(model){
			$("#name").val(model.get("name"));
			$("#form-profile legend:first").html(i18n.t("profile.form.editProfile"));
		}else{
			$("#form-profile legend:first").html(i18n.t("profile.form.createProfile"));
		}
		$("#form-profile").removeClass("hide").addClass("show");
		
		utils.scrollToTop();
	},
	editProfile: function() {
		var models = this.table.getSelectedModels();
		if(models!=null && models.length==1){
			this.resetAndShowForm(models[0]);
		}else{
			window.alert("Debes seleccionar un perfil");
		}
				
	},	
	createProfile: function() {
		this.resetAndShowForm();		
	},
	
	removeProfile: function(id) {
		profile = this.model.get(id);
		this.model.remove(profile);
	}
});

