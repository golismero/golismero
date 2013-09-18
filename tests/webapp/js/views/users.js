window.UsersView = Backbone.View.extend({
	tagName: 'div',
    className: '',
		
	
    initialize: function () {
        this.render();
		this.model.bind('change', this.render, this);
        this.model.bind('remove', this.render, this);
    },

    render: function () {
		$(this.el).html(this.template({list:this.model.toJSON()}));
		$(this.el).i18n();
		this.activateEvents();
        return this;
    },
	
	activateEvents: function(){
		$(this.el).find("#form-user > .close").click(function(){app.usersView.closePanel();});
		$(this.el).find("#btnSaveUser").click(function(){app.usersView.saveUser()});
	},
	
	closePanel: function(){
		$(this.el).find("#form-user").addClass("hide").removeClass("show");
	},
	
	saveUser: function(){
		alert("guardado");
		this.closePanel();
	},
	//resetea, obtiene los datos(si es una edicion) y muestra el formulario
	resetAndShowForm: function(id)
	{
		$("#form-user").removeClass("hide").addClass("show");
		$("#form-user legend:first").html(i18n.t("user.form.editUser"));
		
		utils.scrollToTop();
	},
	editUser: function(id) {
		this.resetAndShowForm(id);
				
	},	
	createUser: function() {
		this.resetAndShowForm();		
	},
	
	removeUser: function(id) {
		user = this.model.get(id);
		this.model.remove(user);
	}
});

