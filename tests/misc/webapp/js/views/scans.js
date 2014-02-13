window.ScansView = Backbone.View.extend({
	tagName: 'div',
    className: '',
	table:null,
	collection :null,
    initialize: function () {
        this.render();
		
    },

    render: function () {
				
		if(this.collection ==null){
			this.collection = new Scans();
		}
		if(this.table ==null){
			var cols = [{ title: i18n.t("scans.table.id"), name: 'id', sorttype: 'number', index: true, },
						   { title: i18n.t("scans.table.name"), name: 'name', index: true , filter: true, filterType: 'input'	},
						   { title: i18n.t("scans.table.status"), name: 'status', index: true, filter: true, filterType: 'select' },
						   { title: i18n.t("scans.table.target"), name: 'targets', index: true, actions:this.renderTarget,filter: true, filterType:'input'},
						   {title: i18n.t("scans.table.progress"), name: 'progress', index: true, actions:this.renderProgress}	
						];
			this.table = new bbGrid.View({        
				container: $('#scansTable'),    
				autofetch:true,
				subgrid:true,
				subgridAccordion: true,    
				onRowExpanded: function($el, rowid) {
					$($el).html("Aqui va a ir el expander");
				},
				rows:10,
				rowList:[10,20,50],
				multiselect:true,
				collection: this.collection,
				colModel: cols
			});	
		}
		$(this.el).html(this.template({list:this.model.toJSON()}));
		$(this.el).find("#scansTable").html(this.table.el);
		$(this.el).i18n();
		//this.activateEvents();
        return this;
    },

	renderTarget: function(id, model){
		var targets = model.targets[0];
		for(var i = 1; i < model.targets.length; i++)
		{
			targets = targets+ "," + model.targets[i];
		}
		return targets;
	},	

	renderProgress: function(id, model){
		return "<div class=\"progress progress-striped active\"><div class=\"bar\" style=\"width:"+model.progress+"%\"></div></div>";
	},
});

